"""Export frontend-safe Kairós Exposure context JSON from node exposure CSV."""

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
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/exposure_context.json"

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]

ALLOWED_STATUSES = {"exposure_available", "data_pending", "data_unavailable"}
STATUS_ORDER = ("exposure_available", "data_pending", "data_unavailable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export safe public JSON for the Kairós Exposure context layer."
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
    validate_public_statuses(observations)
    nodes = build_nodes(observations)
    summary_by_node = build_node_summaries(observations)

    payload = {
        "source_csv": relative_artifact_path(source_csv),
        "layer_type": "exposure_context_only",
        "preferred_source": (
            "Copernicus Land Monitoring Service Global Dynamic Land Cover"
        ),
        "public_safe": True,
        "data_status": derive_payload_status(observations),
        "schema_note": (
            "Kairós Exposure is designed to summarize approximate agricultural "
            "and riparian land-cover context around AOI nodes once an official "
            "CLMS/CDSE raster pull is connected. Current rows remain data_pending "
            "when no official land-cover composition has been obtained."
        ),
        "claim_limit": (
            "This layer does not identify crop types, exact farm boundaries, "
            "private producers, contamination, water safety, or chemical exposure."
        ),
        "nodes": nodes,
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
        "aoi": clean(row.get("aoi")),
        "land_cover_source": clean(row.get("land_cover_source")),
        "agricultural_exposure_status": clean(
            row.get("agricultural_exposure_status")
        ),
        "riparian_context_status": clean(row.get("riparian_context_status")),
        "exposure_confidence": clean(row.get("exposure_confidence")),
        "api_status": clean(row.get("api_status")),
        "api_error": sanitize_text(row.get("api_error")),
        "notes": sanitize_text(row.get("notes")),
    }


def validate_public_statuses(observations: list[dict[str, Any]]) -> None:
    for row in observations:
        for field in ("agricultural_exposure_status", "riparian_context_status"):
            status = clean(row.get(field))
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"Invalid {field}: {status}")


def build_nodes(observations: list[dict[str, Any]]) -> list[dict[str, str]]:
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


def build_node_summaries(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for row in sorted(observations, key=lambda item: clean(item.get("node_id"))):
        summaries.append(
            {
                "node_id": clean(row.get("node_id")),
                "display_name": clean(row.get("node_display_name")),
                "aoi": clean(row.get("aoi")),
                "agricultural_exposure_status": clean(
                    row.get("agricultural_exposure_status")
                ),
                "riparian_context_status": clean(row.get("riparian_context_status")),
                "exposure_confidence": clean(row.get("exposure_confidence")),
            }
        )
    return summaries


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
