"""Search Sentinel-2 L2A acquisitions with the Sentinel Hub Catalog API.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

import requests

from auth_cdse import get_cdse_token
from reproject_aoi import load_geojson
from stats_request import PROJECT_ROOT, save_json


CATALOG_URL = os.getenv(
    "CDSE_CATALOG_URL",
    "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search",
)
RAW_DIR = PROJECT_ROOT / "outputs" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "outputs" / "processed"
CATALOG_CSV = PROCESSED_DIR / "s2_l2a_catalog_candidates.csv"
CATALOG_DATES_CSV = PROJECT_ROOT / "data" / "candidate_dates_from_catalog.csv"


def extract_geometry(geojson: dict[str, Any]) -> dict[str, Any]:
    geojson_type = geojson.get("type")
    if geojson_type == "FeatureCollection":
        features = geojson.get("features", [])
        if not features:
            raise ValueError("AOI FeatureCollection has no features.")
        geometry = features[0].get("geometry")
    elif geojson_type == "Feature":
        geometry = geojson.get("geometry")
    else:
        geometry = geojson

    if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Catalog AOI must be Polygon or MultiPolygon GeoJSON in lon/lat.")
    return geometry


def build_catalog_payload(geometry: dict[str, Any], limit: int, next_token: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "collections": ["sentinel-2-l2a"],
        "datetime": "2025-05-01T00:00:00Z/2025-07-15T23:59:59Z",
        "intersects": geometry,
        "limit": limit,
        "fields": {
            "include": [
                "id",
                "bbox",
                "properties.datetime",
                "properties.eo:cloud_cover",
                "properties.s2:product_uri",
            ]
        },
    }
    if next_token is not None:
        payload["next"] = next_token
    return payload


def post_catalog(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/geo+json",
    }
    response = requests.post(CATALOG_URL, headers=headers, json=payload, timeout=90)
    if not response.ok:
        print(f"CDSE Catalog API HTTP {response.status_code} response: {response.text}")
        raise RuntimeError(f"Catalog API failed with HTTP {response.status_code}: {response.text}")
    return response.json()


def item_to_row(item: dict[str, Any]) -> dict[str, str]:
    properties = item.get("properties", {})
    datetime_value = properties.get("datetime", "")
    date_value = datetime_value[:10] if datetime_value else ""
    cloud_cover = properties.get("eo:cloud_cover")
    item_id = item.get("id", "")
    product_uri = properties.get("s2:product_uri")
    notes = "Catalog-confirmed Sentinel-2 L2A acquisition intersecting approximate AOI."
    if product_uri:
        notes = f"{notes} product_uri={product_uri}"
    return {
        "date": date_value,
        "datetime": datetime_value,
        "cloudCover": "" if cloud_cover is None else str(cloud_cover),
        "item_id": item_id,
        "bbox": json.dumps(item.get("bbox", []), separators=(",", ":")),
        "source": "sentinel-hub-catalog-api",
        "notes": notes,
    }


def write_catalog_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["date", "datetime", "cloudCover", "item_id", "bbox", "source", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def cloud_value(row: dict[str, str]) -> float:
    try:
        return float(row["cloudCover"])
    except (TypeError, ValueError):
        return 999.0


def write_candidate_dates_from_catalog(rows: list[dict[str, str]], path: Path) -> None:
    best_by_date: dict[str, dict[str, str]] = {}
    for row in rows:
        date_value = row["date"]
        if not date_value:
            continue
        current = best_by_date.get(date_value)
        if current is None or cloud_value(row) < cloud_value(current):
            best_by_date[date_value] = row

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["date", "type", "datetime", "cloudCover", "item_id", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in sorted(best_by_date.values(), key=lambda value: value["datetime"]):
            writer.writerow(
                {
                    "date": row["date"],
                    "type": "catalog_acquisition",
                    "datetime": row["datetime"],
                    "cloudCover": row["cloudCover"],
                    "item_id": row["item_id"],
                    "notes": "Selected lowest-cloud catalog item for this acquisition date.",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Sentinel-2 L2A catalog candidates for the private spike.")
    parser.add_argument("--aoi", type=Path, default=PROJECT_ROOT / "data" / "aoi_chitre_la_arena_approx.geojson")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        token = get_cdse_token()
        geometry = extract_geometry(load_geojson(args.aoi))
        all_items: list[dict[str, Any]] = []
        next_token: Any | None = None

        for page in range(args.max_pages):
            payload = build_catalog_payload(geometry, args.limit, next_token)
            save_json(RAW_DIR / f"catalog_search_s2_l2a_payload_page_{page + 1}.json", payload)
            response_json = post_catalog(token, payload)
            save_json(RAW_DIR / f"catalog_search_s2_l2a_raw_page_{page + 1}.json", response_json)
            all_items.extend(response_json.get("features", []))
            next_token = response_json.get("context", {}).get("next")
            if next_token is None:
                break

        rows = sorted([item_to_row(item) for item in all_items], key=lambda row: (row["datetime"], cloud_value(row)))
        write_catalog_csv(rows, CATALOG_CSV)
        write_candidate_dates_from_catalog(rows, CATALOG_DATES_CSV)
        unique_dates = {row["date"] for row in rows if row["date"]}
        print(f"Catalog search: OK - items={len(rows)} unique_dates={len(unique_dates)}")
        print(f"Catalog CSV: {CATALOG_CSV}")
        print(f"Candidate dates CSV: {CATALOG_DATES_CSV}")
        return 0
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"Catalog search: FAIL - {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
