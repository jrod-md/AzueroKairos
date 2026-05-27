"""Run conservative CHIRPS rainfall context for Azuero Kairos nodes."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODES_CONFIG_PATH = Path("configs/aoi_nodes/nodes.yaml")
DEFAULT_PROCESSED_CSV = Path("outputs/processed_csv/hydroclimate_node_context.csv")
CLIMATESERV_BASE_URL = "https://climateserv.servirglobal.net/chirps"
DATA_SOURCE = "CHIRPS daily rainfall via ClimateSERV"

OFFICIAL_DATES = (
    "2025-06-02",
    "2025-06-10",
    "2025-06-15",
    "2025-06-30",
    "2025-07-15",
)

PROCESSED_FIELDNAMES = [
    "node_id",
    "node_display_name",
    "date",
    "rain_24h_mm",
    "rain_72h_mm",
    "rain_7d_mm",
    "hydroclimate_status",
    "recommended_context_action",
    "data_source",
    "api_status",
    "api_error",
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]

CONTEXT_ACTIONS = {
    "dry_or_low_rain": (
        "Use as low-rainfall context only; do not infer water safety or "
        "contamination conditions."
    ),
    "normal_context": (
        "Use rainfall as background context only; keep Sentinel confidence "
        "classification unchanged."
    ),
    "antecedent_rain": (
        "Review antecedent rainfall context before interpreting runoff-sensitive "
        "satellite observations."
    ),
    "heavy_rain_context": (
        "Review recent rainfall and field verification priority; runoff or "
        "sediment movement may be contextually relevant."
    ),
    "data_unavailable": (
        "Rainfall context unavailable; do not infer hydroclimatic conditions "
        "from this layer."
    ),
}


class HydroClimateError(RuntimeError):
    """Raised when hydroclimate context cannot be fetched or parsed."""


@dataclass(frozen=True)
class AoiNode:
    node_id: str
    display_name: str
    geojson_path: Path
    geometry: dict[str, Any]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run CHIRPS rainfall context for Azuero Kairos AOI nodes."
    )
    parser.add_argument(
        "--nodes-config",
        default=str(DEFAULT_NODES_CONFIG_PATH),
        help="Path to configs/aoi_nodes/nodes.yaml.",
    )
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV))
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--max-poll-seconds", type=float, default=120.0)
    args = parser.parse_args(argv)

    try:
        nodes = load_nodes(Path(args.nodes_config))
    except HydroClimateError as exc:
        print(f"HydroClimate context failed safely: {exc}", file=sys.stderr)
        return 1

    target_dates = tuple(parse_iso_date(value) for value in OFFICIAL_DATES)
    start_date = min(target_dates) - timedelta(days=6)
    end_date = max(target_dates)
    rows: list[dict[str, Any]] = []

    for node in nodes:
        try:
            daily_rain = fetch_chirps_daily_rainfall(
                geometry=node.geometry,
                start_date=start_date,
                end_date=end_date,
                timeout_seconds=args.timeout_seconds,
                poll_seconds=args.poll_seconds,
                max_poll_seconds=args.max_poll_seconds,
            )
            rows.extend(build_rows_for_node(node, target_dates, daily_rain))
        except HydroClimateError as exc:
            safe_error = sanitize_text(str(exc))[:500]
            rows.extend(
                unavailable_row(node=node, target_date=target_date, api_error=safe_error)
                for target_date in target_dates
            )

    processed_csv = resolve_project_path(args.processed_csv)
    write_processed_csv(processed_csv, rows)

    rows_ok = sum(
        1 for row in rows if row.get("hydroclimate_status") != "data_unavailable"
    )
    rows_unavailable = len(rows) - rows_ok

    print(f"Nodes processed: {len(nodes)}")
    print(f"Dates processed: {len(OFFICIAL_DATES)}")
    print(f"Rows OK: {rows_ok}")
    print(f"Rows unavailable: {rows_unavailable}")
    print(f"Output CSV path: {display_path(processed_csv)}")
    return 0


def build_rows_for_node(
    node: AoiNode,
    target_dates: tuple[date, ...],
    daily_rain: dict[date, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target_date in target_dates:
        rain_24h = window_sum(daily_rain, target_date, days=1)
        rain_72h = window_sum(daily_rain, target_date, days=3)
        rain_7d = window_sum(daily_rain, target_date, days=7)

        if rain_24h is None or rain_72h is None or rain_7d is None:
            rows.append(
                unavailable_row(
                    node=node,
                    target_date=target_date,
                    api_error="CHIRPS returned incomplete rainfall data for this date.",
                )
            )
            continue

        status = classify_hydroclimate_status(rain_72h, rain_7d)
        rows.append(
            {
                "node_id": node.node_id,
                "node_display_name": node.display_name,
                "date": target_date.isoformat(),
                "rain_24h_mm": format_mm(rain_24h),
                "rain_72h_mm": format_mm(rain_72h),
                "rain_7d_mm": format_mm(rain_7d),
                "hydroclimate_status": status,
                "recommended_context_action": CONTEXT_ACTIONS[status],
                "data_source": DATA_SOURCE,
                "api_status": "OK",
                "api_error": "",
            }
        )
    return rows


def classify_hydroclimate_status(rain_72h_mm: float, rain_7d_mm: float) -> str:
    if rain_72h_mm >= 50:
        return "heavy_rain_context"
    if rain_7d_mm >= 75:
        return "antecedent_rain"
    return "normal_context"


def fetch_chirps_daily_rainfall(
    *,
    geometry: dict[str, Any],
    start_date: date,
    end_date: date,
    timeout_seconds: float,
    poll_seconds: float,
    max_poll_seconds: float,
) -> dict[date, float]:
    job_id = submit_chirps_request(
        geometry=geometry,
        start_date=start_date,
        end_date=end_date,
        timeout_seconds=timeout_seconds,
    )
    wait_for_chirps_job(
        job_id,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
        max_poll_seconds=max_poll_seconds,
    )
    payload = read_json_url(
        f"{CLIMATESERV_BASE_URL}/getDataFromRequest/?"
        f"{parse.urlencode({'id': job_id})}",
        timeout_seconds=timeout_seconds,
    )
    return parse_chirps_response(payload)


def submit_chirps_request(
    *,
    geometry: dict[str, Any],
    start_date: date,
    end_date: date,
    timeout_seconds: float,
) -> str:
    params = {
        "datatype": "0",
        "begintime": format_climateserv_date(start_date),
        "endtime": format_climateserv_date(end_date),
        "intervaltype": "0",
        "operationtype": "5",
        "dateType_Category": "default",
        "isZip_CurrentDataType": "false",
        "geometry": json.dumps(geometry, separators=(",", ":")),
    }
    payload = read_json_url(
        f"{CLIMATESERV_BASE_URL}/submitDataRequest/?{parse.urlencode(params)}",
        timeout_seconds=timeout_seconds,
    )
    job_id = extract_job_id(payload)
    if not job_id:
        raise HydroClimateError("ClimateSERV did not return a CHIRPS job id.")
    return job_id


def wait_for_chirps_job(
    job_id: str,
    *,
    timeout_seconds: float,
    poll_seconds: float,
    max_poll_seconds: float,
) -> None:
    started = time.monotonic()
    while True:
        progress_payload = read_json_url(
            f"{CLIMATESERV_BASE_URL}/getDataRequestProgress/?"
            f"{parse.urlencode({'id': job_id})}",
            timeout_seconds=timeout_seconds,
        )
        progress = as_float(progress_payload)
        if progress is not None and progress >= 100:
            return
        if progress is not None and progress < 0:
            raise HydroClimateError("ClimateSERV reported a failed CHIRPS job.")
        if time.monotonic() - started > max_poll_seconds:
            raise HydroClimateError("ClimateSERV CHIRPS job timed out.")
        time.sleep(max(poll_seconds, 0.25))


def parse_chirps_response(payload: Any) -> dict[date, float]:
    if not isinstance(payload, dict):
        raise HydroClimateError("ClimateSERV CHIRPS response was not an object.")
    data = payload.get("data")
    if not isinstance(data, list):
        raise HydroClimateError("ClimateSERV CHIRPS response did not contain data.")

    daily: dict[date, float] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        item_date = parse_chirps_date(item)
        value = extract_rainfall_value(item.get("value"))
        if item_date is not None and value is not None:
            daily[item_date] = max(value, 0.0)
    if not daily:
        raise HydroClimateError("ClimateSERV CHIRPS response contained no rainfall values.")
    return daily


def extract_job_id(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        return str(payload[0]).strip().strip('"')
    if isinstance(payload, str):
        text = payload.strip()
        if text.startswith("["):
            try:
                return extract_job_id(json.loads(text))
            except json.JSONDecodeError:
                return ""
        return text.strip('"')
    return ""


def parse_chirps_date(item: dict[str, Any]) -> date | None:
    raw_date = item.get("date")
    if isinstance(raw_date, str):
        for pattern in ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw_date.strip(), pattern).date()
            except ValueError:
                continue

    raw_epoch = item.get("epochTime")
    try:
        epoch = float(raw_epoch)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).date()


def extract_rainfall_value(value: Any) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, dict):
        return None
    for key in ("avg", "average", "mean", "sum", "value"):
        number = as_float(value.get(key))
        if number is not None:
            return number
    for candidate in value.values():
        number = as_float(candidate)
        if number is not None:
            return number
    return None


def read_json_url(url: str, *, timeout_seconds: float) -> Any:
    api_request = request.Request(url, headers={"Accept": "application/json"})
    try:
        with request.urlopen(api_request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raise HydroClimateError(
            f"ClimateSERV request failed with HTTP {exc.code}: "
            f"{safe_http_error_message(exc)}"
        ) from exc
    except error.URLError as exc:
        raise HydroClimateError(f"ClimateSERV request failed: {exc.reason}.") from exc
    except TimeoutError as exc:
        raise HydroClimateError("ClimateSERV request timed out.") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise HydroClimateError("ClimateSERV response was not valid JSON.") from exc


def safe_http_error_message(exc: error.HTTPError, max_length: int = 500) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return "No response body."
    compact = " ".join(body.split())
    return sanitize_text(compact)[:max_length] if compact else "No response body."


def load_nodes(path: Path) -> list[AoiNode]:
    nodes_path = resolve_project_path(path)
    if not nodes_path.exists():
        raise HydroClimateError(f"Missing nodes config: {display_path(nodes_path)}")

    try:
        nodes_text = nodes_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HydroClimateError(f"Could not read nodes config: {display_path(nodes_path)}") from exc

    payload = load_nodes_payload(nodes_text)
    raw_nodes = payload.get("nodes") if isinstance(payload, dict) else None
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise HydroClimateError("nodes.yaml must contain a non-empty 'nodes' list.")

    nodes: list[AoiNode] = []
    for index, raw_node in enumerate(raw_nodes, start=1):
        if not isinstance(raw_node, dict):
            raise HydroClimateError(f"Node entry {index} is not an object.")
        node_id = str(raw_node.get("node_id") or "").strip()
        display_name = str(raw_node.get("display_name") or node_id).strip()
        raw_geojson_path = str(raw_node.get("geojson_path") or "").strip()
        if not node_id or not raw_geojson_path:
            raise HydroClimateError(
                f"Node entry {index} requires node_id and geojson_path."
            )
        geojson_path = resolve_project_path(raw_geojson_path)
        geometry = load_geojson_geometry(geojson_path)
        nodes.append(
            AoiNode(
                node_id=node_id,
                display_name=display_name,
                geojson_path=geojson_path,
                geometry=geometry,
            )
        )
    return nodes


def load_nodes_payload(nodes_text: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return parse_simple_nodes_yaml(nodes_text)

    try:
        payload = yaml.safe_load(nodes_text)
    except yaml.YAMLError as exc:
        raise HydroClimateError("Could not parse nodes.yaml.") from exc
    return payload if isinstance(payload, dict) else {}


def parse_simple_nodes_yaml(nodes_text: str) -> dict[str, Any]:
    nodes: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    saw_nodes_key = False

    for raw_line in nodes_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "nodes:":
            saw_nodes_key = True
            continue
        if not saw_nodes_key:
            continue
        if line.startswith("  - "):
            if current:
                nodes.append(current)
            current = {}
            key, value = parse_yaml_key_value(line[4:])
            current[key] = value
            continue
        if line.startswith("    ") and current is not None:
            key, value = parse_yaml_key_value(line[4:])
            current[key] = value

    if current:
        nodes.append(current)
    return {"nodes": nodes}


def parse_yaml_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise HydroClimateError(f"Unsupported nodes.yaml line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip().strip('"').strip("'")


def load_geojson_geometry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HydroClimateError(f"Node GeoJSON does not exist: {display_path(path)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HydroClimateError(f"Could not read node GeoJSON: {display_path(path)}") from exc
    except json.JSONDecodeError as exc:
        raise HydroClimateError(f"Node GeoJSON is not valid JSON: {display_path(path)}") from exc

    geometry: Any
    if payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list) or not features:
            raise HydroClimateError("Node GeoJSON FeatureCollection is empty.")
        geometry = features[0].get("geometry") if isinstance(features[0], dict) else None
    elif payload.get("type") == "Feature":
        geometry = payload.get("geometry")
    else:
        geometry = payload

    if not isinstance(geometry, dict) or "type" not in geometry:
        raise HydroClimateError("Node GeoJSON does not contain a valid geometry.")
    validate_lonlat_geometry(geometry)
    return geometry


def validate_lonlat_geometry(geometry: dict[str, Any]) -> None:
    for lon, lat in iter_positions(geometry.get("coordinates")):
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise HydroClimateError("Node geometry must be EPSG:4326 lon/lat.")
        if not (-50 <= lat <= 50):
            raise HydroClimateError("CHIRPS daily rainfall coverage is 50S to 50N.")


def iter_positions(coordinates: Any):
    if is_position(coordinates):
        yield float(coordinates[0]), float(coordinates[1])
        return
    if isinstance(coordinates, list | tuple):
        for item in coordinates:
            yield from iter_positions(item)
        return
    raise HydroClimateError("Node GeoJSON contains invalid coordinates.")


def is_position(value: Any) -> bool:
    return (
        isinstance(value, list | tuple)
        and len(value) >= 2
        and isinstance(value[0], int | float)
        and isinstance(value[1], int | float)
    )


def unavailable_row(
    *,
    node: AoiNode,
    target_date: date,
    api_error: str,
) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "node_display_name": node.display_name,
        "date": target_date.isoformat(),
        "rain_24h_mm": "",
        "rain_72h_mm": "",
        "rain_7d_mm": "",
        "hydroclimate_status": "data_unavailable",
        "recommended_context_action": CONTEXT_ACTIONS["data_unavailable"],
        "data_source": DATA_SOURCE,
        "api_status": "ERROR",
        "api_error": sanitize_text(api_error)[:500],
    }


def window_sum(daily_rain: dict[date, float], target_date: date, *, days: int) -> float | None:
    start_date = target_date - timedelta(days=days - 1)
    values: list[float] = []
    current = start_date
    while current <= target_date:
        if current not in daily_rain:
            return None
        values.append(daily_rain[current])
        current += timedelta(days=1)
    return sum(values)


def parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HydroClimateError(f"Invalid official date: {value}") from exc


def format_climateserv_date(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def format_mm(value: float) -> str:
    return f"{value:.2f}"


def as_float(value: Any) -> float | None:
    if isinstance(value, list | tuple) and value:
        return as_float(value[0])
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def write_processed_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROCESSED_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PROCESSED_FIELDNAMES})


def sanitize_text(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return ""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "[redacted]", text)
    return " ".join(text.split())


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
