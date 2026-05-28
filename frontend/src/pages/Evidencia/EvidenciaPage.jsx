import React, { useMemo } from "react";
import "./EvidenciaPage.css";

const STATE_LABELS = {
  usable: "USABLE",
  low_confidence: "REVISAR",
  do_not_infer: "NO INFERIR",
};

export default function EvidenciaPage({
  availableDates = [],
  record,
  ledger,
  ledgerRows = [],
  selectedDate,
  setSelectedDate,
}) {
  const stateLabel = getStateLabel(record);
  const ledgerEntries = useMemo(
    () => buildLedgerEntries(ledgerRows.length ? ledgerRows : ledger ? [ledger] : []),
    [ledger, ledgerRows],
  );
  const knowledgeModel = useMemo(
    () => buildKnowledgeModel(record, ledger, stateLabel),
    [ledger, record, stateLabel],
  );

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
                <span>[{entry.id}]</span>
              </div>
            ))
          ) : (
            <div className="evidencia-ledger__row">
              <span>[sin timestamp]</span>
              <span>[sin ledger]</span>
              <span>[sin id]</span>
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

function buildKnowledgeModel(record, ledger, stateLabel) {
  const reason = record?.reason_es || record?.reason || "Motivo no disponible en el JSON público.";
  const action =
    record?.recommended_action_es ||
    record?.recommended_action ||
    "Mantener la decisión dentro de los límites de evidencia disponibles.";
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
            Artefacto:{" "}
            <span className="data-value">
              {record?.brief_path || ledger?.brief_path || "brief no disponible"}
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
        record?.raw_json_path
          ? item("raw-json", (
              <>
                JSON fuente: <span className="data-value">{record.raw_json_path}</span>
              </>
            ))
          : null,
      ]),
    },
  ];
}

function buildLedgerEntries(rows) {
  return rows.map((row, index) => {
    const id =
      row.git_commit ||
      row.run_id ||
      row.raw_json_path ||
      row.brief_path ||
      `entry-${index + 1}`;

    return {
      key: `${row.generated_at_utc || "sin-timestamp"}-${id}-${index}`,
      timestamp: row.generated_at_utc || "sin timestamp",
      eventType: row.evidence_status || row.api_status || row.confidence_class || "evento",
      id,
    };
  });
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
