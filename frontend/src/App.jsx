import React, { useEffect, useMemo, useState } from "react";

const DEFAULT_DATE = "2025-06-10";
const COMPARISON_DATES = ["2025-06-10", "2025-06-30"];

const STATE_META = {
  usable: {
    label: "USABLE",
    tone: "usable",
    decision: "Interpretar con cautela",
    explanation:
      "La observación Sentinel tiene suficiente evidencia válida para una lectura exploratoria con límites explícitos.",
    action:
      "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
    nextAction:
      "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
    comparison:
      "Evidencia suficiente para lectura exploratoria con límites explícitos.",
  },
  low_confidence: {
    label: "REVISAR",
    tone: "review",
    decision: "Revisar / verificar",
    explanation:
      "La observación Sentinel tiene evidencia limitada y requiere revisión o verificación territorial.",
    action: "Revisar con cautela y considerar verificación territorial.",
    nextAction: "Revisar con cautela y considerar verificación territorial.",
    comparison: "Evidencia parcial. Requiere revisión antes de inferir.",
  },
  do_not_infer: {
    label: "NO INFERIR",
    tone: "stop",
    decision: "No inferir",
    explanation:
      "La observación Sentinel no tiene suficiente evidencia válida para una inferencia responsable.",
    action:
      "No usar esta observación para afirmar condiciones del territorio; esperar una nueva adquisición o solicitar verificación territorial.",
    nextAction:
      "Esperar una nueva adquisición o solicitar verificación territorial.",
    comparison: "Evidencia insuficiente para inferencia responsable.",
  },
};

const METRIC_HELP = {
  validPercent: "parte de la observación que sí puede usarse",
  sampleCount: "píxeles o muestras consideradas",
  noDataCount: "muestras descartadas por nube/no-data",
  mndwi_mean: "índice óptico de agua/humedad superficial",
  ndti_mean: "proxy exploratorio hidro-sedimentario",
  resolution_m: "tamaño de análisis satelital",
};

const SCIENTIFIC_LIMITS =
  "Azuero Kairós no detecta pesticidas, atrazina, patógenos, metales pesados, contaminación química disuelta ni agua segura. Las afirmaciones químicas o sanitarias requieren laboratorio o verificación autorizada.";

const DETAIL_TABS = [
  { id: "resumen", label: "Resumen" },
  { id: "evidencia", label: "Evidencia" },
  { id: "trazabilidad", label: "Trazabilidad" },
  { id: "limites", label: "Límites" },
];

const SYSTEM_MODULES = [
  {
    name: "Kairós Signal",
    text: "Clasifica la confianza de cada observación Sentinel.",
  },
  {
    name: "Kairós Brief",
    text: "Traduce la decisión en un informe legible.",
  },
  {
    name: "Kairós Ledger",
    text: "Conserva la cadena auditable de evidencia.",
  },
  {
    name: "Kairós Field",
    text: "Futuro flujo de verificación territorial.",
  },
  {
    name: "Kairós Watch",
    text: "Futuro seguimiento temporal de observaciones.",
  },
];

export default function App() {
  const [observations, setObservations] = useState([]);
  const [ledgerRows, setLedgerRows] = useState([]);
  const [selectedDate, setSelectedDate] = useState(DEFAULT_DATE);
  const [activePage, setActivePage] = useState(getInitialPage);
  const [activeDetailTab, setActiveDetailTab] = useState("resumen");
  const [loadState, setLoadState] = useState({ status: "loading", message: "" });

  useEffect(() => {
    let active = true;

    async function loadData() {
      try {
        const [observationsResponse, ledgerResponse] = await Promise.all([
          fetch("/data/observations.json"),
          fetch("/data/evidence_ledger.json"),
        ]);

        if (!observationsResponse.ok) {
          throw new Error("No se pudo cargar observations.json");
        }

        const observationsPayload = await observationsResponse.json();
        const ledgerPayload = ledgerResponse.ok ? await ledgerResponse.json() : [];

        if (!active) return;
        const cleanObservations = observationsPayload.map(normalizeRecord);
        const cleanLedger = ledgerPayload.map(normalizeRecord);

        setObservations(cleanObservations);
        setLedgerRows(cleanLedger);
        setSelectedDate(
          cleanObservations.some((record) => record.date === DEFAULT_DATE)
            ? DEFAULT_DATE
            : cleanObservations[0]?.date ?? DEFAULT_DATE,
        );
        setLoadState({ status: "ready", message: "" });
      } catch (error) {
        if (!active) return;
        setLoadState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "No se pudo cargar la data pública.",
        });
      }
    }

    loadData();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    function handleHashChange() {
      setActivePage(getInitialPage());
    }

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const selectedRecord = useMemo(() => {
    return (
      observations.find((record) => record.date === selectedDate) ??
      observations[0] ??
      null
    );
  }, [observations, selectedDate]);

  const selectedLedger = useMemo(() => {
    if (!selectedRecord) return null;
    return findLedgerForRecord(ledgerRows, selectedRecord);
  }, [ledgerRows, selectedRecord]);

  const comparisonRecords = useMemo(() => {
    return COMPARISON_DATES.map((date) =>
      observations.find(
        (record) => record.date === date && record.aoi === "corridor_wide",
      ),
    );
  }, [observations]);

  if (loadState.status === "loading") {
    return <LoadingScreen />;
  }

  if (loadState.status === "error" || !selectedRecord) {
    return (
      <main className="app-shell">
        <section className="empty-state">
          <p className="small-label">Data pública</p>
          <h1>Azuero Kairós</h1>
          <p>{loadState.message || "No hay observaciones disponibles."}</p>
        </section>
      </main>
    );
  }

  const availableDates = observations.map((record) => record.date);
  const statusText = buildRunStatus(ledgerRows);

  return (
    <main className="app-shell">
      <Header
        activePage={activePage}
        setActivePage={setPageAndHash}
        statusText={statusText}
      />

      {activePage === "decision" ? (
        <DecisionLanding
          availableDates={availableDates}
          comparisonRecords={comparisonRecords}
          record={selectedRecord}
          ledger={selectedLedger}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          activeDetailTab={activeDetailTab}
          setActiveDetailTab={setActiveDetailTab}
        />
      ) : (
        <TechnicalDashboard
          availableDates={availableDates}
          comparisonRecords={comparisonRecords}
          record={selectedRecord}
          ledger={selectedLedger}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
        />
      )}
    </main>
  );
}

function setPageAndHash(page) {
  const nextHash = page === "technical" ? "#datos-tecnicos" : "#decision";
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash;
    return;
  }
}

function getInitialPage() {
  if (typeof window !== "undefined" && window.location.hash === "#datos-tecnicos") {
    return "technical";
  }
  return "decision";
}

function Header({ activePage, setActivePage, statusText }) {
  return (
    <header className="top-nav">
      <button
        className="brand-button"
        type="button"
        onClick={() => setActivePage("decision")}
        aria-label="Ir a la decisión pública"
      >
        Azuero Kairós
      </button>

      <nav className="view-nav" aria-label="Navegación principal">
        <button
          className={activePage === "decision" ? "active" : ""}
          type="button"
          onClick={() => setActivePage("decision")}
        >
          Decisión
        </button>
        <button
          className={activePage === "technical" ? "active" : ""}
          type="button"
          onClick={() => setActivePage("technical")}
        >
          Datos técnicos
        </button>
      </nav>

      <p className="run-status">{statusText}</p>
    </header>
  );
}

function DecisionLanding({
  availableDates,
  comparisonRecords,
  record,
  ledger,
  selectedDate,
  setSelectedDate,
  activeDetailTab,
  setActiveDetailTab,
}) {
  const state = getStateMeta(record);

  return (
    <>
      <section className="decision-hero" aria-label="Reporte de decisión">
        <article className={`report-panel tone-${state.tone}`}>
          <div className="report-controls">
            <span>Reporte de decisión</span>
            <label>
              <span>Fecha</span>
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

          <p className="risk-note">Una mala inferencia también es un riesgo.</p>

          <div className="decision-word">{state.label}</div>
          <div className="evidence-percent">
            <strong>{formatPercent(record.validPercent)}</strong>
            <span>evidencia válida</span>
          </div>

          <div className="record-facts" aria-label="Metadatos de la observación">
            <span>Fecha: {record.date}</span>
            <span>AOI: {record.aoi}</span>
          </div>

          <p className="plain-explanation">{state.explanation}</p>

          <div className="next-step-box">
            <span>Qué debe pasar ahora</span>
            <p>{state.nextAction}</p>
          </div>

        </article>

        <aside className="why-panel">
          <p className="small-label">Por qué importa</p>
          <h2>La confianza cambia la decisión.</h2>
          <CompactComparison records={comparisonRecords} />
          <p className="insight-text">
            El sistema no fuerza alertas. Decide cuándo Copernicus puede usarse y
            cuándo no.
          </p>
        </aside>
      </section>

      <section className="detail-tabs" aria-label="Detalle de la decisión">
        <div className="tab-list" role="tablist" aria-label="Secciones de detalle">
          {DETAIL_TABS.map((tab) => (
            <button
              key={tab.id}
              className={activeDetailTab === tab.id ? "active" : ""}
              type="button"
              role="tab"
              aria-selected={activeDetailTab === tab.id}
              onClick={() => setActiveDetailTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="tab-panel" role="tabpanel">
          {activeDetailTab === "resumen" ? (
            <SummaryTab record={record} comparisonRecords={comparisonRecords} />
          ) : null}
          {activeDetailTab === "evidencia" ? <EvidenceTab record={record} /> : null}
          {activeDetailTab === "trazabilidad" ? (
            <TraceabilityTab record={record} ledger={ledger} />
          ) : null}
          {activeDetailTab === "limites" ? <LimitsTab /> : null}
        </div>
      </section>

      <DecisionLimitsNotice />
      <ModulesStrip />
    </>
  );
}

function CompactComparison({ records }) {
  const [weakRecord, usableRecord] = records;

  if (!weakRecord || !usableRecord) {
    return (
      <p className="compact-missing">
        Comparación disponible cuando existen 2025-06-10 y 2025-06-30.
      </p>
    );
  }

  return (
    <div className="compact-compare">
      {[weakRecord, usableRecord].map((record) => {
        const state = getStateMeta(record);
        return (
          <article className={`mini-decision tone-${state.tone}`} key={record.date}>
            <span>{record.date}</span>
            <strong>{state.label}</strong>
            <b>{formatPercent(record.validPercent)}</b>
          </article>
        );
      })}
    </div>
  );
}

function SummaryTab({ record, comparisonRecords }) {
  const state = getStateMeta(record);

  return (
    <div className="summary-layout">
      <article className={`summary-card tone-${state.tone}`}>
        <span className="small-label">Decisión seleccionada</span>
        <h3>{state.label}</h3>
        <p>{state.explanation}</p>
        <strong>{state.nextAction}</strong>
      </article>
      <article className="summary-card">
        <span className="small-label">Contraste de demo</span>
        <CompactComparison records={comparisonRecords} />
      </article>
      <article className="summary-card">
        <span className="small-label">Producto</span>
        <p>
          Azuero Kairós convierte observaciones Copernicus en una capa de
          confianza: interpretar, revisar o no inferir.
        </p>
      </article>
    </div>
  );
}

function EvidenceTab({ record }) {
  return (
    <div className="metric-grid detail-grid">
      {metricRows(record).map((metric) => (
        <article className="metric-card" key={metric.key}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <p>{metric.help}</p>
        </article>
      ))}
    </div>
  );
}

function TraceabilityTab({ record, ledger }) {
  return (
    <div className="trace-layout">
      <EvidencePipeline compact={false} />
      <div className="trace-grid">
        <TraceItem label="API status" value={record.api_status || "pendiente"} />
        <TraceItem
          label="Ledger status"
          value={ledger?.evidence_status ?? "sin registro"}
        />
        <TraceItem
          label="raw_json_path"
          value={record.raw_json_path || ledger?.raw_json_path || "pendiente"}
        />
        <TraceItem
          label="brief_path"
          value={record.brief_path || ledger?.brief_path || "no generado"}
        />
      </div>
    </div>
  );
}

function LimitsTab() {
  return (
    <article className="limits-panel">
      <span className="small-label">Límites científicos</span>
      <p>{SCIENTIFIC_LIMITS}</p>
    </article>
  );
}

function DecisionLimitsNotice() {
  return (
    <section className="decision-limits" aria-label="Límites científicos">
      <span>Límites científicos</span>
      <p>{SCIENTIFIC_LIMITS}</p>
    </section>
  );
}

function ModulesStrip() {
  return (
    <section className="modules-strip" aria-label="Módulos del sistema">
      <div>
        <p className="small-label">Sistema modular</p>
        <h2>Atlas de decisión territorial</h2>
      </div>
      <div className="module-list">
        {SYSTEM_MODULES.map((module) => (
          <article className="module-chip" key={module.name}>
            <strong>{module.name}</strong>
            <span>{module.text}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

function TechnicalDashboard({
  availableDates,
  comparisonRecords,
  record,
  ledger,
  selectedDate,
  setSelectedDate,
}) {
  const state = getStateMeta(record);

  return (
    <section className="technical-screen" aria-label="Datos técnicos">
      <div className="technical-heading">
        <div>
          <p className="small-label">Datos técnicos</p>
          <h1>Lectura completa de la observación</h1>
        </div>
        <label className="technical-date">
          <span>Fecha</span>
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

      <div className="technical-status-row">
        <StatusChip label="AOI" value={record.aoi} />
        <StatusChip label="Fuente" value="JSON público oficial" />
        <StatusChip label="API" value={record.api_status || "pendiente"} />
        <StatusChip
          label="Ledger"
          value={ledger?.evidence_status ?? "sin registro"}
        />
      </div>

      <div className="technical-hero-grid">
        <DecisionCard record={record} state={state} />
        <MeaningPanel record={record} ledger={ledger} state={state} />
      </div>

      <ComparisonSection records={comparisonRecords} />
      <MetricsSection record={record} />
      <EvidencePipeline />
      <TechnicalTraceability record={record} ledger={ledger} />
      <BriefPreview record={record} ledger={ledger} state={state} />
      <ScientificLimits />
      <ModulesStrip />
    </section>
  );
}

function DecisionCard({ record, state }) {
  return (
    <article className={`decision-card tone-${state.tone}`}>
      <div className="card-topline">
        <span>Decisión satelital</span>
        <span>{record.date}</span>
      </div>
      <div className="decision-status">{state.label}</div>
      <div className="validity-display">
        <strong>{formatPercent(record.validPercent)}</strong>
        <span>evidencia válida</span>
      </div>
      <p className="decision-message">{state.explanation}</p>
      <div className="next-action">
        <span>Siguiente acción</span>
        <p>{state.nextAction}</p>
      </div>
    </article>
  );
}

function MeaningPanel({ record, ledger, state }) {
  return (
    <aside className="meaning-panel">
      <section className="meaning-copy">
        <p className="small-label">Qué significa esto</p>
        <h2>{state.decision}</h2>
        <p>{record.reason_es || state.explanation}</p>
        <p className="quiet-action">{record.recommended_action_es || state.action}</p>
      </section>

      <section className="identity-card">
        <div className="identity-copy">
          <p className="small-label">Identidad de evidencia</p>
          <dl>
            <DataPair label="AOI" value={record.aoi} />
            <DataPair label="Sensor" value="Sentinel-2 L2A" />
            <DataPair label="Resolución" value={`${record.resolution_m} m`} />
            <DataPair label="Fuente" value="Copernicus CDSE Statistical API" />
            <DataPair label="API" value={record.api_status || "pendiente"} />
            <DataPair
              label="Ledger"
              value={ledger?.evidence_status ?? "sin registro"}
            />
          </dl>
        </div>
      </section>
    </aside>
  );
}

function ComparisonSection({ records }) {
  const [weakRecord, usableRecord] = records;
  const complete = Boolean(weakRecord && usableRecord);

  return (
    <section className="comparison-section" aria-label="Comparación de decisión">
      <div className="section-heading">
        <div>
          <p className="small-label">Por qué esto importa</p>
          <h2>La confianza cambia la decisión</h2>
        </div>
        <p>
          El mismo sistema puede decir NO INFERIR en una fecha y USABLE en otra.
          Esa diferencia evita conclusiones falsas.
        </p>
      </div>

      {complete ? (
        <>
          <div className="comparison-grid">
            <ComparisonCard record={weakRecord} />
            <ComparisonCard record={usableRecord} />
          </div>
          <p className="product-insight">
            El sistema no fuerza alertas; decide cuándo la evidencia Copernicus
            puede usarse y cuándo no.
          </p>
        </>
      ) : (
        <p className="availability-note">
          Comparación disponible cuando el JSON oficial contiene 2025-06-10 y
          2025-06-30.
        </p>
      )}
    </section>
  );
}

function ComparisonCard({ record }) {
  const state = getStateMeta(record);

  return (
    <article className={`comparison-card tone-${state.tone}`}>
      <div>
        <span className="comparison-date">{record.date}</span>
        <h3>{state.label}</h3>
      </div>
      <strong>{formatPercent(record.validPercent)}</strong>
      <p>{state.comparison}</p>
    </article>
  );
}

function MetricsSection({ record }) {
  return (
    <section className="metrics-section" aria-label="Métricas de evidencia">
      <div className="section-heading compact">
        <div>
          <p className="small-label">Métricas que explican la decisión</p>
          <h2>Solo lo necesario para decidir</h2>
        </div>
      </div>
      <div className="metric-grid">
        {metricRows(record).map((metric) => (
          <article className="metric-card" key={metric.key}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <p>{metric.help}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function TechnicalTraceability({ record, ledger }) {
  return (
    <section className="technical-trace-section" aria-label="Trazabilidad técnica">
      <div className="section-heading compact">
        <div>
          <p className="small-label">Trazabilidad</p>
          <h2>Rutas oficiales del artifact</h2>
        </div>
      </div>
      <div className="trace-grid">
        <TraceItem label="raw JSON path" value={record.raw_json_path || "pendiente"} />
        <TraceItem
          label="processed CSV"
          value={ledger?.processed_csv_path ?? "outputs/processed_csv/sentinel2_stats_confidence.csv"}
        />
        <TraceItem
          label="brief path"
          value={record.brief_path || ledger?.brief_path || "no generado"}
        />
        <TraceItem
          label="ledger status"
          value={ledger?.evidence_status ?? "sin registro"}
        />
      </div>
    </section>
  );
}

function EvidencePipeline({ compact = true }) {
  const steps = compact
    ? ["CDSE", "JSON", "CSV", "Confianza", "Brief", "Ledger"]
    : [
        "CDSE",
        "raw JSON",
        "processed CSV",
        "confidence engine",
        "brief",
        "ledger",
      ];

  return (
    <section className="pipeline-section" aria-label="Flujo de evidencia">
      <p className="small-label">Cadena auditable</p>
      <div className="pipeline-row">
        {steps.map((step, index) => (
          <div className="pipeline-item" key={step}>
            <span>{step}</span>
            {index < steps.length - 1 ? <b aria-hidden="true">→</b> : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function BriefPreview({ record, ledger, state }) {
  return (
    <section className="brief-section" aria-label="Resumen del informe de confianza">
      <div className="section-heading compact">
        <div>
          <p className="small-label">Informe de Confianza</p>
          <h2>Vista compacta para demo público</h2>
        </div>
      </div>
      <div className="brief-grid">
        <BriefItem
          label="Decisión ejecutiva"
          value={`${state.label}: ${state.decision}`}
        />
        <BriefItem
          label="Calidad de evidencia"
          value={`${formatPercent(record.validPercent)} válido, ${formatInteger(
            record.sampleCount,
          )} muestras evaluadas.`}
        />
        <BriefItem
          label="Siguiente acción"
          value={record.recommended_action_es || state.action}
        />
        <BriefItem
          label="Trazabilidad"
          value={
            record.brief_path
              ? record.brief_path
              : ledger?.raw_json_path ?? record.raw_json_path ?? "pendiente"
          }
        />
      </div>
    </section>
  );
}

function ScientificLimits() {
  return (
    <section className="limits-card" aria-label="Límites científicos">
      <p className="small-label">Límites científicos</p>
      <p>{SCIENTIFIC_LIMITS}</p>
    </section>
  );
}

function StatusChip({ label, value }) {
  return (
    <div className="status-chip">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DataPair({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

function TraceItem({ label, value }) {
  return (
    <article className="trace-item">
      <span>{label}</span>
      <p>{value}</p>
    </article>
  );
}

function BriefItem({ label, value }) {
  return (
    <article className="brief-item">
      <span>{label}</span>
      <p>{value}</p>
    </article>
  );
}

function LoadingScreen() {
  return (
    <main className="app-shell">
      <section className="empty-state">
        <p className="small-label">Data pública</p>
        <h1>Azuero Kairós</h1>
        <p>Cargando observaciones oficiales exportadas.</p>
      </section>
    </main>
  );
}

function metricRows(record) {
  return [
    {
      key: "validPercent",
      label: "Porcentaje válido",
      value: formatPercent(record.validPercent),
      help: METRIC_HELP.validPercent,
    },
    {
      key: "sampleCount",
      label: "Muestras evaluadas",
      value: formatInteger(record.sampleCount),
      help: METRIC_HELP.sampleCount,
    },
    {
      key: "noDataCount",
      label: "Muestras sin datos",
      value: formatInteger(record.noDataCount),
      help: METRIC_HELP.noDataCount,
    },
    {
      key: "mndwi_mean",
      label: "MNDWI",
      value: formatDecimal(record.mndwi_mean),
      help: METRIC_HELP.mndwi_mean,
    },
    {
      key: "ndti_mean",
      label: "NDTI",
      value: formatDecimal(record.ndti_mean),
      help: METRIC_HELP.ndti_mean,
    },
    {
      key: "resolution_m",
      label: "Resolución",
      value: `${record.resolution_m ?? "pendiente"} m`,
      help: METRIC_HELP.resolution_m,
    },
  ];
}

function getStateMeta(record) {
  const base = STATE_META[record.confidence_class] ?? STATE_META.do_not_infer;
  return {
    ...base,
    label: base.label,
    decision: record.decision_label_es || base.decision,
    action: record.recommended_action_es || base.action,
  };
}

function findLedgerForRecord(rows, record) {
  return rows.find(
    (row) =>
      row.date === record.date &&
      row.aoi === record.aoi &&
      Number(row.resolution_m) === Number(record.resolution_m),
  );
}

function buildRunStatus(ledgerRows) {
  const hasOkLedger = ledgerRows.some((row) =>
    String(row.evidence_status ?? "").includes("official_api_ok"),
  );
  return hasOkLedger
    ? "Official Copernicus run · Evidence ledger OK"
    : "Official Copernicus run · Ledger pendiente";
}

function normalizeRecord(record) {
  return Object.fromEntries(
    Object.entries(record).map(([key, value]) => [
      key,
      typeof value === "string" ? repairMojibake(value) : value,
    ]),
  );
}

function repairMojibake(value) {
  if (!/[ÃÂâ]/.test(value) || typeof TextDecoder === "undefined") {
    return value;
  }

  try {
    const bytes = Uint8Array.from(Array.from(value), (char) =>
      char.charCodeAt(0),
    );
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return value
      .replaceAll("Ã³", "ó")
      .replaceAll("Ã¡", "á")
      .replaceAll("Ã©", "é")
      .replaceAll("Ã­", "í")
      .replaceAll("Ãº", "ú")
      .replaceAll("Ã±", "ñ")
      .replaceAll("Ã¼", "ü")
      .replaceAll("Â", "");
  }
}

function formatPercent(value) {
  return `${formatNumber(value, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function formatInteger(value) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return new Intl.NumberFormat("es-PA", { maximumFractionDigits: 0 }).format(
    Number(value),
  );
}

function formatDecimal(value) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return formatNumber(value, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatNumber(value, options) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return new Intl.NumberFormat("es-PA", options).format(Number(value));
}
