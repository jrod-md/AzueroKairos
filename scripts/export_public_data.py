"""Export safe public JSON data for the Azuero Kairos demo frontend."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from azuero_kairos.confidence_engine import (  # noqa: E402
    CONFIDENCE_LABELS_ES,
    DECISION_LABELS_ES,
    REASONS_ES,
    RECOMMENDED_ACTIONS_ES,
)


DEFAULT_PROCESSED_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel2_stats_confidence.csv"
DEFAULT_LEDGER_CSV = PROJECT_ROOT / "outputs/ledger/evidence_ledger.csv"
DEFAULT_PUBLIC_DATA_DIR = PROJECT_ROOT / "frontend/public/data"

OBSERVATION_FIELDS = [
    "date",
    "aoi",
    "resolution_m",
    "validPercent",
    "sampleCount",
    "noDataCount",
    "mndwi_mean",
    "ndti_mean",
    "confidence_class",
    "decision",
    "confidence_label_es",
    "decision_label_es",
    "reason_es",
    "recommended_action_es",
    "api_status",
    "api_error",
    "raw_json_path",
    "brief_path",
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export safe public JSON files from official Azuero Kairos artifacts."
    )
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV))
    parser.add_argument("--ledger-csv", default=str(DEFAULT_LEDGER_CSV))
    parser.add_argument("--public-data-dir", default=str(DEFAULT_PUBLIC_DATA_DIR))
    args = parser.parse_args(argv)

    processed_csv = Path(args.processed_csv)
    ledger_csv = Path(args.ledger_csv)
    public_data_dir = Path(args.public_data_dir)

    if not processed_csv.exists():
        print(f"Missing source CSV: {as_display_path(processed_csv)}", file=sys.stderr)
        return 1

    ledger_rows = read_csv_rows(ledger_csv) if ledger_csv.exists() else []
    ledger_by_key = {row_key(row): row for row in ledger_rows}
    observations = build_public_observations(processed_csv, ledger_by_key)
    public_ledger = build_public_ledger_rows(ledger_rows)

    public_data_dir.mkdir(parents=True, exist_ok=True)
    observations_path = public_data_dir / "observations.json"
    ledger_path = public_data_dir / "evidence_ledger.json"
    write_json(observations_path, observations)
    write_json(ledger_path, public_ledger)

    print(f"Observations JSON: {as_display_path(observations_path)}")
    print(f"Evidence ledger JSON: {as_display_path(ledger_path)}")
    print(f"Observation rows: {len(observations)}")
    print(f"Ledger rows: {len(public_ledger)}")
    print("Public export sanitized: no secrets, tokens, headers, or absolute local paths.")
    return 0


def build_public_observations(
    processed_csv: Path,
    ledger_by_key: dict[tuple[str, str, str], dict[str, str]],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for row in read_csv_rows(processed_csv):
        confidence_class = clean(row.get("confidence_class"))
        ledger_row = ledger_by_key.get(row_key(row), {})
        brief_path = available_brief_path(ledger_row, row)
        public_row = {
            "date": clean(row.get("date")),
            "aoi": clean(row.get("aoi")),
            "resolution_m": as_number(row.get("resolution_m")),
            "validPercent": as_number(row.get("validPercent")),
            "sampleCount": as_number(row.get("sampleCount")),
            "noDataCount": as_number(row.get("noDataCount")),
            "mndwi_mean": as_number(row.get("mndwi_mean")),
            "ndti_mean": as_number(row.get("ndti_mean")),
            "confidence_class": confidence_class,
            "decision": clean(row.get("decision")),
            "confidence_label_es": localized_value(
                row,
                "confidence_label_es",
                CONFIDENCE_LABELS_ES,
                confidence_class,
            ),
            "decision_label_es": localized_value(
                row,
                "decision_label_es",
                DECISION_LABELS_ES,
                confidence_class,
            ),
            "reason_es": localized_value(row, "reason_es", REASONS_ES, confidence_class),
            "recommended_action_es": localized_value(
                row,
                "recommended_action_es",
                RECOMMENDED_ACTIONS_ES,
                confidence_class,
            ),
            "api_status": clean(row.get("api_status")) or clean(ledger_row.get("api_status")),
            "api_error": sanitize_text(row.get("api_error") or ledger_row.get("api_error")),
            "raw_json_path": relative_artifact_path(
                row.get("raw_json_path") or ledger_row.get("raw_json_path")
            ),
            "brief_path": brief_path,
        }
        observations.append({field: public_row.get(field, "") for field in OBSERVATION_FIELDS})
    return observations


def build_public_ledger_rows(ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    public_rows: list[dict[str, Any]] = []
    for row in ledger_rows:
        public_row: dict[str, Any] = {}
        for key, value in row.items():
            if key == "api_error":
                public_row[key] = sanitize_text(value)
            elif key.endswith("_path"):
                public_row[key] = relative_artifact_path(value)
            elif key in {
                "resolution_m",
                "validPercent",
                "sampleCount",
                "noDataCount",
                "mndwi_mean",
                "ndti_mean",
            }:
                public_row[key] = as_number(value)
            else:
                public_row[key] = clean(value)
        public_rows.append(public_row)
    return public_rows


def available_brief_path(ledger_row: dict[str, str], observation_row: dict[str, str]) -> str:
    candidate = clean(ledger_row.get("brief_path"))
    if not candidate:
        date = clean(observation_row.get("date"))
        aoi = clean(observation_row.get("aoi"))
        candidate = f"outputs/briefs/{date}_{aoi}_confidence_brief.md"

    candidate_path = resolve_project_path(candidate)
    if candidate_path.exists():
        return relative_artifact_path(candidate_path)
    return ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def localized_value(
    row: dict[str, str],
    field_name: str,
    values_by_confidence: dict[str, str],
    confidence_class: str,
) -> str:
    current = clean(row.get(field_name))
    if current:
        return current
    return values_by_confidence.get(confidence_class, "")


def row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        clean(row.get("date")),
        clean(row.get("aoi")),
        clean(row.get("resolution_m")),
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


def resolve_project_path(value: Any) -> Path:
    text = clean(value)
    if not text:
        return PROJECT_ROOT
    path = Path(text)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


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


def as_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
