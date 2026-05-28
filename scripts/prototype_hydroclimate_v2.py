"""Prototype HydroClimate v2 antecedent-rainfall preview for Azuero nodes."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_hydroclimate_context import (  # noqa: E402
    DATA_SOURCE as CHIRPS_DATA_SOURCE,
    DEFAULT_NODES_CONFIG_PATH,
    HydroClimateError,
    AoiNode,
    fetch_chirps_daily_rainfall,
    load_nodes,
    parse_iso_date,
    sanitize_text,
    window_sum,
)


DEFAULT_WATCH_JSON = PROJECT_ROOT / "frontend/public/data/kairos_watch.json"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "outputs/hydroclimate/hydroclimate_context_preview.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "outputs/hydroclimate/hydroclimate_context_preview.json"

SCHEMA_VERSION = "hydroclimate_context_preview_v2"
CHIRPS_SOURCE_RESOLUTION = "0.05 degrees (~5 km)"
CLAIM_LIMIT = (
    "Contexto hidroclimatico auxiliar de lluvia antecedente; no modifica la "
    "clasificacion Sentinel-2 ni sustituye verificacion territorial, laboratorio "
    "o autoridad competente."
)
NORMAL_HINT = "Contexto normal; no cambia la clasificacion Sentinel-2."
REVIEW_HINT = (
    "Revisar lluvia antecedente antes de interpretar observaciones sensibles a "
    "escorrentia; no cambia la clasificacion Sentinel-2."
)
UNAVAILABLE_HINT = "Datos pendientes; no inferir contexto hidroclimatico desde esta capa."
API_ERROR_HINT = "Error de consulta; no usar esta capa para contexto hidroclimatico."

CSV_FIELDNAMES = [
    "node_id",
    "node_name",
    "target_date",
    "rain_24h_mm",
    "rain_72h_mm",
    "rain_7d_mm",
    "rain_14d_mm",
    "data_source",
    "source_resolution",
    "context_status",
    "review_priority_hint",
    "api_status",
    "api_error",
    "claim_limit",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a non-public HydroClimate v2 preview for antecedent rainfall "
            "context. Sentinel-2 confidence classifications are not changed."
        )
    )
    parser.add_argument("--nodes-config", default=str(DEFAULT_NODES_CONFIG_PATH))
    parser.add_argument("--watch-json", default=str(DEFAULT_WATCH_JSON))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--source", choices=("auto", "chirps", "era5-land"), default="auto")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--max-poll-seconds", type=float, default=120.0)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing preview CSV/JSON files.",
    )
    args = parser.parse_args(argv)

    output_csv = resolve_project_path(args.output_csv)
    output_json = resolve_project_path(args.output_json)
    if not args.force:
        existing = [path for path in (output_csv, output_json) if path.exists()]
        if existing:
            paths = ", ".join(display_path(path) for path in existing)
            print(f"Preview output exists; use --force to overwrite: {paths}", file=sys.stderr)
            return 1

    source_choice, source_notes = select_source(args.source)

    try:
        nodes, target_dates = discover_nodes_and_dates(
            nodes_config=Path(args.nodes_config),
            watch_json=Path(args.watch_json),
        )
    except HydroClimateError as exc:
        print(f"HydroClimate v2 preview failed safely: {exc}", file=sys.stderr)
        return 1

    rows = run_preview(
        nodes=nodes,
        target_dates=target_dates,
        source_choice=source_choice,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
        max_poll_seconds=args.max_poll_seconds,
    )

    write_csv(output_csv, rows)
    write_json(
        output_json,
        build_payload(
            rows=rows,
            nodes=nodes,
            target_dates=target_dates,
            source_choice=source_choice,
            source_notes=source_notes,
        ),
    )

    counts = Counter(row["context_status"] for row in rows)
    print(f"Source selected: {source_choice}")
    print(f"Nodes processed: {len(nodes)}")
    print(f"Dates processed: {len(target_dates)}")
    print(f"Rows written: {len(rows)}")
    for status in ("normal_context", "antecedent_rain_review", "data_unavailable", "api_error"):
        print(f"{status}: {counts.get(status, 0)}")
    print(f"Output CSV: {display_path(output_csv)}")
    print(f"Output JSON: {display_path(output_json)}")
    return 0


def select_source(requested_source: str) -> tuple[str, list[str]]:
    era5_notes = era5_feasibility_notes()
    if requested_source == "era5-land":
        if era5_notes:
            raise SystemExit(
                "ERA5-Land is not feasible in this environment: " + "; ".join(era5_notes)
            )
        return "era5-land", []
    if requested_source == "chirps":
        return "chirps", era5_notes
    if not era5_notes:
        return "era5-land", []
    return "chirps", era5_notes


def era5_feasibility_notes() -> list[str]:
    notes: list[str] = []
    credential_names = ("CDSAPI_URL", "CDSAPI_KEY", "CDS_URL", "CDS_KEY")
    if not any(os.environ.get(name) for name in credential_names):
        notes.append("CDS credentials not visible in this shell")
    for module_name in ("cdsapi", "xarray", "netCDF4"):
        try:
            __import__(module_name)
        except ImportError:
            notes.append(f"Python module missing: {module_name}")
    return notes


def discover_nodes_and_dates(
    *,
    nodes_config: Path,
    watch_json: Path,
) -> tuple[list[AoiNode], list[date]]:
    watch_payload = read_json(resolve_project_path(watch_json))
    node_ids = discover_watch_node_ids(watch_payload)
    target_dates = discover_watch_dates(watch_payload)

    nodes = load_nodes(resolve_project_path(nodes_config))
    nodes_by_id = {node.node_id: node for node in nodes}
    if node_ids:
        nodes = [nodes_by_id[node_id] for node_id in node_ids if node_id in nodes_by_id]
    if not nodes:
        raise HydroClimateError("No La Villa nodes could be resolved from project data.")
    if not target_dates:
        raise HydroClimateError("No official dates could be resolved from project data.")
    return nodes, target_dates


def discover_watch_node_ids(payload: Any) -> list[str]:
    raw_nodes = payload.get("nodes") if isinstance(payload, dict) else None
    if not isinstance(raw_nodes, list):
        return []
    node_ids: list[str] = []
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            continue
        node_id = str(raw_node.get("node_id") or "").strip()
        if node_id and node_id not in node_ids:
            node_ids.append(node_id)
    return node_ids


def discover_watch_dates(payload: Any) -> list[date]:
    raw_dates = payload.get("dates") if isinstance(payload, dict) else None
    if isinstance(raw_dates, list) and raw_dates:
        return sorted(parse_iso_date(str(value)) for value in raw_dates)

    observations = payload.get("observations") if isinstance(payload, dict) else None
    if not isinstance(observations, list):
        return []
    dates = {
        parse_iso_date(str(row.get("date")))
        for row in observations
        if isinstance(row, dict) and row.get("date")
    }
    return sorted(dates)


def run_preview(
    *,
    nodes: list[AoiNode],
    target_dates: list[date],
    source_choice: str,
    timeout_seconds: float,
    poll_seconds: float,
    max_poll_seconds: float,
) -> list[dict[str, Any]]:
    if source_choice == "era5-land":
        return [
            unavailable_row(
                node=node,
                target_date=target_date,
                source_choice=source_choice,
                status="data_unavailable",
                api_status="NOT_RUN",
                api_error="ERA5-Land retrieval is not implemented in this sprint gate.",
            )
            for node in nodes
            for target_date in target_dates
        ]

    start_date = min(target_dates) - timedelta(days=13)
    end_date = max(target_dates)
    rows: list[dict[str, Any]] = []
    for node in nodes:
        try:
            daily_rain = fetch_chirps_daily_rainfall(
                geometry=node.geometry,
                start_date=start_date,
                end_date=end_date,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
                max_poll_seconds=max_poll_seconds,
            )
            rows.extend(build_chirps_rows(node, target_dates, daily_rain))
        except HydroClimateError as exc:
            safe_error = sanitize_text(str(exc))[:500]
            rows.extend(
                unavailable_row(
                    node=node,
                    target_date=target_date,
                    source_choice=source_choice,
                    status="api_error",
                    api_status="ERROR",
                    api_error=safe_error,
                )
                for target_date in target_dates
            )
    return rows


def build_chirps_rows(
    node: AoiNode,
    target_dates: list[date],
    daily_rain: dict[date, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target_date in target_dates:
        rain_24h = window_sum(daily_rain, target_date, days=1)
        rain_72h = window_sum(daily_rain, target_date, days=3)
        rain_7d = window_sum(daily_rain, target_date, days=7)
        rain_14d = window_sum(daily_rain, target_date, days=14)
        if any(value is None for value in (rain_24h, rain_72h, rain_7d, rain_14d)):
            rows.append(
                unavailable_row(
                    node=node,
                    target_date=target_date,
                    source_choice="chirps",
                    status="data_unavailable",
                    api_status="OK",
                    api_error="CHIRPS response was incomplete for at least one rainfall window.",
                )
            )
            continue

        status = classify_context(float(rain_72h), float(rain_7d), float(rain_14d))
        rows.append(
            {
                "node_id": node.node_id,
                "node_name": node.display_name,
                "target_date": target_date.isoformat(),
                "rain_24h_mm": format_mm(float(rain_24h)),
                "rain_72h_mm": format_mm(float(rain_72h)),
                "rain_7d_mm": format_mm(float(rain_7d)),
                "rain_14d_mm": format_mm(float(rain_14d)),
                "data_source": CHIRPS_DATA_SOURCE,
                "source_resolution": CHIRPS_SOURCE_RESOLUTION,
                "context_status": status,
                "review_priority_hint": REVIEW_HINT if status == "antecedent_rain_review" else NORMAL_HINT,
                "api_status": "OK",
                "api_error": "",
                "claim_limit": CLAIM_LIMIT,
            }
        )
    return rows


def classify_context(rain_72h_mm: float, rain_7d_mm: float, rain_14d_mm: float) -> str:
    if rain_72h_mm >= 50 or rain_7d_mm >= 75 or rain_14d_mm >= 120:
        return "antecedent_rain_review"
    return "normal_context"


def unavailable_row(
    *,
    node: AoiNode,
    target_date: date,
    source_choice: str,
    status: str,
    api_status: str,
    api_error: str,
) -> dict[str, Any]:
    data_source = (
        CHIRPS_DATA_SOURCE if source_choice == "chirps" else "ERA5-Land hourly precipitation"
    )
    source_resolution = (
        CHIRPS_SOURCE_RESOLUTION if source_choice == "chirps" else "not available"
    )
    return {
        "node_id": node.node_id,
        "node_name": node.display_name,
        "target_date": target_date.isoformat(),
        "rain_24h_mm": "",
        "rain_72h_mm": "",
        "rain_7d_mm": "",
        "rain_14d_mm": "",
        "data_source": data_source,
        "source_resolution": source_resolution,
        "context_status": status,
        "review_priority_hint": API_ERROR_HINT if status == "api_error" else UNAVAILABLE_HINT,
        "api_status": api_status,
        "api_error": sanitize_text(api_error)[:500],
        "claim_limit": CLAIM_LIMIT,
    }


def build_payload(
    *,
    rows: list[dict[str, Any]],
    nodes: list[AoiNode],
    target_dates: list[date],
    source_choice: str,
    source_notes: list[str],
) -> dict[str, Any]:
    counts = Counter(row["context_status"] for row in rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "public_safe": False,
        "preview_only": True,
        "source_selected": source_choice,
        "source_rejections": source_notes,
        "rows_total": len(rows),
        "nodes_total": len(nodes),
        "dates_total": len(target_dates),
        "context_status_counts": {
            "normal_context": counts.get("normal_context", 0),
            "antecedent_rain_review": counts.get("antecedent_rain_review", 0),
            "data_unavailable": counts.get("data_unavailable", 0),
            "api_error": counts.get("api_error", 0),
        },
        "claim_limit": CLAIM_LIMIT,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "nodes": [{"node_id": node.node_id, "node_name": node.display_name} for node in nodes],
        "dates": [target_date.isoformat() for target_date in target_dates],
        "rows": rows,
    }


def read_json(path: Path) -> Any:
    if not path.exists():
        raise HydroClimateError(f"Missing project data file: {display_path(path)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HydroClimateError(f"Project data file is not valid JSON: {display_path(path)}") from exc
    except OSError as exc:
        raise HydroClimateError(f"Could not read project data file: {display_path(path)}") from exc


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDNAMES})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def format_mm(value: float) -> str:
    return f"{value:.2f}"


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
