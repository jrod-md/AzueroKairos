"""Export frontend-safe Sentinel-1 SAR context JSON from node context CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel1_node_context.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/sar_context.json"

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
        description="Export safe public JSON for the Sentinel-1 SAR context layer."
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
        "sensor": "sentinel-1-grd",
        "layer_type": "sar_context_only",
        "public_safe": True,
        "claim_limit": (
            "Sentinel-1 SAR context is a physical observation layer. It does not "
            "detect contamination, validate water safety, or replace Sentinel-2 "
            "optical confidence results."
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
    print(f"SAR available rows: {count_status(observations, 'sar_context_available')}")
    print(f"SAR low-observation rows: {count_status(observations, 'sar_low_observation')}")
    print(f"SAR error rows: {count_status(observations, 'sar_error')}")
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
        "aoi": clean(row.get("aoi")),
        "sensor": clean(row.get("sensor")),
        "vv_mean": as_number(row.get("vv_mean")),
        "vh_mean": as_number(row.get("vh_mean")),
        "vv_vh_ratio": as_number(row.get("vv_vh_ratio")),
        "sampleCount": as_number(row.get("sampleCount")),
        "noDataCount": as_number(row.get("noDataCount")),
        "validPercent": as_number(row.get("validPercent")),
        "context_status": clean(row.get("context_status")),
        "api_status": clean(row.get("api_status")),
        "api_error": sanitize_text(row.get("api_error")),
        "raw_json_path": relative_artifact_path(row.get("raw_json_path")),
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
        summaries.append(
            {
                "node_id": node_id,
                "display_name": clean(rows[0].get("node_display_name")),
                "total_dates": len(rows),
                "sar_context_available_count": count_status(
                    rows, "sar_context_available"
                ),
                "sar_low_observation_count": count_status(
                    rows, "sar_low_observation"
                ),
                "sar_error_count": count_status(rows, "sar_error"),
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
