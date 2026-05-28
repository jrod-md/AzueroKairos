"""Prototype windowed Sentinel-1 SAR context preview for Azuero nodes."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from azuero_kairos.cdse_auth import CDSEAuthError, get_cdse_token  # noqa: E402
from azuero_kairos.sentinel1_stats import (  # noqa: E402
    DEFAULT_RESOLUTION_M,
    DEFAULT_SLEEP_SECONDS,
    DEFAULT_TARGET_EPSG,
    LOW_OBSERVATION_VALID_PERCENT,
    OFFICIAL_DATES,
    SENSOR_NAME,
    SENTINEL1_EVALSCRIPT,
    Sentinel1StatsError,
    compute_valid_percent,
    estimate_request_grid_from_path,
    extract_api_status,
    extract_sar_stats,
    format_optional_float,
    format_request_grid_estimate,
    post_stats_request,
    sanitize_text,
    transform_geometry_to_epsg,
    validate_request_grid,
)
from run_official_s1_nodes import (  # noqa: E402
    DEFAULT_NODES_CONFIG_PATH,
    AoiNode,
    load_nodes,
)


DEFAULT_OUTPUT_CSV = Path("outputs/sar/sentinel1_node_context_preview.csv")
DEFAULT_OUTPUT_JSON = Path("outputs/sar/sentinel1_node_context_preview.json")
DEFAULT_RAW_JSON_DIR = Path("outputs/sar/raw_json")
DEFAULT_WINDOWS = (3, 6)
POLARIZATION = "DV"
ACQUISITION_MODE = "IW"
CLAIM_LIMIT = (
    "Contexto SAR auxiliar; no modifica la clasificacion Sentinel-2 ni sustituye "
    "verificacion territorial, laboratorio ni autoridad competente."
)

PREVIEW_FIELDNAMES = [
    "node_id",
    "node_name",
    "target_date",
    "sar_window_start",
    "sar_window_end",
    "window_days",
    "matched_acquisition_date",
    "source_dataset",
    "polarization",
    "orbit_direction",
    "vv_mean",
    "vh_mean",
    "vv_vh_ratio",
    "sampleCount",
    "noDataCount",
    "validPercent",
    "context_status",
    "api_status",
    "api_error",
    "claim_limit",
    "raw_json_path",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a non-public Sentinel-1 SAR windowed context preview for "
            "Azuero nodes."
        )
    )
    parser.add_argument("--nodes-config", default=str(DEFAULT_NODES_CONFIG_PATH))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--raw-json-dir", default=str(DEFAULT_RAW_JSON_DIR))
    parser.add_argument("--resolution", type=int, default=DEFAULT_RESOLUTION_M)
    parser.add_argument("--windows", default="3,6", help="Half-window days to try.")
    parser.add_argument("--force", action="store_true", help="Ignore cached preview JSON.")
    parser.add_argument("--sleep-seconds", type=float, default=DEFAULT_SLEEP_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    try:
        windows = parse_windows(args.windows)
        nodes = load_nodes(Path(args.nodes_config))
        rows = run_windowed_preview(
            nodes=nodes,
            windows=windows,
            resolution_m=args.resolution,
            raw_json_dir=Path(args.raw_json_dir),
            timeout_seconds=args.timeout_seconds,
            sleep_seconds=args.sleep_seconds,
            force=args.force,
        )
    except (CDSEAuthError, Sentinel1StatsError) as exc:
        print(f"SAR windowed preview failed safely: {sanitize_text(str(exc))}", file=sys.stderr)
        return 1

    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    write_preview_csv(output_csv, rows)
    write_preview_json(output_json, rows, windows=windows, resolution_m=args.resolution)

    status_counts = Counter(row["context_status"] for row in rows)
    print(f"Output CSV path: {display_path(output_csv)}")
    print(f"Output JSON path: {display_path(output_json)}")
    print(f"Rows: {len(rows)}")
    print(f"SAR context available rows: {status_counts.get('sar_context_available', 0)}")
    print(f"SAR low-observation rows: {status_counts.get('sar_low_observation', 0)}")
    print(f"SAR no-acquisition rows: {status_counts.get('sar_no_acquisition', 0)}")
    print(f"SAR API error rows: {status_counts.get('sar_api_error', 0)}")
    return 1 if status_counts.get("sar_api_error", 0) else 0


def parse_windows(raw_value: str) -> tuple[int, ...]:
    windows: list[int] = []
    for part in raw_value.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            window = int(text)
        except ValueError as exc:
            raise Sentinel1StatsError(f"Invalid SAR window value: {text}") from exc
        if window < 0:
            raise Sentinel1StatsError("SAR window days must be zero or positive.")
        windows.append(window)
    if not windows:
        raise Sentinel1StatsError("At least one SAR window must be configured.")
    return tuple(windows)


def run_windowed_preview(
    *,
    nodes: list[AoiNode],
    windows: tuple[int, ...],
    resolution_m: int,
    raw_json_dir: Path,
    timeout_seconds: float,
    sleep_seconds: float,
    force: bool,
) -> list[dict[str, Any]]:
    token = get_cdse_token()
    rows: list[dict[str, Any]] = []

    for node in nodes:
        preflight = estimate_request_grid_from_path(
            node.geojson_path,
            resolution_m=resolution_m,
        )
        print(format_request_grid_estimate(preflight))
        validate_request_grid(preflight)
        geometry = load_geojson_geometry(node.geojson_path)

        for target_date in OFFICIAL_DATES:
            row = run_node_date_preview(
                node=node,
                geometry=geometry,
                target_date=target_date,
                windows=windows,
                resolution_m=resolution_m,
                raw_json_dir=raw_json_dir,
                timeout_seconds=timeout_seconds,
                force=force,
                token=token,
            )
            rows.append(row)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    return rows


def run_node_date_preview(
    *,
    node: AoiNode,
    geometry: dict[str, Any],
    target_date: str,
    windows: tuple[int, ...],
    resolution_m: int,
    raw_json_dir: Path,
    timeout_seconds: float,
    force: bool,
    token: Any,
) -> dict[str, Any]:
    last_row: dict[str, Any] | None = None

    for window_days in windows:
        window_start, window_end = compute_window(target_date, window_days)
        raw_path = raw_response_path(
            raw_json_dir=raw_json_dir,
            node_id=node.node_id,
            target_date=target_date,
            window_days=window_days,
            resolution_m=resolution_m,
        )

        try:
            response_payload = load_or_request_response(
                raw_path=raw_path,
                geometry=geometry,
                window_start=window_start,
                window_end=window_end,
                resolution_m=resolution_m,
                timeout_seconds=timeout_seconds,
                force=force,
                token=token,
            )
            row = build_preview_row(
                response_payload=response_payload,
                node=node,
                target_date=target_date,
                window_start=window_start,
                window_end=window_end,
                window_days=window_days,
                raw_path=raw_path,
            )
        except Sentinel1StatsError as exc:
            row = build_error_row(
                node=node,
                target_date=target_date,
                window_start=window_start,
                window_end=window_end,
                window_days=window_days,
                raw_path=raw_path,
                api_error=str(exc),
            )

        last_row = row
        if row["context_status"] != "sar_no_acquisition":
            return row

    if last_row is None:
        raise Sentinel1StatsError("No SAR windows were evaluated.")
    return last_row


def compute_window(target_date: str, window_days: int) -> tuple[date, date]:
    parsed = parse_date(target_date)
    return parsed - timedelta(days=window_days), parsed + timedelta(days=window_days)


def load_or_request_response(
    *,
    raw_path: Path,
    geometry: dict[str, Any],
    window_start: date,
    window_end: date,
    resolution_m: int,
    timeout_seconds: float,
    force: bool,
    token: Any,
) -> dict[str, Any]:
    if raw_path.exists() and not force:
        return load_json(raw_path)

    payload = build_windowed_stats_request(
        geometry=geometry,
        window_start=window_start,
        window_end=window_end,
        resolution_m=resolution_m,
    )
    response_payload = post_stats_request(
        token=token,
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(response_payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return response_payload


def build_windowed_stats_request(
    *,
    geometry: dict[str, Any],
    window_start: date,
    window_end: date,
    resolution_m: int,
    target_epsg: int = DEFAULT_TARGET_EPSG,
) -> dict[str, Any]:
    metric_geometry = transform_geometry_to_epsg(geometry, target_epsg)
    exclusive_end = window_end + timedelta(days=1)

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
                    "type": SENSOR_NAME,
                    "dataFilter": {
                        "acquisitionMode": ACQUISITION_MODE,
                        "polarization": POLARIZATION,
                        "resolution": "HIGH",
                        "mosaickingOrder": "mostRecent",
                    },
                    "processing": {
                        "orthorectify": True,
                        "backCoeff": "GAMMA0_ELLIPSOID",
                        "demInstance": "COPERNICUS_30",
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {
                "from": f"{window_start.isoformat()}T00:00:00Z",
                "to": f"{exclusive_end.isoformat()}T00:00:00Z",
            },
            "aggregationInterval": {
                "of": "P1D",
            },
            "evalscript": SENTINEL1_EVALSCRIPT,
            "resx": resolution_m,
            "resy": resolution_m,
        },
        "calculations": {
            "sar": {
                "statistics": {
                    "default": {},
                },
            },
        },
    }


def build_preview_row(
    *,
    response_payload: dict[str, Any],
    node: AoiNode,
    target_date: str,
    window_start: date,
    window_end: date,
    window_days: int,
    raw_path: Path,
) -> dict[str, Any]:
    interval_rows = extract_interval_rows(response_payload)
    api_status = extract_api_status(response_payload)

    if not interval_rows:
        return base_preview_row(
            node=node,
            target_date=target_date,
            window_start=window_start,
            window_end=window_end,
            window_days=window_days,
            raw_path=raw_path,
            context_status="sar_no_acquisition",
            api_status=api_status,
        )

    available_rows = [
        row for row in interval_rows if row["context_status"] == "sar_context_available"
    ]
    selected = max(
        available_rows or interval_rows,
        key=lambda row: (float(row["validPercent"]), int(row["sampleCount"])),
    )

    row = base_preview_row(
        node=node,
        target_date=target_date,
        window_start=window_start,
        window_end=window_end,
        window_days=window_days,
        raw_path=raw_path,
        context_status=selected["context_status"],
        api_status=api_status,
    )
    row.update(
        {
            "matched_acquisition_date": selected["matched_acquisition_date"],
            "vv_mean": selected["vv_mean"],
            "vh_mean": selected["vh_mean"],
            "vv_vh_ratio": selected["vv_vh_ratio"],
            "sampleCount": selected["sampleCount"],
            "noDataCount": selected["noDataCount"],
            "validPercent": selected["validPercent"],
        }
    )
    return row


def extract_interval_rows(response_payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = response_payload.get("data")
    if not isinstance(data, list) or not data:
        return []

    rows: list[dict[str, Any]] = []
    for interval in data:
        if not isinstance(interval, dict):
            continue
        stats = extract_sar_stats({"data": [interval], "status": response_payload.get("status")})
        sample_count = int(stats["sampleCount"])
        no_data_count = int(stats["noDataCount"])
        valid_percent = compute_valid_percent(sample_count, no_data_count)
        vv_mean = stats.get("vv_mean")
        vh_mean = stats.get("vh_mean")
        has_metric = is_meaningful_metric(vv_mean) or is_meaningful_metric(vh_mean)
        status = classify_preview_status(
            sample_count=sample_count,
            valid_percent=valid_percent,
            has_metric=has_metric,
        )
        matched_date = (
            extract_interval_date(interval) if sample_count > 0 and has_metric else ""
        )
        rows.append(
            {
                "matched_acquisition_date": matched_date,
                "vv_mean": format_optional_float(vv_mean),
                "vh_mean": format_optional_float(vh_mean),
                "vv_vh_ratio": format_optional_float(stats.get("vv_vh_ratio")),
                "sampleCount": sample_count,
                "noDataCount": no_data_count,
                "validPercent": f"{valid_percent:.2f}",
                "context_status": status,
            }
        )
    return rows


def classify_preview_status(
    *,
    sample_count: int,
    valid_percent: float,
    has_metric: bool,
) -> str:
    if (
        sample_count > 0
        and has_metric
        and valid_percent >= LOW_OBSERVATION_VALID_PERCENT
    ):
        return "sar_context_available"
    return "sar_low_observation"


def is_meaningful_metric(value: Any) -> bool:
    return isinstance(value, int | float) and value != 0


def extract_interval_date(interval: dict[str, Any]) -> str:
    interval_meta = interval.get("interval")
    if not isinstance(interval_meta, dict):
        return ""
    for key in ("from", "to"):
        value = interval_meta.get(key)
        if isinstance(value, str) and len(value) >= 10:
            return value[:10]
    return ""


def base_preview_row(
    *,
    node: AoiNode,
    target_date: str,
    window_start: date,
    window_end: date,
    window_days: int,
    raw_path: Path,
    context_status: str,
    api_status: str,
) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "node_name": node.display_name,
        "target_date": target_date,
        "sar_window_start": window_start.isoformat(),
        "sar_window_end": window_end.isoformat(),
        "window_days": window_days,
        "matched_acquisition_date": "",
        "source_dataset": SENSOR_NAME,
        "polarization": POLARIZATION,
        "orbit_direction": "",
        "vv_mean": "",
        "vh_mean": "",
        "vv_vh_ratio": "",
        "sampleCount": 0,
        "noDataCount": 0,
        "validPercent": "0.00",
        "context_status": context_status,
        "api_status": api_status,
        "api_error": "",
        "claim_limit": CLAIM_LIMIT,
        "raw_json_path": display_path(raw_path),
    }


def build_error_row(
    *,
    node: AoiNode,
    target_date: str,
    window_start: date,
    window_end: date,
    window_days: int,
    raw_path: Path,
    api_error: str,
) -> dict[str, Any]:
    row = base_preview_row(
        node=node,
        target_date=target_date,
        window_start=window_start,
        window_end=window_end,
        window_days=window_days,
        raw_path=raw_path,
        context_status="sar_api_error",
        api_status="ERROR",
    )
    row["api_error"] = sanitize_text(api_error)[:500]
    return row


def load_geojson_geometry(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if isinstance(features, list) and features:
            feature = features[0]
            if isinstance(feature, dict) and isinstance(feature.get("geometry"), dict):
                return feature["geometry"]
    if payload.get("type") == "Feature" and isinstance(payload.get("geometry"), dict):
        return payload["geometry"]
    if isinstance(payload.get("type"), str) and isinstance(payload.get("coordinates"), list):
        return payload
    raise Sentinel1StatsError(f"Could not find GeoJSON geometry in {display_path(path)}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise Sentinel1StatsError(f"Could not read JSON: {display_path(path)}") from exc
    except json.JSONDecodeError as exc:
        raise Sentinel1StatsError(f"Invalid JSON: {display_path(path)}") from exc
    if not isinstance(payload, dict):
        raise Sentinel1StatsError(f"JSON root is not an object: {display_path(path)}")
    return payload


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise Sentinel1StatsError(f"Invalid date: {value}") from exc


def raw_response_path(
    *,
    raw_json_dir: Path,
    node_id: str,
    target_date: str,
    window_days: int,
    resolution_m: int,
) -> Path:
    return (
        raw_json_dir
        / f"{target_date}_{node_id}_pm{window_days}d_{resolution_m}m_s1_stats.json"
    )


def write_preview_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREVIEW_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PREVIEW_FIELDNAMES})


def write_preview_json(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    windows: tuple[int, ...],
    resolution_m: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status_counts = Counter(row["context_status"] for row in rows)
    payload = {
        "schema_version": "s1_windowed_preview_v1",
        "public_safe": False,
        "data_status": "preview",
        "source_dataset": SENSOR_NAME,
        "polarization": POLARIZATION,
        "resolution_m": resolution_m,
        "windows_tested_days": list(windows),
        "claim_limit": CLAIM_LIMIT,
        "status_counts": dict(sorted(status_counts.items())),
        "rows": rows,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
