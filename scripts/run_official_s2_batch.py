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
    estimate_request_grid_from_path,
    format_request_grid_estimate,
    run_official_batch,
    validate_request_grid,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the official Azuero Kairós Sentinel-2 statistics batch."
    )
    parser.add_argument(
        "--aoi",
        default="corridor_wide",
        help="AOI name under configs/ such as corridor_wide, or a GeoJSON path.",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=DEFAULT_RESOLUTION_M,
        help="Spatial resolution in meters.",
    )
    parser.add_argument("--force", action="store_true", help="Ignore cached raw JSON.")
    parser.add_argument("--raw-json-dir", default=str(DEFAULT_RAW_JSON_DIR))
    parser.add_argument("--processed-csv", default=str(DEFAULT_PROCESSED_CSV_PATH))
    parser.add_argument("--sleep-seconds", type=float, default=DEFAULT_SLEEP_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    try:
        aoi_path = resolve_aoi_path(args.aoi)
        preflight = estimate_request_grid_from_path(
            aoi_path,
            resolution_m=args.resolution,
        )
        print(format_request_grid_estimate(preflight))
        validate_request_grid(preflight)
        csv_path = run_official_batch(
            aoi_path=aoi_path,
            dates=OFFICIAL_DATES,
            resolution_m=args.resolution,
            raw_json_dir=args.raw_json_dir,
            processed_csv_path=args.processed_csv,
            sleep_seconds=args.sleep_seconds,
            request_timeout_seconds=args.timeout_seconds,
            force=args.force,
        )
    except Sentinel2StatsError as exc:
        print(f"Official Sentinel-2 batch failed safely: {exc}", file=sys.stderr)
        return 1

    error_count = count_error_rows(csv_path)
    print(f"Wrote processed CSV: {csv_path}")
    print(f"Raw JSON directory: {Path(args.raw_json_dir)}")
    print(f"Dates processed: {len(OFFICIAL_DATES)}")
    print(f"Cache mode: {'force refresh' if args.force else 'cache first'}")
    if error_count:
        print(f"Rows with API/cache errors: {error_count}", file=sys.stderr)
        print("See api_error values in the processed CSV for sanitized details.", file=sys.stderr)
        return 1
    return 0


def resolve_aoi_path(aoi_value: str) -> Path:
    if aoi_value == "corridor_wide":
        return PROJECT_ROOT / DEFAULT_AOI_PATH

    candidate = Path(aoi_value)
    candidate_paths = [candidate]
    if not candidate.is_absolute():
        candidate_paths.append(PROJECT_ROOT / candidate)

    for candidate_path in candidate_paths:
        if candidate_path.exists():
            return candidate_path

    if candidate.suffix.lower() in {".geojson", ".json"}:
        return candidate_paths[-1]

    configured = PROJECT_ROOT / "configs" / f"aoi_{aoi_value}.geojson"
    if configured.exists():
        return configured

    raise Sentinel2StatsError(
        f"Unknown AOI '{aoi_value}'. Expected a configs/aoi_<name>.geojson file or a path."
    )


def count_error_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for row in reader if row.get("api_status") == "ERROR")


if __name__ == "__main__":
    raise SystemExit(main())
