"""Prototype CLMS land-cover exposure context for La Villa nodes.

This script is experimental and writes only under outputs/exposure by default.
It does not update public frontend exports. The default mode is a dry run that
builds request payloads without calling the network. Use --run only when CDSE
credentials are configured in the environment.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml
from pyproj import Transformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from azuero_kairos.cdse_auth import get_cdse_token  # noqa: E402

STATISTICS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
COLLECTION_ID = "828f6b20-8ffd-48f8-a1da-fefd271456db"
SOURCE_DATASET = "CLMS Global Dynamic Land Cover 10m Annual V1"
REFERENCE_YEAR = 2020
SOURCE_RESOLUTION_M = 10
TARGET_EPSG = 32617
DEFAULT_MAX_GRID_DIMENSION = 2400
DEFAULT_MAX_ANALYSIS_RESOLUTION_M = 30
RESOLUTION_STRATEGY = "adaptive_statistical_sampling"
DEFAULT_NODES_PATH = PROJECT_ROOT / "configs" / "aoi_nodes" / "nodes.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "exposure"

CLASS_LABELS = {
    10: "trees",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_sparse",
    70: "snow_ice",
    80: "water",
    90: "wetland",
    95: "mangroves",
    100: "moss_lichen",
    255: "no_data",
}

GROUPS = {
    "cropland_agriculture": {40},
    "tree_vegetation": {10, 20, 30, 100},
    "water_wetland": {80, 90, 95},
    "built_bare_other": {50, 60, 70},
}

CLAIM_LIMIT = (
    "Contexto territorial auxiliar; no se usa como evidencia principal y no "
    "sustituye verificacion territorial, laboratorio ni autoridad competente."
)

EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: [{ bands: ["LCM10", "dataMask"] }],
    output: [
      { id: "classes", bands: 1, sampleType: "UINT8" },
      { id: "dataMask", bands: 1 }
    ]
  };
}

function evaluatePixel(sample) {
  return {
    classes: [sample.LCM10],
    dataMask: [sample.dataMask]
  };
}
"""


@dataclass(frozen=True)
class Node:
    node_id: str
    name: str
    geojson_path: Path


@dataclass(frozen=True)
class GridPlan:
    analysis_resolution_m: int
    grid_width: int
    grid_height: int
    width_m: float
    height_m: float
    max_grid_dimension: int
    max_analysis_resolution_m: int
    resolution_strategy: str = RESOLUTION_STRATEGY


def load_nodes(nodes_path: Path) -> list[Node]:
    with nodes_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    nodes: list[Node] = []
    for item in payload.get("nodes", []):
        node_id = str(item.get("node_id", item.get("id", "")))
        if not node_id:
            raise ValueError(f"Node entry is missing node_id/id in {nodes_path}")
        geojson_path = PROJECT_ROOT / item["geojson_path"]
        nodes.append(
            Node(
                node_id=node_id,
                name=str(item.get("display_name", node_id)),
                geojson_path=geojson_path,
            )
        )
    return nodes


def load_feature_geometry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    features = payload.get("features") or []
    if not features:
        raise ValueError(f"No features found in {path}")
    geometry = features[0].get("geometry")
    if not geometry:
        raise ValueError(f"No geometry found in first feature of {path}")
    return geometry


def transform_position(position: list[float], transformer: Transformer) -> list[float]:
    x, y = transformer.transform(position[0], position[1])
    return [round(x, 3), round(y, 3)]


def transform_coordinates(coordinates: Any, transformer: Transformer) -> Any:
    if isinstance(coordinates, list) and coordinates and isinstance(coordinates[0], (int, float)):
        return transform_position(coordinates, transformer)
    if isinstance(coordinates, list):
        return [transform_coordinates(item, transformer) for item in coordinates]
    return coordinates


def geometry_to_target_crs(geometry: dict[str, Any], target_epsg: int) -> dict[str, Any]:
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{target_epsg}", always_xy=True)
    return {
        "type": geometry["type"],
        "coordinates": transform_coordinates(geometry["coordinates"], transformer),
    }


def collect_positions(coordinates: Any, positions: list[tuple[float, float]]) -> None:
    if isinstance(coordinates, list) and coordinates and isinstance(coordinates[0], (int, float)):
        positions.append((float(coordinates[0]), float(coordinates[1])))
        return
    if isinstance(coordinates, list):
        for item in coordinates:
            collect_positions(item, positions)


def geometry_bounds(geometry_utm: dict[str, Any]) -> tuple[float, float, float, float]:
    positions: list[tuple[float, float]] = []
    collect_positions(geometry_utm.get("coordinates"), positions)
    if not positions:
        raise ValueError("No coordinate positions found after CRS transform")
    xs = [position[0] for position in positions]
    ys = [position[1] for position in positions]
    return min(xs), min(ys), max(xs), max(ys)


def plan_grid(
    geometry_utm: dict[str, Any],
    max_grid_dimension: int,
    max_analysis_resolution_m: int,
) -> GridPlan:
    min_x, min_y, max_x, max_y = geometry_bounds(geometry_utm)
    width_m = max_x - min_x
    height_m = max_y - min_y
    min_resolution = max(
        width_m / max_grid_dimension,
        height_m / max_grid_dimension,
        SOURCE_RESOLUTION_M,
    )
    analysis_resolution_m = int(math.ceil(min_resolution))

    while (
        math.ceil(width_m / analysis_resolution_m) > max_grid_dimension
        or math.ceil(height_m / analysis_resolution_m) > max_grid_dimension
    ):
        analysis_resolution_m += 1

    if analysis_resolution_m > max_analysis_resolution_m:
        raise RuntimeError(
            "Adaptive CLMS sampling would require "
            f"{analysis_resolution_m} m resolution, above the configured "
            f"{max_analysis_resolution_m} m limit. Tile the AOI before running."
        )

    return GridPlan(
        analysis_resolution_m=analysis_resolution_m,
        grid_width=math.ceil(width_m / analysis_resolution_m),
        grid_height=math.ceil(height_m / analysis_resolution_m),
        width_m=round(width_m, 3),
        height_m=round(height_m, 3),
        max_grid_dimension=max_grid_dimension,
        max_analysis_resolution_m=max_analysis_resolution_m,
    )


def grid_plan_payload(grid_plan: GridPlan) -> dict[str, Any]:
    return {
        "source_resolution_m": SOURCE_RESOLUTION_M,
        "analysis_resolution_m": grid_plan.analysis_resolution_m,
        "grid_width": grid_plan.grid_width,
        "grid_height": grid_plan.grid_height,
        "width_m": grid_plan.width_m,
        "height_m": grid_plan.height_m,
        "max_grid_dimension": grid_plan.max_grid_dimension,
        "max_analysis_resolution_m": grid_plan.max_analysis_resolution_m,
        "resolution_strategy": grid_plan.resolution_strategy,
    }


def build_stats_payload(geometry_utm: dict[str, Any], analysis_resolution_m: int) -> dict[str, Any]:
    return {
        "input": {
            "bounds": {
                "geometry": geometry_utm,
                "properties": {"crs": f"http://www.opengis.net/def/crs/EPSG/0/{TARGET_EPSG}"},
            },
            "data": [
                {
                    "type": f"byoc-{COLLECTION_ID}",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{REFERENCE_YEAR}-01-01T00:00:00Z",
                            "to": f"{REFERENCE_YEAR + 1}-01-01T00:00:00Z",
                        }
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {
                "from": f"{REFERENCE_YEAR}-01-01T00:00:00Z",
                "to": f"{REFERENCE_YEAR + 1}-01-01T00:00:00Z",
            },
            "aggregationInterval": {"of": "P1Y"},
            "resx": analysis_resolution_m,
            "resy": analysis_resolution_m,
            "evalscript": EVALSCRIPT,
        },
        "calculations": {
            "classes": {
                "histograms": {
                    "default": {
                        "nBins": 256,
                        "lowEdge": 0,
                        "highEdge": 256,
                    }
                }
            }
        },
    }


def write_request_preview(
    nodes: list[Node],
    output_dir: Path,
    max_grid_dimension: int,
    max_analysis_resolution_m: int,
) -> Path:
    requests: list[dict[str, Any]] = []
    for node in nodes:
        geometry = load_feature_geometry(node.geojson_path)
        geometry_utm = geometry_to_target_crs(geometry, TARGET_EPSG)
        grid_plan = plan_grid(geometry_utm, max_grid_dimension, max_analysis_resolution_m)
        requests.append(
            {
                "node_id": node.node_id,
                "node_name": node.name,
                "aoi_or_buffer_source": str(node.geojson_path.relative_to(PROJECT_ROOT)),
                "sampling_plan": grid_plan_payload(grid_plan),
                "statistics_payload": build_stats_payload(
                    geometry_utm,
                    grid_plan.analysis_resolution_m,
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "clms_exposure_request_preview.json"
    preview = {
        "mode": "dry_run_no_network",
        "source_dataset": SOURCE_DATASET,
        "collection_id": COLLECTION_ID,
        "reference_year": REFERENCE_YEAR,
        "source_resolution_m": SOURCE_RESOLUTION_M,
        "max_grid_dimension": max_grid_dimension,
        "max_analysis_resolution_m": max_analysis_resolution_m,
        "resolution_strategy": RESOLUTION_STRATEGY,
        "target_epsg": TARGET_EPSG,
        "note": "Request preview only; no land-cover metrics were produced.",
        "requests": requests,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(preview, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return output_path


def post_statistics(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        STATISTICS_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Statistics API request failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Statistics API request failed: {exc.reason}") from exc


def find_histogram_bins(payload: Any) -> list[dict[str, Any]] | None:
    if isinstance(payload, dict):
        if "bins" in payload and isinstance(payload["bins"], list):
            bins = payload["bins"]
            if all(isinstance(item, dict) and "count" in item for item in bins):
                return bins
        for value in payload.values():
            found = find_histogram_bins(value)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = find_histogram_bins(item)
            if found is not None:
                return found
    return None


def bin_class_value(bin_item: dict[str, Any]) -> int | None:
    for key in ("lowEdge", "x", "value"):
        if key in bin_item:
            try:
                return int(round(float(bin_item[key])))
            except (TypeError, ValueError):
                return None
    return None


def summarize_histogram(
    node: Node,
    aoi_source: Path,
    response: dict[str, Any],
    grid_plan: GridPlan,
) -> dict[str, Any]:
    bins = find_histogram_bins(response)
    if bins is None:
        raise ValueError(f"No histogram bins found for {node.node_id}")

    histogram: dict[int, int] = {}
    for item in bins:
        class_value = bin_class_value(item)
        if class_value is None:
            continue
        count = int(round(float(item.get("count", 0))))
        if count > 0:
            histogram[class_value] = histogram.get(class_value, 0) + count

    total_pixels = sum(histogram.values())
    no_data_pixels = histogram.get(255, 0)
    valid_pixels = total_pixels - no_data_pixels

    def pct_for(classes: set[int]) -> float | None:
        if valid_pixels <= 0:
            return None
        group_pixels = sum(count for class_value, count in histogram.items() if class_value in classes)
        return round((group_pixels / valid_pixels) * 100, 2)

    class_percentages = {
        str(class_value): round((count / valid_pixels) * 100, 2)
        for class_value, count in sorted(histogram.items())
        if class_value != 255 and valid_pixels > 0
    }

    return {
        "node_id": node.node_id,
        "node_name": node.name,
        "source_dataset": SOURCE_DATASET,
        "reference_year": REFERENCE_YEAR,
        "source_resolution_m": SOURCE_RESOLUTION_M,
        "analysis_resolution_m": grid_plan.analysis_resolution_m,
        "grid_width": grid_plan.grid_width,
        "grid_height": grid_plan.grid_height,
        "max_grid_dimension": grid_plan.max_grid_dimension,
        "max_analysis_resolution_m": grid_plan.max_analysis_resolution_m,
        "resolution_strategy": grid_plan.resolution_strategy,
        "aoi_or_buffer_source": str(aoi_source.relative_to(PROJECT_ROOT)),
        "histogram_count_unit": "analysis_grid_samples",
        "total_samples": total_pixels,
        "valid_samples": valid_pixels,
        "total_area_ha": round(valid_pixels * (grid_plan.analysis_resolution_m**2) / 10000, 2),
        "class_histogram": {str(key): value for key, value in sorted(histogram.items())},
        "class_percentages": class_percentages,
        "cropland_agriculture_pct": pct_for(GROUPS["cropland_agriculture"]),
        "tree_vegetation_pct": pct_for(GROUPS["tree_vegetation"]),
        "water_wetland_pct": pct_for(GROUPS["water_wetland"]),
        "built_bare_other_pct": pct_for(GROUPS["built_bare_other"]),
        "class_labels": {str(key): value for key, value in CLASS_LABELS.items()},
        "exposure_status": "exposure_available",
        "claim_limit": CLAIM_LIMIT,
    }


def write_metric_outputs(rows: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "clms_exposure_preview.csv"
    json_path = output_dir / "clms_exposure_preview.json"

    fieldnames = [
        "node_id",
        "node_name",
        "source_dataset",
        "reference_year",
        "source_resolution_m",
        "analysis_resolution_m",
        "grid_width",
        "grid_height",
        "max_grid_dimension",
        "max_analysis_resolution_m",
        "resolution_strategy",
        "aoi_or_buffer_source",
        "histogram_count_unit",
        "total_samples",
        "valid_samples",
        "total_area_ha",
        "class_histogram",
        "class_percentages",
        "cropland_agriculture_pct",
        "tree_vegetation_pct",
        "water_wetland_pct",
        "built_bare_other_pct",
        "class_labels",
        "exposure_status",
        "claim_limit",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            for key in ("class_histogram", "class_percentages", "class_labels"):
                csv_row[key] = json.dumps(csv_row[key], ensure_ascii=False, sort_keys=True)
            writer.writerow(csv_row)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "source_dataset": SOURCE_DATASET,
                "collection_id": COLLECTION_ID,
                "reference_year": REFERENCE_YEAR,
                "source_resolution_m": SOURCE_RESOLUTION_M,
                "resolution_strategy": RESOLUTION_STRATEGY,
                "nodes": rows,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")

    return csv_path, json_path


def run_requests(
    nodes: list[Node],
    output_dir: Path,
    max_grid_dimension: int,
    max_analysis_resolution_m: int,
) -> tuple[Path, Path]:
    if not os.environ.get("CDSE_CLIENT_ID") or not os.environ.get("CDSE_CLIENT_SECRET"):
        raise RuntimeError(
            "CDSE_CLIENT_ID and CDSE_CLIENT_SECRET are required for --run. "
            "Default dry-run mode does not require credentials."
        )

    token = get_cdse_token()
    rows: list[dict[str, Any]] = []
    for node in nodes:
        geometry = load_feature_geometry(node.geojson_path)
        geometry_utm = geometry_to_target_crs(geometry, TARGET_EPSG)
        grid_plan = plan_grid(geometry_utm, max_grid_dimension, max_analysis_resolution_m)
        response = post_statistics(
            token.access_token,
            build_stats_payload(geometry_utm, grid_plan.analysis_resolution_m),
        )
        rows.append(summarize_histogram(node, node.geojson_path, response, grid_plan))

    return write_metric_outputs(rows, output_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prototype CLMS land-cover exposure context for La Villa nodes."
    )
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-grid-dimension", type=int, default=DEFAULT_MAX_GRID_DIMENSION)
    parser.add_argument(
        "--max-analysis-resolution",
        type=int,
        default=DEFAULT_MAX_ANALYSIS_RESOLUTION_M,
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Call the CDSE Statistical API and write real metric outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    nodes = load_nodes(args.nodes)
    if args.run:
        csv_path, json_path = run_requests(
            nodes,
            args.output_dir,
            args.max_grid_dimension,
            args.max_analysis_resolution,
        )
        print(f"Wrote real CLMS exposure metrics: {csv_path}")
        print(f"Wrote real CLMS exposure metrics: {json_path}")
        return 0

    preview_path = write_request_preview(
        nodes,
        args.output_dir,
        args.max_grid_dimension,
        args.max_analysis_resolution,
    )
    print(f"Wrote dry-run CLMS request preview: {preview_path}")
    print("No network call was made and no exposure metrics were produced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
