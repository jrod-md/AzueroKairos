"""Export frontend-safe HydroClimate context JSON from node rainfall CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_CSV = PROJECT_ROOT / "outputs/processed_csv/hydroclimate_node_context.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/hydroclimate_context.json"

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]

STATUS_ORDER = (
    "dry_or_low_rain",
    "normal_context",
    "antecedent_rain",
    "heavy_rain_context",
    "data_unavailable",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export safe public JSON for the HydroClimate context layer."
    )
    parser.add_argument("--source-csv", default=str(DEFAULT_SOURCE_CSV))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    args = parser.parse_args(argv)

    source_csv = Path(args.source_csv)
    output_json = Path(args.output_json)

    if not source_csv.exists():
        print(f"Missing source CSV: {display_path(source_csv)}", file=sys.stderr)
        return 1

    rows = read_csv_rows(source_csv)
    observations = [build_public_observation(row) for row in rows]
    nodes = build_nodes(observations)
    dates = sorted({clean(row.get("date")) for row in observations if row.get("date")})
    summary_by_node = build_node_summaries(observations)

    payload = {
        "source_csv": relative_artifact_path(source_csv),
        "layer_type": "hydroclimate_context_only",
        "data_source": "CHIRPS daily rainfall via ClimateSERV",
        "public_safe": True,
        "thresholds": {
            "heavy_rain_context": "rain_72h_mm >= 50",
            "antecedent_rain": "rain_7d_mm >= 75",
            "note": "MVP contextual thresholds only; not regulatory thresholds.",
        },
        "claim_limit": (
            "Contexto hidroclimatico auxiliar. No modifica la clasificacion "
            "Sentinel-2 ni sustituye verificacion territorial, laboratorio o "
            "autoridad competente."
        ),
        "nodes": nodes,
        "dates": dates,
        "observations": observations,
        "summary_by_node": summary_by_node,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_json, payload)

    print(f"Output path: {display_path(output_json)}")
    print(f"Nodes: {len(nodes)}")
    print(f"Observation rows: {len(observations)}")
    for status in STATUS_ORDER:
        print(f"{status}: {count_status(observations, status)}")
    print("Public export sanitized: no secrets, tokens, or absolute local paths.")
    return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_public_observation(row: dict[str, str]) -> dict[str, Any]:
    return {
        "node_id": clean(row.get("node_id")),
        "node_display_name": clean(row.get("node_display_name")),
        "date": clean(row.get("date")),
        "rain_24h_mm": as_number(row.get("rain_24h_mm")),
        "rain_72h_mm": as_number(row.get("rain_72h_mm")),
        "rain_7d_mm": as_number(row.get("rain_7d_mm")),
        "hydroclimate_status": clean(row.get("hydroclimate_status")),
        "recommended_context_action": clean(row.get("recommended_context_action")),
        "data_source": clean(row.get("data_source")),
        "api_status": clean(row.get("api_status")),
        "api_error": sanitize_text(row.get("api_error")),
    }


def build_nodes(observations: list[dict[str, Any]]) -> list[dict[str, str]]:
    nodes_by_id: dict[str, dict[str, str]] = {}
    for row in observations:
        node_id = clean(row.get("node_id"))
        if not node_id or node_id in nodes_by_id:
            continue
        nodes_by_id[node_id] = {
            "node_id": node_id,
            "display_name": clean(row.get("node_display_name")),
        }
    return [nodes_by_id[node_id] for node_id in sorted(nodes_by_id)]


def build_node_summaries(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in observations:
        node_id = clean(row.get("node_id"))
        if node_id:
            grouped.setdefault(node_id, []).append(row)

    summaries: list[dict[str, Any]] = []
    for node_id in sorted(grouped):
        rows = sorted(grouped[node_id], key=lambda row: clean(row.get("date")))
        numeric_24h = numeric_values(rows, "rain_24h_mm")
        numeric_72h = numeric_values(rows, "rain_72h_mm")
        numeric_7d = numeric_values(rows, "rain_7d_mm")
        wettest_row = max(rows, key=lambda row: sortable_number(row, "rain_72h_mm"))

        summary = {
            "node_id": node_id,
            "display_name": clean(rows[0].get("node_display_name")),
            "total_dates": len(rows),
            "max_rain_24h_mm": max(numeric_24h) if numeric_24h else "",
            "max_rain_72h_mm": max(numeric_72h) if numeric_72h else "",
            "max_rain_7d_mm": max(numeric_7d) if numeric_7d else "",
            "wettest_72h_date": clean(wettest_row.get("date"))
            if sortable_number(wettest_row, "rain_72h_mm") >= 0
            else "",
        }
        for status in STATUS_ORDER:
            summary[f"{status}_count"] = count_status(rows, status)
        summaries.append(summary)
    return summaries


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(field)
        if isinstance(value, int | float):
            values.append(round(float(value), 2))
    return values


def sortable_number(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    if isinstance(value, int | float):
        return float(value)
    return -1.0


def count_status(rows: list[dict[str, Any]], status: str) -> int:
    return sum(1 for row in rows if row.get("hydroclimate_status") == status)


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
    return " ".join(text.split())[:500]


def as_number(value: Any) -> int | float | str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return sanitize_text(text)
    if number.is_integer():
        return int(number)
    return round(number, 2)


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
