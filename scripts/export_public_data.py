"""Export safe public JSON data for the Azuero Kairos demo frontend."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
HASH_PAYLOAD_SCHEMA = (
    "event_type,observation_date,aoi_or_node_id,artifact_ref,status,source_layer,decision_class"
)
PUBLIC_OBSERVATIONS_REF = "/data/observations.json"
PUBLIC_LEDGER_REF = "/data/evidence_ledger.json"
PRIVATE_ARTIFACT_STATUS = "internal_artifact_not_public"

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
    "public_artifact_ref",
    "public_ledger_ref",
    "source_artifact_status",
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
    ledger_by_key = build_ledger_index(ledger_rows)
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
            "public_artifact_ref": PUBLIC_OBSERVATIONS_REF,
            "public_ledger_ref": PUBLIC_LEDGER_REF,
            "source_artifact_status": PRIVATE_ARTIFACT_STATUS,
        }
        observations.append({field: public_row.get(field, "") for field in OBSERVATION_FIELDS})
    return observations


def build_public_ledger_rows(ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    public_rows: list[dict[str, Any]] = []
    for row in ledger_rows:
        artifact_ref = public_artifact_ref(row)
        public_hash = hash_public_event_payload(row, artifact_ref)
        public_row = {
            "run_id": clean(row.get("run_id")),
            "generated_at_utc": clean(row.get("generated_at_utc")),
            "git_commit": clean(row.get("git_commit")),
            "event_index": as_number(row.get("event_index")),
            "event_type": clean(row.get("event_type")) or "audit_event",
            "event_label": clean(row.get("event_label_es")) or clean(row.get("event_label")),
            "artifact_ref": artifact_ref,
            "artifact_ref_status": "public" if artifact_ref else PRIVATE_ARTIFACT_STATUS,
            "status": clean(row.get("status")) or clean(row.get("evidence_status")),
            "source_layer": clean(row.get("source_layer")) or "sentinel_2",
            "decision_class": clean(row.get("decision_class")) or clean(row.get("confidence_class")),
            "event_hash": public_hash,
            "hash_short": public_hash[:12],
            "hash_method": "event_payload_sha256",
            "hash_payload_schema": HASH_PAYLOAD_SCHEMA,
            "artifact_hash": clean(row.get("artifact_hash")),
            "artifact_hash_method": clean(row.get("artifact_hash_method")),
            "artifact_available_in_repo": as_bool(row.get("artifact_available_in_repo")),
            "public_runtime_available": as_bool(row.get("public_runtime_available")),
            "sanitization_note": clean(row.get("sanitization_note"))
            or "Public ledger exposes metadata only; no secrets, headers, credentials, or raw API responses.",
            "date": clean(row.get("date")),
            "aoi": clean(row.get("aoi")),
            "resolution_m": as_number(row.get("resolution_m")),
            "confidence_class": clean(row.get("confidence_class")),
            "decision": clean(row.get("decision")),
            "validPercent": as_number(row.get("validPercent")),
            "sampleCount": as_number(row.get("sampleCount")),
            "noDataCount": as_number(row.get("noDataCount")),
            "mndwi_mean": as_number(row.get("mndwi_mean")),
            "ndti_mean": as_number(row.get("ndti_mean")),
            "api_status": clean(row.get("api_status")),
            "api_error": sanitize_text(row.get("api_error")),
            "source_artifact_status": PRIVATE_ARTIFACT_STATUS,
            "evidence_status": clean(row.get("evidence_status")),
        }
        public_rows.append(public_row)
    return public_rows


def build_ledger_index(
    ledger_rows: list[dict[str, str]],
) -> dict[tuple[str, str, str], dict[str, str]]:
    indexed: dict[tuple[str, str, str], dict[str, str]] = {}
    rank = {
        "confidence_decision_computed": 0,
        "brief_generated": 1,
        "processed_metrics_created": 2,
        "raw_observation_received": 3,
    }
    current_rank: dict[tuple[str, str, str], int] = {}

    for row in ledger_rows:
        key = row_key(row)
        event_rank = rank.get(clean(row.get("event_type")), 9)
        if key not in indexed or event_rank < current_rank[key]:
            indexed[key] = row
            current_rank[key] = event_rank
    return indexed


def hash_public_event_payload(row: dict[str, str], artifact_ref: str) -> str:
    payload = {
        "event_type": clean(row.get("event_type")) or "audit_event",
        "observation_date": clean(row.get("date")),
        "aoi_or_node_id": clean(row.get("aoi")),
        "artifact_ref": artifact_ref,
        "status": clean(row.get("status")) or clean(row.get("evidence_status")),
        "source_layer": clean(row.get("source_layer")) or "sentinel_2",
        "decision_class": clean(row.get("decision_class")) or clean(row.get("confidence_class")),
    }
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


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


def as_bool(value: Any) -> bool:
    return clean(value).lower() == "true"


def public_artifact_ref(row: dict[str, str]) -> str:
    direct_ref = safe_public_ref(row.get("artifact_ref"))
    if direct_ref:
        return direct_ref

    event_type = clean(row.get("event_type"))
    if event_type in {
        "raw_observation_received",
        "processed_metrics_created",
        "confidence_decision_computed",
        "brief_generated",
        "public_export_sanitized",
    }:
        return PUBLIC_OBSERVATIONS_REF

    return PUBLIC_LEDGER_REF


def safe_public_ref(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""

    text = text.replace("\\", "/")
    path = Path(text)
    if path.is_absolute() or re.match(r"^[A-Za-z]:/", text):
        return ""
    if text.startswith("frontend/public/"):
        return "/" + text.removeprefix("frontend/public/").lstrip("/")
    if text.startswith("public/"):
        return "/" + text.removeprefix("public/").lstrip("/")
    if text.startswith("/data/") or text.startswith("/trust/"):
        return text

    return ""


def as_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
