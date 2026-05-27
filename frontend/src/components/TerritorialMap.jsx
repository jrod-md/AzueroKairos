import React, { useEffect, useMemo, useState } from "react";

const AOI_GEOJSON_URL = "/data/aoi_corridor_wide.geojson";
const TERRITORIAL_CONTEXT_URL = "/data/territorial_context.json";
const SVG_WIDTH = 420;
const SVG_HEIGHT = 250;
const SVG_PADDING = 34;

const FALLBACK_CONTEXT = {
  country: "Panamá",
  region: "Azuero",
  corridor_name: "Río La Villa",
  aoi_name: "corridor_wide",
  centroid: [-80.485, 7.96],
  bbox: [-80.61, 7.82, -80.36, 8.1],
};

export default function TerritorialMap({ record, state, variant = "decision" }) {
  const [geoState, setGeoState] = useState({
    status: "loading",
    geojson: null,
    context: FALLBACK_CONTEXT,
  });

  useEffect(() => {
    let active = true;

    async function loadMapData() {
      try {
        const [geojsonResponse, contextResponse] = await Promise.all([
          fetch(AOI_GEOJSON_URL),
          fetch(TERRITORIAL_CONTEXT_URL),
        ]);

        if (!geojsonResponse.ok) {
          throw new Error("No se pudo cargar el AOI público.");
        }

        const geojson = await geojsonResponse.json();
        const context = contextResponse.ok
          ? await contextResponse.json()
          : FALLBACK_CONTEXT;

        if (!active) return;
        setGeoState({
          status: "ready",
          geojson,
          context: { ...FALLBACK_CONTEXT, ...context },
        });
      } catch (error) {
        if (!active) return;
        setGeoState((current) => ({
          ...current,
          status: "error",
        }));
      }
    }

    loadMapData();
    return () => {
      active = false;
    };
  }, []);

  const mapGeometry = useMemo(() => {
    if (!geoState.geojson) return null;
    return buildMapGeometry(geoState.geojson, geoState.context);
  }, [geoState.geojson, geoState.context]);

  const tone = state?.tone ?? "stop";
  const statusLabel = state?.label ?? "NO INFERIR";
  const aoiName = geoState.context.aoi_name || record?.aoi || "corridor_wide";

  return (
    <section
      className={`territorial-map tone-${tone} ${variant}`}
      aria-label="Contexto territorial del AOI oficial"
    >
      <div className="territorial-map-heading">
        <div>
          <p className="small-label">Contexto territorial</p>
          <h3>Azuero, Panamá</h3>
        </div>
        <span>{record?.date}</span>
      </div>

      <div className="territorial-map-body">
        <div className="territorial-map-canvas">
          {geoState.status === "ready" && mapGeometry ? (
            <svg
              viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
              role="img"
              aria-label="Mapa contextual con geometría oficial del AOI corridor_wide"
            >
              <rect className="map-paper" x="1" y="1" width="418" height="248" rx="26" />
              <path className="map-grid-line horizontal" d="M24 86 H396" />
              <path className="map-grid-line horizontal" d="M24 164 H396" />
              <path className="map-grid-line vertical" d="M140 24 V226" />
              <path className="map-grid-line vertical" d="M280 24 V226" />
              {mapGeometry.paths.map((path, index) => (
                <path className="aoi-shape" d={path} key={index} />
              ))}
              <circle
                className="aoi-marker-halo"
                cx={mapGeometry.centroid.x}
                cy={mapGeometry.centroid.y}
                r="18"
              />
              <circle
                className="aoi-marker"
                cx={mapGeometry.centroid.x}
                cy={mapGeometry.centroid.y}
                r="6.5"
              />
              <text className="map-label main" x={mapGeometry.centroid.x + 13} y={mapGeometry.centroid.y - 9}>
                AOI oficial
              </text>
              <text className="map-label corner" x="24" y="224">
                EPSG:4326 · lon/lat
              </text>
            </svg>
          ) : (
            <div className="territorial-map-empty">
              {geoState.status === "loading"
                ? "Cargando AOI oficial"
                : "AOI oficial no disponible"}
            </div>
          )}
        </div>

        <div className="territorial-map-facts">
          <span>{geoState.context.region}, {geoState.context.country}</span>
          <strong>Corredor {geoState.context.corridor_name}</strong>
          <span>AOI: {aoiName}</span>
          <span className={`map-state tone-${tone}`}>{statusLabel}</span>
        </div>
      </div>

      <p className="territorial-map-note">
        Visualización contextual del AOI oficial, no verificación de campo.
      </p>
    </section>
  );
}

function buildMapGeometry(geojson, context) {
  const rings = getOuterRings(geojson);
  if (!rings.length) return null;

  const bbox = normalizeBbox(context.bbox) ?? computeBbox(rings.flat());
  const paddedBbox = padBbox(bbox);
  const project = createProjector(paddedBbox);
  const centroid = normalizePosition(context.centroid) ?? computeBboxCenter(bbox);

  return {
    paths: rings.map((ring) => ringToPath(ring, project)),
    centroid: project(centroid),
  };
}

function getOuterRings(geojson) {
  if (!geojson || typeof geojson !== "object") return [];

  if (geojson.type === "FeatureCollection") {
    return geojson.features.flatMap(getOuterRings);
  }

  if (geojson.type === "Feature") {
    return getOuterRings(geojson.geometry);
  }

  if (geojson.type === "Polygon") {
    const [outerRing] = geojson.coordinates ?? [];
    return outerRing ? [outerRing.map(normalizePosition).filter(Boolean)] : [];
  }

  if (geojson.type === "MultiPolygon") {
    return (geojson.coordinates ?? [])
      .map((polygon) => polygon?.[0]?.map(normalizePosition).filter(Boolean))
      .filter((ring) => ring?.length);
  }

  return [];
}

function ringToPath(ring, project) {
  return ring
    .map((position, index) => {
      const point = project(position);
      return `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
    })
    .join(" ")
    .concat(" Z");
}

function createProjector([west, south, east, north]) {
  const width = Math.max(east - west, 0.000001);
  const height = Math.max(north - south, 0.000001);

  return ([lon, lat]) => ({
    x: SVG_PADDING + ((lon - west) / width) * (SVG_WIDTH - SVG_PADDING * 2),
    y:
      SVG_HEIGHT -
      SVG_PADDING -
      ((lat - south) / height) * (SVG_HEIGHT - SVG_PADDING * 2),
  });
}

function computeBbox(positions) {
  const lons = positions.map(([lon]) => lon);
  const lats = positions.map(([, lat]) => lat);
  return [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)];
}

function computeBboxCenter([west, south, east, north]) {
  return [(west + east) / 2, (south + north) / 2];
}

function padBbox([west, south, east, north]) {
  const lonPad = Math.max((east - west) * 0.22, 0.015);
  const latPad = Math.max((north - south) * 0.22, 0.015);
  return [west - lonPad, south - latPad, east + lonPad, north + latPad];
}

function normalizeBbox(bbox) {
  if (!Array.isArray(bbox) || bbox.length !== 4) return null;
  const normalized = bbox.map(Number);
  return normalized.every(Number.isFinite) ? normalized : null;
}

function normalizePosition(position) {
  if (!Array.isArray(position) || position.length < 2) return null;
  const lon = Number(position[0]);
  const lat = Number(position[1]);
  return Number.isFinite(lon) && Number.isFinite(lat) ? [lon, lat] : null;
}
