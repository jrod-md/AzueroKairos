"""Export frontend-safe Kairos Exposure context JSON."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_CSV = PROJECT_ROOT / "outputs/processed_csv/exposure_node_context.csv"
DEFAULT_CLMS_PREVIEW_JSON = PROJECT_ROOT / "outputs/exposure/clms_exposure_preview.json"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/exposure_context.json"

SCHEMA_VERSION = "clms_exposure_v1"
REQUIRED_NODE_IDS = ("la_villa_oeste", "la_villa_central", "la_villa_este")
REQUIRED_CLMS_NODE_FIELDS = (
    "node_id",
    "exposure_status",
    "source_dataset",
    "reference_year",
    "source_resolution_m",
    "analysis_resolution_m",
    "grid_width",
    "grid_height",
    "max_grid_dimension",
    "resolution_strategy",
    "histogram_count_unit",
    "total_samples",
    "valid_samples",
    "total_area_ha",
    "class_histogram",
    "class_percentages",
    "cropland_agriculture_pct",
    "tree_vegetation_pct",
    "water_wetland_pct",
    "built_bare_other_pct",
    "class_labels",
    "claim_limit",
)

ALLOWED_STATUSES = {"exposure_available", "data_pending", "data_unavailable"}
STATUS_ORDER = ("exposure_available", "data_pending", "data_unavailable")

CLAIM_LIMIT = (
    "Contexto territorial CLMS 2020. Capa auxiliar; no se usa como evidencia "
    "principal y no sustituye verificación territorial, laboratorio ni autoridad "
    "competente."
)
ANALYSIS_NOTE = (
    "Resumen territorial derivado de CLMS Global Dynamic Land Cover 10m Annual "
    "V1, año de referencia 2020. El análisis usa muestreo estadístico "
    "adaptativo para mantener la consulta dentro de límites de grilla de la API."
)
NODE_NOTE = (
    "Contexto territorial auxiliar por nodo. No modifica la clasificación "
    "Sentinel-2 ni la decisión pública de confianza."
)
PENDING_NOTE = (
    "Capa de exposición preparada en esquema. Valores territoriales pendientes; "
    "no se usa como evidencia principal."
)


def redaction_patterns() -> list[re.Pattern[str]]:
    parts = [
        r"(?i)(bear" + r"er\s+)[A-Za-z0-9._~+/=-]+",
        r"(?i)(author" + r"ization\s*[:=]\s*)[^\s,;]+",
        r"(?i)(client_" + r"sec" + r"ret\s*[:=]\s*)[^\s,;]+",
        r"(?i)(access_" + r"to" + r"ken\s*[:=]\s*)[^\s,;]+",
        r"(?i)(refresh_" + r"to" + r"ken\s*[:=]\s*)[^\s,;]+",
    ]
    return [re.compile(part) for part in parts]


REDACTION_PATTERNS = redaction_patterns()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export safe public JSON for the Kairos Exposure context layer."
    )
    parser.add_argument("--source-csv", default=str(DEFAULT_SOURCE_CSV))
    parser.add_argument("--clms-preview-json", default=str(DEFAULT_CLMS_PREVIEW_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    args = parser.parse_args(argv)

    source_csv = Path(args.source_csv)
    clms_preview_json = Path(args.clms_preview_json)
    output_json = Path(args.output_json)

    payload = try_build_clms_payload(clms_preview_json)
    if payload is None:
        payload = build_pending_payload(source_csv)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_json, payload)

    print(f"Output path: {display_path(output_json)}")
    print(f"Data status: {payload.get('data_status')}")
    print(f"Nodes: {len(payload.get('nodes', []))}")
    print("Public export sanitized: no credential-like strings or absolute local paths.")
    return 0


def try_build_clms_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"CLMS preview unavailable, using pending fallback: {exc}", file=sys.stderr)
        return None

    try:
        return build_clms_payload(payload, path)
    except ValueError as exc:
        print(f"CLMS preview invalid, using pending fallback: {exc}", file=sys.stderr)
        return None


def build_clms_payload(payload: dict[str, Any], source_path: Path) -> dict[str, Any]:
    source_dataset = required_clean(payload, "source_dataset")
    collection_id = required_clean(payload, "collection_id")
    reference_year = required_number(payload, "reference_year")
    source_resolution_m = required_number(payload, "source_resolution_m")
    resolution_strategy = required_clean(payload, "resolution_strategy")
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, list):
        raise ValueError("CLMS preview must include a nodes list.")

    nodes_by_id = {clean(row.get("node_id")): row for row in raw_nodes if isinstance(row, dict)}
    missing_nodes = [node_id for node_id in REQUIRED_NODE_IDS if node_id not in nodes_by_id]
    if missing_nodes:
        raise ValueError(f"Missing required nodes: {', '.join(missing_nodes)}")

    public_nodes = [
        build_clms_node(
            nodes_by_id[node_id],
            source_dataset=source_dataset,
            collection_id=collection_id,
            reference_year=reference_year,
            source_resolution_m=source_resolution_m,
            resolution_strategy=resolution_strategy,
        )
        for node_id in REQUIRED_NODE_IDS
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "source_preview_json": relative_artifact_path(source_path),
        "layer_type": "exposure_context_only",
        "public_safe": True,
        "data_status": "exposure_available",
        "source_dataset": source_dataset,
        "collection_id": collection_id,
        "reference_year": reference_year,
        "source_resolution_m": source_resolution_m,
        "analysis_note": ANALYSIS_NOTE,
        "resolution_strategy": resolution_strategy,
        "claim_limit": CLAIM_LIMIT,
        "nodes": public_nodes,
        "observations": public_nodes,
        "summary_by_node": build_clms_summaries(public_nodes),
    }


def build_clms_node(
    row: dict[str, Any],
    *,
    source_dataset: str,
    collection_id: str,
    reference_year: int | float,
    source_resolution_m: int | float,
    resolution_strategy: str,
) -> dict[str, Any]:
    merged = {
        **row,
        "source_dataset": source_dataset,
        "collection_id": collection_id,
        "reference_year": reference_year,
        "source_resolution_m": source_resolution_m,
        "resolution_strategy": resolution_strategy,
    }
    missing_fields = [
        field
        for field in REQUIRED_CLMS_NODE_FIELDS
        if field not in merged or merged.get(field) in ("", None)
    ]
    if missing_fields:
        raise ValueError(f"{clean(row.get('node_id')) or 'node'} missing fields: {missing_fields}")
    if clean(merged.get("exposure_status")) != "exposure_available":
        raise ValueError(f"{merged.get('node_id')} is not exposure_available.")
    if number_value(merged.get("valid_samples")) <= 0:
        raise ValueError(f"{merged.get('node_id')} has no valid samples.")
    if number_value(merged.get("total_samples")) <= 0:
        raise ValueError(f"{merged.get('node_id')} has no total samples.")
    if not isinstance(merged.get("class_histogram"), dict) or not merged["class_histogram"]:
        raise ValueError(f"{merged.get('node_id')} has no class histogram.")
    if not isinstance(merged.get("class_percentages"), dict) or not merged["class_percentages"]:
        raise ValueError(f"{merged.get('node_id')} has no class percentages.")
    for field in (
        "cropland_agriculture_pct",
        "tree_vegetation_pct",
        "water_wetland_pct",
        "built_bare_other_pct",
    ):
        number_value(merged.get(field))

    return {
        "node_id": clean(merged.get("node_id")),
        "node_name": clean(merged.get("node_name")),
        "exposure_status": "exposure_available",
        "source_dataset": source_dataset,
        "collection_id": collection_id,
        "reference_year": int(reference_year),
        "source_resolution_m": number_value(source_resolution_m),
        "analysis_resolution_m": number_value(merged.get("analysis_resolution_m")),
        "grid_width": int(number_value(merged.get("grid_width"))),
        "grid_height": int(number_value(merged.get("grid_height"))),
        "max_grid_dimension": int(number_value(merged.get("max_grid_dimension"))),
        "resolution_strategy": resolution_strategy,
        "histogram_count_unit": clean(merged.get("histogram_count_unit")),
        "total_samples": int(number_value(merged.get("total_samples"))),
        "valid_samples": int(number_value(merged.get("valid_samples"))),
        "total_area_ha": number_value(merged.get("total_area_ha")),
        "class_histogram": normalize_numeric_mapping(merged.get("class_histogram")),
        "class_percentages": normalize_numeric_mapping(merged.get("class_percentages")),
        "cropland_agriculture_pct": number_value(merged.get("cropland_agriculture_pct")),
        "tree_vegetation_pct": number_value(merged.get("tree_vegetation_pct")),
        "water_wetland_pct": number_value(merged.get("water_wetland_pct")),
        "built_bare_other_pct": number_value(merged.get("built_bare_other_pct")),
        "class_labels": normalize_text_mapping(merged.get("class_labels")),
        "aoi_or_buffer_source": relative_artifact_path(merged.get("aoi_or_buffer_source")),
        "claim_limit": CLAIM_LIMIT,
        "notes": NODE_NOTE,
    }


def build_clms_summaries(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node["node_id"],
            "node_name": node["node_name"],
            "exposure_status": node["exposure_status"],
            "total_area_ha": node["total_area_ha"],
            "cropland_agriculture_pct": node["cropland_agriculture_pct"],
            "tree_vegetation_pct": node["tree_vegetation_pct"],
            "water_wetland_pct": node["water_wetland_pct"],
            "built_bare_other_pct": node["built_bare_other_pct"],
            "analysis_resolution_m": node["analysis_resolution_m"],
            "resolution_strategy": node["resolution_strategy"],
        }
        for node in nodes
    ]


def build_pending_payload(source_csv: Path) -> dict[str, Any]:
    if not source_csv.exists():
        print(f"Missing source CSV: {display_path(source_csv)}", file=sys.stderr)
        return {
            "schema_version": SCHEMA_VERSION,
            "source_csv": relative_artifact_path(source_csv),
            "layer_type": "exposure_context_only",
            "public_safe": True,
            "data_status": "data_unavailable",
            "analysis_note": PENDING_NOTE,
            "claim_limit": CLAIM_LIMIT,
            "nodes": [],
            "observations": [],
            "summary_by_node": [],
        }

    rows = read_csv_rows(source_csv)
    observations = [build_pending_observation(row) for row in rows]
    validate_public_statuses(observations)
    nodes = build_pending_nodes(observations)
    summary_by_node = build_pending_summaries(observations)

    return {
        "schema_version": SCHEMA_VERSION,
        "source_csv": relative_artifact_path(source_csv),
        "layer_type": "exposure_context_only",
        "public_safe": True,
        "data_status": derive_payload_status(observations),
        "analysis_note": PENDING_NOTE,
        "claim_limit": CLAIM_LIMIT,
        "nodes": nodes,
        "observations": observations,
        "summary_by_node": summary_by_node,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_pending_observation(row: dict[str, str]) -> dict[str, Any]:
    return {
        "node_id": clean(row.get("node_id")),
        "node_display_name": clean(row.get("node_display_name")),
        "aoi": clean(row.get("aoi")),
        "land_cover_source": clean(row.get("land_cover_source")),
        "agricultural_exposure_status": clean(row.get("agricultural_exposure_status")),
        "riparian_context_status": clean(row.get("riparian_context_status")),
        "exposure_confidence": clean(row.get("exposure_confidence")),
        "api_status": clean(row.get("api_status")),
        "api_error": sanitize_text(row.get("api_error")),
        "notes": sanitize_text(row.get("notes")) or PENDING_NOTE,
    }


def validate_public_statuses(observations: list[dict[str, Any]]) -> None:
    for row in observations:
        for field in ("agricultural_exposure_status", "riparian_context_status"):
            status = clean(row.get(field))
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"Invalid {field}: {status}")


def build_pending_nodes(observations: list[dict[str, Any]]) -> list[dict[str, str]]:
    nodes_by_id: dict[str, dict[str, str]] = {}
    for row in observations:
        node_id = clean(row.get("node_id"))
        if not node_id or node_id in nodes_by_id:
            continue
        nodes_by_id[node_id] = {
            "node_id": node_id,
            "display_name": clean(row.get("node_display_name")),
            "aoi": clean(row.get("aoi")),
        }
    return [nodes_by_id[node_id] for node_id in sorted(nodes_by_id)]


def build_pending_summaries(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "node_id": clean(row.get("node_id")),
            "display_name": clean(row.get("node_display_name")),
            "aoi": clean(row.get("aoi")),
            "agricultural_exposure_status": clean(row.get("agricultural_exposure_status")),
            "riparian_context_status": clean(row.get("riparian_context_status")),
            "exposure_confidence": clean(row.get("exposure_confidence")),
        }
        for row in sorted(observations, key=lambda item: clean(item.get("node_id")))
    ]


def derive_payload_status(observations: list[dict[str, Any]]) -> str:
    if not observations:
        return "data_unavailable"
    if any(row.get("agricultural_exposure_status") == "exposure_available" for row in observations):
        return "exposure_available"
    if any(row.get("agricultural_exposure_status") == "data_pending" for row in observations):
        return "data_pending"
    return "data_unavailable"


def count_status(observations: list[dict[str, Any]], status: str) -> int:
    return sum(
        1
        for row in observations
        if row.get("agricultural_exposure_status") == status
        or row.get("riparian_context_status") == status
    )


def required_clean(payload: dict[str, Any], key: str) -> str:
    value = clean(payload.get(key))
    if not value:
        raise ValueError(f"Missing {key}.")
    return value


def required_number(payload: dict[str, Any], key: str) -> int | float:
    value = number_value(payload.get(key))
    if value <= 0:
        raise ValueError(f"Invalid {key}.")
    return value


def number_value(value: Any) -> int | float:
    if isinstance(value, bool):
        raise ValueError("Boolean is not a numeric metric.")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"Invalid numeric value: {value}") from exc
        return int(parsed) if parsed.is_integer() else round(parsed, 4)
    raise ValueError(f"Invalid numeric value: {value}")


def normalize_numeric_mapping(value: Any) -> dict[str, int | float]:
    if not isinstance(value, dict):
        raise ValueError("Expected numeric mapping.")
    return {str(key): number_value(metric) for key, metric in sorted(value.items())}


def normalize_text_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("Expected text mapping.")
    return {str(key): clean(metric) for key, metric in sorted(value.items())}


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def sanitize_text(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    for pattern in REDACTION_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "[redacted]", text)
    return " ".join(text.split())[:700]


def relative_artifact_path(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""

    path = Path(text)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return path.name
    return text.replace("\\", "/")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
