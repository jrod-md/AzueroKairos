"""Create a reviewed official artifact snapshot for Azuero Kairos."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import UTC, date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSED_CSV = PROJECT_ROOT / "outputs/processed_csv/sentinel2_stats_confidence.csv"
DEFAULT_LEDGER_CSV = PROJECT_ROOT / "outputs/ledger/evidence_ledger.csv"
DEFAULT_RAW_JSON_DIR = PROJECT_ROOT / "outputs/raw_json"
DEFAULT_BRIEFS_DIR = PROJECT_ROOT / "outputs/briefs"
DEFAULT_SNAPSHOT_ROOT = PROJECT_ROOT / "official_artifacts"

PROJECT_NAME = "Azuero Kairós"
SOURCE_NAME = "Copernicus CDSE Statistical API"
AOI_NAME = "corridor_wide"
RESOLUTION_LABEL = "20 m"

SCIENTIFIC_LIMITS_SUMMARY = (
    "Azuero Kairós classifies confidence of Sentinel-2 observations for cautious "
    "exploratory hydro-sedimentary interpretation. It does not detect pesticides, "
    "atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe "
    "water. Chemical or sanitary claims require laboratory or authorized field "
    "verification."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create an official Azuero Kairos artifact snapshot."
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--snapshot-root", default=str(DEFAULT_SNAPSHOT_ROOT))
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV))
    parser.add_argument("--ledger-csv", default=str(DEFAULT_LEDGER_CSV))
    parser.add_argument("--raw-json-dir", default=str(DEFAULT_RAW_JSON_DIR))
    parser.add_argument("--briefs-dir", default=str(DEFAULT_BRIEFS_DIR))
    args = parser.parse_args(argv)

    snapshot_root = Path(args.snapshot_root)
    processed_csv = Path(args.processed_csv)
    ledger_csv = Path(args.ledger_csv)
    raw_json_dir = Path(args.raw_json_dir)
    briefs_dir = Path(args.briefs_dir)

    if not processed_csv.exists():
        print(f"Missing source CSV: {as_display_path(processed_csv)}", file=sys.stderr)
        return 1

    run_id = args.run_id or next_default_run_id(snapshot_root)
    snapshot_dir = snapshot_root / run_id
    if snapshot_dir.exists():
        print(f"Snapshot already exists: {as_display_path(snapshot_dir)}", file=sys.stderr)
        return 1

    copied_files: list[Path] = []
    copied_files.append(copy_artifact(processed_csv, snapshot_dir))

    if ledger_csv.exists():
        copied_files.append(copy_artifact(ledger_csv, snapshot_dir))

    for raw_json in sorted(raw_json_dir.glob("*.json")) if raw_json_dir.exists() else []:
        copied_files.append(copy_artifact(raw_json, snapshot_dir))

    if briefs_dir.exists():
        for brief in sorted(briefs_dir.glob("*.md")):
            copied_files.append(copy_artifact(brief, snapshot_dir))

    dates = official_dates_from_csv(processed_csv)
    run_notes_path = snapshot_dir / "RUN_NOTES.md"
    run_notes_path.write_text(
        build_run_notes(run_id=run_id, dates=dates),
        encoding="utf-8",
    )
    copied_files.append(run_notes_path)

    print(f"Snapshot path: {as_display_path(snapshot_dir)}")
    print(f"Run ID: {run_id}")
    print(f"Files copied: {len(copied_files)}")
    print(f"Dates included: {', '.join(dates)}")
    print("Credentials note: environment variables only; no secrets stored.")
    return 0


def next_default_run_id(snapshot_root: Path) -> str:
    today = date.today().isoformat()
    for index in range(1, 1000):
        run_id = f"{today}_run_{index:03d}"
        if not (snapshot_root / run_id).exists():
            return run_id
    raise RuntimeError("Unable to allocate a run_id after 999 attempts.")


def copy_artifact(source: Path, snapshot_dir: Path) -> Path:
    destination = snapshot_dir / source.resolve().relative_to(PROJECT_ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def official_dates_from_csv(processed_csv: Path) -> list[str]:
    with processed_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        dates = [str(row.get("date", "")).strip() for row in reader]
    return [value for value in dates if value]


def build_run_notes(*, run_id: str, dates: list[str]) -> str:
    generated_at_utc = datetime.now(UTC).isoformat()
    date_lines = "\n".join(f"- {value}" for value in dates)
    return f"""# Official Artifact Snapshot

- run_id: `{run_id}`
- generated_at_utc: `{generated_at_utc}`
- project: {PROJECT_NAME}
- source: {SOURCE_NAME}
- AOI: {AOI_NAME}
- resolution: {RESOLUTION_LABEL}

## Dates Used

{date_lines}

## Scientific Limits Summary

{SCIENTIFIC_LIMITS_SUMMARY}

## Credential Handling

CDSE credentials were provided through environment variables only. Credentials, tokens, request headers, and secrets are not stored in this snapshot.

## Official Hackathon Artifact Note

These outputs are official hackathon-window artifacts generated from the clean Azuero Kairós repository. They are preserved here for reproducible review and demo resilience.
"""


def as_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
