from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_AOI_PATH = PROJECT_ROOT / "configs" / "aoi_corridor_wide_mvp.geojson"
FALLBACK_AOI_PATH = PROJECT_ROOT / "configs" / "aoi_corridor_wide.geojson"
OUTPUT_DIR = PROJECT_ROOT / "configs" / "aoi_nodes"

NODE_DEFINITIONS = [
    ("la_villa_oeste", "La Villa Oeste"),
    ("la_villa_central", "La Villa Central"),
    ("la_villa_este", "La Villa Este"),
]

DERIVATION_NOTE = (
    "analytical sub-AOI derived from corridor_wide for hackathon MVP"
)


def main() -> int:
    source_path = ACTIVE_AOI_PATH if ACTIVE_AOI_PATH.exists() else FALLBACK_AOI_PATH
    if not source_path.exists():
        raise SystemExit(
            "Missing source AOI. Expected configs/aoi_corridor_wide_mvp.geojson "
            "or configs/aoi_corridor_wide.geojson."
        )

    source_geojson = read_geojson(source_path)
    polygons = list(iter_polygon_rings(source_geojson))
    if not polygons:
        raise SystemExit(f"Source AOI has no polygon geometry: {source_path}")

    bbox = compute_bbox(list(iter_positions_from_polygons(polygons)))
    min_lon, _, max_lon, _ = bbox
    lon_breaks = [
        min_lon,
        min_lon + (max_lon - min_lon) / 3,
        min_lon + 2 * (max_lon - min_lon) / 3,
        max_lon,
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    node_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for index, (node_id, display_name) in enumerate(NODE_DEFINITIONS):
        min_clip = lon_breaks[index]
        max_clip = lon_breaks[index + 1]
        segment_geometry = build_segment_geometry(polygons, min_clip, max_clip)
        if segment_geometry is None:
            raise SystemExit(f"Could not build non-empty segment for {node_id}")

        segment_feature_collection = build_feature_collection(
            node_id=node_id,
            display_name=display_name,
            source_path=source_path,
            geometry=segment_geometry,
        )
        output_path = OUTPUT_DIR / f"{node_id}.geojson"
        write_json(output_path, segment_feature_collection)

        node_bbox = compute_bbox(list(iter_lonlat_positions(segment_geometry)))
        area_km2 = estimate_area_km2(segment_geometry)
        valid = is_valid_geojson_geometry(segment_geometry)
        node_rows.append(
            {
                "node_id": node_id,
                "display_name": display_name,
                "geojson_path": relative_to_project(output_path),
                "region": "Azuero",
                "corridor": "Río La Villa",
                "note": DERIVATION_NOTE,
            }
        )
        summary_rows.append(
            {
                "node_id": node_id,
                "bbox": node_bbox,
                "area_km2": area_km2,
                "valid": valid,
            }
        )

    nodes_path = OUTPUT_DIR / "nodes.yaml"
    write_nodes_yaml(nodes_path, node_rows)

    print(f"Source AOI: {relative_to_project(source_path)}")
    print("Created analytical AOI nodes:")
    for row in summary_rows:
        valid_text = "yes" if row["valid"] else "no"
        area_text = f"{row['area_km2']:.3f} km^2" if row["area_km2"] is not None else "unavailable"
        print(
            f"- {row['node_id']}: bbox={row['bbox']}, "
            f"area_estimate={area_text}, valid_geojson={valid_text}"
        )
    print(f"Nodes manifest: {relative_to_project(nodes_path)}")
    return 0


def read_geojson(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"AOI is not valid JSON: {path}") from exc

    if payload.get("type") not in {"Feature", "FeatureCollection", "Polygon", "MultiPolygon"}:
        raise SystemExit(f"Unsupported GeoJSON type in {path}: {payload.get('type')}")
    return payload


def build_feature_collection(
    *,
    node_id: str,
    display_name: str,
    source_path: Path,
    geometry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": node_id,
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "node_id": node_id,
                    "display_name": display_name,
                    "region": "Azuero",
                    "corridor": "Río La Villa",
                    "source_aoi": "corridor_wide",
                    "derived_from": relative_to_project(source_path),
                    "note": DERIVATION_NOTE,
                },
                "geometry": geometry,
            }
        ],
    }


def iter_polygon_rings(payload: dict[str, Any]):
    geojson_type = payload.get("type")
    if geojson_type == "FeatureCollection":
        for feature in payload.get("features", []):
            yield from iter_polygon_rings(feature)
    elif geojson_type == "Feature":
        yield from iter_polygon_rings(payload.get("geometry") or {})
    elif geojson_type == "Polygon":
        coordinates = payload.get("coordinates") or []
        if coordinates:
            yield coordinates
    elif geojson_type == "MultiPolygon":
        for polygon in payload.get("coordinates") or []:
            if polygon:
                yield polygon


def build_segment_geometry(
    polygons: list[list[list[list[float]]]],
    min_lon: float,
    max_lon: float,
) -> dict[str, Any] | None:
    clipped_polygons: list[list[list[list[float]]]] = []
    for polygon in polygons:
        clipped_rings: list[list[list[float]]] = []
        for ring_index, ring in enumerate(polygon):
            clipped_ring = clip_ring_to_lon_range(ring, min_lon, max_lon)
            if is_valid_ring(clipped_ring):
                clipped_rings.append(clipped_ring)
            elif ring_index == 0:
                clipped_rings = []
                break

        if clipped_rings:
            clipped_polygons.append(clipped_rings)

    if not clipped_polygons:
        return None

    if len(clipped_polygons) == 1:
        return {"type": "Polygon", "coordinates": clipped_polygons[0]}
    return {"type": "MultiPolygon", "coordinates": clipped_polygons}


def clip_ring_to_lon_range(
    ring: list[list[float]],
    min_lon: float,
    max_lon: float,
) -> list[list[float]]:
    points = normalize_open_ring(ring)
    if len(points) < 3:
        return []

    points = clip_points_against_lon(points, min_lon, keep_greater=True)
    points = clip_points_against_lon(points, max_lon, keep_greater=False)
    points = remove_consecutive_duplicates(points)
    if len(points) < 3:
        return []

    closed = [[round(point[0], 8), round(point[1], 8)] for point in points]
    if closed[0] != closed[-1]:
        closed.append(closed[0])
    return closed


def clip_points_against_lon(
    points: list[list[float]],
    boundary_lon: float,
    *,
    keep_greater: bool,
) -> list[list[float]]:
    def is_inside(point: list[float]) -> bool:
        return point[0] >= boundary_lon if keep_greater else point[0] <= boundary_lon

    def intersection(start: list[float], end: list[float]) -> list[float]:
        start_lon, start_lat = start
        end_lon, end_lat = end
        if end_lon == start_lon:
            return [boundary_lon, start_lat]
        ratio = (boundary_lon - start_lon) / (end_lon - start_lon)
        return [boundary_lon, start_lat + ratio * (end_lat - start_lat)]

    if not points:
        return []

    clipped: list[list[float]] = []
    previous = points[-1]
    previous_inside = is_inside(previous)
    for current in points:
        current_inside = is_inside(current)
        if current_inside:
            if not previous_inside:
                clipped.append(intersection(previous, current))
            clipped.append(current)
        elif previous_inside:
            clipped.append(intersection(previous, current))
        previous = current
        previous_inside = current_inside

    return clipped


def normalize_open_ring(ring: list[list[float]]) -> list[list[float]]:
    points = [[float(point[0]), float(point[1])] for point in ring if len(point) >= 2]
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    return points


def remove_consecutive_duplicates(points: list[list[float]]) -> list[list[float]]:
    deduped: list[list[float]] = []
    for point in points:
        rounded = [round(point[0], 10), round(point[1], 10)]
        if not deduped or rounded != deduped[-1]:
            deduped.append(rounded)
    if len(deduped) > 1 and deduped[0] == deduped[-1]:
        deduped = deduped[:-1]
    return deduped


def is_valid_geojson_geometry(geometry: dict[str, Any]) -> bool:
    if geometry.get("type") == "Polygon":
        return all(is_valid_ring(ring) for ring in geometry.get("coordinates") or [])
    if geometry.get("type") == "MultiPolygon":
        return all(
            all(is_valid_ring(ring) for ring in polygon)
            for polygon in geometry.get("coordinates") or []
        )
    return False


def is_valid_ring(ring: list[list[float]]) -> bool:
    return (
        len(ring) >= 4
        and ring[0] == ring[-1]
        and abs(planar_ring_area(ring)) > 0
    )


def compute_bbox(positions: list[list[float]]) -> list[float]:
    if not positions:
        raise ValueError("Cannot compute bbox without positions.")
    longitudes = [position[0] for position in positions]
    latitudes = [position[1] for position in positions]
    return [
        round(min(longitudes), 6),
        round(min(latitudes), 6),
        round(max(longitudes), 6),
        round(max(latitudes), 6),
    ]


def iter_positions_from_polygons(polygons: list[list[list[list[float]]]]):
    for polygon in polygons:
        for ring in polygon:
            for point in ring:
                if len(point) >= 2:
                    yield [float(point[0]), float(point[1])]


def iter_lonlat_positions(payload: dict[str, Any]):
    geojson_type = payload.get("type")
    if geojson_type == "FeatureCollection":
        for feature in payload.get("features", []):
            yield from iter_lonlat_positions(feature)
    elif geojson_type == "Feature":
        yield from iter_lonlat_positions(payload.get("geometry") or {})
    elif geojson_type == "Polygon":
        yield from walk_positions(payload.get("coordinates", []))
    elif geojson_type == "MultiPolygon":
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


def estimate_area_km2(geometry: dict[str, Any]) -> float | None:
    try:
        from pyproj import Geod

        geod = Geod(ellps="WGS84")
        area_m2 = 0.0
        for polygon in iter_geometry_polygons(geometry):
            for index, ring in enumerate(polygon):
                lons = [point[0] for point in ring]
                lats = [point[1] for point in ring]
                ring_area, _ = geod.polygon_area_perimeter(lons, lats)
                if index == 0:
                    area_m2 += abs(ring_area)
                else:
                    area_m2 -= abs(ring_area)
        return round(abs(area_m2) / 1_000_000, 3)
    except Exception:
        return round(estimate_area_km2_planar(geometry), 3)


def estimate_area_km2_planar(geometry: dict[str, Any]) -> float:
    total = 0.0
    for polygon in iter_geometry_polygons(geometry):
        for index, ring in enumerate(polygon):
            area = abs(planar_ring_area(ring))
            total += area if index == 0 else -area
    return abs(total) * 111.32 * 111.32


def iter_geometry_polygons(geometry: dict[str, Any]):
    if geometry.get("type") == "Polygon":
        yield geometry.get("coordinates") or []
    elif geometry.get("type") == "MultiPolygon":
        yield from geometry.get("coordinates") or []


def planar_ring_area(ring: list[list[float]]) -> float:
    if len(ring) < 4:
        return 0.0
    area_twice = 0.0
    for current, following in zip(ring, ring[1:]):
        area_twice += current[0] * following[1] - following[0] * current[1]
    return area_twice / 2


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_nodes_yaml(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["nodes:"]
    for row in rows:
        lines.extend(
            [
                f"  - node_id: {row['node_id']}",
                f"    display_name: {row['display_name']}",
                f"    geojson_path: {row['geojson_path']}",
                f"    region: {row['region']}",
                f"    corridor: {row['corridor']}",
                f"    note: {row['note']}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def relative_to_project(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
