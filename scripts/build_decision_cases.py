"""Build Azuero Kairós decision cases from available context layers."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from azuero_kairos.decision_engine import (  # noqa: E402
    DECISION_CASE_FIELDNAMES,
    build_decision_cases,
)


DEFAULT_SENTINEL2_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel2_node_confidence.csv"
DEFAULT_SENTINEL1_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel1_node_context.csv"
DEFAULT_EXPOSURE_CSV = PROJECT_ROOT / "outputs/processed_csv/exposure_node_context.csv"
DEFAULT_HYDROCLIMATE_CSV = PROJECT_ROOT / "outputs/processed_csv/hydroclimate_node_context.csv"
DEFAULT_LEDGER_CSV = PROJECT_ROOT / "outputs/ledger/evidence_ledger.csv"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "outputs/processed_csv/decision_cases.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build conservative Azuero Kairós decision cases."
    )
    parser.add_argument("--sentinel2-csv", default=str(DEFAULT_SENTINEL2_CSV))
    parser.add_argument("--sentinel1-csv", default=str(DEFAULT_SENTINEL1_CSV))
    parser.add_argument("--exposure-csv", default=str(DEFAULT_EXPOSURE_CSV))
    parser.add_argument("--hydroclimate-csv", default=str(DEFAULT_HYDROCLIMATE_CSV))
    parser.add_argument("--ledger-csv", default=str(DEFAULT_LEDGER_CSV))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    args = parser.parse_args(argv)

    sentinel2_path = Path(args.sentinel2_csv)
    if not sentinel2_path.exists():
        print(
            f"Missing required Sentinel-2 node confidence CSV: {display_path(sentinel2_path)}",
            file=sys.stderr,
        )
        return 1

    sentinel2_rows = read_csv_rows(sentinel2_path)
    sar_rows = read_optional_csv(Path(args.sentinel1_csv))
    exposure_rows = read_optional_csv(Path(args.exposure_csv))
    hydroclimate_rows = read_optional_csv(Path(args.hydroclimate_csv))
    ledger_rows = read_optional_csv(Path(args.ledger_csv))

    cases = build_decision_cases(
        sentinel2_rows=sentinel2_rows,
        sar_rows=sar_rows,
        exposure_rows=exposure_rows,
        hydroclimate_rows=hydroclimate_rows,
        ledger_rows=ledger_rows,
    )

    output_csv = Path(args.output_csv)
    write_decision_cases(output_csv, cases)
    print_summary(cases=cases, output_csv=output_csv)
    return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv_rows(path)


def write_decision_cases(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_CASE_FIELDNAMES)
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {field: case.get(field, "") for field in DECISION_CASE_FIELDNAMES}
            )


def print_summary(*, cases: list[dict[str, Any]], output_csv: Path) -> None:
    by_decision = Counter(case.get("decision_label", "") for case in cases)
    field_recommended = sum(
        1
        for case in cases
        if "recomendada" in str(case.get("field_verification_status", "")).lower()
    )
    with_gaps = sum(
        1
        for case in cases
        if str(case.get("evidence_gaps", "")).strip()
        and case.get("evidence_gaps") != "sin brechas críticas"
    )

    print(f"Total cases: {len(cases)}")
    print("Cases by decision_label:")
    for label in sorted(by_decision):
        print(f"  {label}: {by_decision[label]}")
    print(f"Cases with field verification recommended: {field_recommended}")
    print(f"Cases with evidence gaps: {with_gaps}")
    print(f"Output CSV path: {display_path(output_csv)}")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
