"""Build the official Azuero Kairos evidence ledger CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEFAULT_PROCESSED_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel2_stats_confidence.csv"
DEFAULT_RAW_JSON_DIR = PROJECT_ROOT / "outputs/raw_json"
DEFAULT_BRIEFS_DIR = PROJECT_ROOT / "outputs/briefs"
DEFAULT_LEDGER_PATH = PROJECT_ROOT / "outputs/ledger/evidence_ledger.csv"
DEFAULT_PUBLIC_OBSERVATIONS_JSON = PROJECT_ROOT / "frontend/public/data/observations.json"
DEFAULT_PUBLIC_LEDGER_JSON = PROJECT_ROOT / "frontend/public/data/evidence_ledger.json"
DEFAULT_DECISION_CASES_JSON = PROJECT_ROOT / "frontend/public/data/decision_cases.json"

HASH_PAYLOAD_SCHEMA = (
    "event_type,observation_date,aoi_or_node_id,artifact_ref,status,source_layer,decision_class"
)

LEDGER_FIELDNAMES = [
    "run_id",
    "generated_at_utc",
    "git_commit",
    "event_index",
    "event_type",
    "event_label_es",
    "artifact_ref",
    "status",
    "source_layer",
    "decision_class",
    "event_hash",
    "hash_short",
    "hash_method",
    "hash_payload_schema",
    "artifact_hash",
    "artifact_hash_method",
    "artifact_available_in_repo",
    "public_runtime_available",
    "sanitization_note",
    "date",
    "aoi",
    "resolution_m",
    "confidence_class",
    "decision",
    "validPercent",
    "sampleCount",
    "noDataCount",
    "mndwi_mean",
    "ndti_mean",
    "api_status",
    "api_error",
    "raw_json_path",
    "processed_csv_path",
    "brief_path",
    "evidence_status",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the Azuero Kairos evidence ledger from processed Sentinel-2 CSV output."
    )
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV))
    parser.add_argument("--raw-json-dir", default=str(DEFAULT_RAW_JSON_DIR))
    parser.add_argument("--briefs-dir", default=str(DEFAULT_BRIEFS_DIR))
    parser.add_argument("--output", default=str(DEFAULT_LEDGER_PATH))
    args = parser.parse_args(argv)

    processed_csv_path = Path(args.processed_csv)
    raw_json_dir = Path(args.raw_json_dir)
    briefs_dir = Path(args.briefs_dir)
    output_path = Path(args.output)

    if not processed_csv_path.exists():
        print(f"Processed CSV not found: {as_display_path(processed_csv_path)}", file=sys.stderr)
        return 1

    rows = build_rows(
        processed_csv_path=processed_csv_path,
        raw_json_dir=raw_json_dir,
        briefs_dir=briefs_dir,
    )
    write_csv(rows, output_path)
    print_summary(rows, output_path)
    return 0


def build_rows(
    *,
    processed_csv_path: Path,
    raw_json_dir: Path,
    briefs_dir: Path,
) -> list[dict[str, str]]:
    run_id = str(uuid4())
    git_commit = get_git_commit_hash()
    processed_csv_display = as_display_path(processed_csv_path)
    generated_at = datetime.now(UTC).replace(microsecond=0)
    event_index = 0
    rows: list[dict[str, str]] = []

    with processed_csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row in reader:
            confidence_class = clean(source_row.get("confidence_class"))
            decision = clean(source_row.get("decision"))
            reason = clean(source_row.get("reason"))
            api_status = clean(source_row.get("api_status"))
            api_error = clean(source_row.get("api_error"))
            raw_json_path = resolve_raw_json_path(source_row, raw_json_dir)
            brief_path = resolve_brief_path(source_row, briefs_dir)

            base_row = {
                "run_id": run_id,
                "git_commit": git_commit,
                "date": clean(source_row.get("date")),
                "aoi": clean(source_row.get("aoi")),
                "resolution_m": clean(source_row.get("resolution_m")),
                "confidence_class": confidence_class,
                "decision": decision,
                "validPercent": clean(source_row.get("validPercent")),
                "sampleCount": clean(source_row.get("sampleCount")),
                "noDataCount": clean(source_row.get("noDataCount")),
                "mndwi_mean": clean(source_row.get("mndwi_mean")),
                "ndti_mean": clean(source_row.get("ndti_mean")),
                "api_status": api_status,
                "api_error": api_error,
                "raw_json_path": as_display_path(raw_json_path),
                "processed_csv_path": processed_csv_display,
                "brief_path": as_display_path(brief_path),
                "evidence_status": evidence_status(
                    api_status=api_status,
                    api_error=api_error,
                    raw_json_path=raw_json_path,
                    brief_path=brief_path,
                ),
            }

            for event in build_event_definitions(
                source_row=source_row,
                processed_csv_path=processed_csv_path,
                raw_json_path=raw_json_path,
                brief_path=brief_path,
                api_status=api_status,
                api_error=api_error,
                confidence_class=confidence_class,
            ):
                timestamp = generated_at + timedelta(seconds=event_index)
                event_payload = build_hash_payload(base_row, event)
                artifact_path = resolve_project_path(event["artifact_ref"])
                artifact_hash = hash_artifact_if_safe(artifact_path)
                event_hash = hash_event_payload(event_payload)
                rows.append(
                    {
                        **base_row,
                        "generated_at_utc": timestamp.isoformat(),
                        "event_index": str(event_index + 1),
                        "event_type": event["event_type"],
                        "event_label_es": event["event_label_es"],
                        "artifact_ref": event["artifact_ref"],
                        "status": event["status"],
                        "source_layer": event["source_layer"],
                        "decision_class": confidence_class,
                        "event_hash": event_hash,
                        "hash_short": event_hash[:12],
                        "hash_method": "event_payload_sha256",
                        "hash_payload_schema": HASH_PAYLOAD_SCHEMA,
                        "artifact_hash": artifact_hash,
                        "artifact_hash_method": "artifact_content_sha256" if artifact_hash else "",
                        "artifact_available_in_repo": "true" if artifact_path.exists() else "false",
                        "public_runtime_available": (
                            "true" if is_public_runtime_artifact(artifact_path) else "false"
                        ),
                        "sanitization_note": (
                            "public row contains metadata only; raw API payloads and secrets are not exported"
                        ),
                    }
                )
                event_index += 1

    return rows


def build_event_definitions(
    *,
    source_row: dict[str, str],
    processed_csv_path: Path,
    raw_json_path: Path,
    brief_path: Path,
    api_status: str,
    api_error: str,
    confidence_class: str,
) -> list[dict[str, str]]:
    raw_status = "api_ok_raw_observation_recorded"
    if api_error.strip() or api_status.upper() == "ERROR":
        raw_status = "api_error_recorded"
    elif not raw_json_path.exists():
        raw_status = "raw_artifact_missing"

    brief_status = "brief_available" if brief_path.exists() else "brief_missing"
    public_status = (
        "public_json_available"
        if DEFAULT_PUBLIC_OBSERVATIONS_JSON.exists()
        else "public_json_pending_export"
    )
    case_status = (
        "case_registry_available"
        if DEFAULT_DECISION_CASES_JSON.exists()
        else "case_registry_pending_export"
    )

    decision_status = f"decision_{confidence_class or 'unknown'}"

    return [
        event(
            "raw_observation_received",
            "Observación cruda recibida",
            as_display_path(raw_json_path),
            raw_status,
            "sentinel_2_raw",
        ),
        event(
            "processed_metrics_created",
            "Métricas procesadas creadas",
            as_display_path(processed_csv_path),
            "metrics_csv_recorded",
            "sentinel_2_processed",
        ),
        event(
            "confidence_decision_computed",
            "Decisión de confianza calculada",
            as_display_path(processed_csv_path),
            decision_status,
            "sentinel_2_decision",
        ),
        event(
            "brief_generated",
            "Brief de evidencia generado",
            as_display_path(brief_path),
            brief_status,
            "public_brief",
        ),
        event(
            "public_export_sanitized",
            "Exportación pública sanitizada",
            as_display_path(DEFAULT_PUBLIC_OBSERVATIONS_JSON),
            public_status,
            "public_export",
        ),
        event(
            "evidence_case_registered",
            "Caso de evidencia registrado",
            as_display_path(DEFAULT_DECISION_CASES_JSON),
            case_status,
            "case_registry",
        ),
    ]


def event(
    event_type: str,
    event_label_es: str,
    artifact_ref: str,
    status: str,
    source_layer: str,
) -> dict[str, str]:
    return {
        "event_type": event_type,
        "event_label_es": event_label_es,
        "artifact_ref": artifact_ref,
        "status": status,
        "source_layer": source_layer,
    }


def build_hash_payload(base_row: dict[str, str], event_row: dict[str, str]) -> dict[str, str]:
    return {
        "event_type": event_row["event_type"],
        "observation_date": base_row["date"],
        "aoi_or_node_id": base_row["aoi"],
        "artifact_ref": event_row["artifact_ref"],
        "status": event_row["status"],
        "source_layer": event_row["source_layer"],
        "decision_class": base_row["confidence_class"],
    }


def hash_event_payload(payload: dict[str, str]) -> str:
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def hash_artifact_if_safe(path: Path) -> str:
    if not path.exists() or not path.is_file() or not is_safe_hash_path(path):
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_safe_hash_path(path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return False

    parts = {part.lower() for part in relative.parts}
    if ".env" in parts or ".streamlit" in parts:
        return False
    if any(part in {"secrets.toml", "secrets.json"} for part in parts):
        return False
    return True


def is_public_runtime_artifact(path: Path) -> bool:
    try:
        path.resolve().relative_to(PROJECT_ROOT / "frontend" / "public")
    except ValueError:
        return False
    return path.exists()


def write_csv(rows: list[dict[str, str]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def print_summary(rows: list[dict[str, str]], output_path: Path) -> None:
    api_ok_count = sum(
        1
        for row in rows
        if row["api_status"].upper() == "OK" and row["api_error"].strip() == ""
    )
    missing_brief_count = sum(
        1 for row in rows if "brief_missing" in row["evidence_status"].split(";")
    )
    api_error_count = sum(
        1
        for row in rows
        if row["api_error"].strip() or row["api_status"].upper() == "ERROR"
    )
    event_types = sorted({row["event_type"] for row in rows})
    short_hashes = [row["hash_short"] for row in rows if row["hash_short"]]

    print(f"Ledger path: {as_display_path(output_path)}")
    print(f"Total rows: {len(rows)}")
    print(f"Event types: {', '.join(event_types)}")
    print(f"Unique short hashes: {len(set(short_hashes))}/{len(short_hashes)}")
    print(f"Rows API OK: {api_ok_count}")
    print(f"Rows with missing briefs: {missing_brief_count}")
    print(f"Rows with API errors: {api_error_count}")


def get_git_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

    return result.stdout.strip() or "unknown"


def resolve_raw_json_path(source_row: dict[str, str], raw_json_dir: Path) -> Path:
    raw_json_value = clean(source_row.get("raw_json_path"))
    if raw_json_value:
        return resolve_project_path(raw_json_value)

    date = clean(source_row.get("date"))
    aoi = clean(source_row.get("aoi"))
    resolution = clean(source_row.get("resolution_m"))
    return raw_json_dir / f"{date}_{aoi}_mndwi_ndti_{resolution}m_s2_stats.json"


def resolve_brief_path(source_row: dict[str, str], briefs_dir: Path) -> Path:
    date = clean(source_row.get("date"))
    aoi = clean(source_row.get("aoi"))
    return briefs_dir / f"{date}_{aoi}_confidence_brief.md"


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def evidence_status(
    *,
    api_status: str,
    api_error: str,
    raw_json_path: Path,
    brief_path: Path,
) -> str:
    statuses: list[str] = []
    if api_status.upper() == "OK" and api_error.strip() == "":
        statuses.append("official_api_ok")
    if api_error.strip():
        statuses.append("api_error")
    if not raw_json_path.exists():
        statuses.append("raw_json_missing")
    if not brief_path.exists():
        statuses.append("brief_missing")
    return ";".join(statuses) if statuses else "status_unknown"


def observation_id(source_row: dict[str, str]) -> str:
    return "_".join(
        value
        for value in (
            clean(source_row.get("date")),
            clean(source_row.get("aoi")),
            clean(source_row.get("resolution_m")),
        )
        if value
    )


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def as_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
