"""Sentinel-2 Statistical API runner for official Azuero Kairós batches."""

from __future__ import annotations

import csv
import json
import math
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, request

from azuero_kairos.cdse_auth import CDSEAuthError, CDSEToken, get_cdse_token
from azuero_kairos.confidence_engine import classify_confidence


STATISTICS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
DEFAULT_AOI_PATH = Path("configs/aoi_corridor_wide_mvp.geojson")
DEFAULT_RAW_JSON_DIR = Path("outputs/raw_json")
DEFAULT_PROCESSED_CSV_PATH = Path("outputs/processed_csv/sentinel2_stats_confidence.csv")
DEFAULT_RESOLUTION_M = 20
DEFAULT_SLEEP_SECONDS = 1.0
DEFAULT_TARGET_EPSG = 32617
MAX_STATISTICAL_GRID_SIDE = 2500
INDEX_SET_NAME = "mndwi_ndti"

OFFICIAL_DATES = (
    "2025-06-02",
    "2025-06-10",
    "2025-06-15",
    "2025-06-30",
    "2025-07-15",
)

PROCESSED_FIELDNAMES = [
    "date",
    "aoi",
    "resolution_m",
    "mndwi_mean",
    "ndti_mean",
    "sampleCount",
    "noDataCount",
    "validPercent",
    "confidence_class",
    "decision",
    "reason",
    "recommended_action",
    "raw_json_path",
    "api_status",
    "api_error",
]

SENTINEL2_EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B03", "B04", "B11", "SCL", "dataMask"]
    }],
    output: [
      {
        id: "indices",
        bands: ["mndwi", "ndti"],
        sampleType: "FLOAT32"
      },
      {
        id: "dataMask",
        bands: 1
      }
    ]
  };
}

function isClearObservation(scl) {
  return scl !== 0 &&
    scl !== 1 &&
    scl !== 2 &&
    scl !== 3 &&
    scl !== 8 &&
    scl !== 9 &&
    scl !== 10 &&
    scl !== 11;
}

function safeIndex(a, b) {
  var denominator = a + b;
  if (denominator === 0) {
    return 0;
  }
  return (a - b) / denominator;
}

function evaluatePixel(sample) {
  var mndwiDenominator = sample.B03 + sample.B11;
  var ndtiDenominator = sample.B04 + sample.B03;
  var valid = sample.dataMask === 1 &&
    isClearObservation(sample.SCL) &&
    mndwiDenominator !== 0 &&
    ndtiDenominator !== 0;

  return {
    indices: [
      safeIndex(sample.B03, sample.B11),
      safeIndex(sample.B04, sample.B03)
    ],
    dataMask: [valid ? 1 : 0]
  };
}
""".strip()


class Sentinel2StatsError(RuntimeError):
    """Raised when a Sentinel-2 Statistical API operation cannot complete."""


@dataclass(frozen=True)
class AoiConfig:
    """AOI geometry and display identifier."""

    name: str
    geometry: dict[str, Any]


@dataclass(frozen=True)
class RequestGridEstimate:
    """Estimated Statistical API grid size for one AOI request."""

    aoi_name: str
    resolution_m: int
    target_epsg: int
    lonlat_bounds: tuple[float, float, float, float]
    metric_bounds: tuple[float, float, float, float]
    width_m: float
    height_m: float
    width_px: int
    height_px: int


def run_official_batch(
    *,
    aoi_path: str | Path = DEFAULT_AOI_PATH,
    dates: Iterable[str] = OFFICIAL_DATES,
    resolution_m: int = DEFAULT_RESOLUTION_M,
    raw_json_dir: str | Path = DEFAULT_RAW_JSON_DIR,
    processed_csv_path: str | Path = DEFAULT_PROCESSED_CSV_PATH,
    sleep_seconds: float = DEFAULT_SLEEP_SECONDS,
    request_timeout_seconds: float = 60.0,
    force: bool = False,
) -> Path:
    """Run the official Sentinel-2 batch and write one processed CSV."""

    rows = run_stats_rows(
        aoi_path=aoi_path,
        dates=dates,
        resolution_m=resolution_m,
        raw_json_dir=raw_json_dir,
        sleep_seconds=sleep_seconds,
        request_timeout_seconds=request_timeout_seconds,
        force=force,
    )

    csv_path = Path(processed_csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_processed_csv(csv_path, rows)
    return csv_path


def run_stats_rows(
    *,
    aoi_path: str | Path = DEFAULT_AOI_PATH,
    dates: Iterable[str] = OFFICIAL_DATES,
    resolution_m: int = DEFAULT_RESOLUTION_M,
    raw_json_dir: str | Path = DEFAULT_RAW_JSON_DIR,
    sleep_seconds: float = DEFAULT_SLEEP_SECONDS,
    request_timeout_seconds: float = 60.0,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Run one Sentinel-2 AOI batch and return processed rows without writing CSV."""

    if resolution_m <= 0:
        raise Sentinel2StatsError("Resolution must be a positive integer.")

    aoi = load_aoi(aoi_path)
    preflight = estimate_request_grid(
        aoi,
        resolution_m=resolution_m,
        target_epsg=DEFAULT_TARGET_EPSG,
    )
    validate_request_grid(preflight)

    raw_dir = Path(raw_json_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    token: CDSEToken | None = None
    auth_error: CDSEAuthError | None = None

    for target_date in dates:
        raw_path = raw_response_path(
            raw_dir,
            target_date=target_date,
            aoi_name=aoi.name,
            resolution_m=resolution_m,
        )

        if raw_path.exists() and not force:
            rows.append(
                row_from_cached_response(
                    raw_path=raw_path,
                    target_date=target_date,
                    aoi_name=aoi.name,
                    resolution_m=resolution_m,
                )
            )
            continue

        if auth_error is not None:
            rows.append(
                error_row(
                    target_date=target_date,
                    aoi_name=aoi.name,
                    resolution_m=resolution_m,
                    raw_path=raw_path,
                    api_error=str(auth_error),
                )
            )
            continue

        if token is None:
            try:
                token = get_cdse_token()
            except CDSEAuthError as exc:
                auth_error = exc
                rows.append(
                    error_row(
                        target_date=target_date,
                        aoi_name=aoi.name,
                        resolution_m=resolution_m,
                        raw_path=raw_path,
                        api_error=str(exc),
                    )
                )
                continue

        try:
            stats_request = build_stats_request(
                geometry=aoi.geometry,
                target_date=target_date,
                resolution_m=resolution_m,
            )
            raw_response = post_stats_request(
                token=token,
                payload=stats_request,
                timeout_seconds=request_timeout_seconds,
            )
            save_raw_response(raw_path, raw_response)
            rows.append(
                processed_row_from_response(
                    raw_response,
                    target_date=target_date,
                    aoi_name=aoi.name,
                    resolution_m=resolution_m,
                    raw_path=raw_path,
                )
            )
        except Sentinel2StatsError as exc:
            rows.append(
                error_row(
                    target_date=target_date,
                    aoi_name=aoi.name,
                    resolution_m=resolution_m,
                    raw_path=raw_path,
                    api_error=str(exc),
                )
            )
        finally:
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    return rows


def load_aoi(path: str | Path) -> AoiConfig:
    """Load the first geometry from a GeoJSON AOI file."""

    aoi_path = Path(path)
    try:
        payload = json.loads(aoi_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise Sentinel2StatsError(f"Could not read AOI file: {aoi_path}") from exc
    except json.JSONDecodeError as exc:
        raise Sentinel2StatsError(f"AOI file is not valid JSON: {aoi_path}") from exc

    geometry: dict[str, Any] | None = None
    raw_name = payload.get("name") or aoi_path.stem

    if payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list) or not features:
            raise Sentinel2StatsError("AOI FeatureCollection does not contain features.")
        feature = features[0]
        if isinstance(feature, dict):
            properties = feature.get("properties", {})
            if isinstance(properties, dict):
                raw_name = properties.get("id") or raw_name
            geometry = feature.get("geometry")
    elif payload.get("type") == "Feature":
        properties = payload.get("properties", {})
        if isinstance(properties, dict):
            raw_name = properties.get("id") or raw_name
        geometry = payload.get("geometry")
    else:
        geometry = payload

    if not isinstance(geometry, dict) or "type" not in geometry:
        raise Sentinel2StatsError("AOI file does not contain a valid GeoJSON geometry.")

    return AoiConfig(name=normalize_aoi_name(str(raw_name)), geometry=geometry)


def estimate_request_grid(
    aoi: AoiConfig,
    *,
    resolution_m: int = DEFAULT_RESOLUTION_M,
    target_epsg: int = DEFAULT_TARGET_EPSG,
) -> RequestGridEstimate:
    """Estimate the Statistical API grid size before making a request."""

    if resolution_m <= 0:
        raise Sentinel2StatsError("Resolution must be a positive integer.")

    lonlat_positions = list(iter_positions(aoi.geometry.get("coordinates")))
    lonlat_bounds = coordinate_bounds(lonlat_positions)
    metric_geometry = transform_geometry_to_epsg(aoi.geometry, target_epsg)
    metric_positions = list(iter_positions(metric_geometry.get("coordinates")))
    metric_bounds = coordinate_bounds(metric_positions)

    min_x, min_y, max_x, max_y = metric_bounds
    width_m = max_x - min_x
    height_m = max_y - min_y

    return RequestGridEstimate(
        aoi_name=aoi.name,
        resolution_m=resolution_m,
        target_epsg=target_epsg,
        lonlat_bounds=lonlat_bounds,
        metric_bounds=metric_bounds,
        width_m=width_m,
        height_m=height_m,
        width_px=math.ceil(width_m / resolution_m),
        height_px=math.ceil(height_m / resolution_m),
    )


def estimate_request_grid_from_path(
    aoi_path: str | Path,
    *,
    resolution_m: int = DEFAULT_RESOLUTION_M,
    target_epsg: int = DEFAULT_TARGET_EPSG,
) -> RequestGridEstimate:
    """Load an AOI and estimate its Statistical API grid size."""

    return estimate_request_grid(
        load_aoi(aoi_path),
        resolution_m=resolution_m,
        target_epsg=target_epsg,
    )


def validate_request_grid(
    estimate: RequestGridEstimate,
    *,
    max_grid_side: int = MAX_STATISTICAL_GRID_SIDE,
) -> None:
    """Fail before the API call if the estimated request grid is too large."""

    if estimate.width_px <= max_grid_side and estimate.height_px <= max_grid_side:
        return

    raise Sentinel2StatsError(
        "AOI/resolution preflight failed: "
        f"{estimate.aoi_name} at {estimate.resolution_m} m estimates "
        f"width={estimate.width_px}, height={estimate.height_px}; "
        f"the Statistical API limit is {max_grid_side} pixels per side. "
        "Use a tighter AOI for the official MVP run. Resolution was not changed automatically."
    )


def format_request_grid_estimate(estimate: RequestGridEstimate) -> str:
    min_lon, min_lat, max_lon, max_lat = estimate.lonlat_bounds
    return (
        "AOI preflight: "
        f"{estimate.aoi_name} | "
        f"lon/lat bounds=({min_lon:.5f}, {min_lat:.5f}, {max_lon:.5f}, {max_lat:.5f}) | "
        f"EPSG:{estimate.target_epsg} grid={estimate.width_px}x{estimate.height_px} px "
        f"at {estimate.resolution_m} m"
    )


def iter_positions(coordinates: Any) -> Iterable[tuple[float, float]]:
    if is_position(coordinates):
        yield (float(coordinates[0]), float(coordinates[1]))
        return
    if isinstance(coordinates, list | tuple):
        for item in coordinates:
            yield from iter_positions(item)
        return
    raise Sentinel2StatsError("AOI geometry contains invalid coordinates.")


def coordinate_bounds(
    positions: Sequence[tuple[float, float]],
) -> tuple[float, float, float, float]:
    if not positions:
        raise Sentinel2StatsError("AOI geometry does not contain coordinates.")

    xs = [position[0] for position in positions]
    ys = [position[1] for position in positions]
    return (min(xs), min(ys), max(xs), max(ys))


def normalize_aoi_name(raw_name: str) -> str:
    if raw_name.startswith("aoi_"):
        return raw_name[4:]
    return raw_name


def raw_response_path(
    raw_json_dir: str | Path,
    *,
    target_date: str,
    aoi_name: str,
    resolution_m: int,
) -> Path:
    safe_aoi = safe_slug(aoi_name)
    return (
        Path(raw_json_dir)
        / f"{target_date}_{safe_aoi}_{INDEX_SET_NAME}_{resolution_m}m_s2_stats.json"
    )


def safe_slug(value: str) -> str:
    return value.replace("/", "_").replace("\\", "_").replace(" ", "_")


def build_stats_request(
    *,
    geometry: dict[str, Any],
    target_date: str,
    resolution_m: int = DEFAULT_RESOLUTION_M,
    target_epsg: int = DEFAULT_TARGET_EPSG,
) -> dict[str, Any]:
    start = parse_date(target_date)
    end = start + timedelta(days=1)
    metric_geometry = transform_geometry_to_epsg(geometry, target_epsg)

    return {
        "input": {
            "bounds": {
                "geometry": metric_geometry,
                "properties": {
                    "crs": f"http://www.opengis.net/def/crs/EPSG/0/{target_epsg}",
                },
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "mosaickingOrder": "leastCC",
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {
                "from": f"{start.isoformat()}T00:00:00Z",
                "to": f"{end.isoformat()}T00:00:00Z",
            },
            "aggregationInterval": {
                "of": "P1D",
            },
            "evalscript": SENTINEL2_EVALSCRIPT,
            "resx": resolution_m,
            "resy": resolution_m,
        },
        "calculations": {
            "indices": {
                "statistics": {
                    "default": {},
                },
            },
        },
    }


def transform_geometry_to_epsg(geometry: dict[str, Any], target_epsg: int) -> dict[str, Any]:
    """Transform GeoJSON coordinates from WGS84 lon/lat into a metric CRS."""

    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise Sentinel2StatsError(
            "pyproj is required for 20 m Statistical API geometry requests. "
            "Install requirements.txt before running the batch."
        ) from exc

    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{target_epsg}", always_xy=True)
    transformed = dict(geometry)
    transformed["coordinates"] = transform_coordinates(
        geometry.get("coordinates"),
        transformer,
    )
    return transformed


def transform_coordinates(coordinates: Any, transformer: Any) -> Any:
    if is_position(coordinates):
        x, y = transformer.transform(float(coordinates[0]), float(coordinates[1]))
        return [round(x, 3), round(y, 3)]
    if isinstance(coordinates, list):
        return [transform_coordinates(item, transformer) for item in coordinates]
    raise Sentinel2StatsError("AOI geometry contains invalid coordinates.")


def is_position(value: Any) -> bool:
    return (
        isinstance(value, Sequence)
        and len(value) >= 2
        and isinstance(value[0], int | float)
        and isinstance(value[1], int | float)
    )


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise Sentinel2StatsError(f"Invalid date: {value}") from exc


def post_stats_request(
    *,
    token: CDSEToken,
    payload: dict[str, Any],
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    stats_request = request.Request(
        STATISTICS_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": token.authorization_header,
        },
    )

    try:
        with request.urlopen(stats_request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        message = safe_http_error_message(exc)
        raise Sentinel2StatsError(
            f"Statistical API request failed with HTTP {exc.code}: {message}"
        ) from exc
    except error.URLError as exc:
        raise Sentinel2StatsError(
            f"Statistical API request failed: {exc.reason}."
        ) from exc
    except TimeoutError as exc:
        raise Sentinel2StatsError("Statistical API request timed out.") from exc
    except json.JSONDecodeError as exc:
        raise Sentinel2StatsError(
            "Statistical API response was not valid JSON."
        ) from exc


def safe_http_error_message(exc: error.HTTPError, max_length: int = 500) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return "No response body."
    if not body:
        return "No response body."
    compact = " ".join(body.split())
    return compact[:max_length]


def save_raw_response(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_raw_response(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise Sentinel2StatsError(f"Could not read cached raw JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise Sentinel2StatsError(f"Cached raw JSON is invalid: {path}") from exc

    if not isinstance(payload, dict):
        raise Sentinel2StatsError(f"Cached raw JSON is not an object: {path}")
    return payload


def row_from_cached_response(
    *,
    raw_path: Path,
    target_date: str,
    aoi_name: str,
    resolution_m: int,
) -> dict[str, Any]:
    try:
        raw_response = load_raw_response(raw_path)
        return processed_row_from_response(
            raw_response,
            target_date=target_date,
            aoi_name=aoi_name,
            resolution_m=resolution_m,
            raw_path=raw_path,
        )
    except Sentinel2StatsError as exc:
        return error_row(
            target_date=target_date,
            aoi_name=aoi_name,
            resolution_m=resolution_m,
            raw_path=raw_path,
            api_error=str(exc),
        )


def processed_row_from_response(
    response_payload: dict[str, Any],
    *,
    target_date: str,
    aoi_name: str,
    resolution_m: int,
    raw_path: Path,
) -> dict[str, Any]:
    stats = extract_index_stats(response_payload)
    sample_count = stats["sampleCount"]
    no_data_count = stats["noDataCount"]
    valid_percent = compute_valid_percent(sample_count, no_data_count)
    classification = classify_confidence(
        valid_percent,
        sample_count=sample_count,
        no_data_count=no_data_count,
    )

    return {
        "date": target_date,
        "aoi": aoi_name,
        "resolution_m": resolution_m,
        "mndwi_mean": format_optional_float(stats["mndwi_mean"]),
        "ndti_mean": format_optional_float(stats["ndti_mean"]),
        "sampleCount": sample_count,
        "noDataCount": no_data_count,
        "validPercent": format_optional_float(valid_percent),
        "confidence_class": classification["confidence_class"],
        "decision": classification["decision"],
        "reason": classification["reason"],
        "recommended_action": classification["recommended_action"],
        "raw_json_path": as_posix_path(raw_path),
        "api_status": extract_api_status(response_payload),
        "api_error": "",
    }


def extract_api_status(response_payload: dict[str, Any]) -> str:
    status = response_payload.get("status")
    if isinstance(status, str) and status:
        return status

    data = response_payload.get("data")
    if isinstance(data, list) and data:
        first_interval = data[0]
        if isinstance(first_interval, dict):
            interval_status = first_interval.get("status")
            if isinstance(interval_status, str) and interval_status:
                return interval_status

    return "OK"


def extract_index_stats(response_payload: dict[str, Any]) -> dict[str, Any]:
    data = response_payload.get("data")
    if not isinstance(data, list) or not data:
        return empty_stats()

    first_interval = data[0]
    if not isinstance(first_interval, dict):
        return empty_stats()

    outputs = first_interval.get("outputs")
    if not isinstance(outputs, dict):
        return empty_stats()

    indices_output = outputs.get("indices") or outputs.get("default")
    if not isinstance(indices_output, dict):
        return empty_stats()

    bands = indices_output.get("bands")
    if not isinstance(bands, dict):
        return empty_stats()

    mndwi_band = pick_band(bands, ("mndwi", "B0", "band_0", "0"))
    ndti_band = pick_band(bands, ("ndti", "B1", "band_1", "1"))
    mndwi_stats = get_stats(mndwi_band)
    ndti_stats = get_stats(ndti_band)
    count_stats = mndwi_stats or ndti_stats or {}

    return {
        "mndwi_mean": mndwi_stats.get("mean") if mndwi_stats else None,
        "ndti_mean": ndti_stats.get("mean") if ndti_stats else None,
        "sampleCount": normalize_count(count_stats.get("sampleCount")),
        "noDataCount": normalize_count(count_stats.get("noDataCount")),
    }


def empty_stats() -> dict[str, Any]:
    return {
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": 0,
        "noDataCount": 0,
    }


def pick_band(
    bands: dict[str, Any],
    names: tuple[str, ...],
) -> dict[str, Any] | None:
    for name in names:
        band = bands.get(name)
        if isinstance(band, dict):
            return band
    return None


def get_stats(band: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(band, dict):
        return {}
    stats = band.get("stats")
    if isinstance(stats, dict):
        return stats
    return {}


def normalize_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, float):
        return max(int(value), 0)
    return 0


def compute_valid_percent(sample_count: int, no_data_count: int) -> float:
    if sample_count <= 0:
        return 0.0
    valid_count = max(sample_count - no_data_count, 0)
    return round((valid_count / sample_count) * 100, 2)


def format_optional_float(value: Any) -> str:
    if not isinstance(value, int | float):
        return ""
    return f"{float(value):.2f}"


def error_row(
    *,
    target_date: str,
    aoi_name: str,
    resolution_m: int,
    raw_path: Path,
    api_error: str,
) -> dict[str, Any]:
    classification = classify_confidence(0.0, sample_count=0, no_data_count=0)
    return {
        "date": target_date,
        "aoi": aoi_name,
        "resolution_m": resolution_m,
        "mndwi_mean": "",
        "ndti_mean": "",
        "sampleCount": 0,
        "noDataCount": 0,
        "validPercent": "0.00",
        "confidence_class": classification["confidence_class"],
        "decision": classification["decision"],
        "reason": classification["reason"],
        "recommended_action": classification["recommended_action"],
        "raw_json_path": as_posix_path(raw_path),
        "api_status": "ERROR",
        "api_error": api_error[:500],
    }


def write_processed_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROCESSED_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def as_posix_path(path: Path) -> str:
    return path.as_posix()
