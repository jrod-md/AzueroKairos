"""Run the official Azuero Kairós Sentinel-2 Statistical API batch."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from azuero_kairos.sentinel2_stats import (  # noqa: E402
    DEFAULT_AOI_PATH,
    DEFAULT_PROCESSED_CSV_PATH,
    DEFAULT_RAW_JSON_DIR,
    DEFAULT_RESOLUTION_M,
    DEFAULT_SLEEP_SECONDS,
    OFFICIAL_DATES,
    Sentinel2StatsError,
    run_official_batch,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the official Azuero Kairós Sentinel-2 statistics batch."
    )
    parser.add_argument("--aoi", default=str(DEFAULT_AOI_PATH))
    parser.add_argument("--raw-json-dir", default=str(DEFAULT_RAW_JSON_DIR))
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV_PATH))
    parser.add_argument("--sleep-seconds", type=float, default=DEFAULT_SLEEP_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    try:
        csv_path = run_official_batch(
            aoi_path=args.aoi,
            dates=OFFICIAL_DATES,
            resolution_m=DEFAULT_RESOLUTION_M,
            raw_json_dir=args.raw_json_dir,
            processed_csv_path=args.processed_csv,
            sleep_seconds=args.sleep_seconds,
            request_timeout_seconds=args.timeout_seconds,
        )
    except Sentinel2StatsError as exc:
        print(f"Official Sentinel-2 batch failed: {exc}", file=sys.stderr)
        return 1

    error_count = count_error_rows(csv_path)
    print(f"Wrote processed CSV: {csv_path}")
    print(f"Dates processed: {len(OFFICIAL_DATES)}")
    if error_count:
        print(f"Rows with API/cache errors: {error_count}", file=sys.stderr)
        return 1
    return 0


def count_error_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for row in reader if row.get("api_status") == "ERROR")


if __name__ == "__main__":
    raise SystemExit(main())
