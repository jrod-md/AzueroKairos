"""Summarize exploratory Statistical API responses by AOI and quality.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "outputs" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "outputs" / "processed"
NOTES_DIR = PROJECT_ROOT / "notes"
SUMMARY_CSV = PROCESSED_DIR / "exploratory_stats_summary.csv"
LEGACY_PATTERN = re.compile(r"^(?P<index>mndwi|ndti)_(?P<date>\d{4}-\d{2}-\d{2})(?:_(?P<resolution>\d+)m)?_raw\.json$")
CATALOG_PATTERN = re.compile(
    r"^catalog_(?P<aoi_label>.+?)_(?P<index>mndwi|ndti)_(?P<date>\d{4}-\d{2}-\d{2})_"
    r"(?P<resolution>\d+)m_(?P<window_days>\d+)d_raw\.json$"
)
AOI_LABEL_NORMALIZATION = {
    "broad": "broad_aoi",
    "river": "river_corridor_aoi",
}
AOI_ORDER = ["broad_aoi", "corridor_wide", "river_corridor_aoi"]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_date_metadata() -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for row in read_csv_rows(PROJECT_ROOT / "data" / "candidate_dates.csv"):
        if row.get("date"):
            metadata[row["date"]] = row
    for row in read_csv_rows(PROJECT_ROOT / "data" / "candidate_dates_from_catalog.csv"):
        if row.get("date"):
            metadata[row["date"]] = row
    return metadata


def extract_stats(response_json: dict[str, Any], output_id: str) -> dict[str, Any]:
    data = response_json.get("data", [])
    if not data:
        return {}
    outputs = data[0].get("outputs", {})
    output = outputs.get(output_id)
    if output is None and outputs:
        output = next(iter(outputs.values()))
    if not output:
        return {}
    bands = output.get("bands", {})
    if not bands:
        return {}
    return next(iter(bands.values())).get("stats", {})


def response_interval(response_json: dict[str, Any]) -> tuple[str, str]:
    data = response_json.get("data", [])
    if not data:
        return "", ""
    interval = data[0].get("interval", {})
    return interval.get("from", ""), interval.get("to", "")


def valid_percent(stats: dict[str, Any]) -> float | None:
    sample_count = stats.get("sampleCount")
    no_data_count = stats.get("noDataCount")
    if not isinstance(sample_count, (int, float)) or sample_count <= 0:
        return None
    if not isinstance(no_data_count, (int, float)):
        return None
    return round(100.0 * (sample_count - no_data_count) / sample_count, 2)


def quality_label(valid_pct: float | None) -> str:
    if valid_pct is None:
        return "invalid_no_data"
    if valid_pct < 10:
        return "invalid_lt_10pct"
    if valid_pct <= 30:
        return "low_confidence_10_30pct"
    return "usable_gt_30pct"


def probable_reason(stats: dict[str, Any], valid_pct: float | None) -> str:
    sample_count = stats.get("sampleCount")
    no_data_count = stats.get("noDataCount")
    if not stats:
        return "No stats returned; date/window/AOI may have no matching pixels."
    if sample_count == no_data_count:
        return "No valid pixels after dataMask/SCL filtering; likely cloud, shadow, or no useful acquisition."
    if valid_pct is not None and valid_pct < 10:
        return "Below interpretation threshold; do not interpret."
    if valid_pct is not None and valid_pct <= 30:
        return "Low confidence; compare cautiously."
    return ""


def parse_raw_file(path: Path, metadata_by_date: dict[str, dict[str, str]]) -> dict[str, Any] | None:
    catalog_match = CATALOG_PATTERN.match(path.name)
    legacy_match = LEGACY_PATTERN.match(path.name)

    if catalog_match:
        groups = catalog_match.groupdict()
        aoi_label = AOI_LABEL_NORMALIZATION.get(groups["aoi_label"], groups["aoi_label"])
        index = groups["index"]
        date_value = groups["date"]
        resolution = groups["resolution"]
        window_days = groups["window_days"]
    elif legacy_match:
        groups = legacy_match.groupdict()
        aoi_label = "broad_aoi"
        index = groups["index"]
        date_value = groups["date"]
        resolution = groups.get("resolution") or ""
        window_days = ""
    else:
        return None

    with path.open("r", encoding="utf-8") as handle:
        response_json = json.load(handle)
    stats = extract_stats(response_json, index)
    valid_pct = valid_percent(stats)
    interval_from, interval_to = response_interval(response_json)
    metadata = metadata_by_date.get(date_value, {})

    return {
        "aoi_label": aoi_label,
        "date": date_value,
        "date_type": metadata.get("type", ""),
        "datetime": metadata.get("datetime", ""),
        "cloudCover": metadata.get("cloudCover", ""),
        "item_id": metadata.get("item_id", ""),
        "index": index,
        "resolution_meters": resolution,
        "window_days": window_days,
        "interval_from": interval_from,
        "interval_to": interval_to,
        "mean": stats.get("mean"),
        "stDev": stats.get("stDev"),
        "sampleCount": stats.get("sampleCount"),
        "noDataCount": stats.get("noDataCount"),
        "valid_percent_approx": valid_pct,
        "quality": quality_label(valid_pct),
        "raw_file": path.name,
        "notes": probable_reason(stats, valid_pct),
    }


def row_rank(row: dict[str, Any]) -> tuple[int, int]:
    has_resolution = 1 if row.get("resolution_meters") else 0
    has_stats = 1 if row.get("sampleCount") not in (None, "") else 0
    return has_resolution, has_stats


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["aoi_label"], row["date"], row["index"], str(row.get("window_days", "")))
        current = best.get(key)
        if current is None or row_rank(row) > row_rank(current):
            best[key] = row
    return sorted(best.values(), key=lambda row: (row["aoi_label"], row["date"], row["index"], row.get("window_days", "")))


def collect_rows() -> list[dict[str, Any]]:
    metadata_by_date = load_date_metadata()
    rows: list[dict[str, Any]] = []
    for path in sorted(RAW_DIR.glob("*_raw.json")):
        row = parse_raw_file(path, metadata_by_date)
        if row is not None:
            rows.append(row)
    return dedupe_rows(rows)


def write_summary_csv(rows: list[dict[str, Any]]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    columns = [
        "aoi_label",
        "date",
        "date_type",
        "datetime",
        "cloudCover",
        "item_id",
        "index",
        "resolution_meters",
        "window_days",
        "interval_from",
        "interval_to",
        "mean",
        "stDev",
        "sampleCount",
        "noDataCount",
        "valid_percent_approx",
        "quality",
        "raw_file",
        "notes",
    ]
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def useful_date_count(rows: list[dict[str, Any]], aoi_label: str | None = None) -> int:
    return len(
        {
            row["date"]
            for row in rows
            if row["quality"] == "usable_gt_30pct" and (aoi_label is None or row["aoi_label"] == aoi_label)
        }
    )


def row_count(rows: list[dict[str, Any]], aoi_label: str) -> int:
    return len([row for row in rows if row["aoi_label"] == aoi_label])


def most_usable_aoi(rows: list[dict[str, Any]]) -> str:
    counts = {aoi_label: useful_date_count(rows, aoi_label) for aoi_label in AOI_ORDER}
    best_label = max(counts, key=lambda label: (counts[label], -AOI_ORDER.index(label)))
    return f"{best_label} ({counts[best_label]} usable dates)"


def usable_counts_text(rows: list[dict[str, Any]]) -> str:
    return ", ".join(f"{label}={useful_date_count(rows, label)}" for label in AOI_ORDER)


def defensible_aoi_assessment(rows: list[dict[str, Any]]) -> str:
    corridor_wide_useful = useful_date_count(rows, "corridor_wide")
    river_useful = useful_date_count(rows, "river_corridor_aoi")
    broad_useful = useful_date_count(rows, "broad_aoi")
    if corridor_wide_useful > 0:
        return "corridor_wide, because it balances river adjacency with enough surrounding riparian/agricultural pixels to reduce pure narrow-channel noise."
    if river_useful > 0:
        return "river_corridor_aoi is hydrologically targeted, but it may be too narrow; corridor_wide should be tested before locking the science."
    if broad_useful > 0:
        return "broad_aoi is technically robust but scientifically diluted; corridor_wide is the next defensible hypothesis to test."
    return "No AOI is scientifically defensible yet; corridor_wide should be tested before any stronger claim."


def product_ceiling_assessment(rows: list[dict[str, Any]]) -> str:
    if useful_date_count(rows, "corridor_wide") > 0:
        return "Satellite confidence semaforo, with a possible upgrade to hydro-sedimentary exploratory semaforo only after a clear corridor_wide comparison."
    return "Satellite confidence semaforo. It is stronger than a data access demo, but not yet a hydro-sedimentary or agricultural decision semaforo."


def decision_from_rows(rows: list[dict[str, Any]]) -> str:
    corridor_rows = [row for row in rows if row["aoi_label"] == "river_corridor_aoi"]
    if corridor_rows and all(row["quality"].startswith("invalid") for row in corridor_rows):
        return "ADJUST AOI"
    if rows:
        return "GO TECHNICAL, ADJUST SCIENTIFIC"
    return "ADJUST AOI"


def format_value(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def table_lines(rows: list[dict[str, Any]], limit: int = 14) -> list[str]:
    lines = [
        "| aoi | date | index | mean | stDev | sampleCount | noDataCount | valid % | quality |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    format_value(row["aoi_label"]),
                    format_value(row["date"]),
                    format_value(row["index"]),
                    format_value(row["mean"]),
                    format_value(row["stDev"]),
                    format_value(row["sampleCount"]),
                    format_value(row["noDataCount"]),
                    format_value(row["valid_percent_approx"]),
                    format_value(row["quality"]),
                ]
            )
            + " |"
        )
    if not rows:
        lines.append("|  |  |  |  |  |  |  |  |  |")
    return lines


def write_spike_results(rows: list[dict[str, Any]], decision: str) -> None:
    path = NOTES_DIR / "spike_results.md"
    usable = [row for row in rows if row["quality"] == "usable_gt_30pct"]
    low = [row for row in rows if row["quality"] == "low_confidence_10_30pct"]
    invalid = [row for row in rows if row["quality"].startswith("invalid")]

    lines = [
        "# Internal Spike Results",
        "",
        "PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.",
        "",
        f"Current recommendation: {decision}.",
        "",
        "Technical viability is demonstrated by existing CDSE authentication, EPSG:32617 reprojection, and returned MNDWI/NDTI statistics. Scientific signal remains inconclusive until catalog-confirmed acquisition dates are compared across broad_aoi, corridor_wide, and river_corridor_aoi.",
        "",
        "Quality rule: validPercent < 10% is not interpreted; 10-30% is low confidence; >30% is usable for exploratory comparison.",
        "",
        "## Technical ceiling assessment",
        "",
        f"Usable-date counts by AOI: {usable_counts_text(rows)}.",
        "",
        f"AOI with most usable dates: {most_usable_aoi(rows)}.",
        "",
        f"Most scientifically defensible AOI: {defensible_aoi_assessment(rows)}",
        "",
        f"Product ceiling: {product_ceiling_assessment(rows)}",
        "",
        "## Usable Dates",
        "",
    ]
    lines.extend(table_lines(usable))
    lines.extend(["", "## Low Confidence Dates", ""])
    lines.extend(table_lines(low))
    lines.extend(["", "## Invalid / Low-Validity Dates", ""])
    lines.extend(table_lines(invalid))
    lines.extend(
        [
            "",
            "Interpretation limit: MNDWI supports observable water/wetness signal. NDTI is only a proxy for señal satelital exploratoria asociada a riesgo hidro-sedimentario observable. This does not detect pesticides, atrazine, dissolved chemicals, metals, pathogens, or complete water quality.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_go_no_go(rows: list[dict[str, Any]], decision: str) -> None:
    path = NOTES_DIR / "go_no_go_decision.md"
    broad_count = row_count(rows, "broad_aoi")
    corridor_wide_count = row_count(rows, "corridor_wide")
    river_count = row_count(rows, "river_corridor_aoi")
    lines = [
        "# Go/No-Go Decision for AgroShield Spike",
        "",
        "PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.",
        "",
        "## 1. Executive decision: GO, ADJUST AOI, or PIVOT.",
        "",
        decision,
        "",
        "## 2. Evidence summary.",
        "",
        f"Summarized rows: {len(rows)}. Broad AOI rows: {broad_count}. Corridor-wide rows: {corridor_wide_count}. River corridor AOI rows: {river_count}. Usable broad dates: {useful_date_count(rows, 'broad_aoi')}. Usable corridor-wide dates: {useful_date_count(rows, 'corridor_wide')}. Usable river dates: {useful_date_count(rows, 'river_corridor_aoi')}.",
        "",
        "## 3. CDSE authentication result.",
        "",
        "Auth: OK based on current spike status.",
        "",
        "## 4. AOI validity.",
        "",
        "Broad AOI returns data but likely dilutes river signal with urban/agricultural pixels. River corridor AOI is hydrologically targeted but can be too sparse. Corridor-wide is the intermediate technical-ceiling AOI and remains approximate.",
        "",
        "## 5. Sentinel-2 data availability.",
        "",
        "CDSE Statistical API: OK. Catalog-confirmed date discovery must drive the next comparison rather than arbitrary windows.",
        "",
        "## 6. MNDWI interpretability.",
        "",
        "MNDWI statistics are returned. Interpretation should be limited to observable water/wetness support and filtered by validPercent.",
        "",
        "## 7. NDTI/Red-Green interpretability.",
        "",
        "NDTI statistics are returned. Current scientific signal is inconclusive; no crisis validation is claimed.",
        "",
        "## 8. Main technical risk.",
        "",
        "The broad AOI may dilute signal, the river-only AOI may be too sparse, and corridor_wide must be tested in small cached batches. Cloud/SCL filtering may leave too few valid pixels on some dates.",
        "",
        "## 9. Recommended next action.",
        "",
        "Use Catalog API dates, cache-first Statistical API runs, 1-day windows with 2-day fallback if data are empty, and compare broad AOI, corridor_wide, and river corridor AOI before deciding whether scientific signal is strong enough. A final MVP should use cached precomputed outputs and optionally one live CDSE refresh, not repeated uncached request bursts.",
        "",
        "## 10. What must NOT be reused in official hackathon repo.",
        "",
        "Do not reuse this folder, code, evalscripts, raw outputs, processed CSVs, notes, AOI files, or wording as official hackathon deliverables.",
        "",
        "CRS/reprojection: OK. Current scientific signal: inconclusive. Next decision depends on corridor_wide and river corridor AOIs plus catalog-confirmed dates.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = collect_rows()
    write_summary_csv(rows)
    decision = decision_from_rows(rows)
    write_spike_results(rows, decision)
    write_go_no_go(rows, decision)
    print(f"Summary CSV: {SUMMARY_CSV}")
    print(f"Recommendation: {decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
