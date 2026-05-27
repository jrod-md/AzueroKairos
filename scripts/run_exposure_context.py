"""Create conservative agricultural/riparian exposure context rows.

This script intentionally does not infer exposure values without an official
land-cover pull. It prepares the Kairós Exposure schema and marks each node as
data_pending until CLMS land-cover composition can be computed from an official
raster source.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODES_CONFIG_PATH = Path("configs/aoi_nodes/nodes.yaml")
DEFAULT_PROCESSED_CSV = Path("outputs/processed_csv/exposure_node_context.csv")

LAND_COVER_SOURCE = (
    "Copernicus Land Monitoring Service Global Dynamic Land Cover "
    "(official pull pending)"
)
PENDING_NOTE = (
    "Kairós Exposure schema is prepared for official CLMS land-cover "
    "composition around each node. Values remain data_pending until a CLMS/CDSE "
    "raster pull and zonal summary are completed. No crop types, farm "
    "boundaries, private producers, contamination, or water-safety claims are "
    "inferred."
)

PROCESSED_FIELDNAMES = [
    "node_id",
    "node_display_name",
    "aoi",
    "land_cover_source",
    "agricultural_exposure_status",
    "riparian_context_status",
    "exposure_confidence",
    "api_status",
    "api_error",
    "notes",
]

ALLOWED_STATUSES = {"exposure_available", "data_pending", "data_unavailable"}

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]


class ExposureContextError(RuntimeError):
    """Raised when exposure context setup cannot complete."""


@dataclass(frozen=True)
class AoiNode:
    node_id: str
    display_name: str
    geojson_path: Path
    aoi: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create Kairós Exposure context rows for AOI nodes. The current MVP "
            "exports data_pending rows unless an official CLMS pull has been "
            "added in a future iteration."
        )
    )
    parser.add_argument(
        "--nodes-config",
        default=str(DEFAULT_NODES_CONFIG_PATH),
        help="Path to configs/aoi_nodes/nodes.yaml.",
    )
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV))
    args = parser.parse_args(argv)

    try:
        nodes = load_nodes(Path(args.nodes_config))
    except ExposureContextError as exc:
        print(f"Kairós Exposure failed safely: {exc}", file=sys.stderr)
        return 1

    rows = [pending_row(node) for node in nodes]
    processed_csv = resolve_project_path(args.processed_csv)
    write_processed_csv(processed_csv, rows)

    print(f"Nodes processed: {len(nodes)}")
    print(f"Rows exposure_available: {count_status(rows, 'exposure_available')}")
    print(f"Rows data_pending: {count_status(rows, 'data_pending')}")
    print(f"Rows data_unavailable: {count_status(rows, 'data_unavailable')}")
    print(f"Output CSV path: {display_path(processed_csv)}")
    print("Real CLMS land-cover values obtained: no")
    return 0


def pending_row(node: AoiNode) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "node_display_name": node.display_name,
        "aoi": node.aoi,
        "land_cover_source": LAND_COVER_SOURCE,
        "agricultural_exposure_status": "data_pending",
        "riparian_context_status": "data_pending",
        "exposure_confidence": "data_pending",
        "api_status": "PENDING_OFFICIAL_CLMS_PULL",
        "api_error": "",
        "notes": PENDING_NOTE,
    }


def load_nodes(path: Path) -> list[AoiNode]:
    nodes_path = resolve_project_path(path)
    if not nodes_path.exists():
        raise ExposureContextError(f"Missing nodes config: {display_path(nodes_path)}")

    try:
        nodes_text = nodes_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExposureContextError(
            f"Could not read nodes config: {display_path(nodes_path)}"
        ) from exc

    payload = load_nodes_payload(nodes_text)
    raw_nodes = payload.get("nodes") if isinstance(payload, dict) else None
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ExposureContextError("nodes.yaml must contain a non-empty 'nodes' list.")

    nodes: list[AoiNode] = []
    for index, raw_node in enumerate(raw_nodes, start=1):
        if not isinstance(raw_node, dict):
            raise ExposureContextError(f"Node entry {index} is not an object.")

        node_id = str(raw_node.get("node_id") or "").strip()
        display_name = str(raw_node.get("display_name") or node_id).strip()
        raw_geojson_path = str(raw_node.get("geojson_path") or "").strip()
        if not node_id or not raw_geojson_path:
            raise ExposureContextError(
                f"Node entry {index} requires node_id and geojson_path."
            )

        geojson_path = resolve_project_path(raw_geojson_path)
        aoi = load_aoi_name(geojson_path, fallback=node_id)
        nodes.append(
            AoiNode(
                node_id=node_id,
                display_name=display_name,
                geojson_path=geojson_path,
                aoi=aoi,
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
        raise ExposureContextError("Could not parse nodes.yaml.") from exc
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
        raise ExposureContextError(f"Unsupported nodes.yaml line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip().strip('"').strip("'")


def load_aoi_name(path: Path, *, fallback: str) -> str:
    if not path.exists():
        raise ExposureContextError(f"Node GeoJSON does not exist: {display_path(path)}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ExposureContextError(
            f"Could not read node GeoJSON: {display_path(path)}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ExposureContextError(
            f"Node GeoJSON is not valid JSON: {display_path(path)}"
        ) from exc

    raw_name = payload.get("name") or fallback
    feature: dict[str, Any] | None = None
    if payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if isinstance(features, list) and features and isinstance(features[0], dict):
            feature = features[0]
    elif payload.get("type") == "Feature":
        feature = payload

    if feature:
        properties = feature.get("properties")
        if isinstance(properties, dict):
            raw_name = properties.get("id") or properties.get("name") or raw_name
        if not isinstance(feature.get("geometry"), dict):
            raise ExposureContextError("Node GeoJSON feature is missing geometry.")
    elif not isinstance(payload.get("coordinates"), list):
        raise ExposureContextError("Node GeoJSON does not contain a valid geometry.")

    return normalize_aoi_name(str(raw_name))


def normalize_aoi_name(raw_name: str) -> str:
    value = raw_name.strip()
    if value.startswith("aoi_"):
        return value[4:]
    return value


def count_status(rows: list[dict[str, Any]], status: str) -> int:
    return sum(
        1
        for row in rows
        if row.get("agricultural_exposure_status") == status
        or row.get("riparian_context_status") == status
    )


def write_processed_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        validate_row(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROCESSED_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PROCESSED_FIELDNAMES})


def validate_row(row: dict[str, Any]) -> None:
    for field in ("agricultural_exposure_status", "riparian_context_status"):
        status = str(row.get(field) or "")
        if status not in ALLOWED_STATUSES:
            raise ExposureContextError(f"Invalid {field}: {status}")


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
