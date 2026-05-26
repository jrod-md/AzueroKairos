const TERRITORIAL_CONTEXT_URL = "/data/territorial_context.json";

export async function loadTerritorialContext(fetcher = fetch) {
  const response = await fetcher(TERRITORIAL_CONTEXT_URL);

  if (!response.ok) {
    throw new Error("No se pudo cargar territorial_context.json");
  }

  const payload = await response.json();
  return normalizeTerritorialContext(payload);
}

export function normalizeTerritorialContext(context) {
  return {
    country: stringOrDefault(context.country, "Panama"),
    region: stringOrDefault(context.region, "Azuero"),
    corridorName: stringOrDefault(context.corridor_name, "Río La Villa"),
    aoiName: stringOrDefault(context.aoi_name, "corridor_wide"),
    note: stringOrDefault(context.note, "Contextual geography only."),
    coordinateOrder: stringOrDefault(context.coordinate_order, "lat_lng"),
    panamaCenter: normalizePoint(context.panama_center),
    azueroCenter: normalizePoint(context.azuero_center),
    corridorCenter: normalizePoint(context.corridor_center),
    extent: normalizeExtent(context.extent),
    corridorPath: normalizePath(context.corridor_path),
    labels: {
      country: stringOrDefault(context.labels?.country, "Panamá"),
      region: stringOrDefault(context.labels?.region, "Azuero"),
      corridor: stringOrDefault(
        context.labels?.corridor,
        "Corredor Río La Villa",
      ),
      aoi: stringOrDefault(context.labels?.aoi, "AOI: corridor_wide"),
      precisionNote: stringOrDefault(
        context.labels?.precision_note,
        "Ubicación contextual, no cartografía de precisión.",
      ),
    },
    metadata: {
      publicSafe: Boolean(context.metadata?.public_safe),
      containsSecrets: Boolean(context.metadata?.contains_secrets),
      intendedUse: stringOrDefault(context.metadata?.intended_use, ""),
      precision: stringOrDefault(context.metadata?.precision, "approximate"),
    },
  };
}

function normalizePoint(point) {
  if (!Array.isArray(point) || point.length !== 2) {
    return null;
  }

  const [lat, lng] = point.map(Number);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }

  return { lat, lng };
}

function normalizePath(points) {
  if (!Array.isArray(points)) {
    return [];
  }

  return points.map(normalizePoint).filter(Boolean);
}

function normalizeExtent(extent) {
  if (!extent || typeof extent !== "object") {
    return null;
  }

  const normalized = {
    south: Number(extent.south),
    west: Number(extent.west),
    north: Number(extent.north),
    east: Number(extent.east),
  };

  return Object.values(normalized).every(Number.isFinite) ? normalized : null;
}

function stringOrDefault(value, fallback) {
  return typeof value === "string" && value.trim() ? value : fallback;
}
