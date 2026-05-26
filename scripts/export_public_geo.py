"""Export frontend-safe AOI geography for the Azuero Kairós public demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_AOI_PATH = PROJECT_ROOT / "configs" / "aoi_corridor_wide_mvp.geojson"
FALLBACK_AOI_PATH = PROJECT_ROOT / "configs" / "aoi_corridor_wide.geojson"
PUBLIC_DATA_DIR = PROJECT_ROOT / "frontend" / "public" / "data"
PUBLIC_AOI_PATH = PUBLIC_DATA_DIR / "aoi_corridor_wide.geojson"
PUBLIC_CONTEXT_PATH = PUBLIC_DATA_DIR / "territorial_context.json"


def main() -> int:
    source_aoi_path = ACTIVE_AOI_PATH if ACTIVE_AOI_PATH.exists() else FALLBACK_AOI_PATH
    if not source_aoi_path.exists():
        raise SystemExit(
            "Missing source AOI. Expected configs/aoi_corridor_wide_mvp.geojson "
            "or configs/aoi_corridor_wide.geojson."
        )

    source_geojson = read_geojson(source_aoi_path)
    public_geojson = make_public_geojson(source_geojson)
    positions = list(iter_lonlat_positions(public_geojson))
    if not positions:
        raise SystemExit(f"Source AOI has no coordinates: {source_aoi_path}")

    bbox = compute_bbox(positions)
    centroid = compute_centroid(public_geojson, positions)
    context = build_context(bbox=bbox, centroid=centroid)

    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_json(PUBLIC_AOI_PATH, public_geojson)
    write_json(PUBLIC_CONTEXT_PATH, context)

    print(f"Source AOI path: {relative_to_project(source_aoi_path)}")
    print(f"Output GeoJSON path: {relative_to_project(PUBLIC_AOI_PATH)}")
    print(f"Centroid: {centroid}")
    print(f"BBox: {bbox}")
    print("Public-safe: yes")
    return 0


def read_geojson(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"AOI is not valid JSON: {path}") from exc

    if payload.get("type") not in {"Feature", "FeatureCollection", "Polygon", "MultiPolygon"}:
        raise SystemExit(f"Unsupported GeoJSON type in {path}: {payload.get('type')}")
    return payload


def make_public_geojson(payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = json.loads(json.dumps(payload))
    public_payload["name"] = "aoi_corridor_wide"
    public_payload["public_safe"] = True

    for feature in public_payload.get("features", []):
        properties = feature.setdefault("properties", {})
        properties["id"] = "aoi_corridor_wide"
        properties["public_safe"] = True
        properties["source"] = "Azuero Kairós official MVP AOI config"
        properties.pop("local_path", None)
        properties.pop("request_headers", None)
        properties.pop("credentials", None)

    return public_payload


def build_context(*, bbox: list[float], centroid: list[float]) -> dict[str, Any]:
    return {
        "country": "Panamá",
        "region": "Azuero",
        "corridor_name": "Río La Villa",
        "aoi_name": "corridor_wide",
        "source": "Copernicus CDSE Statistical API",
        "sensor": "Sentinel-2 L2A",
        "resolution_m": 20,
        "note": (
            "Contexto territorial del caso piloto. La geometría oficial se procesa "
            "desde el AOI del pipeline."
        ),
        "bbox": bbox,
        "centroid": centroid,
        "geometry_file": "/data/aoi_corridor_wide.geojson",
        "coordinate_reference_system": "EPSG:4326",
        "coordinate_order": "lon_lat_geojson",
        "public_safe": True,
    }


def iter_lonlat_positions(payload: dict[str, Any]):
    geojson_type = payload.get("type")
    if geojson_type == "FeatureCollection":
        for feature in payload.get("features", []):
            yield from iter_lonlat_positions(feature)
    elif geojson_type == "Feature":
        geometry = payload.get("geometry") or {}
        yield from iter_lonlat_positions(geometry)
    elif geojson_type in {"Polygon", "MultiPolygon"}:
        yield from walk_positions(payload.get("coordinates", []))


def walk_positions(value: Any):
    if (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        yield [float(value[0]), float(value[1])]
        return

    if isinstance(value, list):
        for item in value:
            yield from walk_positions(item)


def compute_bbox(positions: list[list[float]]) -> list[float]:
    longitudes = [position[0] for position in positions]
    latitudes = [position[1] for position in positions]
    return [
        round(min(longitudes), 6),
        round(min(latitudes), 6),
        round(max(longitudes), 6),
        round(max(latitudes), 6),
    ]


def compute_centroid(payload: dict[str, Any], positions: list[list[float]]) -> list[float]:
    rings = list(iter_polygon_outer_rings(payload))
    weighted_centroids = [polygon_ring_centroid(ring) for ring in rings]
    weighted_centroids = [item for item in weighted_centroids if item is not None]

    if weighted_centroids:
        total_area = sum(abs(item["area"]) for item in weighted_centroids)
        if total_area:
            lon = sum(item["lon"] * abs(item["area"]) for item in weighted_centroids) / total_area
            lat = sum(item["lat"] * abs(item["area"]) for item in weighted_centroids) / total_area
            return [round(lon, 6), round(lat, 6)]

    lon = sum(position[0] for position in positions) / len(positions)
    lat = sum(position[1] for position in positions) / len(positions)
    return [round(lon, 6), round(lat, 6)]


def iter_polygon_outer_rings(payload: dict[str, Any]):
    geojson_type = payload.get("type")
    if geojson_type == "FeatureCollection":
        for feature in payload.get("features", []):
            yield from iter_polygon_outer_rings(feature)
    elif geojson_type == "Feature":
        yield from iter_polygon_outer_rings(payload.get("geometry") or {})
    elif geojson_type == "Polygon":
        coordinates = payload.get("coordinates") or []
        if coordinates:
            yield coordinates[0]
    elif geojson_type == "MultiPolygon":
        for polygon in payload.get("coordinates") or []:
            if polygon:
                yield polygon[0]


def polygon_ring_centroid(ring: list[list[float]]) -> dict[str, float] | None:
    if len(ring) < 4:
        return None

    area_twice = 0.0
    lon_sum = 0.0
    lat_sum = 0.0
    for current, following in zip(ring, ring[1:]):
        x0, y0 = float(current[0]), float(current[1])
        x1, y1 = float(following[0]), float(following[1])
        cross = x0 * y1 - x1 * y0
        area_twice += cross
        lon_sum += (x0 + x1) * cross
        lat_sum += (y0 + y1) * cross

    if area_twice == 0:
        return None

    return {
        "lon": lon_sum / (3 * area_twice),
        "lat": lat_sum / (3 * area_twice),
        "area": area_twice / 2,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def relative_to_project(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
