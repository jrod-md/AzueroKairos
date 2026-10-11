// Evidence assistant: organizes an already audited packet. It never decides.
// A deterministic brief is always available; the server function is optional.

import {
  decisionEvent,
  formatDate,
  formatPercent,
  hydroStatusForDate,
  stateOf,
  statusLabel,
} from "./data.js";

export const ASSISTANT_LENSES = [
  { id: "brief", label: "Resumen" },
  { id: "field", label: "Ficha de campo" },
  { id: "passport", label: "Passport" },
];

function publicArtifactRef(value) {
  const text = typeof value === "string" ? value.trim().replaceAll("\\", "/") : "";
  if (!text) return "";
  if (text.startsWith("/data/") || text.startsWith("/trust/")) return text;
  return "";
}

function unique(items) {
  return Array.from(new Set(items.filter(Boolean)));
}

export function buildEvidencePacket({ data, ledgerRows, lens, record }) {
  const decision = decisionEvent(ledgerRows);
  const artifactRefs = unique([
    publicArtifactRef(record?.public_artifact_ref),
    publicArtifactRef(record?.public_ledger_ref),
    "/data/observations.json",
    "/data/evidence_ledger.json",
    ...ledgerRows.map((row) => publicArtifactRef(row.artifact_ref)),
  ]);

  return {
    assistant_lens: lens,
    selected_date: record?.date || "sin fecha",
    aoi: record?.aoi || "sin AOI",
    decision_label: stateOf(record?.confidence_class).label,
    sentinel2: {
      api_status: record?.api_status || "pendiente",
      confidence_class: record?.confidence_class || "do_not_infer",
      reason: record?.reason_es || "Motivo no disponible.",
      recommended_action:
        record?.recommended_action_es || "Mantener la salida dentro de los límites de evidencia.",
      valid_percent: Number(record?.validPercent),
    },
    ledger: {
      hash_short: decision?.hash_short || String(decision?.event_hash || "sin hash").slice(0, 12),
      status: decision?.evidence_status || decision?.status || "sin registro",
    },
    ledger_events: ledgerRows.slice(0, 8).map((row) => ({
      artifact_ref: publicArtifactRef(row.artifact_ref) || "metadata pública sin ruta interna",
      event_label: row.event_label || "Evento auditado",
      event_type: row.event_type || "audit_event",
      hash_short: row.hash_short || String(row.event_hash || "").slice(0, 12),
      status: row.status || "sin estado",
      timestamp: row.generated_at_utc || "sin timestamp",
    })),
    auxiliary_context: {
      exposure_status: data.exposure?.data_status || "pendiente",
      hydroclimate_status: hydroStatusForDate(data, record?.date),
      sar_status: data.sar?.data_status || "pendiente",
    },
    boundaries: [
      "Usar solo evidencia provista por el paquete auditado.",
      "No cambiar la clasificación Sentinel-2.",
      "Separar observación, verificación territorial y autoridad competente.",
    ],
    artifact_refs: artifactRefs.length ? artifactRefs : ["sin artefacto público"],
  };
}

export function buildDeterministicBrief(packet) {
  const lensActions = {
    brief: "Preparar un resumen público con decisión, evidencia usada, brechas y límites visibles.",
    field: "Preparar una ficha de campo con observaciones visibles y cierre sin inferencia adicional.",
    passport: "Adjuntar la trazabilidad al Passport manteniendo límites explícitos del paquete.",
  };

  return {
    artifact_refs: packet.artifact_refs.slice(0, 6),
    decision_summary: `${packet.decision_label}: ${packet.sentinel2.reason}`,
    evidence_gaps: [
      "Sin verificación territorial registrada en esta interfaz.",
      "Las capas auxiliares orientan contexto, no sustituyen la decisión Sentinel-2.",
      "El paquete no contiene resultado externo de autoridad competente.",
    ],
    evidence_used: [
      `Fecha ${formatDate(packet.selected_date, { year: true })}, ${statusLabel(packet.aoi)}.`,
      `Sentinel-2: ${packet.decision_label}, ${formatPercent(packet.sentinel2.valid_percent)} válido.`,
      `Ledger: ${statusLabel(packet.ledger.status)}, hash #${packet.ledger.hash_short}.`,
      `Lluvia antecedente: ${statusLabel(packet.auxiliary_context.hydroclimate_status).toLowerCase()}.`,
    ],
    limits: [
      "Resumen determinístico basado solo en el paquete visible.",
      "No cambia la decisión primaria ni agrega fuentes nuevas.",
      "No reemplaza revisión territorial, laboratorio o autoridad competente.",
    ],
    recommended_action: lensActions[packet.assistant_lens] || packet.sentinel2.recommended_action,
  };
}

export async function requestEvidenceBrief(packet) {
  // The Pages Function does not exist under the Vite dev server.
  if (import.meta.env.DEV && typeof window !== "undefined" && window.location.port) {
    return { mode: "fallback", reason: "endpoint_unavailable" };
  }

  try {
    const response = await fetch("/api/evidence-brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ evidence_packet: packet }),
    });

    if (!response.ok) {
      return {
        mode: "fallback",
        reason: response.status === 404 ? "endpoint_unavailable" : `http_${response.status}`,
      };
    }

    const payload = await response.json();
    if (payload?.mode !== "ai") {
      return { mode: "fallback", reason: payload?.reason || "provider_unavailable" };
    }

    const brief = checkBrief(payload);
    if (!brief) return { mode: "fallback", reason: "claim_guard" };

    return { brief, mode: "ai", model: safeText(payload.model, 120) };
  } catch {
    return { mode: "fallback", reason: "request_failed" };
  }
}

function checkBrief(payload) {
  if (!payload || typeof payload !== "object") return null;
  if (containsUnsafeClaim(payload)) return null;

  const brief = {
    artifact_refs: cleanList(payload.artifact_refs),
    decision_summary: safeText(payload.decision_summary, 700),
    evidence_gaps: cleanList(payload.evidence_gaps),
    evidence_used: cleanList(payload.evidence_used),
    limits: cleanList(payload.limits),
    recommended_action: safeText(payload.recommended_action, 700),
  };

  const complete =
    brief.artifact_refs.length &&
    brief.decision_summary &&
    brief.evidence_gaps.length &&
    brief.evidence_used.length &&
    brief.limits.length &&
    brief.recommended_action;

  return complete ? brief : null;
}

function cleanList(value) {
  if (!Array.isArray(value)) return [];
  return unique(value.map((entry) => safeText(entry, 420))).slice(0, 8);
}

function safeText(value, maxLength = 700) {
  if (typeof value !== "string") return "";
  return value.trim().replace(/\s+/g, " ").slice(0, maxLength);
}

function containsUnsafeClaim(value) {
  const text = String(JSON.stringify(value) || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
  const checks = [
    ["contamin"],
    ["quimic"],
    ["sanitari"],
    ["potab"],
    ["agua", "segur"],
    ["safe", "water"],
    ["pest" + "ic"],
    ["metal", "pesad"],
    ["patog" + "en"],
    ["cri" + "sis"],
    ["detect"],
    ["decid"],
    ["confir" + "ma"],
  ];
  return checks.some((parts) => parts.every((part) => text.includes(part)));
}

export function assistantStatusLabel(state) {
  if (state.status === "loading") return "Preparando";
  if (state.mode === "ai") return "Redacción asistida";
  if (state.reason === "missing_key" || state.reason === "endpoint_unavailable") {
    return "Modelo no configurado: resumen determinístico";
  }
  return "Resumen determinístico";
}
