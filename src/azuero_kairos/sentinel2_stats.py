"""Sentinel-2 Statistical API runner for official Azuero Kairós batches."""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, request

from azuero_kairos.cdse_auth import CDSEAuthError, CDSEToken, get_cdse_token
from azuero_kairos.confidence_engine import classify_confidence


STATISTICS_URL = "https://sh.dataspace.copernicus.eu/statistics/v1"
DEFAULT_AOI_PATH = Path("configs/aoi_corridor_wide.geojson")
DEFAULT_RAW_JSON_DIR = Path("outputs/raw_json")
DEFAULT_PROCESSED_CSV_PATH = Path("outputs/processed_csv/sentinel2_stats_confidence.csv")
DEFAULT_RESOLUTION_M = 20
DEFAULT_SLEEP_SECONDS = 1.0
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
    """Raised when a Sentinel-2 Statistical API request cannot complete."""


@dataclass(frozen=True)
class AoiConfig:
    """AOI geometry and display identifier."""

    name: str
    geometry: dict[str, Any]


def run_official_batch(
    *,
    aoi_path: str | Path = DEFAULT_AOI_PATH,
    dates: Iterable[str] = OFFICIAL_DATES,
    resolution_m: int = DEFAULT_RESOLUTION_M,
    raw_json_dir: str | Path = DEFAULT_RAW_JSON_DIR,
    processed_csv_path: str | Path = DEFAULT_PROCESSED_CSV_PATH,
    sleep_seconds: float = DEFAULT_SLEEP_SECONDS,
    request_timeout_seconds: float = 60.0,
) -> Path:
    """Run the official Sentinel-2 batch and write one processed CSV."""

    aoi = load_aoi(aoi_path)
    raw_dir = Path(raw_json_dir)
    csv_path = Path(processed_csv_path)
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    token: CDSEToken | None = None
    auth_error: CDSEAuthError | None = None

    for target_date in dates:
        raw_path = raw_response_path(raw_dir, target_date, aoi.name)

        if raw_path.exists():
            try:
                raw_response = load_raw_response(raw_path)
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

        stats_request = build_stats_request(
            geometry=aoi.geometry,
            target_date=target_date,
            resolution_m=resolution_m,
        )

        try:
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

    write_processed_csv(csv_path, rows)
    return csv_path


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
            raw_name = feature.get("properties", {}).get("id") or raw_name
            geometry = feature.get("geometry")
    elif payload.get("type") == "Feature":
        raw_name = payload.get("properties", {}).get("id") or raw_name
        geometry = payload.get("geometry")
    else:
        geometry = payload

    if not isinstance(geometry, dict) or "type" not in geometry:
        raise Sentinel2StatsError("AOI file does not contain a valid GeoJSON geometry.")

    return AoiConfig(name=normalize_aoi_name(str(raw_name)), geometry=geometry)


def normalize_aoi_name(raw_name: str) -> str:
    if raw_name.startswith("aoi_"):
        return raw_name[4:]
    return raw_name


def raw_response_path(raw_json_dir: str | Path, target_date: str, aoi_name: str) -> Path:
    safe_aoi = aoi_name.replace("/", "_").replace("\\", "_")
    return Path(raw_json_dir) / f"{target_date}_{safe_aoi}_s2_stats.json"


def build_stats_request(
    *,
    geometry: dict[str, Any],
    target_date: str,
    resolution_m: int = DEFAULT_RESOLUTION_M,
) -> dict[str, Any]:
    start = parse_date(target_date)
    end = start + timedelta(days=1)

    return {
        "input": {
            "bounds": {
                "geometry": geometry,
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326",
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
    }


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
        raise Sentinel2StatsError(
            f"Statistical API request failed with HTTP {exc.code}."
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
        "api_status": str(response_payload.get("status", "UNKNOWN")),
        "api_error": "",
    }


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

    mndwi_band = pick_band(bands, ("mndwi", "B0", "band_0"))
    ndti_band = pick_band(bands, ("ndti", "B1", "band_1"))
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
        "api_error": api_error,
    }


def write_processed_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROCESSED_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def as_posix_path(path: Path) -> str:
    return path.as_posix()
