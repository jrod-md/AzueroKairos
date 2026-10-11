// Public data access and shared vocabulary for the Kairós interface.
// The browser only reads committed exports under /data and /trust/v1.

export const THRESHOLDS = { review: 10, usable: 30 };

export const NODE_ORDER = ["la_villa_oeste", "la_villa_central", "la_villa_este"];

export const NODES = {
  la_villa_oeste: { name: "La Villa Oeste", short: "Oeste", letter: "O" },
  la_villa_central: { name: "La Villa Central", short: "Centro", letter: "C" },
  la_villa_este: { name: "La Villa Este", short: "Este", letter: "E" },
};

export const STATES = {
  usable: {
    id: "usable",
    label: "USABLE",
    tone: "usable",
    inference: "Permitida con límites",
    rule: "30% o más de cobertura válida",
    reason:
      "La observación tiene suficiente evidencia válida para una lectura exploratoria con límites explícitos.",
    action: "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
  },
  low_confidence: {
    id: "low_confidence",
    label: "REVISAR",
    tone: "review",
    inference: "Requiere revisión",
    rule: "Entre 10% y 30% de cobertura válida",
    reason:
      "La observación tiene evidencia limitada y requiere revisión o verificación territorial.",
    action: "Revisar con cautela y considerar verificación territorial.",
  },
  do_not_infer: {
    id: "do_not_infer",
    label: "NO INFERIR",
    tone: "stop",
    inference: "Bloqueada",
    rule: "Menos de 10% de cobertura válida",
    reason:
      "La observación no tiene suficiente evidencia válida para una inferencia responsable.",
    action:
      "No usar esta observación para afirmar condiciones del territorio; esperar una nueva adquisición o solicitar verificación territorial.",
  },
};

export function stateOf(confidenceClass) {
  return STATES[confidenceClass] ?? STATES.do_not_infer;
}

const STATUS_LABELS = {
  sar_context_available: "Disponible",
  sar_no_acquisition: "Sin adquisición",
  sar_low_observation: "Observación baja",
  node_context_available: "Disponible",
  exposure_available: "Disponible",
  normal_context: "Contexto normal",
  antecedent_rain: "Lluvia antecedente",
  antecedent_rain_review: "Lluvia antecedente",
  official_api_ok: "Oficial, API OK",
  regional_ledger_available: "Ledger regional disponible",
  api_ok_raw_observation_recorded: "Observación registrada",
  metrics_csv_recorded: "Métricas registradas",
  decision_usable: "Decisión: USABLE",
  decision_low_confidence: "Decisión: REVISAR",
  decision_do_not_infer: "Decisión: NO INFERIR",
  brief_available: "Brief disponible",
  public_json_available: "JSON público disponible",
  case_registry_available: "Caso registrado",
  corridor_wide: "corredor completo",
  public: "Público",
  pass: "Aprobada",
  passed: "Aprobado",
};

export function statusLabel(value) {
  if (!value) return "Sin dato";
  return STATUS_LABELS[value] ?? String(value).replaceAll("_", " ");
}

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

export function formatDate(iso, { year = false } = {}) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ""));
  if (!match) return "sin fecha";
  const label = `${Number(match[3])} ${MONTHS[Number(match[2]) - 1]}`;
  return year ? `${label} ${match[1]}` : label;
}

export function formatPercent(value, digits = 2) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "sin dato";
  return `${numeric.toFixed(digits)}%`;
}

export function formatCount(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "sin dato";
  return new Intl.NumberFormat("en-US").format(numeric);
}

export function formatNumber(value, digits = 2) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "sin dato";
  return numeric.toFixed(digits);
}

export function daysBetween(fromIso, toIso) {
  const from = Date.parse(`${fromIso}T00:00:00Z`);
  const to = Date.parse(`${toIso}T00:00:00Z`);
  if (!Number.isFinite(from) || !Number.isFinite(to)) return null;
  return Math.round((to - from) / 86400000);
}

// Several public exports were written without diacritics. The values stay
// untouched on disk; this only restores spelling for display.
const ACCENT_WORDS = {
  observacion: "observación",
  verificacion: "verificación",
  adquisicion: "adquisición",
  interpretacion: "interpretación",
  afirmacion: "afirmación",
  clasificacion: "clasificación",
  demostracion: "demostración",
  comparacion: "comparación",
  conclusion: "conclusión",
  condicion: "condición",
  decision: "decisión",
  revision: "revisión",
  fraccion: "fracción",
  patron: "patrón",
  valida: "válida",
  valido: "válido",
  quimicas: "químicas",
  quimica: "química",
  hidroclimatico: "hidroclimático",
  hidroclimatica: "hidroclimática",
  practicamente: "prácticamente",
  tecnica: "técnica",
  publico: "público",
  publica: "pública",
  limites: "límites",
  explicitos: "explícitos",
  senal: "señal",
  mas: "más",
  util: "útil",
  utiles: "útiles",
  dia: "día",
  operativas: "operativas",
};

export function accent(text) {
  if (typeof text !== "string" || !text) return "";
  return text
    .replace(/\besta disponible\b/g, "está disponible")
    .replace(/[A-Za-z]+/g, (word) => {
      const fixed = ACCENT_WORDS[word.toLowerCase()];
      if (!fixed) return word;
      return word[0] === word[0].toUpperCase() ? fixed[0].toUpperCase() + fixed.slice(1) : fixed;
    });
}

export function splitList(value) {
  return String(value ?? "")
    .split("|")
    .map((part) => accent(part.trim()))
    .filter(Boolean);
}

async function fetchJson(path) {
  try {
    const response = await fetch(path);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export { fetchJson };

export async function loadPublicData() {
  const [observations, ledger, watch, sar, hydro, cases, exposure, trustIndex, validation] =
    await Promise.all([
      fetchJson("/data/observations.json"),
      fetchJson("/data/evidence_ledger.json"),
      fetchJson("/data/kairos_watch.json"),
      fetchJson("/data/sar_context.json"),
      fetchJson("/data/hydroclimate_context.json"),
      fetchJson("/data/decision_cases.json"),
      fetchJson("/data/exposure_context.json"),
      fetchJson("/trust/v1/index.json"),
      fetchJson("/trust/v1/validation_report.json"),
    ]);

  if (!Array.isArray(observations) || !observations.length) {
    throw new Error("No se pudo cargar /data/observations.json.");
  }

  return {
    observations: [...observations].sort((a, b) => a.date.localeCompare(b.date)),
    ledger: Array.isArray(ledger) ? ledger : [],
    watch: Array.isArray(watch?.observations) ? watch.observations : [],
    sar: sar ?? null,
    sarRows: Array.isArray(sar?.rows) ? sar.rows : [],
    hydro: hydro ?? null,
    hydroRows: Array.isArray(hydro?.rows) ? hydro.rows : [],
    cases: Array.isArray(cases?.cases) ? cases.cases : [],
    claimFirewall: cases?.claim_firewall ?? "",
    exposure: exposure ?? null,
    exposureNodes: Array.isArray(exposure?.nodes) ? exposure.nodes : [],
    trustIndex,
    validation,
  };
}

export function ledgerForDate(ledger, date) {
  return ledger
    .filter((row) => row.date === date)
    .sort((a, b) => Number(a.event_index) - Number(b.event_index));
}

export function decisionEvent(rows) {
  return rows.find((row) => row.event_type === "confidence_decision_computed") ?? rows[0] ?? null;
}

export function nodeObservation(data, nodeId, date) {
  return data.watch.find((row) => row.node_id === nodeId && row.date === date) ?? null;
}

export function sarFor(data, nodeId, date) {
  return data.sarRows.find((row) => row.node_id === nodeId && row.target_date === date) ?? null;
}

export function hydroFor(data, nodeId, date) {
  return data.hydroRows.find((row) => row.node_id === nodeId && row.target_date === date) ?? null;
}

export function exposureFor(data, nodeId) {
  return data.exposureNodes.find((row) => row.node_id === nodeId) ?? null;
}

export function hydroStatusForDate(data, date) {
  const rows = data.hydroRows.filter((row) => row.target_date === date);
  if (!rows.length) return "sin dato";
  const review = rows.filter((row) => row.context_status === "antecedent_rain_review").length;
  return review > rows.length / 2 ? "antecedent_rain_review" : "normal_context";
}

const PRIORITY_RANK = { alta: 0, "media-alta": 1, media: 2, normal: 3 };

export function sortCases(cases) {
  return [...cases].sort((a, b) => {
    const rank = (PRIORITY_RANK[a.priority_level] ?? 9) - (PRIORITY_RANK[b.priority_level] ?? 9);
    if (rank !== 0) return rank;
    return a.date.localeCompare(b.date) || a.node_id.localeCompare(b.node_id);
  });
}

export function priorityLabel(level) {
  if (level === "alta") return "Prioridad alta";
  if (level === "media-alta") return "Prioridad media-alta";
  return "Prioridad normal";
}

// The widest gap between a blocked scene and the best later acquisition.
export function findContrast(observations) {
  const blocked = observations.filter((row) => row.confidence_class === "do_not_infer");
  if (!blocked.length) return null;
  const weak = blocked.reduce((a, b) => (a.validPercent <= b.validPercent ? a : b));
  const later = observations.filter((row) => row.date > weak.date);
  if (!later.length) return null;
  const strong = later.reduce((a, b) => (a.validPercent >= b.validPercent ? a : b));
  return { weak, strong, days: daysBetween(weak.date, strong.date) };
}
