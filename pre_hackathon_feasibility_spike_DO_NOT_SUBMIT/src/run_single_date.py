"""Run one exploratory Statistical API request for one date and index.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Run one private DO_NOT_SUBMIT Statistical API spike request.")
    parser.add_argument("--date", required=True, help="Date as YYYY-MM-DD. Uses a one-day UTC window by default.")
    parser.add_argument("--index", choices=sorted(INDEX_EVALSCRIPTS), default="mndwi")
    parser.add_argument("--window-days", type=int, default=1)
    parser.add_argument("--resolution-meters", type=int, default=20)
    parser.add_argument("--aoi", type=Path, default=PROJECT_ROOT / "data" / "aoi_chitre_la_arena_approx.geojson")
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "outputs" / "raw")
    return parser.parse_args()


def run(
    date_value: str,
    index: str,
    window_days: int,
    resolution_meters: int,
    aoi_path: Path,
    out_dir: Path,
) -> bool:
    token = get_cdse_token()
    geometry = load_aoi_geometry(aoi_path)
    evalscript = read_evalscript(INDEX_EVALSCRIPTS[index])
    start_iso, end_iso = one_day_window(date_value, window_days)
    payload = build_stats_payload(
        geometry,
        evalscript,
        start_iso,
        end_iso,
        window_days=window_days,
        resolution_meters=resolution_meters,
    )

    debug_payload_path = out_dir / f"request_payload_{index}_{date_value}_{resolution_meters}m.json"
    payload_resx = payload["aggregation"]["resx"]
    payload_resy = payload["aggregation"]["resy"]
    debug_context = payload_debug_context(geometry, resolution_meters)
    print(
        "Request debug: "
        f"window={start_iso} to {end_iso} "
        f"aoi={aoi_path} index={index} "
        f"source_crs={debug_context['source_crs']} "
        f"target_crs={debug_context['target_crs']} "
        f"resolution_meters={debug_context['resolution_meters']} "
        f"projected_bounds={debug_context['projected_bounds']} "
        f"user_resolution_meters={resolution_meters} "
        f"payload_resx={payload_resx} payload_resy={payload_resy}"
    )
    response_json = post_statistics(token, payload, debug_payload_path=debug_payload_path)

    raw_path = out_dir / f"{index}_{date_value}_{resolution_meters}m_raw.json"
    save_json(raw_path, response_json)

    stats = first_band_stats(response_json, index)
    valid_pct = valid_percent(stats)
    print(f"Single-date stats: OK - saved {raw_path}")
    print(
        "Stats summary: "
        f"mean={stats.get('mean')} stDev={stats.get('stDev')} "
        f"sampleCount={stats.get('sampleCount')} noDataCount={stats.get('noDataCount')} "
        f"validPercent={valid_pct}"
    )
    return True


def main() -> int:
    args = parse_args()
    try:
        run(args.date, args.index, args.window_days, args.resolution_meters, args.aoi, args.out_dir)
    except RuntimeError as exc:
        print(f"Single-date stats: FAIL - {exc}")
        return 2
    except ValueError as exc:
        print(f"Single-date stats: FAIL - {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
