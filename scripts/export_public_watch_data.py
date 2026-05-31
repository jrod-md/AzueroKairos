"""Export frontend-safe Kairós Watch JSON from node confidence CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODE_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel2_node_confidence.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/kairos_watch.json"
PUBLIC_WATCH_REF = "/data/kairos_watch.json"
PRIVATE_ARTIFACT_STATUS = "internal_artifact_not_public"

CONFIDENCE_LABELS_ES = {
    "usable": "USABLE",
    "low_confidence": "REVISAR",
    "do_not_infer": "NO INFERIR",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export safe public JSON for the Azuero Kairós Watch atlas."
    )
    parser.add_argument("--source-csv", default=str(DEFAULT_NODE_CSV))
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
        "source_dataset": "sentinel2_node_confidence_public_metadata",
        "nodes": nodes,
        "dates": dates,
        "observations": observations,
        "summary_by_node": summary_by_node,
        "public_safe": True,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_json, payload)

    api_ok_rows = sum(1 for row in observations if row.get("api_status") == "OK")
    error_rows = sum(
        1
        for row in observations
        if row.get("api_status") == "ERROR" or bool(row.get("api_error"))
    )

    print(f"Output path: {display_path(output_json)}")
    print(f"Nodes: {len(nodes)}")
    print(f"Observation rows: {len(observations)}")
    print(f"API OK rows: {api_ok_rows}")
    print(f"Error rows: {error_rows}")
    return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_public_observation(row: dict[str, str]) -> dict[str, Any]:
    confidence_class = clean(row.get("confidence_class"))
    return {
        "node_id": clean(row.get("node_id")),
        "node_display_name": clean(row.get("node_display_name")),
        "date": clean(row.get("date")),
        "aoi": clean(row.get("aoi")),
        "resolution_m": as_number(row.get("resolution_m")),
        "mndwi_mean": as_number(row.get("mndwi_mean")),
        "ndti_mean": as_number(row.get("ndti_mean")),
        "sampleCount": as_number(row.get("sampleCount")),
        "noDataCount": as_number(row.get("noDataCount")),
        "validPercent": as_number(row.get("validPercent")),
        "confidence_class": confidence_class,
        "confidence_label_es": CONFIDENCE_LABELS_ES.get(confidence_class, ""),
        "decision": clean(row.get("decision")),
        "reason": clean(row.get("reason")),
        "recommended_action": clean(row.get("recommended_action")),
        "api_status": clean(row.get("api_status")),
        "api_error": sanitize_text(row.get("api_error")),
        "public_artifact_ref": PUBLIC_WATCH_REF,
        "source_artifact_status": PRIVATE_ARTIFACT_STATUS,
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
        valid_values = [
            float(row["validPercent"])
            for row in rows
            if isinstance(row.get("validPercent"), int | float)
        ]
        worst_row = min(rows, key=lambda row: sortable_valid_percent(row))
        best_row = max(rows, key=lambda row: sortable_valid_percent(row))
        summaries.append(
            {
                "node_id": node_id,
                "display_name": clean(rows[0].get("node_display_name")),
                "total_dates": len(rows),
                "usable_count": count_confidence(rows, "usable"),
                "low_confidence_count": count_confidence(rows, "low_confidence"),
                "do_not_infer_count": count_confidence(rows, "do_not_infer"),
                "mean_validPercent": round(sum(valid_values) / len(valid_values), 2)
                if valid_values
                else "",
                "worst_date": clean(worst_row.get("date")),
                "best_date": clean(best_row.get("date")),
            }
        )
    return summaries


def count_confidence(rows: list[dict[str, Any]], confidence_class: str) -> int:
    return sum(1 for row in rows if row.get("confidence_class") == confidence_class)


def sortable_valid_percent(row: dict[str, Any]) -> float:
    value = row.get("validPercent")
    if isinstance(value, int | float):
        return float(value)
    return -1.0


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
