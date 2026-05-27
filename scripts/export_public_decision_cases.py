"""Export frontend-safe decision cases JSON."""

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
DEFAULT_SOURCE_CSV = PROJECT_ROOT / "outputs/processed_csv/decision_cases.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "frontend/public/data/decision_cases.json"

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export public JSON for Azuero Kairós decision cases."
    )
    parser.add_argument("--source-csv", default=str(DEFAULT_SOURCE_CSV))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    args = parser.parse_args(argv)

    source_csv = Path(args.source_csv)
    output_json = Path(args.output_json)
    if not source_csv.exists():
        print(f"Missing source CSV: {display_path(source_csv)}", file=sys.stderr)
        return 1

    cases = [sanitize_case(row) for row in read_csv_rows(source_csv)]
    payload = {
        "source_csv": relative_artifact_path(source_csv),
        "layer_type": "decision_cases",
        "public_safe": True,
        "claim_firewall": (
            "No detecta pesticidas, metales pesados, patógenos, contaminación "
            "química disuelta ni agua segura."
        ),
        "decision_principle": (
            "Sentinel-2 confidence is primary. Auxiliary layers may add context, "
            "priority, or evidence gaps, but never override the primary confidence "
            "decision."
        ),
        "nodes": build_nodes(cases),
        "dates": sorted({case["date"] for case in cases if case.get("date")}),
        "cases": cases,
        "summary": build_summary(cases),
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_json, payload)
    print_summary(cases=cases, output_json=output_json)
    return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sanitize_case(row: dict[str, str]) -> dict[str, str]:
    return {key: sanitize_text(value) for key, value in row.items()}


def build_nodes(cases: list[dict[str, str]]) -> list[dict[str, str]]:
    nodes_by_id: dict[str, dict[str, str]] = {}
    for case in cases:
        node_id = sanitize_text(case.get("node_id", ""))
        if not node_id or node_id in nodes_by_id:
            continue
        nodes_by_id[node_id] = {
            "node_id": node_id,
            "display_name": sanitize_text(case.get("node_display_name", "")),
        }
    return [nodes_by_id[node_id] for node_id in sorted(nodes_by_id)]


def build_summary(cases: list[dict[str, str]]) -> dict[str, Any]:
    by_decision = Counter(case.get("decision_label", "") for case in cases)
    by_priority = Counter(case.get("priority_level", "") for case in cases)
    field_recommended = sum(
        1
        for case in cases
        if "recomendada" in case.get("field_verification_status", "").lower()
    )
    with_gaps = sum(1 for case in cases if has_evidence_gap(case))

    return {
        "total_cases": len(cases),
        "cases_by_decision_label": dict(sorted(by_decision.items())),
        "cases_by_priority_level": dict(sorted(by_priority.items())),
        "field_verification_recommended_count": field_recommended,
        "evidence_gap_count": with_gaps,
    }


def has_evidence_gap(case: dict[str, str]) -> bool:
    gaps = case.get("evidence_gaps", "").strip()
    return bool(gaps and gaps != "sin brechas críticas")


def print_summary(*, cases: list[dict[str, str]], output_json: Path) -> None:
    summary = build_summary(cases)
    print(f"Total cases: {summary['total_cases']}")
    print("Cases by decision_label:")
    for label, count in summary["cases_by_decision_label"].items():
        print(f"  {label}: {count}")
    print(
        "Cases with field verification recommended: "
        f"{summary['field_verification_recommended_count']}"
    )
    print(f"Cases with evidence gaps: {summary['evidence_gap_count']}")
    print(f"Output JSON path: {display_path(output_json)}")
    print("Public export sanitized: no secrets, tokens, or absolute local paths.")


def sanitize_text(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return ""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "[redacted]", text)
    return " ".join(text.split())[:900]


def relative_artifact_path(value: Any) -> str:
    text = sanitize_text(value)
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
