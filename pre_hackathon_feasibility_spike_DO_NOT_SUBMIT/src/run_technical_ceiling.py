"""Controlled technical-ceiling runner for the disposable AgroShield spike.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from auth_cdse import get_cdse_token
from stats_request import (
    PROJECT_ROOT,
    build_stats_payload,
    first_band_stats,
    load_aoi_geometry,
    one_day_window,
    post_statistics,
    read_evalscript,
    save_json,
    valid_percent,
)


RAW_DIR = PROJECT_ROOT / "outputs" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "outputs" / "processed"
NOTES_DIR = PROJECT_ROOT / "notes"
MATRIX_CSV = PROCESSED_DIR / "technical_ceiling_matrix.csv"
SUMMARY_CSV = PROCESSED_DIR / "technical_ceiling_summary.csv"
REPORT_MD = NOTES_DIR / "technical_ceiling_report.md"

AOI_PATHS = {
    "broad": PROJECT_ROOT / "data" / "aoi_chitre_la_arena_approx.geojson",
    "river": PROJECT_ROOT / "data" / "aoi_chitre_river_corridor_test.geojson",
    "corridor_wide": PROJECT_ROOT / "data" / "aoi_chitre_corridor_wide_test.geojson",
}
AOI_CACHE_ALIASES = {
    "broad": ["broad", "broad_aoi"],
    "river": ["river", "river_corridor_aoi"],
    "corridor_wide": ["corridor_wide"],
}
INDEX_EVALSCRIPTS = {
    "mndwi": PROJECT_ROOT / "evalscripts" / "exploratory_mndwi.js",
    "ndti": PROJECT_ROOT / "evalscripts" / "exploratory_ndti.js",
}
MATRIX_COLUMNS = [
    "aoi_label",
    "date",
    "index",
    "resolution_meters",
    "mean",
    "stDev",
    "sampleCount",
    "noDataCount",
    "validPercent",
    "confidence_label",
    "source",
    "status",
    "error_summary",
    "raw_path",
]


@dataclass
class RunState:
    api_requests: int = 0
    rate_limit_stop: bool = False
    auth_ok: bool = False
    stopped_by_max_requests: bool = False


class RateLimitStop(RuntimeError):
    pass


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a controlled technical-ceiling matrix for the private spike.")
    parser.add_argument("--max-dates", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=int, default=20)
    parser.add_argument("--max-requests", type=int, default=30)
    parser.add_argument("--indices", default="mndwi,ndti")
    parser.add_argument("--aois", default="broad,river,corridor_wide")
    parser.add_argument("--resolution-meters", type=int, default=20)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-empty", action="store_true")
    return parser.parse_args()


def read_catalog_dates(max_dates: int) -> list[dict[str, str]]:
    path = PROJECT_ROOT / "data" / "candidate_dates_from_catalog.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing catalog date file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("date")]
    return rows[:max_dates] if max_dates > 0 else rows


def read_existing_matrix() -> list[dict[str, str]]:
    if not MATRIX_CSV.exists():
        return []
    with MATRIX_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def matrix_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (str(row["aoi_label"]), str(row["date"]), str(row["index"]), str(row["resolution_meters"]))


def is_resume_complete(row: dict[str, str], retry_empty: bool) -> bool:
    status = row.get("status", "")
    if status == "ok":
        return True
    if status == "empty" and not retry_empty:
        return True
    return False


def choose_aois(labels: list[str]) -> dict[str, Path]:
    selected: dict[str, Path] = {}
    for label in labels:
        if label not in AOI_PATHS:
            raise ValueError(f"Unknown AOI label: {label}. Use broad, river, corridor_wide.")
        path = AOI_PATHS[label]
        if path.exists():
            selected[label] = path
        elif label == "corridor_wide":
            print(f"Skipping corridor_wide because file does not exist: {path}")
        else:
            raise FileNotFoundError(f"Missing AOI file for {label}: {path}")
    return selected


def choose_indices(labels: list[str]) -> dict[str, Path]:
    selected: dict[str, Path] = {}
    for label in labels:
        if label not in INDEX_EVALSCRIPTS:
            raise ValueError(f"Unknown index: {label}. Use mndwi, ndti.")
        selected[label] = INDEX_EVALSCRIPTS[label]
    return selected


def confidence_label(valid_pct: float | None) -> str:
    if valid_pct is None or valid_pct < 10:
        return "invalid"
    if valid_pct < 30:
        return "low_confidence"
    return "usable"


def raw_paths(aoi_label: str, date_value: str, index: str, resolution_meters: int) -> list[Path]:
    candidates = [
        RAW_DIR / f"technical_ceiling_{aoi_label}_{date_value}_{index}_{resolution_meters}m_raw.json",
        RAW_DIR / f"technical_ceiling_{aoi_label}_{index}_{date_value}_{resolution_meters}m_raw.json",
    ]
    for alias in AOI_CACHE_ALIASES.get(aoi_label, [aoi_label]):
        candidates.append(RAW_DIR / f"catalog_{alias}_{index}_{date_value}_{resolution_meters}m_1d_raw.json")
        candidates.append(RAW_DIR / f"catalog_{alias}_{index}_{date_value}_{resolution_meters}m_2d_raw.json")
    return candidates


def preferred_raw_path(aoi_label: str, date_value: str, index: str, resolution_meters: int) -> Path:
    return RAW_DIR / f"technical_ceiling_{aoi_label}_{date_value}_{index}_{resolution_meters}m_raw.json"


def payload_path(aoi_label: str, date_value: str, index: str, resolution_meters: int) -> Path:
    return RAW_DIR / f"technical_ceiling_{aoi_label}_{date_value}_{index}_{resolution_meters}m_payload.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def cached_response(aoi_label: str, date_value: str, index: str, resolution_meters: int) -> tuple[Path | None, dict[str, Any] | None, str]:
    first_empty_or_failed: tuple[Path | None, dict[str, Any] | None, str] = (None, None, "")
    for path in raw_paths(aoi_label, date_value, index, resolution_meters):
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            if first_empty_or_failed[0] is None:
                first_empty_or_failed = (path, None, "failed")
            continue
        stats = first_band_stats(payload, index)
        if stats:
            return path, payload, "ok"
        if first_empty_or_failed[0] is None:
            first_empty_or_failed = (path, payload, "empty")
    return first_empty_or_failed


def row_from_response(
    aoi_label: str,
    date_value: str,
    index: str,
    resolution_meters: int,
    source: str,
    status: str,
    response_json: dict[str, Any] | None,
    raw_path: Path | None,
    error_summary: str = "",
) -> dict[str, Any]:
    stats = first_band_stats(response_json or {}, index)
    valid_pct = valid_percent(stats) if stats else None
    return {
        "aoi_label": aoi_label,
        "date": date_value,
        "index": index,
        "resolution_meters": resolution_meters,
        "mean": stats.get("mean"),
        "stDev": stats.get("stDev"),
        "sampleCount": stats.get("sampleCount"),
        "noDataCount": stats.get("noDataCount"),
        "validPercent": valid_pct,
        "confidence_label": confidence_label(valid_pct),
        "source": source,
        "status": status,
        "error_summary": error_summary[:500],
        "raw_path": str(raw_path) if raw_path else "",
    }


def post_with_rate_limit_stop(token: str, payload: dict[str, Any], debug_payload_path: Path, state: RunState) -> dict[str, Any]:
    try:
        return post_statistics(token, payload, debug_payload_path=debug_payload_path)
    except RuntimeError as exc:
        message = str(exc)
        if "HTTP 429" not in message and "RATE_LIMIT" not in message:
            raise
        print("Rate limit hit: waiting 60 seconds before one retry.")
        time.sleep(60)
        try:
            return post_statistics(token, payload, debug_payload_path=debug_payload_path)
        except RuntimeError as retry_exc:
            retry_message = str(retry_exc)
            if "HTTP 429" in retry_message or "RATE_LIMIT" in retry_message:
                state.rate_limit_stop = True
                raise RateLimitStop(retry_message) from retry_exc
            raise


def write_matrix(rows: list[dict[str, Any]]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in MATRIX_COLUMNS})


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    aoi_labels = sorted({str(row["aoi_label"]) for row in rows})
    for aoi_label in aoi_labels:
        aoi_rows = [row for row in rows if row["aoi_label"] == aoi_label]
        usable = [row for row in aoi_rows if row["confidence_label"] == "usable"]
        low = [row for row in aoi_rows if row["confidence_label"] == "low_confidence"]
        invalid = [row for row in aoi_rows if row["confidence_label"] == "invalid"]
        valid_values = [float(row["validPercent"]) for row in aoi_rows if row.get("validPercent") not in (None, "")]
        summary.append(
            {
                "aoi_label": aoi_label,
                "total_rows": len(aoi_rows),
                "usable_rows": len(usable),
                "low_confidence_rows": len(low),
                "invalid_rows": len(invalid),
                "ok_rows": len([row for row in aoi_rows if row["status"] == "ok"]),
                "empty_rows": len([row for row in aoi_rows if row["status"] == "empty"]),
                "error_rows": len([row for row in aoi_rows if row["status"] == "error"]),
                "rate_limited_rows": len([row for row in aoi_rows if row["status"] == "rate_limited"]),
                "usable_dates": len({row["date"] for row in usable}),
                "mean_validPercent": round(sum(valid_values) / len(valid_values), 2) if valid_values else "",
            }
        )
    return summary


def write_summary(summary_rows: list[dict[str, Any]]) -> None:
    columns = [
        "aoi_label",
        "total_rows",
        "usable_rows",
        "low_confidence_rows",
        "invalid_rows",
        "ok_rows",
        "empty_rows",
        "error_rows",
        "rate_limited_rows",
        "usable_dates",
        "mean_validPercent",
    ]
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(summary_rows)


def best_aoi_by_usable(summary_rows: list[dict[str, Any]]) -> str:
    if not summary_rows:
        return "none"
    best = max(summary_rows, key=lambda row: (int(row["usable_rows"]), int(row["usable_dates"])))
    return f"{best['aoi_label']} ({best['usable_rows']} usable rows, {best['usable_dates']} usable dates)"


def best_aoi_by_science(summary_rows: list[dict[str, Any]]) -> str:
    by_label = {row["aoi_label"]: row for row in summary_rows}
    corridor = by_label.get("corridor_wide")
    river = by_label.get("river")
    broad = by_label.get("broad")
    if corridor and int(corridor["usable_rows"]) > 0:
        return "corridor_wide: best balance between signal coverage and hydrologic/riparian defensibility."
    if river and int(river["usable_rows"]) > 0:
        return "river: most hydrologically targeted, but may under-sample valid pixels."
    if broad and int(broad["usable_rows"]) > 0:
        return "broad: technically robust but scientifically diluted."
    return "none yet: all tested AOIs lack usable rows."


def executive_decision(summary_rows: list[dict[str, Any]], auth_ok: bool) -> str:
    if not auth_ok:
        return "ADJUST SCIENTIFIC"
    if any(int(row["usable_rows"]) > 0 for row in summary_rows):
        return "GO TECHNICAL / ADJUST SCIENTIFIC"
    if summary_rows and all(int(row["total_rows"]) > 0 for row in summary_rows):
        return "PIVOT"
    return "ADJUST SCIENTIFIC"


def product_shape(summary_rows: list[dict[str, Any]]) -> str:
    by_label = {row["aoi_label"]: row for row in summary_rows}
    if int(by_label.get("corridor_wide", {}).get("usable_rows", 0)) > 0:
        return "Satellite confidence semaforo; hydro-sedimentary exploratory semaforo remains possible after stronger temporal contrast."
    if any(int(row["usable_rows"]) > 0 for row in summary_rows):
        return "Satellite confidence semaforo."
    return "Data access demo."


def write_report(rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], state: RunState) -> str:
    decision = executive_decision(summary_rows, state.auth_ok)
    report_lines = [
        "# Technical Ceiling Report",
        "",
        "PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.",
        "",
        f"Executive decision: {decision}",
        "",
        "## What is technically proven",
        "",
        "- CDSE authentication, Statistical API access, EPSG:32617 reprojection, caching, and resumable matrix execution are technically testable in this spike.",
        "- Returned Sentinel-2 L2A MNDWI/NDTI statistics can be summarized with explicit valid-pixel confidence labels when API/cache rows exist.",
        "",
        "## What is not proven",
        "",
        "- June 2025 crisis validation is not proven.",
        "- Chemical, pesticide, pathogen, metal, dissolved contaminant, or complete water-quality detection is not proven.",
        "- Agricultural operational decisions are not proven.",
        "",
        "## AOI assessment",
        "",
        f"Best AOI by usable date count: {best_aoi_by_usable(summary_rows)}.",
        "",
        f"Best AOI by scientific defensibility: {best_aoi_by_science(summary_rows)}",
        "",
        "June 2025 crisis validated: No.",
        "",
        "## Rate limit implications",
        "",
        f"rate_limit_stop={str(state.rate_limit_stop).lower()}",
        "",
        "CDSE rate limits require cache-first runs, small batches, sleeps between non-cached requests, and at most one live refresh pattern in any future MVP.",
        "",
        "## Recommended product shape",
        "",
        product_shape(summary_rows),
        "",
        "## Allowed claims",
        "",
        "- Sentinel-2 L2A can return exploratory MNDWI/NDTI statistics over tested AOIs.",
        "- Outputs can support a satellite confidence semaforo with explicit uncertainty if enough usable rows exist.",
        "- Language should remain: señal satelital exploratoria asociada a riesgo hidro-sedimentario observable.",
        "",
        "## Forbidden claims",
        "",
        "- Do not claim validated crisis detection.",
        "- Do not claim pesticide, atrazine, pathogen, metal, dissolved chemical, or complete water-quality detection.",
        "- Do not claim irrigation shutdown, intake closure, or agricultural operational decision authority.",
        "",
        "## Next 3 technical actions",
        "",
        "1. Run corridor_wide in small cached batches around June dates and compare against broad/river.",
        "2. Tighten catalog-date selection around low-cloud acquisitions and explicitly separate cloudy dates from signal dates.",
        "3. If corridor_wide improves usable rows, regenerate all official work from zero during the competition window.",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return decision


def run_matrix(args: argparse.Namespace) -> tuple[list[dict[str, Any]], RunState]:
    state = RunState()
    selected_aois = choose_aois(parse_csv_list(args.aois))
    selected_indices = choose_indices(parse_csv_list(args.indices))
    date_rows = read_catalog_dates(args.max_dates)
    geometries = {label: load_aoi_geometry(path) for label, path in selected_aois.items()}
    evalscripts = {label: read_evalscript(path) for label, path in selected_indices.items()}

    rows: list[dict[str, Any]] = []
    resume_done: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if args.resume:
        for row in read_existing_matrix():
            if is_resume_complete(row, args.retry_empty):
                resume_done[matrix_key(row)] = row
        rows.extend(resume_done.values())

    token: str | None = None
    for date_row in date_rows:
        date_value = date_row["date"]
        for aoi_label, geometry in geometries.items():
            for index, evalscript in evalscripts.items():
                key = (aoi_label, date_value, index, str(args.resolution_meters))
                if key in resume_done:
                    print(f"Resume skip: aoi={aoi_label} date={date_value} index={index}")
                    continue

                cached_path, cached_json, cache_status = cached_response(aoi_label, date_value, index, args.resolution_meters)
                if cache_status == "ok":
                    print(f"Cache hit: aoi={aoi_label} date={date_value} index={index} raw={cached_path}")
                    rows.append(
                        row_from_response(
                            aoi_label,
                            date_value,
                            index,
                            args.resolution_meters,
                            "cache",
                            "ok",
                            cached_json,
                            cached_path,
                        )
                    )
                    continue
                if cache_status in {"empty", "failed"} and not args.retry_empty:
                    print(f"Cache {cache_status}: aoi={aoi_label} date={date_value} index={index} raw={cached_path}")
                    rows.append(
                        row_from_response(
                            aoi_label,
                            date_value,
                            index,
                            args.resolution_meters,
                            "cache",
                            cache_status if cache_status == "empty" else "error",
                            cached_json,
                            cached_path,
                            "Cached response had no usable stats; pass --retry-empty to retry once.",
                        )
                    )
                    continue

                if state.api_requests >= args.max_requests:
                    state.stopped_by_max_requests = True
                    print(f"Stopping: reached max_requests={args.max_requests}.")
                    return rows, state

                if token is None:
                    try:
                        token = get_cdse_token()
                        state.auth_ok = True
                    except Exception as exc:
                        rows.append(
                            row_from_response(
                                aoi_label,
                                date_value,
                                index,
                                args.resolution_meters,
                                "api",
                                "error",
                                None,
                                preferred_raw_path(aoi_label, date_value, index, args.resolution_meters),
                                f"Auth or network failure before API request: {exc}",
                            )
                        )
                        return rows, state

                start_iso, end_iso = one_day_window(date_value, 1)
                request_payload = build_stats_payload(
                    geometry,
                    evalscript,
                    start_iso,
                    end_iso,
                    window_days=1,
                    resolution_meters=args.resolution_meters,
                )
                raw_path = preferred_raw_path(aoi_label, date_value, index, args.resolution_meters)
                debug_payload_path = payload_path(aoi_label, date_value, index, args.resolution_meters)
                print(
                    "API request: "
                    f"aoi={aoi_label} date={date_value} index={index} "
                    f"request={state.api_requests + 1}/{args.max_requests}"
                )
                try:
                    response_json = post_with_rate_limit_stop(token, request_payload, debug_payload_path, state)
                    state.api_requests += 1
                    save_json(raw_path, response_json)
                    stats = first_band_stats(response_json, index)
                    status = "ok" if stats else "empty"
                    rows.append(
                        row_from_response(
                            aoi_label,
                            date_value,
                            index,
                            args.resolution_meters,
                            "api",
                            status,
                            response_json,
                            raw_path,
                        )
                    )
                    if args.sleep_seconds > 0:
                        time.sleep(args.sleep_seconds)
                except RateLimitStop as exc:
                    state.api_requests += 1
                    rows.append(
                        row_from_response(
                            aoi_label,
                            date_value,
                            index,
                            args.resolution_meters,
                            "api",
                            "rate_limited",
                            None,
                            raw_path,
                            str(exc),
                        )
                    )
                    return rows, state
                except RuntimeError as exc:
                    state.api_requests += 1
                    rows.append(
                        row_from_response(
                            aoi_label,
                            date_value,
                            index,
                            args.resolution_meters,
                            "api",
                            "error",
                            None,
                            raw_path,
                            str(exc),
                        )
                    )
                    if args.sleep_seconds > 0:
                        time.sleep(args.sleep_seconds)
    if token is not None:
        state.auth_ok = True
    elif rows:
        state.auth_ok = True
    return rows, state


def print_requested_summary(rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], state: RunState, recommendation: str) -> None:
    print(f"total rows: {len(rows)}")
    for row in summary_rows:
        print(f"usable rows by AOI - {row['aoi_label']}: {row['usable_rows']}")
    for row in summary_rows:
        print(f"low-confidence rows by AOI - {row['aoi_label']}: {row['low_confidence_rows']}")
    for row in summary_rows:
        print(f"invalid rows by AOI - {row['aoi_label']}: {row['invalid_rows']}")
    print(f"rate limit hit: {'yes' if state.rate_limit_stop else 'no'}")
    print(f"recommendation: {recommendation}")


def main() -> int:
    args = parse_args()
    try:
        rows, state = run_matrix(args)
    except Exception as exc:
        rows = []
        state = RunState(auth_ok=False)
        summary_rows = []
        write_matrix(rows)
        write_summary(summary_rows)
        recommendation = write_report(rows, summary_rows, state)
        print(f"Technical ceiling: FAIL - {exc}")
        print_requested_summary(rows, summary_rows, state, recommendation)
        return 2

    write_matrix(rows)
    summary_rows = summarize_rows(rows)
    write_summary(summary_rows)
    recommendation = write_report(rows, summary_rows, state)
    print_requested_summary(rows, summary_rows, state, recommendation)
    return 2 if state.rate_limit_stop else 0


if __name__ == "__main__":
    raise SystemExit(main())
