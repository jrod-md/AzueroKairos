"""Run the official Azuero Kairós Sentinel-2 batch across AOI nodes."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from azuero_kairos.sentinel2_stats import (  # noqa: E402
    DEFAULT_RESOLUTION_M,
    DEFAULT_SLEEP_SECONDS,
    OFFICIAL_DATES,
    Sentinel2StatsError,
    error_row,
    estimate_request_grid_from_path,
    format_request_grid_estimate,
    raw_response_path,
    run_stats_rows,
    validate_request_grid,
)


DEFAULT_NODES_CONFIG_PATH = Path("configs/aoi_nodes/nodes.yaml")
DEFAULT_NODE_RAW_JSON_DIR = Path("outputs/raw_json/nodes")
DEFAULT_NODE_PROCESSED_CSV_PATH = Path(
    "outputs/processed_csv/sentinel2_node_confidence.csv"
)

NODE_FIELDNAMES = [
    "node_id",
    "node_display_name",
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
    "api_status",
    "api_error",
    "raw_json_path",
]


@dataclass(frozen=True)
class AoiNode:
    node_id: str
    display_name: str
    geojson_path: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run official Sentinel-2 confidence batches for Azuero AOI nodes."
    )
    parser.add_argument(
        "--nodes-config",
        default=str(DEFAULT_NODES_CONFIG_PATH),
        help="Path to configs/aoi_nodes/nodes.yaml.",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=DEFAULT_RESOLUTION_M,
        help="Spatial resolution in meters.",
    )
    parser.add_argument("--force", action="store_true", help="Ignore cached raw JSON.")
    parser.add_argument("--raw-json-dir", default=str(DEFAULT_NODE_RAW_JSON_DIR))
    parser.add_argument("--processed-csv", default=str(DEFAULT_NODE_PROCESSED_CSV_PATH))
    parser.add_argument("--sleep-seconds", type=float, default=DEFAULT_SLEEP_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    try:
        nodes = load_nodes(Path(args.nodes_config))
    except Sentinel2StatsError as exc:
        print(f"Official Sentinel-2 node batch failed safely: {exc}", file=sys.stderr)
        return 1

    raw_json_dir = Path(args.raw_json_dir)
    processed_csv_path = Path(args.processed_csv)
    rows: list[dict[str, Any]] = []

    for node in nodes:
        try:
            preflight = estimate_request_grid_from_path(
                node.geojson_path,
                resolution_m=args.resolution,
            )
            print(format_request_grid_estimate(preflight))
            validate_request_grid(preflight)
            node_rows = run_stats_rows(
                aoi_path=node.geojson_path,
                dates=OFFICIAL_DATES,
                resolution_m=args.resolution,
                raw_json_dir=raw_json_dir,
                sleep_seconds=args.sleep_seconds,
                request_timeout_seconds=args.timeout_seconds,
                force=args.force,
            )
        except Sentinel2StatsError as exc:
            node_rows = [
                error_row(
                    target_date=target_date,
                    aoi_name=node.node_id,
                    resolution_m=args.resolution,
                    raw_path=raw_response_path(
                        raw_json_dir,
                        target_date=target_date,
                        aoi_name=node.node_id,
                        resolution_m=args.resolution,
                    ),
                    api_error=str(exc),
                )
                for target_date in OFFICIAL_DATES
            ]

        rows.extend(add_node_columns(node_rows, node))

    write_node_csv(processed_csv_path, rows)
    ok_rows = count_ok_rows(rows)
    error_rows = count_error_rows(rows)

    print(f"Nodes processed: {len(nodes)}")
    print(f"Dates processed: {len(OFFICIAL_DATES)}")
    print(f"Rows OK: {ok_rows}")
    print(f"Rows with errors: {error_rows}")
    print(f"Output CSV path: {processed_csv_path}")
    return 1 if error_rows else 0


def load_nodes(path: Path) -> list[AoiNode]:
    nodes_path = resolve_project_path(path)
    if not nodes_path.exists():
        raise Sentinel2StatsError(f"Missing nodes config: {nodes_path}")

    try:
        nodes_text = nodes_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Sentinel2StatsError(f"Could not read nodes config: {nodes_path}") from exc

    payload = load_nodes_payload(nodes_text)
    raw_nodes = payload.get("nodes") if isinstance(payload, dict) else None
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise Sentinel2StatsError("nodes.yaml must contain a non-empty 'nodes' list.")

    nodes: list[AoiNode] = []
    for index, raw_node in enumerate(raw_nodes, start=1):
        if not isinstance(raw_node, dict):
            raise Sentinel2StatsError(f"Node entry {index} is not an object.")

        node_id = str(raw_node.get("node_id") or "").strip()
        display_name = str(raw_node.get("display_name") or node_id).strip()
        raw_geojson_path = str(raw_node.get("geojson_path") or "").strip()
        if not node_id or not raw_geojson_path:
            raise Sentinel2StatsError(
                f"Node entry {index} requires node_id and geojson_path."
            )

        geojson_path = resolve_project_path(raw_geojson_path)
        if not geojson_path.exists():
            raise Sentinel2StatsError(
                f"Node '{node_id}' GeoJSON does not exist: {geojson_path}"
            )

        nodes.append(
            AoiNode(
                node_id=node_id,
                display_name=display_name,
                geojson_path=geojson_path,
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
        raise Sentinel2StatsError("Could not parse nodes.yaml.") from exc
    return payload if isinstance(payload, dict) else {}


def parse_simple_nodes_yaml(nodes_text: str) -> dict[str, Any]:
    """Parse the small official nodes.yaml shape without requiring PyYAML."""

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
        raise Sentinel2StatsError(f"Unsupported nodes.yaml line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip().strip('"').strip("'")


def add_node_columns(rows: list[dict[str, Any]], node: AoiNode) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node.node_id,
            "node_display_name": node.display_name,
            **row,
        }
        for row in rows
    ]


def write_node_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=NODE_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in NODE_FIELDNAMES})


def count_error_rows(rows: list[dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("api_status") == "ERROR" or bool(row.get("api_error"))
    )


def count_ok_rows(rows: list[dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("api_status") == "OK" and not row.get("api_error")
    )


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
