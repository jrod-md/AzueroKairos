"""Minimal Sentinel Hub Statistical API request helpers.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from reproject_aoi import (
    SOURCE_CRS_LABEL,
    TARGET_CRS_LABEL,
    projected_bounds,
    reproject_geometry_to_epsg32617,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATS_URL = "https://sh.dataspace.copernicus.eu/statistics/v1"
EPSG32617_CRS = "http://www.opengis.net/def/crs/EPSG/0/32617"


def stats_url() -> str:
    return os.getenv("CDSE_STATS_URL", DEFAULT_STATS_URL)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_aoi_geometry(path: Path) -> dict[str, Any]:
    geojson = read_json(path)
    geojson_type = geojson.get("type")

    if geojson_type == "FeatureCollection":
        features = geojson.get("features", [])
        if not features:
            raise ValueError(f"AOI file has no features: {path}")
        geometry = features[0].get("geometry")
    elif geojson_type == "Feature":
        geometry = geojson.get("geometry")
    else:
        geometry = geojson

    if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"AOI must be Polygon or MultiPolygon GeoJSON: {path}")

    return reproject_geometry_to_epsg32617(geometry)


def read_evalscript(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def one_day_window(day: str, window_days: int = 1) -> tuple[str, str]:
    start_date = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_date = start_date + timedelta(days=window_days)
    return start_date.isoformat().replace("+00:00", "Z"), end_date.isoformat().replace("+00:00", "Z")


def build_stats_payload(
    geometry: dict[str, Any],
    evalscript: str,
    start_iso: str,
    end_iso: str,
    window_days: int = 1,
    resolution_meters: int | float = 20,
) -> dict[str, Any]:
    if resolution_meters <= 0:
        raise ValueError("resolution_meters must be a positive integer.")

    return {
        "input": {
            "bounds": {
                "geometry": geometry,
                "properties": {"crs": EPSG32617_CRS},
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "mosaickingOrder": "leastCC",
                        "maxCloudCoverage": 100,
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {
                "from": start_iso,
                "to": end_iso,
            },
            "aggregationInterval": {
                "of": f"P{window_days}D",
            },
            "evalscript": evalscript,
            "resx": resolution_meters,
            "resy": resolution_meters,
        },
    }


def payload_debug_context(geometry: dict[str, Any], resolution_meters: int | float) -> dict[str, Any]:
    return {
        "source_crs": SOURCE_CRS_LABEL,
        "target_crs": TARGET_CRS_LABEL,
        "resolution_meters": resolution_meters,
        "projected_bounds": projected_bounds(geometry),
    }


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def post_statistics(token: str, payload: dict[str, Any], debug_payload_path: Path | None = None) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if debug_payload_path:
        save_json(debug_payload_path, payload)

    response = requests.post(stats_url(), headers=headers, json=payload, timeout=90)

    if response.status_code == 400:
        print(f"CDSE Statistical API HTTP 400 response: {response.text}")
        raise RuntimeError(
            "Statistical API rejected the request with HTTP 400. "
            f"Sanitized payload saved to {debug_payload_path}. Response: {response.text}"
        )

    if response.status_code == 401:
        raise RuntimeError(
            "Statistical API returned HTTP 401. Recheck CDSE_CLIENT_ID/CDSE_CLIENT_SECRET "
            "and confirm the OAuth client is valid for Sentinel Hub APIs. "
            f"Response: {response.text}"
        )

    if response.status_code == 429:
        raise RuntimeError(
            "Statistical API returned HTTP 429. Rate limit or processing-unit limit likely hit. "
            f"Response: {response.text}"
        )

    if not response.ok:
        raise RuntimeError(
            f"Statistical API returned HTTP {response.status_code}: {response.text}"
        )

    return response.json()


def first_band_stats(response_json: dict[str, Any], output_id: str) -> dict[str, Any]:
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

    first_band = next(iter(bands.values()))
    return first_band.get("stats", {})


def valid_percent(stats: dict[str, Any]) -> float | None:
    sample_count = stats.get("sampleCount")
    no_data_count = stats.get("noDataCount")
    if not isinstance(sample_count, (int, float)) or sample_count == 0:
        return None
    if not isinstance(no_data_count, (int, float)):
        return None
    return round(100.0 * (sample_count - no_data_count) / sample_count, 2)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
