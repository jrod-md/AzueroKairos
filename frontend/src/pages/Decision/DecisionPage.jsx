import React, { useMemo } from "react";
import ConfidenceCompass from "../../components/ConfidenceCompass/ConfidenceCompass.jsx";
import DecisionStamp from "../../components/DecisionStamp/DecisionStamp.jsx";
import GateChain from "../../components/GateChain/GateChain.jsx";
import "./DecisionPage.css";

const STATE_META = {
  USABLE: {
    key: "usable",
    stamp: "USABLE",
    label: "USABLE",
    explanation:
      "La observación Sentinel tiene evidencia válida para una lectura exploratoria con límites explícitos.",
    action:
      "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
  },
  REVISAR: {
    key: "revisar",
    stamp: "REVISAR",
    label: "REVISAR",
    explanation:
      "La observación Sentinel requiere revisión antes de sostener una interpretación territorial.",
    action: "Revisar con cautela y considerar verificación territorial.",
  },
  NO_INFERIR: {
    key: "no-inferir",
    stamp: "NO_INFERIR",
    label: "NO INFERIR",
    explanation:
      "La observación no tiene evidencia válida suficiente para una inferencia responsable.",
    action:
      "Esperar una nueva adquisición o solicitar verificación territorial.",
  },
};

export default function DecisionPage({
  observations = [],
  comparisonRecords = [],
  record,
  ledger,
  selectedDate,
  setSelectedDate,
}) {
  const observationRecords = useMemo(
    () => [...observations].sort((left, right) => left.date.localeCompare(right.date)),
    [observations],
  );

  if (!record) return null;

  const state = getDecisionState(record);
  const gates = buildGateChain(record, ledger, state);
  const technicalRows = buildTechnicalRows(record, ledger);
  const contrastRecords = comparisonRecords.filter(Boolean);

  return (
    <section
      className={`decision-page decision-page--${state.key}`}
      aria-labelledby="decision-page-title"
    >
      <header className="decision-page__heading">
        <div>
          <p className="section-label">DECISIÓN SENTINEL-2</p>
          <h1 id="decision-page-title">Decisión ejecutiva: {state.label}</h1>
        </div>
        <p>
          {record.date} · {record.aoi || "corridor_wide"} ·{" "}
          {formatPercent(record.validPercent)} evidencia válida
        </p>
      </header>

      <DateSelector
        records={observationRecords}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
      />

      <section className="decision-page__instrument" aria-label="Reporte ejecutivo de campo">
        <div className="decision-page__compass-column">
          <ConfidenceCompass validPercent={record.validPercent} size={260} />
        </div>

        <div className="decision-page__decision-column">
          <DecisionStamp state={state.stamp} />
          <p className="decision-page__explanation">
            {record.reason_es || state.explanation}
          </p>
          {state.stamp === "NO_INFERIR" ? (
            <ScientificRigorNote record={record} ledger={ledger} />
          ) : null}
          <div className="decision-page__next-action">
            <span className="section-label">Siguiente acción</span>
            <p>{record.recommended_action_es || state.action}</p>
          </div>
        </div>

        <TechnicalStrip rows={technicalRows} />
      </section>

      <section className="decision-page__gate-card" aria-label="Cadena de decisión">
        <GateChain key={`${record.date}-${record.aoi}-${state.stamp}`} gates={gates} />
      </section>

      <ContrastPanel records={contrastRecords} />

      <ObservationList
        records={observationRecords}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
      />
    </section>
  );
}

function DateSelector({ records, selectedDate, setSelectedDate }) {
  return (
    <div className="decision-page__date-row" aria-label="Selector de fecha">
      {records.slice(0, 5).map((dateRecord) => {
        const state = getDecisionState(dateRecord);
        const active = dateRecord.date === selectedDate;

        return (
          <button
            key={dateRecord.date}
            type="button"
            className={`decision-page__date-tab decision-page__date-tab--${state.key}${active ? " is-active" : ""}`}
            onClick={() => setSelectedDate(dateRecord.date)}
          >
            <span>{dateRecord.date}</span>
            <i aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}

function TechnicalStrip({ rows }) {
  return (
    <dl className="decision-page__technical-strip" aria-label="Lectura técnica">
      {rows.map((row) => (
        <div className="decision-page__technical-row" key={row.label}>
          <dt>{row.label}</dt>
          <dd>
            {row.ok ? <span className="decision-page__ok-dot" aria-hidden="true" /> : null}
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function ScientificRigorNote({ record, ledger }) {
  const apiStatus = record.api_status || ledger?.api_status || "pendiente";

  return (
    <aside
      className="decision-page__science-note"
      aria-label="Rigor cientifico de la decision"
    >
      <span className="section-label">Rigor cientifico</span>
      <p>
        API {displayValue(apiStatus)} confirma ejecucion tecnica; no autoriza
        inferencia si solo {formatPercent(record.validPercent)} de la observacion
        es evidencia valida. Kairos conserva trazabilidad hasta nueva adquisicion
        o verificacion territorial.
      </p>
    </aside>
  );
}

function ContrastPanel({ records }) {
  if (records.length < 2) return null;

  return (
    <section className="decision-page__contrast" aria-label="Contraste oficial">
      <p className="section-label">Contraste oficial</p>
      <div className="decision-page__contrast-grid">
        {records.slice(0, 2).map((contrastRecord) => {
          const state = getDecisionState(contrastRecord);

          return (
            <article className="decision-page__contrast-card" key={contrastRecord.date}>
              <ConfidenceCompass validPercent={contrastRecord.validPercent} size={160} />
              <DecisionStamp state={state.stamp} size="small" />
              <p className="decision-page__contrast-date">{contrastRecord.date}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function ObservationList({ records, selectedDate, setSelectedDate }) {
  return (
    <section className="decision-page__observations" aria-label="Observaciones oficiales">
      <div className="decision-page__section-head">
        <p className="section-label">Observaciones oficiales</p>
        <h2>Registro de campo Sentinel-2</h2>
      </div>
      <div className="decision-page__observation-grid">
        {records.map((observation) => {
          const state = getDecisionState(observation);
          const active = observation.date === selectedDate;

          return (
            <button
              key={`${observation.date}-${observation.aoi}`}
              type="button"
              className={`decision-page__observation-card decision-page__observation-card--${state.key}${active ? " is-active" : ""}`}
              onClick={() => setSelectedDate(observation.date)}
            >
              <span className="decision-page__observation-kicker">{state.label}</span>
              <h3>{observation.date}</h3>
              <dl>
                <div>
                  <dt>Valid%</dt>
                  <dd>{formatPercent(observation.validPercent)}</dd>
                </div>
                <div>
                  <dt>AOI</dt>
                  <dd>{displayValue(observation.aoi)}</dd>
                </div>
                <div>
                  <dt>API</dt>
                  <dd>{displayValue(observation.api_status)}</dd>
                </div>
              </dl>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function buildTechnicalRows(record, ledger) {
  const apiStatus = record.api_status || ledger?.api_status || "PENDIENTE";
  const validPixels = Math.max(
    0,
    safeNumber(record.sampleCount) - safeNumber(record.noDataCount),
  );
  const ledgerOk = Boolean(ledger?.evidence_status);

  return [
    { label: "API CDSE", value: apiStatus, ok: apiStatus === "OK" },
    { label: "Valid pixels", value: formatInteger(validPixels) },
    { label: "AOI", value: displayValue(record.aoi) },
    { label: "Ledger", value: ledgerOk ? "OK" : "PENDIENTE", ok: ledgerOk },
  ];
}

function buildGateChain(record, ledger, state) {
  const apiOk = (record.api_status || ledger?.api_status) === "OK";
  const qualityState =
    state.stamp === "USABLE"
      ? "passed"
      : state.stamp === "NO_INFERIR"
        ? "failed"
        : "pending";
  const downstreamState = state.stamp === "USABLE" ? "passed" : "pending";

  return [
    {
      id: "api",
      label: "API",
      result: apiOk ? "OK" : "PENDIENTE",
      state: apiOk ? "passed" : "pending",
    },
    {
      id: "quality",
      label: "CALIDAD",
      result:
        qualityState === "failed"
          ? `FALLA ${formatPercent(record.validPercent)}`
          : qualityState === "passed"
            ? `${formatPercent(record.validPercent)} VÁLIDO`
            : `REVISAR ${formatPercent(record.validPercent)}`,
      state: qualityState,
    },
    {
      id: "inference",
      label: "INFERENCIA",
      result: state.label,
      state: downstreamState,
    },
    {
      id: "action",
      label: "ACCIÓN",
      result: getActionShort(state.stamp),
      state: downstreamState,
    },
  ];
}

function getDecisionState(record) {
  const className = String(record?.confidence_class || "").toLowerCase();
  const label = String(record?.confidence_label_es || "").toUpperCase();

  if (className === "usable" || label === "USABLE") return STATE_META.USABLE;
  if (className === "low_confidence" || label === "REVISAR") return STATE_META.REVISAR;
  return STATE_META.NO_INFERIR;
}

function getActionShort(stamp) {
  if (stamp === "USABLE") return "INTERPRETAR";
  if (stamp === "REVISAR") return "VERIFICAR";
  return "ESPERAR";
}

function displayValue(value) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return String(value);
}

function formatPercent(value) {
  const numeric = safeNumber(value);
  return `${numeric.toFixed(2)}%`;
}

function formatInteger(value) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return new Intl.NumberFormat("es-PA", { maximumFractionDigits: 0 }).format(
    Number(value),
  );
}

function safeNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
}
