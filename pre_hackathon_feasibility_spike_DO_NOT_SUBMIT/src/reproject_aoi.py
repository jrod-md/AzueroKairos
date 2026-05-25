"""AOI reprojection helpers for the private Statistical API spike.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform


SOURCE_CRS_LABEL = "CRS84/lonlat"
TARGET_EPSG = 32617
TARGET_CRS_LABEL = "EPSG:32617"


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_positions(coordinates: Any):
    if not coordinates:
        return
    first = coordinates[0]
    if isinstance(first, (int, float)):
        yield coordinates
        return
    for item in coordinates:
        yield from _iter_positions(item)


def _validate_coordinate_order_lonlat(geojson_geometry: dict[str, Any]) -> None:
    positions = list(_iter_positions(geojson_geometry.get("coordinates")))
    if not positions:
        raise ValueError("AOI geometry has no coordinates.")

    for position in positions:
        if len(position) < 2:
            raise ValueError(f"Invalid AOI coordinate with fewer than two values: {position}")
        lon, lat = position[:2]
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise ValueError(
                "AOI coordinates are not valid lon/lat degrees. "
                f"Got coordinate {position}; expected [longitude, latitude]."
            )

    xs = [position[0] for position in positions]
    ys = [position[1] for position in positions]
    looks_like_azuero_lonlat = min(xs) >= -84 and max(xs) <= -77 and min(ys) >= 6 and max(ys) <= 10
    looks_swapped_for_azuero = min(xs) >= 6 and max(xs) <= 10 and min(ys) >= -84 and max(ys) <= -77

    if looks_swapped_for_azuero:
        raise ValueError(
            "AOI coordinates look swapped for Panama/Azuero. "
            "Use [longitude, latitude], for example [-80.45, 7.98]."
        )

    if not looks_like_azuero_lonlat:
        raise ValueError(
            "AOI coordinates are valid degrees but do not look like the expected Azuero lon/lat area. "
            "Confirm coordinate order [longitude, latitude] before using this spike."
        )


def _to_shapely_geometry(geojson_geometry: dict[str, Any]) -> BaseGeometry:
    geometry_type = geojson_geometry.get("type")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"AOI must be Polygon or MultiPolygon GeoJSON, got: {geometry_type}")

    geometry = shape(geojson_geometry)
    if geometry.is_empty:
        raise ValueError("AOI geometry is empty.")
    if not geometry.is_valid:
        raise ValueError(f"AOI geometry is invalid: {geometry.wkt[:500]}")
    return geometry


def reproject_geometry_to_epsg32617(geojson_geometry: dict[str, Any]) -> dict[str, Any]:
    """Return a Polygon/MultiPolygon GeoJSON geometry projected to EPSG:32617 meters."""
    _validate_coordinate_order_lonlat(geojson_geometry)
    source_geometry = _to_shapely_geometry(geojson_geometry)
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{TARGET_EPSG}", always_xy=True)
    projected = transform(transformer.transform, source_geometry)
    if projected.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"Projected AOI changed to unsupported geometry type: {projected.geom_type}")
    return mapping(projected)


def projected_bounds(geojson_geometry: dict[str, Any]) -> list[float]:
    geometry = shape(geojson_geometry)
    minx, miny, maxx, maxy = geometry.bounds
    return [round(minx, 3), round(miny, 3), round(maxx, 3), round(maxy, 3)]
