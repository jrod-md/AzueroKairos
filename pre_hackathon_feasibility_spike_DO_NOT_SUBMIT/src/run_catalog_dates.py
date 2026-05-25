"""Run Statistical API stats on catalog-confirmed Sentinel-2 dates.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

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
DEFAULT_AOIS = {
    "broad_aoi": PROJECT_ROOT / "data" / "aoi_chitre_la_arena_approx.geojson",
    "river_corridor_aoi": PROJECT_ROOT / "data" / "aoi_chitre_river_corridor_test.geojson",
}
OUTPUT_CSV = PROJECT_ROOT / "outputs" / "processed" / "catalog_date_stats_by_aoi.csv"
TECHNICAL_ERRORS = PROJECT_ROOT / "notes" / "technical_errors.md"
RAW_DIR = PROJECT_ROOT / "outputs" / "raw"
CACHE_LABEL_ALIASES = {
    "broad_aoi": ["broad_aoi", "broad"],
    "river_corridor_aoi": ["river_corridor_aoi", "river"],
    "corridor_wide": ["corridor_wide"],
}


class RateLimitStop(RuntimeError):
    """Stop this disposable run without hammering CDSE after repeated 429s."""


def quality_label(valid_pct: float | None) -> str:
    if valid_pct is None:
        return "invalid_no_data"
    if valid_pct < 10:
        return "invalid_lt_10pct"
    if valid_pct <= 30:
        return "low_confidence_10_30pct"
    return "usable_gt_30pct"


def parse_aoi_specs(values: list[str] | None) -> dict[str, Path]:
    if not values:
        return DEFAULT_AOIS
    aois: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"AOI must be label=path, got: {value}")
        label, path = value.split("=", 1)
        if not label:
            raise ValueError(f"AOI label is empty in: {value}")
        aois[label] = Path(path)
    return aois


def parse_indices(values: list[str] | None) -> list[str]:
    raw_values = values or ["mndwi,ndti"]
    parsed: list[str] = []
    for value in raw_values:
        for item in value.split(","):
            index = item.strip().lower()
            if index:
                parsed.append(index)
    unknown = [index for index in parsed if index not in INDEX_EVALSCRIPTS]
    if unknown:
        raise ValueError(f"Unsupported indices: {unknown}. Use mndwi, ndti, or mndwi,ndti.")
    return list(dict.fromkeys(parsed))


def parse_date_filter(value: str | None) -> set[str]:
    if not value:
        return set()
    dates = {item.strip() for item in value.split(",") if item.strip()}
    for date_value in dates:
        datetime.strptime(date_value, "%Y-%m-%d")
    return dates


def read_catalog_dates(path: Path, max_dates: int = 5, date_filter: set[str] | None = None) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Catalog dates file not found: {path}. Run src/catalog_search_s2.py first.")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("date")]
    if date_filter:
        rows = [row for row in rows if row["date"] in date_filter]
    if max_dates > 0:
        return rows[:max_dates]
    return rows


def has_stats(response_json: dict[str, Any], index: str) -> bool:
    return bool(first_band_stats(response_json, index))


def append_technical_error(message: str) -> None:
    TECHNICAL_ERRORS.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with TECHNICAL_ERRORS.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {timestamp}\n\n{message}\n")


def cache_labels(aoi_label: str) -> list[str]:
    return CACHE_LABEL_ALIASES.get(aoi_label, [aoi_label])


def raw_cache_candidates(aoi_label: str, index: str, date_value: str, resolution_meters: int, window_days: int) -> list[Path]:
    candidates: list[Path] = []
    for label in cache_labels(aoi_label):
        candidates.append(RAW_DIR / f"catalog_{label}_{index}_{date_value}_{resolution_meters}m_{window_days}d_raw.json")
    return candidates


def first_nonempty_cache_path(
    aoi_label: str,
    index: str,
    date_value: str,
    resolution_meters: int,
    window_days: int,
) -> Path | None:
    for path in raw_cache_candidates(aoi_label, index, date_value, resolution_meters, window_days):
        if path.exists() and path.stat().st_size > 0:
            return path
    return None


def load_cached_response(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def post_statistics_with_backoff(token: str, payload: dict[str, Any], payload_path: Path) -> dict[str, Any]:
    try:
        return post_statistics(token, payload, debug_payload_path=payload_path)
    except RuntimeError as exc:
        message = str(exc)
        if "HTTP 429" not in message and "RATE_LIMIT" not in message:
            raise
        print("Rate limit hit: waiting 30 seconds before one retry.")
        time.sleep(30)
        try:
            return post_statistics(token, payload, debug_payload_path=payload_path)
        except RuntimeError as retry_exc:
            retry_message = str(retry_exc)
            if "HTTP 429" in retry_message or "RATE_LIMIT" in retry_message:
                note = (
                    "CDSE Statistical API returned HTTP 429 RATE_LIMIT_EXCEEDED after one retry. "
                    "This is a rate-limit/request-management issue, not a Sentinel-2 data failure. "
                    f"Sanitized payload path: {payload_path}. Response: {retry_message}"
                )
                append_technical_error(note)
                raise RateLimitStop(note) from retry_exc
            raise


def run_one(
    token: str | None,
    aoi_label: str,
    aoi_path: Path,
    geometry: dict[str, Any],
    date_row: dict[str, str],
    index: str,
    evalscript: str,
    window_days: int,
    resolution_meters: int,
    sleep_seconds: int,
) -> dict[str, Any]:
    date_value = date_row["date"]
    raw_path = RAW_DIR / f"catalog_{aoi_label}_{index}_{date_value}_{resolution_meters}m_{window_days}d_raw.json"
    cached_path = first_nonempty_cache_path(aoi_label, index, date_value, resolution_meters, window_days)
    if cached_path:
        print(
            "Cache hit: "
            f"aoi_label={aoi_label} index={index} date={date_value} "
            f"resolution_meters={resolution_meters} window_days={window_days} raw={cached_path}"
        )
        response_json = load_cached_response(cached_path)
        raw_path = cached_path
        api_call_made = False
    else:
        api_call_made = True
        print(
            "Cache miss: "
            f"aoi_label={aoi_label} index={index} date={date_value} "
            f"resolution_meters={resolution_meters} window_days={window_days}"
        )

    start_iso, end_iso = one_day_window(date_value, window_days)
    payload = build_stats_payload(
        geometry,
        evalscript,
        start_iso,
        end_iso,
        window_days=window_days,
        resolution_meters=resolution_meters,
    )
    debug_context = payload_debug_context(geometry, resolution_meters)
    payload_resx = payload["aggregation"]["resx"]
    payload_resy = payload["aggregation"]["resy"]
    payload_path = RAW_DIR / f"catalog_{aoi_label}_{index}_{date_value}_{resolution_meters}m_{window_days}d_payload.json"

    print(
        "Catalog-date request debug: "
        f"window={start_iso} to {end_iso} "
        f"aoi={aoi_path} aoi_label={aoi_label} index={index} "
        f"source_crs={debug_context['source_crs']} "
        f"target_crs={debug_context['target_crs']} "
        f"resolution_meters={debug_context['resolution_meters']} "
        f"projected_bounds={debug_context['projected_bounds']} "
        f"user_resolution_meters={resolution_meters} "
        f"payload_resx={payload_resx} payload_resy={payload_resy}"
    )

    if api_call_made:
        if token is None:
            raise RuntimeError("Internal error: token is required for a cache miss before calling CDSE.")
        response_json = post_statistics_with_backoff(token, payload, payload_path)
        save_json(raw_path, response_json)
        if sleep_seconds > 0:
            print(f"Sleeping {sleep_seconds} seconds before the next API request.")
            time.sleep(sleep_seconds)
    stats = first_band_stats(response_json, index)
    valid_pct = valid_percent(stats)
    return {
        "aoi_label": aoi_label,
        "aoi_path": str(aoi_path),
        "date": date_value,
        "datetime": date_row.get("datetime", ""),
        "cloudCover": date_row.get("cloudCover", ""),
        "item_id": date_row.get("item_id", ""),
        "index": index,
        "window_days": window_days,
        "resolution_meters": resolution_meters,
        "mean": stats.get("mean"),
        "stDev": stats.get("stDev"),
        "sampleCount": stats.get("sampleCount"),
        "noDataCount": stats.get("noDataCount"),
        "validPercent": valid_pct,
        "quality": quality_label(valid_pct),
        "raw_path": str(raw_path),
        "notes": "cache_hit" if not api_call_made else ("fallback_2day" if window_days > 1 else "catalog_confirmed_1day"),
        "_has_stats": has_stats(response_json, index),
        "_api_call_made": api_call_made,
    }


def write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "aoi_label",
        "aoi_path",
        "date",
        "datetime",
        "cloudCover",
        "item_id",
        "index",
        "window_days",
        "resolution_meters",
        "mean",
        "stDev",
        "sampleCount",
        "noDataCount",
        "validPercent",
        "quality",
        "raw_path",
        "notes",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run catalog-confirmed date stats for exploratory AOIs.")
    parser.add_argument("--dates", type=Path, default=PROJECT_ROOT / "data" / "candidate_dates_from_catalog.csv")
    parser.add_argument("--aoi", action="append", help="Single AOI spec as label=path. Can be repeated.")
    parser.add_argument("--aois", nargs="*", help="Optional AOI specs as label=path. Defaults to broad and river corridor. Use --aoi corridor_wide=... for the intermediate AOI.")
    parser.add_argument("--indices", nargs="+", default=["mndwi,ndti"], help="Comma-separated or space-separated indices. Default: mndwi,ndti.")
    parser.add_argument("--date-filter", default="", help="Comma-separated YYYY-MM-DD dates to run.")
    parser.add_argument("--max-dates", type=int, default=5, help="Maximum catalog dates to process per run. Default: 5.")
    parser.add_argument("--sleep-seconds", type=int, default=8, help="Sleep between API requests. Default: 8.")
    parser.add_argument("--resolution-meters", type=int, default=20)
    parser.add_argument("--preferred-window-days", type=int, default=1)
    parser.add_argument("--fallback-window-days", type=int, default=2)
    parser.add_argument("--limit-dates", type=int, default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    output_rows: list[dict[str, Any]] = []
    try:
        args = parse_args()
        date_filter = parse_date_filter(args.date_filter)
        max_dates = args.limit_dates if args.limit_dates is not None else args.max_dates
        date_rows = read_catalog_dates(args.dates, max_dates=max_dates, date_filter=date_filter)
        if not date_rows:
            raise RuntimeError(f"No catalog-confirmed dates found in {args.dates}. Run catalog search first.")
        token: str | None = None

        aoi_values = []
        if args.aois:
            aoi_values.extend(args.aois)
        if args.aoi:
            aoi_values.extend(args.aoi)
        aois = parse_aoi_specs(aoi_values or None)
        indices = parse_indices(args.indices)
        evalscripts = {index: read_evalscript(INDEX_EVALSCRIPTS[index]) for index in indices}
        for aoi_label, aoi_path in aois.items():
            geometry = load_aoi_geometry(aoi_path)
            for date_row in date_rows:
                for index, evalscript in evalscripts.items():
                    if first_nonempty_cache_path(
                        aoi_label,
                        index,
                        date_row["date"],
                        args.resolution_meters,
                        args.preferred_window_days,
                    ) is None and token is None:
                        token = get_cdse_token()
                    row = run_one(
                        token,
                        aoi_label,
                        aoi_path,
                        geometry,
                        date_row,
                        index,
                        evalscript,
                        args.preferred_window_days,
                        args.resolution_meters,
                        args.sleep_seconds,
                    )
                    output_rows.append(row)
                    if not row["_has_stats"] and args.fallback_window_days != args.preferred_window_days:
                        if first_nonempty_cache_path(
                            aoi_label,
                            index,
                            date_row["date"],
                            args.resolution_meters,
                            args.fallback_window_days,
                        ) is None and token is None:
                            token = get_cdse_token()
                        fallback = run_one(
                            token,
                            aoi_label,
                            aoi_path,
                            geometry,
                            date_row,
                            index,
                            evalscript,
                            args.fallback_window_days,
                            args.resolution_meters,
                            args.sleep_seconds,
                        )
                        output_rows.append(fallback)

        write_rows(output_rows)
        usable = sum(1 for row in output_rows if row["quality"] == "usable_gt_30pct")
        low = sum(1 for row in output_rows if row["quality"] == "low_confidence_10_30pct")
        invalid = len(output_rows) - usable - low
        print(f"Catalog-date stats: OK - rows={len(output_rows)} usable={usable} low_confidence={low} invalid={invalid}")
        print(f"Stats CSV: {OUTPUT_CSV}")
        return 0
    except RateLimitStop as exc:
        if output_rows:
            write_rows(output_rows)
            print(f"Partial stats CSV saved before stopping: {OUTPUT_CSV}")
        print(f"Catalog-date stats: STOPPED_RATE_LIMIT - {exc}")
        return 2
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"Catalog-date stats: FAIL - {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
