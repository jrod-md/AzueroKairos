"""Export frontend-safe Sentinel-1 SAR auxiliary context JSON."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREVIEW_JSON = PROJECT_ROOT / "outputs/sar/sentinel1_node_context_preview.json"
DEFAULT_PREVIEW_CSV = PROJECT_ROOT / "outputs/sar/sentinel1_node_context_preview.csv"
DEFAULT_FALLBACK_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel1_node_context.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/sar_context.json"
SOURCE_DATASET = "sentinel-1-grd"
SCHEMA_VERSION = "sar_context_v2"
TOP_LEVEL_CLAIM_LIMIT = (
    "Contexto Sentinel-1 SAR auxiliar. No modifica la clasificacion Sentinel-2 "
    "ni sustituye verificacion territorial, laboratorio o autoridad competente."
)
ROW_CLAIM_LIMIT = "Contexto SAR auxiliar; no usado como evidencia principal."
SUMMARY_TEXT = (
    "Sentinel-1 SAR aporta continuidad de observacion en ventanas temporales "
    "ampliadas. Cuando la adquisicion radar no coincide con la fecha objetivo, "
    "se reporta la ventana y la fecha SAR asociada."
)

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]
ENV_CREDENTIAL_PATTERNS = [
    re.compile(r"CDSE_CLIENT_ID", re.IGNORECASE),
    re.compile(r"CDSE_CLIENT_SECRET", re.IGNORECASE),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export safe public JSON for the Sentinel-1 SAR auxiliary layer."
    )
    parser.add_argument("--preview-json", default=str(DEFAULT_PREVIEW_JSON))
    parser.add_argument("--preview-csv", default=str(DEFAULT_PREVIEW_CSV))
    parser.add_argument("--fallback-csv", default=str(DEFAULT_FALLBACK_CSV))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    args = parser.parse_args(argv)

    preview_json = Path(args.preview_json)
    preview_csv = Path(args.preview_csv)
    fallback_csv = Path(args.fallback_csv)
    output_json = Path(args.output_json)

    rows, export_source, source_path = load_best_available_rows(
        preview_json=preview_json,
        preview_csv=preview_csv,
        fallback_csv=fallback_csv,
    )
    payload = build_public_payload(rows, export_source=export_source, source_path=source_path)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_json, payload)

    print(f"Output path: {display_path(output_json)}")
    print(f"Export source: {export_source}")
    print(f"Source path: {display_path(source_path)}")
    print(f"Rows: {payload['rows_total']}")
    print(f"SAR available rows: {payload['sar_context_available_count']}")
    print(f"SAR no-acquisition rows: {payload['sar_no_acquisition_count']}")
    print(f"SAR low-observation rows: {payload['sar_low_observation_count']}")
    print(f"SAR API error rows: {payload['sar_api_error_count']}")
    print("Public export sanitized: no credentials, headers, or raw request bodies.")
    return 0


def load_best_available_rows(
    *,
    preview_json: Path,
    preview_csv: Path,
    fallback_csv: Path,
) -> tuple[list[dict[str, Any]], str, Path]:
    json_rows = load_preview_json_rows(preview_json)
    if valid_preview_rows(json_rows):
        return json_rows, "windowed_preview_json", preview_json

    csv_rows = read_csv_rows(preview_csv) if preview_csv.exists() else []
    if valid_preview_rows(csv_rows):
        return csv_rows, "windowed_preview_csv", preview_csv

    if not fallback_csv.exists():
        print(
            "Missing valid SAR preview and fallback CSV; exporting demoted empty SAR context.",
            file=sys.stderr,
        )
        return [], "demoted_missing_source", fallback_csv

    return read_csv_rows(fallback_csv), "demoted_same_day_fallback_csv", fallback_csv


def load_preview_json_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else []


def valid_preview_rows(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    required = {
        "node_id",
        "target_date",
        "sar_window_start",
        "sar_window_end",
        "window_days",
        "context_status",
        "api_status",
    }
    return all(isinstance(row, dict) and required.issubset(row.keys()) for row in rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_public_payload(
    rows: list[dict[str, Any]],
    *,
    export_source: str,
    source_path: Path,
) -> dict[str, Any]:
    public_rows = [build_public_row(row) for row in rows]
    counts = Counter(clean(row.get("context_status")) for row in public_rows)
    available_count = counts.get("sar_context_available", 0)

    return {
        "schema_version": SCHEMA_VERSION,
        "public_safe": True,
        "data_status": "sar_context_available"
        if available_count > 0
        else "sar_context_unavailable",
        "source_dataset": SOURCE_DATASET,
        "source_type": export_source,
        "source_path": relative_artifact_path(source_path),
        "rows_total": len(public_rows),
        "sar_context_available_count": available_count,
        "sar_no_acquisition_count": counts.get("sar_no_acquisition", 0),
        "sar_low_observation_count": counts.get("sar_low_observation", 0),
        "sar_api_error_count": counts.get("sar_api_error", 0)
        + counts.get("sar_error", 0),
        "claim_limit": TOP_LEVEL_CLAIM_LIMIT,
        "summary": SUMMARY_TEXT,
        "nodes": build_nodes(public_rows),
        "dates": sorted(
            {clean(row.get("target_date")) for row in public_rows if row.get("target_date")}
        ),
        "summary_by_node": build_node_summaries(public_rows),
        "rows": public_rows,
    }


def build_public_row(row: dict[str, Any]) -> dict[str, Any]:
    target_date = clean(row.get("target_date") or row.get("date"))
    node_name = clean(row.get("node_name") or row.get("node_display_name"))
    context_status = normalize_context_status(row.get("context_status"))

    return {
        "node_id": clean(row.get("node_id")),
        "node_name": node_name,
        "target_date": target_date,
        "sar_window_start": clean(row.get("sar_window_start") or target_date),
        "sar_window_end": clean(row.get("sar_window_end") or target_date),
        "window_days": as_number(row.get("window_days")),
        "matched_acquisition_date": clean(row.get("matched_acquisition_date")),
        "source_dataset": clean(row.get("source_dataset")) or SOURCE_DATASET,
        "polarization": clean(row.get("polarization")),
        "orbit_direction": clean(row.get("orbit_direction")),
        "vv_mean": as_number(row.get("vv_mean")),
        "vh_mean": as_number(row.get("vh_mean")),
        "vv_vh_ratio": as_number(row.get("vv_vh_ratio")),
        "sampleCount": as_number(row.get("sampleCount")),
        "validPercent": as_number(row.get("validPercent")),
        "context_status": context_status,
        "api_status": clean(row.get("api_status")),
        "api_error": sanitize_text(row.get("api_error")),
        "claim_limit": ROW_CLAIM_LIMIT,
    }


def normalize_context_status(value: Any) -> str:
    status = clean(value)
    if status == "sar_error":
        return "sar_api_error"
    return status


def build_nodes(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    nodes_by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        node_id = clean(row.get("node_id"))
        if not node_id or node_id in nodes_by_id:
            continue
        nodes_by_id[node_id] = {
            "node_id": node_id,
            "node_name": clean(row.get("node_name")),
        }
    return [nodes_by_id[node_id] for node_id in sorted(nodes_by_id)]


def build_node_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        node_id = clean(row.get("node_id"))
        if node_id:
            grouped.setdefault(node_id, []).append(row)

    summaries: list[dict[str, Any]] = []
    for node_id in sorted(grouped):
        node_rows = sorted(grouped[node_id], key=lambda row: clean(row.get("target_date")))
        valid_values = [
            float(row["validPercent"])
            for row in node_rows
            if isinstance(row.get("validPercent"), int | float)
        ]
        summaries.append(
            {
                "node_id": node_id,
                "node_name": clean(node_rows[0].get("node_name")),
                "rows_total": len(node_rows),
                "sar_context_available_count": count_status(
                    node_rows, "sar_context_available"
                ),
                "sar_no_acquisition_count": count_status(
                    node_rows, "sar_no_acquisition"
                ),
                "sar_low_observation_count": count_status(
                    node_rows, "sar_low_observation"
                ),
                "sar_api_error_count": count_status(node_rows, "sar_api_error"),
                "mean_validPercent": round(sum(valid_values) / len(valid_values), 2)
                if valid_values
                else "",
            }
        )
    return summaries


def count_status(rows: list[dict[str, Any]], context_status: str) -> int:
    return sum(1 for row in rows if row.get("context_status") == context_status)


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def sanitize_text(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "[redacted]", text)
    for pattern in ENV_CREDENTIAL_PATTERNS:
        text = pattern.sub("[credential_variable]", text)
    return text[:500]


def as_number(value: Any) -> int | float | str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return int(number)
    return number


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
    return path.as_posix()


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
