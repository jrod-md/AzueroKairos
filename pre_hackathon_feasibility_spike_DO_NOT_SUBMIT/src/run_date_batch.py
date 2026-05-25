"""Run a short exploratory date batch against the Statistical API.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from auth_cdse import get_cdse_token
from stats_request import (
    PROJECT_ROOT,
    build_stats_payload,
    first_band_stats,
    load_aoi_geometry,
    one_day_window,
    payload_debug_context,
    post_statistics,
    read_evalscript,
    save_json,
    valid_percent,
)


INDEX_EVALSCRIPTS = {
    "mndwi": PROJECT_ROOT / "evalscripts" / "exploratory_mndwi.js",
    "ndti": PROJECT_ROOT / "evalscripts" / "exploratory_ndti.js",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run private DO_NOT_SUBMIT Statistical API date batch.")
    parser.add_argument("--dates", type=Path, default=PROJECT_ROOT / "data" / "candidate_dates.csv")
    parser.add_argument("--aoi", type=Path, default=PROJECT_ROOT / "data" / "aoi_chitre_la_arena_approx.geojson")
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "outputs" / "raw")
    parser.add_argument("--window-days", type=int, default=1)
    parser.add_argument("--resolution-meters", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0, help="Optional number of candidate dates to process.")
    parser.add_argument("--indices", nargs="+", choices=sorted(INDEX_EVALSCRIPTS), default=["mndwi", "ndti"])
    return parser.parse_args()


def read_candidate_dates(path: Path, limit: int = 0) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if limit > 0:
        return rows[:limit]
    return rows


def append_technical_error(message: str) -> None:
    path = PROJECT_ROOT / "notes" / "technical_errors.md"
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {timestamp}\n\n{message}\n")


def run_batch(args: argparse.Namespace) -> bool:
    token = get_cdse_token()
    geometry = load_aoi_geometry(args.aoi)
    dates = read_candidate_dates(args.dates, args.limit)
    evalscripts = {index: read_evalscript(path) for index, path in INDEX_EVALSCRIPTS.items() if index in args.indices}

    successes = 0
    failures = 0

    for row in dates:
        date_value = row["date"]
        start_iso, end_iso = one_day_window(date_value, args.window_days)
        for index, evalscript in evalscripts.items():
            payload = build_stats_payload(
                geometry,
                evalscript,
                start_iso,
                end_iso,
                window_days=args.window_days,
                resolution_meters=args.resolution_meters,
            )
            debug_payload_path = args.out_dir / f"request_payload_{index}_{date_value}_{args.resolution_meters}m.json"
            raw_path = args.out_dir / f"{index}_{date_value}_{args.resolution_meters}m_raw.json"
            payload_resx = payload["aggregation"]["resx"]
            payload_resy = payload["aggregation"]["resy"]
            debug_context = payload_debug_context(geometry, args.resolution_meters)
            print(
                "Request debug: "
                f"window={start_iso} to {end_iso} "
                f"aoi={args.aoi} index={index} "
                f"source_crs={debug_context['source_crs']} "
                f"target_crs={debug_context['target_crs']} "
                f"resolution_meters={debug_context['resolution_meters']} "
                f"projected_bounds={debug_context['projected_bounds']} "
                f"user_resolution_meters={args.resolution_meters} "
                f"payload_resx={payload_resx} payload_resy={payload_resy}"
            )
            try:
                response_json = post_statistics(token, payload, debug_payload_path=debug_payload_path)
                save_json(raw_path, response_json)
                stats = first_band_stats(response_json, index)
                valid_pct = valid_percent(stats)
                print(
                    f"OK {date_value} {index}: "
                    f"mean={stats.get('mean')} sampleCount={stats.get('sampleCount')} "
                    f"noDataCount={stats.get('noDataCount')} validPercent={valid_pct}"
                )
                successes += 1
            except RuntimeError as exc:
                failures += 1
                message = f"{date_value} {index}: {exc}"
                print(f"FAIL {message}")
                append_technical_error(message)

    print(f"Batch stats: {'OK' if successes > 0 else 'FAIL'} - successes={successes} failures={failures}")
    return successes > 0


def main() -> int:
    args = parse_args()
    try:
        ok = run_batch(args)
    except RuntimeError as exc:
        print(f"Batch stats: FAIL - {exc}")
        return 2
    except ValueError as exc:
        print(f"Batch stats: FAIL - {exc}")
        return 2
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
