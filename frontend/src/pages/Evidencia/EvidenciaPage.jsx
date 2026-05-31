import React, { useEffect, useMemo, useState } from "react";
import "./EvidenciaPage.css";

const STATE_LABELS = {
  usable: "USABLE",
  low_confidence: "REVISAR",
  do_not_infer: "NO INFERIR",
};

const ASSISTANT_DISCLAIMER =
  "La IA no decide ni crea evidencia; organiza un paquete de evidencia ya auditado.";

const ASSISTANT_LENSES = [
  { id: "brief", label: "Brief" },
  { id: "field", label: "Campo" },
  { id: "passport", label: "Passport" },
];

export default function EvidenciaPage({
  availableDates = [],
  exposureContext,
  hydroClimateContext,
  record,
  ledger,
  ledgerRows = [],
  sarLoadState,
  selectedDate,
  setSelectedDate,
}) {
  const [assistantLens, setAssistantLens] = useState("brief");
  const [assistantState, setAssistantState] = useState({
    brief: null,
    mode: "fallback",
    reason: "not_requested",
    status: "idle",
  });
  const stateLabel = getStateLabel(record);
  const ledgerEntries = useMemo(
    () => buildLedgerEntries(ledgerRows.length ? ledgerRows : ledger ? [ledger] : []),
    [ledger, ledgerRows],
  );
  const knowledgeModel = useMemo(
    () => buildKnowledgeModel(record, ledger, stateLabel),
    [ledger, record, stateLabel],
  );
  const evidencePacket = useMemo(
    () =>
      buildEvidencePacket({
        assistantLens,
        exposureContext,
        hydroClimateContext,
        ledger,
        ledgerEntries,
        record,
        sarLoadState,
        stateLabel,
      }),
    [
      assistantLens,
      exposureContext,
      hydroClimateContext,
      ledger,
      ledgerEntries,
      record,
      sarLoadState,
      stateLabel,
    ],
  );
  const deterministicBrief = useMemo(
    () => buildDeterministicEvidenceBrief(evidencePacket, assistantLens),
    [assistantLens, evidencePacket],
  );
  const assistantBrief = assistantState.brief || deterministicBrief;
  const assistantStatusLabel = getAssistantStatusChipLabel(assistantState);

  useEffect(() => {
    setAssistantState({
      brief: null,
      mode: "fallback",
      reason: "date_changed",
      status: "idle",
    });
  }, [assistantLens, selectedDate]);

  async function prepareAssistantBrief() {
    setAssistantState({
      brief: deterministicBrief,
      mode: "fallback",
      reason: "preparing",
      status: "loading",
    });

    const result = await requestEvidenceBrief(evidencePacket);

    if (result.mode === "ai" && result.brief) {
      setAssistantState({
        brief: result.brief,
        mode: "ai",
        model: result.model,
        reason: "",
        status: "ready",
      });
      return;
    }

    setAssistantState({
      brief: deterministicBrief,
      mode: "fallback",
      reason: result.reason || "fallback",
      status: "ready",
    });
  }

  return (
    <section className="evidencia-page" aria-label="Evidencia">
      <div className="evidencia-page__heading">
        <div>
          <p className="section-label">EVIDENCIA</p>
          <h1 className="display-heading">Archivo de auditoría territorial</h1>
        </div>
        <label className="evidencia-page__date">
          <span className="section-label">FECHA</span>
          <select
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
          >
            {availableDates.map((date) => (
              <option key={date} value={date}>
                {date}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="evidencia-page__status-strip" aria-label="Lecturas principales">
        <DataReadout label="DECISIÓN" value={stateLabel} />
        <DataReadout label="VALID PIXELS" value={formatPercent(record?.validPercent)} />
        <DataReadout label="API CDSE" value={record?.api_status || "pendiente"} />
        <DataReadout label="LEDGER" value={ledger?.evidence_status || "sin registro"} />
      </div>

      <EvidenceAssistantPanel
        assistantBrief={assistantBrief}
        assistantLens={assistantLens}
        assistantState={assistantState}
        assistantStatusLabel={assistantStatusLabel}
        evidencePacket={evidencePacket}
        onPrepare={prepareAssistantBrief}
        setAssistantLens={setAssistantLens}
      />

      <section className="evidencia-page__knowledge" aria-label="Informe de campo">
        {knowledgeModel.map((section) => (
          <article
            className={`evidencia-card${section.tone ? ` evidencia-card--${section.tone}` : ""}`}
            key={section.title}
          >
            <p className="section-label">{section.label}</p>
            <h2>{section.title}</h2>
            <ul>
              {section.items.map((item) => (
                <li key={item.key}>{item.content}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <section className="evidencia-ledger" aria-label="Ledger de auditoría">
        <div className="evidencia-ledger__heading">
          <p className="section-label">LEDGER</p>
          <h2>Registro auditable</h2>
        </div>
        <div className="evidencia-ledger__rows">
          {ledgerEntries.length ? (
            ledgerEntries.map((entry) => (
              <div className="evidencia-ledger__row" key={entry.key}>
                <span>[{entry.timestamp}]</span>
                <span>[{entry.eventType}]</span>
                <span>{entry.eventLabel}</span>
                <span>{entry.artifactRef}</span>
                <span>[{entry.status}]</span>
                <span>#{entry.hashShort}</span>
              </div>
            ))
          ) : (
            <div className="evidencia-ledger__row">
              <span>[sin timestamp]</span>
              <span>[sin ledger]</span>
              <span>sin evento</span>
              <span>sin artefacto</span>
              <span>[sin estado]</span>
              <span>#sin-hash</span>
            </div>
          )}
        </div>
      </section>
    </section>
  );
}

function DataReadout({ label, value }) {
  return (
    <div className="evidencia-readout">
      <span className="section-label">{label}</span>
      <strong className="data-value">{value}</strong>
    </div>
  );
}

function EvidenceAssistantPanel({
  assistantBrief,
  assistantLens,
  assistantState,
  assistantStatusLabel,
  evidencePacket,
  onPrepare,
  setAssistantLens,
}) {
  return (
    <section className="evidence-assistant" aria-label="Asistente de Evidencia Kairos">
      <div className="evidence-assistant__header">
        <div>
          <p className="section-label">ASISTENTE DE EVIDENCIA KAIROS</p>
          <h2>Organizar el paquete, no ampliar el alcance.</h2>
        </div>
        <div className="evidence-assistant__controls">
          <span className={`assistant-status assistant-status--${assistantState.mode}`}>
            {assistantStatusLabel}
          </span>
          <button
            disabled={assistantState.status === "loading"}
            onClick={onPrepare}
            type="button"
          >
            {assistantState.status === "loading"
              ? "Preparando..."
              : "Preparar brief asistido"}
          </button>
        </div>
      </div>

      <p className="evidence-assistant__disclaimer">{ASSISTANT_DISCLAIMER}</p>

      <div className="evidence-assistant__lens" aria-label="Lente del asistente">
        {ASSISTANT_LENSES.map((lens) => (
          <button
            className={assistantLens === lens.id ? "is-active" : ""}
            key={lens.id}
            onClick={() => setAssistantLens(lens.id)}
            type="button"
          >
            {lens.label}
          </button>
        ))}
      </div>

      <div className="evidence-assistant__grid">
        <article className="assistant-packet-card">
          <p className="section-label">PAQUETE AUDITADO</p>
          <dl>
            <AssistantDataPair label="Fecha" value={evidencePacket.selected_date} />
            <AssistantDataPair label="Decisión" value={evidencePacket.decision_label} />
            <AssistantDataPair
              label="ValidPercent"
              value={formatPercent(evidencePacket.sentinel2.valid_percent)}
            />
            <AssistantDataPair label="Ledger" value={evidencePacket.ledger.status} />
            <AssistantDataPair
              label="HydroClimate"
              value={evidencePacket.auxiliary_context.hydroclimate_status}
            />
            <AssistantDataPair
              label="Eventos"
              value={`${evidencePacket.ledger_events.length} referencias`}
            />
          </dl>
        </article>

        <article className="assistant-brief-card">
          <div className="assistant-brief-card__top">
            <div>
              <p className="section-label">RESUMEN</p>
              <h3>{assistantBrief.decision_summary}</h3>
            </div>
            <span>{assistantState.model || "fallback local"}</span>
          </div>
          <p>{assistantBrief.recommended_action}</p>
        </article>
      </div>

      <div className="assistant-output-grid" aria-label="Salida del asistente">
        <AssistantList title="Evidencia usada" items={assistantBrief.evidence_used} />
        <AssistantList title="Brechas" items={assistantBrief.evidence_gaps} />
        <AssistantList title="Límites" items={assistantBrief.limits} />
        <AssistantList title="Artefactos" items={assistantBrief.artifact_refs} mono />
      </div>
    </section>
  );
}

function AssistantDataPair({ label, value }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value || "pendiente"}</dd>
    </div>
  );
}

function AssistantList({ items, mono = false, title }) {
  return (
    <article className="assistant-list">
      <p className="section-label">{title}</p>
      <ul className={mono ? "assistant-list__mono" : ""}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}

function buildKnowledgeModel(record, ledger, stateLabel) {
  const reason = record?.reason_es || record?.reason || "Motivo no disponible en el JSON público.";
  const action =
    record?.recommended_action_es ||
    record?.recommended_action ||
    "Mantener la decisión dentro de los límites de evidencia disponibles.";
  const publicRefs = buildPublicEvidenceRefs(record, ledger);
  const noInferContent =
    stateLabel === "NO INFERIR"
      ? (
          <>
            {reason} La fracción válida Sentinel-2 es{" "}
            <span className="data-value">{formatPercent(record?.validPercent)}</span>.
          </>
        )
      : (
          <>
            La regla NO INFERIR no se activa en esta fecha. Decisión actual:{" "}
            <span className="data-value">{stateLabel}</span>.
          </>
        );

  return [
    {
      label: "QUÉ SABEMOS",
      title: "Evidencia disponible",
      items: compactItems([
        item("date-aoi", (
          <>
            Fecha <span className="data-value">{record?.date || "sin fecha"}</span>; AOI{" "}
            <span className="data-value">{record?.aoi || "sin AOI"}</span>.
          </>
        )),
        item("valid-percent", (
          <>
            Sentinel-2 reporta{" "}
            <span className="data-value">{formatPercent(record?.validPercent)}</span> de
            evidencia válida.
          </>
        )),
        item("api-ledger", (
          <>
            API <span className="data-value">{record?.api_status || "pendiente"}</span>;
            ledger{" "}
            <span className="data-value">{ledger?.evidence_status || "sin registro"}</span>.
          </>
        )),
        item("brief", (
          <>
            Artefacto público:{" "}
            <span className="data-value">
              {publicRefs[0] || "referencia pública no disponible"}
            </span>.
          </>
        )),
      ]),
    },
    {
      label: "QUÉ NO SABEMOS",
      title: "Brechas de evidencia",
      tone: "unknown",
      items: compactItems([
        item("field-verification", "No hay verificación territorial registrada en esta interfaz."),
        item("lab-authority", "No hay resultado químico, sanitario o de autoridad competente."),
        item("auxiliary-layers", "Las capas auxiliares no cambian la decisión Sentinel-2."),
      ]),
    },
    {
      label: "POR QUÉ NO INFERIR",
      title: "Frontera de inferencia",
      items: compactItems([
        item("no-infer-rule", noInferContent),
        item(
          "scope-limit",
          "La plataforma conserva la decisión dentro de confianza de observación, sin extenderla a causalidad territorial.",
        ),
      ]),
    },
    {
      label: "QUÉ ACCIÓN SIGUE",
      title: "Próximo paso responsable",
      items: compactItems([
        item("action", action),
        item("public-refs", (
          <>
            Referencias verificables:{" "}
            <span className="data-value">
              {publicRefs.join(" | ") || "solo metadata pública"}
            </span>.
          </>
        )),
      ]),
    },
  ];
}

function buildLedgerEntries(rows) {
  return [...rows]
    .sort(compareLedgerRows)
    .map((row, index) => {
      const hashShort =
        row.hash_short ||
        String(row.event_hash || row.artifact_hash || row.git_commit || `entry-${index + 1}`).slice(0, 12);

      return {
        key: `${row.generated_at_utc || "sin-timestamp"}-${hashShort}-${index}`,
        timestamp: row.generated_at_utc || "sin timestamp",
        eventType: row.event_type || row.evidence_status || row.api_status || "audit_event",
        eventLabel: row.event_label || row.event_label_es || "Evento auditado",
        artifactRef:
          publicArtifactRef(row.artifact_ref) ||
          publicArtifactRef(row.public_artifact_ref) ||
          publicArtifactRef(row.public_ledger_ref) ||
          "metadata pública sin ruta interna",
        status: row.status || row.evidence_status || row.api_status || "sin estado",
        hashShort,
      };
    });
}

function buildEvidencePacket({
  assistantLens,
  exposureContext,
  hydroClimateContext,
  ledger,
  ledgerEntries,
  record,
  sarLoadState,
  stateLabel,
}) {
  const artifactRefs = buildPublicEvidenceRefs(record, ledger, ledgerEntries);

  return {
    assistant_lens: assistantLens,
    selected_date: record?.date || "sin fecha",
    aoi: record?.aoi || "sin AOI",
    decision_label: stateLabel,
    sentinel2: {
      api_status: record?.api_status || "pendiente",
      confidence_class: record?.confidence_class || "do_not_infer",
      reason: record?.reason_es || record?.reason || "Motivo no disponible.",
      recommended_action:
        record?.recommended_action_es ||
        record?.recommended_action ||
        "Mantener la salida dentro de los límites de evidencia.",
      valid_percent: Number(record?.validPercent),
    },
    ledger: {
      hash_short:
        ledger?.hash_short ||
        String(ledger?.event_hash || ledger?.artifact_hash || "sin hash").slice(0, 12),
      status: ledger?.evidence_status || ledger?.status || "sin registro",
    },
    ledger_events: ledgerEntries.slice(0, 8).map((entry) => ({
      artifact_ref: entry.artifactRef,
      event_label: entry.eventLabel,
      event_type: entry.eventType,
      hash_short: entry.hashShort,
      status: entry.status,
      timestamp: entry.timestamp,
    })),
    auxiliary_context: {
      exposure_status: exposureContext?.data_status || "pendiente",
      hydroclimate_status:
        hydroClimateContext?.hydroclimate_status ||
        hydroClimateContext?.status ||
        "sin dato",
      sar_status: sarLoadState?.status || "pendiente",
    },
    boundaries: [
      "Usar solo evidencia provista por el paquete auditado.",
      "No cambiar la clasificación Sentinel-2.",
      "Separar observación, verificación territorial y autoridad competente.",
    ],
    artifact_refs: artifactRefs.length ? artifactRefs : ["sin artefacto público"],
  };
}

function buildPublicEvidenceRefs(record, ledger, ledgerEntries = []) {
  return uniqueAssistantItems([
    publicArtifactRef(record?.public_artifact_ref),
    publicArtifactRef(record?.public_ledger_ref),
    publicArtifactRef(ledger?.artifact_ref),
    publicArtifactRef(ledger?.public_artifact_ref),
    publicArtifactRef(ledger?.public_ledger_ref),
    "/data/observations.json",
    "/data/evidence_ledger.json",
    ...ledgerEntries.map((entry) => publicArtifactRef(entry.artifactRef)),
  ]);
}

function publicArtifactRef(value) {
  const text = typeof value === "string" ? value.trim().replaceAll("\\", "/") : "";
  if (!text) return "";
  if (text.startsWith("/data/") || text.startsWith("/trust/")) return text;
  return "";
}

function buildDeterministicEvidenceBrief(packet, assistantLens) {
  const validPercent = formatPercent(packet.sentinel2.valid_percent);
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
      `Fecha ${packet.selected_date}, AOI ${packet.aoi}.`,
      `Sentinel-2: ${packet.sentinel2.confidence_class}, ${validPercent}.`,
      `Ledger: ${packet.ledger.status}, hash ${packet.ledger.hash_short}.`,
      `HydroClimate: ${packet.auxiliary_context.hydroclimate_status}.`,
    ],
    limits: [
      "Resumen determinístico basado solo en el paquete visible.",
      "No cambia la decisión primaria ni agrega fuentes nuevas.",
      "No reemplaza revisión territorial, laboratorio o autoridad competente.",
    ],
    recommended_action:
      lensActions[assistantLens] || packet.sentinel2.recommended_action,
  };
}

async function requestEvidenceBrief(evidencePacket) {
  if (import.meta.env.DEV && typeof window !== "undefined" && window.location.port) {
    return { mode: "fallback", reason: "endpoint_unavailable" };
  }

  try {
    const response = await fetch("/api/evidence-brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ evidence_packet: evidencePacket }),
    });

    if (!response.ok) {
      return {
        mode: "fallback",
        reason: response.status === 404 ? "endpoint_unavailable" : `http_${response.status}`,
      };
    }

    const payload = await response.json();
    if (payload?.mode !== "ai") {
      return {
        mode: "fallback",
        reason: payload?.reason || "provider_unavailable",
      };
    }

    const brief = checkAssistantBrief(payload);
    if (!brief) {
      return { mode: "fallback", reason: "claim_guard" };
    }

    return {
      brief,
      mode: "ai",
      model: safeAssistantText(payload.model, 120),
    };
  } catch {
    return { mode: "fallback", reason: "request_failed" };
  }
}

function checkAssistantBrief(payload) {
  if (!payload || typeof payload !== "object") return null;
  if (containsUnsafeAssistantClaim(payload)) return null;

  const brief = {
    artifact_refs: cleanAssistantList(payload.artifact_refs),
    decision_summary: safeAssistantText(payload.decision_summary, 700),
    evidence_gaps: cleanAssistantList(payload.evidence_gaps),
    evidence_used: cleanAssistantList(payload.evidence_used),
    limits: cleanAssistantList(payload.limits),
    recommended_action: safeAssistantText(payload.recommended_action, 700),
  };

  if (
    !brief.artifact_refs.length ||
    !brief.decision_summary ||
    !brief.evidence_gaps.length ||
    !brief.evidence_used.length ||
    !brief.limits.length ||
    !brief.recommended_action
  ) {
    return null;
  }

  return brief;
}

function getAssistantStatusChipLabel(state) {
  if (state.status === "loading") return "Preparando";
  if (state.mode === "ai") return "IA conectada";
  if (state.reason === "missing_key" || state.reason === "endpoint_unavailable") {
    return "Modelo no configurado";
  }
  return "Resumen deterministico";
}

function cleanAssistantList(value) {
  if (!Array.isArray(value)) return [];
  return uniqueAssistantItems(value.map((item) => safeAssistantText(item, 420))).slice(0, 8);
}

function uniqueAssistantItems(items) {
  return Array.from(new Set(items.filter(Boolean)));
}

function safeAssistantText(value, maxLength = 700) {
  if (typeof value !== "string") return "";
  return value.trim().replace(/\s+/g, " ").slice(0, maxLength);
}

function containsUnsafeAssistantClaim(value) {
  const text = stripMarks(JSON.stringify(value)).toLowerCase();
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

function stripMarks(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function compareLedgerRows(left, right) {
  const leftIndex = Number(left.event_index);
  const rightIndex = Number(right.event_index);
  if (Number.isFinite(leftIndex) && Number.isFinite(rightIndex)) {
    return leftIndex - rightIndex;
  }
  return String(left.generated_at_utc || "").localeCompare(String(right.generated_at_utc || ""));
}

function compactItems(items) {
  return items.filter((entry) => entry?.content);
}

function item(key, content) {
  return { key, content };
}

function getStateLabel(record) {
  const label = String(record?.confidence_label_es || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, " ");
  if (label) return label;
  return STATE_LABELS[record?.confidence_class] || "NO INFERIR";
}

function formatPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "sin dato";
  return `${numeric.toFixed(2)}%`;
}
