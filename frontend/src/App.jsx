import React, { useEffect, useMemo, useState } from "react";
import TerritorialMap from "./components/TerritorialMap.jsx";

const DEFAULT_DATE = "2025-06-10";
const COMPARISON_DATES = ["2025-06-10", "2025-06-30"];
const CORRIDOR_NODE_ORDER = [
  "la_villa_oeste",
  "la_villa_central",
  "la_villa_este",
];

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
  "Azuero Kairós limita la decisión pública a confianza de observación Sentinel. No hace afirmaciones químicas, sanitarias, de aptitud de uso ni de respuesta institucional.";

const SAR_LIMITS =
  "Sentinel-1 SAR fue evaluado como contexto auxiliar, pero este corte no produjo observaciones útiles. No se usa como evidencia principal en la decisión pública.";

const HYDROCLIMATE_LIMITS =
  "El contexto hidroclimático solo orienta revisión; no cambia la decisión Sentinel-2.";

const HYDROCLIMATE_INSIGHT =
  "La lluvia antecedente no confirma riesgo. Ayuda a priorizar dónde revisar cuando la evidencia satelital es baja.";

const CASES_INSIGHT =
  "Cada caso traduce capas de evidencia en una acción responsable.";

const LAB_ESCALATION_COPY =
  "Requiere verificación territorial o autoridad competente.";

const EVIDENCE_SOURCE = "Sentinel-2 / CDSE Statistical API";
const THRESHOLD_RULE = "NO INFERIR <10%; REVISAR 10-30%; USABLE >=30%.";

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
    text: "Solicita verificación territorial cuando la confianza satelital no alcanza.",
  },
  {
    name: "Kairós Watch",
    text: "Futuro seguimiento temporal de observaciones.",
  },
];

const MODULE_FLOW = [
  "Kairós Signal",
  "Kairós Brief",
  "Kairós Ledger",
  "Kairós Field",
  "Kairós Watch",
];

const FIELD_CONDITION_OPTIONS = [
  "Agua turbia visible",
  "Sedimento o arrastre superficial",
  "Coloración anómala visible",
  "Erosión de ribera",
  "Descarga visible",
  "Sin condición visible registrada",
  "Requiere laboratorio",
];

export default function App() {
  const [observations, setObservations] = useState([]);
  const [ledgerRows, setLedgerRows] = useState([]);
  const [watchData, setWatchData] = useState(null);
  const [sarContext, setSarContext] = useState(null);
  const [hydroClimate, setHydroClimate] = useState(null);
  const [decisionCases, setDecisionCases] = useState(null);
  const [selectedDate, setSelectedDate] = useState(DEFAULT_DATE);
  const [activePage, setActivePage] = useState(getInitialPage);
  const [activeDetailTab, setActiveDetailTab] = useState("resumen");
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [casePanelMode, setCasePanelMode] = useState("evidence");
  const [loadState, setLoadState] = useState({ status: "loading", message: "" });
  const [watchLoadState, setWatchLoadState] = useState({
    status: "loading",
    message: "",
  });
  const [sarLoadState, setSarLoadState] = useState({
    status: "loading",
    message: "",
  });
  const [hydroClimateLoadState, setHydroClimateLoadState] = useState({
    status: "loading",
    message: "",
  });
  const [decisionCasesLoadState, setDecisionCasesLoadState] = useState({
    status: "loading",
    message: "",
  });

  useEffect(() => {
    let active = true;

    async function loadData() {
      try {
        const [
          observationsResponse,
          ledgerResponse,
          watchResult,
          sarResult,
          hydroClimateResult,
          decisionCasesResult,
        ] = await Promise.all([
          fetch("/data/observations.json"),
          fetch("/data/evidence_ledger.json"),
          loadWatchData(),
          loadSarContext(),
          loadHydroClimateContext(),
          loadDecisionCases(),
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
        setWatchData(watchResult.payload);
        setWatchLoadState({
          status: watchResult.status,
          message: watchResult.message,
        });
        setSarContext(sarResult.payload);
        setSarLoadState({
          status: sarResult.status,
          message: sarResult.message,
        });
        setHydroClimate(hydroClimateResult.payload);
        setHydroClimateLoadState({
          status: hydroClimateResult.status,
          message: hydroClimateResult.message,
        });
        setDecisionCases(decisionCasesResult.payload);
        setDecisionCasesLoadState({
          status: decisionCasesResult.status,
          message: decisionCasesResult.message,
        });
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
        setWatchLoadState({
          status: "error",
          message: "No se pudo cargar Kairós Watch.",
        });
        setSarLoadState({
          status: "error",
          message: "No se pudo cargar la nota técnica Sentinel-1.",
        });
        setHydroClimateLoadState({
          status: "error",
          message: "No se pudo cargar Kairós HydroClimate.",
        });
        setDecisionCasesLoadState({
          status: "error",
          message: "No se pudo cargar Kairós Cases.",
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

  const selectedHydroClimateContext = useMemo(() => {
    if (!selectedRecord) return null;
    return findHydroContextForRecord(hydroClimate, selectedRecord);
  }, [hydroClimate, selectedRecord]);

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
          observations={observations}
          comparisonRecords={comparisonRecords}
          record={selectedRecord}
          ledger={selectedLedger}
          hydroClimateContext={selectedHydroClimateContext}
          watchData={watchData}
          watchLoadState={watchLoadState}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          activeDetailTab={activeDetailTab}
          setActiveDetailTab={setActiveDetailTab}
        />
      ) : activePage === "technical" ? (
        <TechnicalDashboard
          availableDates={availableDates}
          comparisonRecords={comparisonRecords}
          record={selectedRecord}
          ledger={selectedLedger}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          sarContext={sarContext}
          sarLoadState={sarLoadState}
        />
      ) : activePage === "cases" ? (
        <KairosCases
          data={decisionCases}
          loadState={decisionCasesLoadState}
          activeCaseId={activeCaseId}
          setActiveCaseId={setActiveCaseId}
          casePanelMode={casePanelMode}
          setCasePanelMode={setCasePanelMode}
        />
      ) : (
        <KairosWatch
          data={watchData}
          loadState={watchLoadState}
          hydroClimate={hydroClimate}
          hydroClimateLoadState={hydroClimateLoadState}
        />
      )}
    </main>
  );
}

async function loadWatchData() {
  try {
    const response = await fetch("/data/kairos_watch.json");
    if (!response.ok) {
      return {
        status: "missing",
        message:
          "Kairós Watch estará disponible cuando exista /data/kairos_watch.json.",
        payload: null,
      };
    }

    return {
      status: "ready",
      message: "",
      payload: normalizeWatchPayload(await response.json()),
    };
  } catch {
    return {
      status: "error",
      message: "No se pudo cargar /data/kairos_watch.json.",
      payload: null,
    };
  }
}

async function loadSarContext() {
  try {
    const response = await fetch("/data/sar_context.json");
    if (!response.ok) {
      return {
        status: "missing",
        message:
          "La nota técnica Sentinel-1 estará disponible cuando exista /data/sar_context.json.",
        payload: null,
      };
    }

    return {
      status: "ready",
      message: "",
      payload: normalizeSarPayload(await response.json()),
    };
  } catch {
    return {
      status: "error",
      message: "No se pudo cargar /data/sar_context.json.",
      payload: null,
    };
  }
}

async function loadHydroClimateContext() {
  try {
    const response = await fetch("/data/hydroclimate_context.json");
    if (!response.ok) {
      return {
        status: "missing",
        message:
          "Kairós HydroClimate estará disponible cuando exista /data/hydroclimate_context.json.",
        payload: null,
      };
    }

    return {
      status: "ready",
      message: "",
      payload: normalizeHydroClimatePayload(await response.json()),
    };
  } catch {
    return {
      status: "error",
      message: "No se pudo cargar /data/hydroclimate_context.json.",
      payload: null,
    };
  }
}

async function loadDecisionCases() {
  try {
    const response = await fetch("/data/decision_cases.json");
    if (!response.ok) {
      return {
        status: "missing",
        message:
          "Kairós Cases estará disponible cuando exista /data/decision_cases.json.",
        payload: null,
      };
    }

    return {
      status: "ready",
      message: "",
      payload: normalizeDecisionCasesPayload(await response.json()),
    };
  } catch {
    return {
      status: "error",
      message: "No se pudo cargar /data/decision_cases.json.",
      payload: null,
    };
  }
}

function setPageAndHash(page) {
  const nextHash =
    page === "technical"
      ? "#datos-tecnicos"
      : page === "watch"
        ? "#kairos-watch"
        : page === "cases"
          ? "#kairos-cases"
          : "#decision";
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash;
    return;
  }
}

function getInitialPage() {
  if (typeof window !== "undefined" && window.location.hash === "#datos-tecnicos") {
    return "technical";
  }
  if (typeof window !== "undefined" && window.location.hash === "#kairos-watch") {
    return "watch";
  }
  if (typeof window !== "undefined" && window.location.hash === "#kairos-cases") {
    return "cases";
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
        <button
          className={activePage === "watch" ? "active" : ""}
          type="button"
          onClick={() => setActivePage("watch")}
        >
          Kairós Watch
        </button>
        <button
          className={activePage === "cases" ? "active" : ""}
          type="button"
          onClick={() => setActivePage("cases")}
        >
          Kairós Cases
        </button>
      </nav>

      <p className="run-status">{statusText}</p>
    </header>
  );
}

function DecisionLanding({
  availableDates,
  observations,
  comparisonRecords,
  record,
  ledger,
  hydroClimateContext,
  watchData,
  watchLoadState,
  selectedDate,
  setSelectedDate,
  activeDetailTab,
  setActiveDetailTab,
}) {
  const state = getStateMeta(record);
  const showHydroBadge = isHydroReviewContext(hydroClimateContext);

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

          <div className="decision-content" key={record.date}>
            <div className="decision-word">{state.label}</div>
            <div className="evidence-percent">
              <strong>{formatPercent(record.validPercent)}</strong>
              <span>evidencia válida</span>
            </div>

            <div className="record-facts" aria-label="Metadatos de la observación">
              <span>Fecha: {record.date}</span>
              <span>AOI: {record.aoi}</span>
            </div>

            {showHydroBadge ? (
              <div
                className={`hydro-decision-badge ${hydroStatusTone(
                  hydroClimateContext.hydroclimate_status,
                )}`}
              >
                Lluvia antecedente: revisar contexto territorial.
              </div>
            ) : null}

            <p className="plain-explanation">{state.explanation}</p>

            <div className="next-step-box">
              <span>Qué debe pasar ahora</span>
              <p>{state.nextAction}</p>
            </div>

            <EvidencePassport
              comparisonRecords={comparisonRecords}
              ledger={ledger}
              record={record}
              state={state}
            />
          </div>
        </article>

        <aside className="why-panel instrument-panel">
          <div className="why-copy">
            <p className="small-label">Por qué importa</p>
            <h2>La confianza cambia la decisión.</h2>
            <CompactComparison records={comparisonRecords} />
            <p className="insight-text">
              El sistema no fuerza alertas. Decide cuándo Copernicus puede usarse y
              cuándo no.
            </p>
          </div>
          <ConfidenceThresholdVisual record={record} />
          <TerritorialMap record={record} state={state} />
          <AzueroCorridorEvidenceView
            data={watchData}
            loadState={watchLoadState}
            selectedDate={selectedDate}
          />
        </aside>
      </section>

      <div className="decision-timeline-row">
        <ObservationTimeline
          records={observations}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
        />
      </div>

      <KairosFieldLite record={record} />

      <div className="decision-below-fold">
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
              <SummaryTab record={record} />
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
      </div>
    </>
  );
}

function EvidencePassport({ comparisonRecords, record, ledger, state }) {
  const decisionMessage =
    record.confidence_class === "usable"
      ? "La observación permite interpretación hidro-sedimentaria exploratoria con límites explícitos."
      : "La observación no tiene evidencia válida suficiente para una inferencia responsable.";

  const items = [
    ["Fecha", record.date],
    ["AOI", record.aoi],
    ["Fuente", EVIDENCE_SOURCE],
    ["API status", record.api_status || ledger?.api_status],
    ["Evidencia válida", formatPassportPercent(record.validPercent)],
    ["sampleCount", formatPassportInteger(record.sampleCount)],
    ["noDataCount", formatPassportInteger(record.noDataCount)],
    ["Decisión", `${state.label}: ${state.decision}`],
    ["Regla de umbral", THRESHOLD_RULE],
    ["raw JSON", record.raw_json_path || ledger?.raw_json_path],
    ["processed CSV", ledger?.processed_csv_path],
    ["brief", record.brief_path || ledger?.brief_path],
    ["Ledger", ledger?.evidence_status],
    ["run_id", ledger?.run_id],
    ["commit", ledger?.git_commit],
  ];

  return (
    <section className="evidence-passport" aria-label="Pasaporte de evidencia">
      <div className="evidence-passport-title">
        <span>Pasaporte de evidencia</span>
        <strong>{state.label}</strong>
      </div>

      <p className="evidence-passport-message">
        API OK confirma ejecución técnica; no confirma evidencia suficiente para inferir.
      </p>
      <p className="evidence-passport-message secondary">{decisionMessage}</p>

      <OfficialContrastStrip records={comparisonRecords} />

      <dl className="evidence-passport-grid">
        {items.map(([label, value]) => (
          <div className="evidence-passport-item" key={label}>
            <dt>{label}</dt>
            <dd>{displayValue(value)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function OfficialContrastStrip({ records }) {
  const availableRecords = (records ?? []).filter(Boolean);
  if (availableRecords.length < 2) return null;

  const contrastCopy = {
    "2025-06-10": "2025-06-10 muestra por qué el sistema no debe inferir.",
    "2025-06-30":
      "2025-06-30 muestra una observación usable para interpretación hidro-sedimentaria exploratoria.",
  };

  return (
    <div className="official-contrast-strip" aria-label="Contraste oficial de evidencia">
      <span>Contraste oficial</span>
      <div className="official-contrast-cards">
        {availableRecords.map((contrastRecord) => {
          const contrastState = getStateMeta(contrastRecord);
          return (
            <article
              className={`official-contrast-card tone-${contrastState.tone}`}
              key={contrastRecord.date}
            >
              <div>
                <strong>{contrastRecord.date}</strong>
                <b>{contrastState.label}</b>
              </div>
              <p>{contrastCopy[contrastRecord.date] || contrastState.comparison}</p>
              <em>{formatPercent(contrastRecord.validPercent)} evidencia válida</em>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function AzueroCorridorEvidenceView({ data, loadState, selectedDate }) {
  const ready = loadState.status === "ready" && data;
  const observations = ready ? data.observations ?? [] : [];
  const nodes = useMemo(
    () => orderCorridorNodes(data?.nodes ?? [], observations),
    [data?.nodes, observations],
  );
  const observationMap = useMemo(
    () =>
      new Map(
        observations.map((observation) => [
          `${observation.node_id}|${observation.date}`,
          observation,
        ]),
      ),
    [observations],
  );
  const activeDate = selectedDate || DEFAULT_DATE;
  const selectedRows = nodes
    .map((node) => observationMap.get(`${node.node_id}|${activeDate}`))
    .filter(Boolean);
  const apiOkCount = selectedRows.filter((row) => row.api_status === "OK").length;
  const noInferCount = selectedRows.filter(
    (row) => row.confidence_class === "do_not_infer",
  ).length;
  const evidenceNodeCount = Math.max(selectedRows.length, nodes.length);
  const selectedLabel =
    noInferCount === nodes.length && nodes.length
      ? "NO INFERIR en todo el corredor"
      : noInferCount > 0
        ? "Revisar nodos sin evidencia suficiente"
        : "Contraste usable para lectura exploratoria";
  const apiEvidenceCopy = evidenceNodeCount
    ? `API OK en ${apiOkCount}/${evidenceNodeCount} nodos; eso no basta si la evidencia valida es insuficiente.`
    : "Sin nodos disponibles para resumir la confianza del corredor.";

  if (!ready) {
    return (
      <section className="corridor-evidence-view empty" aria-label="Vista de evidencia del corredor">
        <div className="corridor-heading">
          <div>
            <p className="small-label">Corredor Rio La Villa</p>
            <h3>Azuero corridor evidence view</h3>
          </div>
          <span>representacion esquematica</span>
        </div>
        <p className="corridor-empty-message">
          {loadState.message ||
            "La vista de corredor estara disponible cuando exista kairos_watch.json."}
        </p>
      </section>
    );
  }

  return (
    <section className="corridor-evidence-view" aria-label="Vista de evidencia del corredor Rio La Villa">
      <div className="corridor-heading">
        <div>
          <p className="small-label">Corredor Rio La Villa</p>
          <h3>Azuero corridor evidence view</h3>
        </div>
        <span>representacion esquematica</span>
      </div>

      <div className="corridor-strip-wrap">
        <svg
          className="corridor-strip"
          viewBox="0 0 680 210"
          role="img"
          aria-label={`Representacion esquematica oeste a este del corredor para ${activeDate}`}
        >
          <rect className="corridor-paper" x="1" y="1" width="678" height="208" rx="22" />
          <path
            className="corridor-river-line"
            d="M54 126 C146 74 222 157 330 108 C444 56 514 131 628 82"
          />
          <path
            className="corridor-aoi-band"
            d="M54 145 C151 95 218 174 332 128 C442 85 514 151 628 104"
          />
          {nodes.map((node, index) => {
            const observation = observationMap.get(`${node.node_id}|${activeDate}`);
            const state = getStateMeta(observation);
            const x = 92 + index * 248;
            const y = index === 1 ? 102 : 124;
            return (
              <g className={`corridor-node tone-${state.tone}`} key={node.node_id}>
                <line className="corridor-node-stem" x1={x} x2={x} y1={y + 9} y2="166" />
                <circle className="corridor-node-halo" cx={x} cy={y} r="22" />
                <circle className="corridor-node-dot" cx={x} cy={y} r="8" />
                <text className="corridor-node-name" x={x} y="32">
                  {node.display_name || node.node_id}
                </text>
                <text className="corridor-node-status" x={x} y="57">
                  {observation?.confidence_label_es || state.label}
                </text>
                <text className="corridor-node-percent" x={x} y="186">
                  {observation ? `${formatPercent(observation.validPercent)} valido` : "sin dato"}
                </text>
              </g>
            );
          })}
          <text className="corridor-axis-label west" x="48" y="198">
            oeste
          </text>
          <text className="corridor-axis-label east" x="600" y="198">
            este
          </text>
        </svg>
      </div>

      <div className="corridor-evidence-facts">
        <span>Fecha activa: {activeDate}</span>
        <strong>{selectedLabel}</strong>
        <span>{apiEvidenceCopy}</span>
      </div>

      <div className="corridor-contrast-row" aria-label="Contraste de fechas del corredor">
        {COMPARISON_DATES.map((date) => (
          <CorridorDateContrast
            date={date}
            isActive={date === activeDate}
            key={date}
            nodes={nodes}
            observationMap={observationMap}
          />
        ))}
      </div>

      <p className="corridor-note">
        Esta vista resume confianza de observacion y brechas de evidencia. No es un
        mapa satelital ni una lectura geoespacial exacta.
      </p>
    </section>
  );
}

function CorridorDateContrast({ date, isActive, nodes, observationMap }) {
  const rows = nodes
    .map((node) => observationMap.get(`${node.node_id}|${date}`))
    .filter(Boolean);
  const noInferCount = rows.filter((row) => row.confidence_class === "do_not_infer").length;
  const usableCount = rows.filter((row) => row.confidence_class === "usable").length;
  const tone =
    noInferCount === nodes.length && nodes.length
      ? "stop"
      : usableCount === nodes.length && nodes.length
        ? "usable"
        : "review";

  return (
    <article className={`corridor-contrast-card tone-${tone} ${isActive ? "active" : ""}`}>
      <span>{date}</span>
      <strong>
        {noInferCount === nodes.length && nodes.length
          ? "NO INFERIR"
          : usableCount === nodes.length && nodes.length
            ? "USABLE"
            : "MIXTO"}
      </strong>
      <p>
        {noInferCount ? `${noInferCount} sin evidencia suficiente` : `${usableCount} usables`}
      </p>
    </article>
  );
}

function orderCorridorNodes(nodes, observations) {
  const nodeMap = new Map();
  nodes.forEach((node) => {
    if (node?.node_id) nodeMap.set(node.node_id, node);
  });
  observations.forEach((observation) => {
    if (!observation?.node_id || nodeMap.has(observation.node_id)) return;
    nodeMap.set(observation.node_id, {
      node_id: observation.node_id,
      display_name: observation.node_display_name || observation.node_id,
    });
  });

  const ordered = CORRIDOR_NODE_ORDER.map((nodeId) => nodeMap.get(nodeId)).filter(Boolean);
  if (ordered.length) return ordered;
  return [...nodeMap.values()].sort((a, b) =>
    String(a.display_name ?? a.node_id).localeCompare(String(b.display_name ?? b.node_id)),
  );
}

function KairosFieldLite({ record }) {
  const state = getStateMeta(record);
  const needsVerification =
    record.confidence_class === "do_not_infer" ||
    record.confidence_class === "low_confidence";
  const status = "Verificación territorial recomendada";
  const reason =
    record.confidence_class === "do_not_infer"
      ? "La observación Sentinel no tiene suficiente evidencia válida para una inferencia responsable."
      : "La observación Sentinel tiene evidencia limitada y requiere revisión o verificación territorial.";

  if (!needsVerification) {
    return null;
  }

  const fieldRows = [
    ["Fecha de inspección", "pendiente"],
    ["Responsable / rol", "técnico territorial"],
    ["Coordenadas", "pendiente"],
    ["Condición visible", "pendiente"],
    ["Nota de campo", "pendiente"],
    ["Estado", "pendiente de verificación"],
  ];

  return (
    <section className={`field-lite-section tone-${state.tone}`} aria-label="Kairós Field">
      <div className="field-lite-heading">
        <div>
          <p className="small-label">Kairós Field</p>
          <h2>Kairós Field</h2>
          <p>
            Cuando la evidencia satelital no alcanza, el sistema solicita
            verificación territorial.
          </p>
        </div>
        <span>{status}</span>
      </div>

      <article className="field-lite-card">
        <div className="field-lite-summary">
          <span className="small-label">Workflow territorial</span>
          <h3>{status}</h3>
          <p>{reason}</p>
          <div className="field-lite-meta">
            <span>Fecha: {record.date}</span>
            <span>AOI: {record.aoi}</span>
          </div>
        </div>

        <div className="field-lite-form" aria-label="Formulario demo de verificación">
          <div className="field-lite-grid">
            {fieldRows.map(([label, value]) => (
              <div className="field-lite-item" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>

          <div className="condition-control">
            <div className="condition-control-heading">
              <span>Condiciones visibles a registrar</span>
              <strong>pendiente</strong>
            </div>
            <div className="condition-options" aria-label="Opciones de condición visible">
              {FIELD_CONDITION_OPTIONS.map((option) => (
                <span className="condition-option" key={option}>
                  {option}
                </span>
              ))}
            </div>
          </div>
        </div>

        <p className="field-lite-disclaimer">
          Esta verificación documenta condiciones visibles y contexto territorial.
          No sustituye análisis externo ni decisión de autoridad competente.
        </p>
      </article>
    </section>
  );
}

function ConfidenceThresholdVisual({ record, compact = false }) {
  const state = getStateMeta(record);
  const markerPosition = clampPercentage(record.validPercent);

  return (
    <section
      className={`threshold-visual tone-${state.tone} ${compact ? "compact" : ""}`}
      aria-label="Escala de umbral de confianza"
    >
      <div className="threshold-heading">
        <div>
          <p className="small-label">Umbral de confianza</p>
          <h3>{formatPercent(record.validPercent)} evidencia válida</h3>
        </div>
        <strong>{state.label}</strong>
      </div>

      <div className="threshold-track-wrap">
        <div className="threshold-track" aria-hidden="true">
          <span className="threshold-zone zone-stop" style={{ width: "10%" }} />
          <span className="threshold-zone zone-review" style={{ width: "20%" }} />
          <span className="threshold-zone zone-usable" style={{ width: "70%" }} />
          <span
            className="threshold-marker"
            style={{ left: `${markerPosition}%` }}
          >
            <i />
          </span>
        </div>
        <div className="threshold-boundaries" aria-hidden="true">
          <span>0%</span>
          <span>10%</span>
          <span>30%</span>
          <span>100%</span>
        </div>
        <div className="threshold-labels">
          <span>No inferir</span>
          <span>Revisar</span>
          <span>Usable</span>
        </div>
      </div>

      <p className="threshold-note">
        El umbral mide si la observación tiene suficiente evidencia válida para
        interpretarse.
      </p>
    </section>
  );
}

function ObservationTimeline({ records, selectedDate, setSelectedDate }) {
  const sortedRecords = [...records].sort((left, right) =>
    left.date.localeCompare(right.date),
  );

  return (
    <section className="observation-timeline" aria-label="Línea temporal oficial">
      <div className="timeline-heading">
        <p className="small-label">Observaciones oficiales</p>
        <span>5 fechas Sentinel-2</span>
      </div>
      <div className="timeline-rail">
        {sortedRecords.map((record) => {
          const state = getStateMeta(record);
          const isSelected = record.date === selectedDate;

          return (
            <button
              className={`timeline-point tone-${state.tone} ${
                isSelected ? "active" : ""
              }`}
              key={record.date}
              type="button"
              onClick={() => setSelectedDate(record.date)}
              aria-label={`${record.date}, ${state.label}, ${formatPercent(
                record.validPercent,
              )}`}
            >
              <span className="timeline-dot" aria-hidden="true" />
              <span className="timeline-date">{record.date}</span>
              <strong>{formatPercent(record.validPercent)}</strong>
            </button>
          );
        })}
      </div>
    </section>
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

function SummaryTab({ record }) {
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
        <span className="small-label">Lectura rápida</span>
        <p>
          La decisión resume si la observación Sentinel tiene suficiente evidencia
          válida para interpretarse en el corredor seleccionado.
        </p>
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
        <div className="module-flow" aria-label="Flujo modular Kairós">
          {MODULE_FLOW.map((step, index) => (
            <React.Fragment key={step}>
              <span>{step}</span>
              {index < MODULE_FLOW.length - 1 ? <b aria-hidden="true">→</b> : null}
            </React.Fragment>
          ))}
        </div>
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

function KairosWatch({
  data,
  loadState,
  hydroClimate,
  hydroClimateLoadState,
}) {
  const ready = loadState.status === "ready" && data;
  const nodes = ready ? data.nodes ?? [] : [];
  const dates = ready ? data.dates ?? [] : [];
  const observations = ready ? data.observations ?? [] : [];
  const summaries = ready ? data.summary_by_node ?? [] : [];
  const observationMap = useMemo(
    () =>
      new Map(
        observations.map((observation) => [
          `${observation.node_id}|${observation.date}`,
          observation,
        ]),
      ),
    [observations],
  );

  if (!ready) {
    return (
      <section className="watch-screen" aria-label="Kairós Watch">
        <div className="watch-hero">
          <div>
            <p className="small-label">Kairós Watch</p>
            <h1>Atlas de confianza para Azuero</h1>
            <p>Confianza satelital por subcorredor y fecha.</p>
          </div>
          <article className="watch-empty-card">
            <span>Data regional no disponible</span>
            <p>
              {loadState.message ||
                "Kairós Watch estará disponible cuando se exporte kairos_watch.json."}
            </p>
          </article>
        </div>
      </section>
    );
  }

  return (
    <section className="watch-screen" aria-label="Kairós Watch">
      <div className="watch-hero">
        <div>
          <p className="small-label">Kairós Watch</p>
          <h1>Atlas de confianza para Azuero</h1>
          <p>Confianza satelital por subcorredor y fecha.</p>
        </div>
        <article className="watch-insight-card">
          <span>Lectura regional</span>
          <p>
            El atlas no busca producir alertas constantes. Identifica dónde y
            cuándo la evidencia Copernicus es suficientemente confiable para apoyar
            una decisión.
          </p>
        </article>
      </div>

      <section className="watch-matrix-section" aria-label="Matriz regional de confianza">
        <div className="section-heading compact">
          <div>
            <p className="small-label">Matriz de confianza</p>
            <h2>Subcorredores por fecha</h2>
          </div>
          <p>
            Cada celda resume si la observación Sentinel puede interpretarse,
            revisarse o no inferirse.
          </p>
        </div>

        <div className="watch-matrix-wrap">
          <table className="watch-matrix">
            <thead>
              <tr>
                <th scope="col">Nodo</th>
                {dates.map((date) => (
                  <th scope="col" key={date}>
                    {date}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {nodes.map((node) => (
                <tr key={node.node_id}>
                  <th scope="row">
                    <strong>{node.display_name}</strong>
                    <span>{node.node_id}</span>
                  </th>
                  {dates.map((date) => {
                    const observation = observationMap.get(`${node.node_id}|${date}`);
                    return (
                      <WatchMatrixCell
                        date={date}
                        key={`${node.node_id}-${date}`}
                        observation={observation}
                      />
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <HydroClimateWatchSection
        data={hydroClimate}
        loadState={hydroClimateLoadState}
      />

      <WatchSummaryCards summaries={summaries} />

      <section className="watch-limits" aria-label="Límite científico de Kairós Watch">
        <span>Límite científico</span>
        <p>
          Estos estados miden confianza de observación y brechas de evidencia; no
          sustituyen verificación externa.
        </p>
      </section>
    </section>
  );
}

function HydroClimateWatchSection({ data, loadState }) {
  const ready = loadState.status === "ready" && data;
  if (!ready) {
    return null;
  }

  const observations = [...(data.observations ?? [])].sort(sortHydroObservation);
  if (!observations.length) {
    return null;
  }

  return (
    <section className="hydro-context-section" aria-label="Kairós HydroClimate">
      <div className="section-heading compact">
        <div>
          <p className="small-label">Contexto hidroclimático</p>
          <h2>Kairós HydroClimate</h2>
        </div>
        <p>Contexto de lluvia antecedente para priorizar revisión territorial.</p>
      </div>

      <div className="hydro-context-grid">
        {observations.map((observation) => (
          <article
            className={`hydro-context-card ${hydroStatusTone(
              observation.hydroclimate_status,
            )}`}
            key={`${observation.node_id}-${observation.date}`}
          >
            <div className="hydro-card-top">
              <div>
                <span>{observation.node_display_name || observation.node_id}</span>
                <strong>{observation.date}</strong>
              </div>
            </div>

            <dl className="hydro-rain-grid">
              <div>
                <dt>72h</dt>
                <dd>{formatRainMm(observation.rain_72h_mm)}</dd>
              </div>
              <div>
                <dt>7d</dt>
                <dd>{formatRainMm(observation.rain_7d_mm)}</dd>
              </div>
            </dl>

            <span className="hydro-status-chip">
              {observation.hydroclimate_status || "data_unavailable"}
            </span>
            <p>{observation.recommended_context_action || "Contexto no disponible."}</p>
          </article>
        ))}
      </div>

      <div className="hydro-context-notes">
        <p>{HYDROCLIMATE_INSIGHT}</p>
        <span>{HYDROCLIMATE_LIMITS}</span>
      </div>
    </section>
  );
}

function WatchMatrixCell({ observation, date }) {
  if (!observation) {
    return (
      <td>
        <div className="watch-cell missing">
          <span>{date}</span>
          <strong>Sin dato</strong>
        </div>
      </td>
    );
  }

  const state = getStateMeta(observation);
  return (
    <td>
      <div className={`watch-cell tone-${state.tone}`}>
        <span>{state.label}</span>
        <strong>{formatPercent(observation.validPercent)}</strong>
      </div>
    </td>
  );
}

function WatchSummaryCards({ summaries }) {
  return (
    <section className="watch-summary-section" aria-label="Resumen por nodo">
      <div className="section-heading compact">
        <div>
          <p className="small-label">Resumen por nodo</p>
          <h2>Lectura comparativa del corredor</h2>
        </div>
      </div>
      <div className="watch-summary-grid">
        {summaries.map((summary) => (
          <article className="watch-summary-card" key={summary.node_id}>
            <div className="watch-summary-title">
              <span>{summary.node_id}</span>
              <h3>{summary.display_name}</h3>
            </div>
            <div className="watch-summary-stats">
              <WatchStat label="Total fechas" value={summary.total_dates} />
              <WatchStat label="Usable" value={summary.usable_count} />
              <WatchStat label="Revisar" value={summary.low_confidence_count} />
              <WatchStat label="No inferir" value={summary.do_not_infer_count} />
              <WatchStat
                label="Promedio válido"
                value={formatPercent(summary.mean_validPercent)}
              />
              <WatchStat label="Mejor fecha" value={summary.best_date} />
              <WatchStat label="Peor fecha" value={summary.worst_date} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function WatchStat({ label, value }) {
  return (
    <div className="watch-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function KairosCases({
  data,
  loadState,
  activeCaseId,
  setActiveCaseId,
  casePanelMode,
  setCasePanelMode,
}) {
  const ready = loadState.status === "ready" && data;
  const cases = useMemo(() => {
    if (!ready) return [];
    return [...(data.cases ?? [])].sort(sortDecisionCase);
  }, [data, ready]);
  const summary = ready ? data.summary ?? {} : {};
  const selectedCase =
    cases.find((caseItem) => caseItem.case_id === activeCaseId) ?? cases[0] ?? null;

  function selectCase(caseItem, mode) {
    setActiveCaseId(caseItem.case_id);
    setCasePanelMode(mode);
  }

  if (!ready) {
    return (
      <section className="cases-screen" aria-label="Kairós Cases">
        <div className="cases-hero">
          <div>
            <p className="small-label">Kairós Cases</p>
            <h1>Workflow de decisión territorial</h1>
            <p>{CASES_INSIGHT}</p>
          </div>
          <article className="cases-empty-card">
            <span>Casos no disponibles</span>
            <p>
              {loadState.message ||
                "Kairós Cases estará disponible cuando se exporte decision_cases.json."}
            </p>
          </article>
        </div>
      </section>
    );
  }

  return (
    <section className="cases-screen" aria-label="Kairós Cases">
      <div className="cases-hero">
        <div>
          <p className="small-label">Kairós Cases</p>
          <h1>Workflow de decisión territorial</h1>
          <p>{CASES_INSIGHT}</p>
        </div>
        <article className="cases-insight-card">
          <span>Decision Engine</span>
          <dl>
            <div>
              <dt>Total casos</dt>
              <dd>{summary.total_cases ?? cases.length}</dd>
            </div>
            <div>
              <dt>Verificación</dt>
              <dd>{summary.field_verification_recommended_count ?? 0}</dd>
            </div>
            <div>
              <dt>Brechas</dt>
              <dd>{summary.evidence_gap_count ?? 0}</dd>
            </div>
          </dl>
        </article>
      </div>

      <div className="case-board-layout">
        <section className="case-board-section" aria-label="Tablero de casos">
          <div className="section-heading compact">
            <div>
              <p className="small-label">Case board</p>
              <h2>Acciones recomendadas por nodo y fecha</h2>
            </div>
            <p>Kairós Watch sigue siendo el panorama regional. Este tablero organiza la acción.</p>
          </div>

          <div className="case-card-grid">
            {cases.map((caseItem) => (
              <DecisionCaseCard
                caseItem={caseItem}
                isActive={selectedCase?.case_id === caseItem.case_id}
                key={caseItem.case_id}
                onSelect={selectCase}
              />
            ))}
          </div>
        </section>

        <CaseActionPanel caseItem={selectedCase} mode={casePanelMode} />
      </div>

      <section className="cases-limit-note" aria-label="Límite científico de Kairós Cases">
        <span>Firewall de claims</span>
        <p>
          {data.claim_firewall ||
            "No hace afirmaciones químicas, sanitarias, de aptitud de uso ni de respuesta institucional."}
        </p>
      </section>
    </section>
  );
}

function DecisionCaseCard({ caseItem, isActive, onSelect }) {
  const tone = decisionCaseTone(caseItem);
  const verificationEnabled = canRequestVerification(caseItem);

  return (
    <article className={`case-card tone-${tone} ${isActive ? "active" : ""}`}>
      <div className="case-card-top">
        <div>
          <span>{caseItem.node_display_name || caseItem.node_id}</span>
          <strong>{caseItem.date}</strong>
        </div>
        <b className="case-priority-pill">{caseItem.priority_level || "normal"}</b>
      </div>

      <div className="case-label-row">
        <span className={`case-label tone-${tone}`}>{caseItem.decision_label}</span>
        <span>{formatCasePercent(caseItem.primary_validPercent)} válido</span>
      </div>

      <div className="case-meta-grid">
        <CaseFact label="Workflow" value={caseItem.recommended_workflow} />
        <CaseFact label="Verificación" value={caseItem.field_verification_status} />
        <CaseFact label="Laboratorio" value={caseItem.lab_escalation_status} />
      </div>

      <div className="case-gap-box">
        <span>Brechas de evidencia</span>
        <ul>
          {splitEvidenceGaps(caseItem.evidence_gaps).map((gap) => (
            <li key={gap}>{gap}</li>
          ))}
        </ul>
      </div>

      <div className="case-actions" aria-label="Acciones del caso">
        <button type="button" onClick={() => onSelect(caseItem, "evidence")}>
          Ver evidencia
        </button>
        <button type="button" onClick={() => onSelect(caseItem, "brief")}>
          Ver brief compacto
        </button>
        <button
          type="button"
          disabled={!verificationEnabled}
          title={
            verificationEnabled
              ? "Abre una vista de solicitud sin guardar datos."
              : "Disponible solo para NO INFERIR o REVISAR."
          }
          onClick={() => onSelect(caseItem, "verification")}
        >
          Solicitar verificación
        </button>
        <button type="button" disabled title={LAB_ESCALATION_COPY}>
          Escalar a laboratorio
        </button>
      </div>
      <p className="case-lab-copy">{LAB_ESCALATION_COPY}</p>
    </article>
  );
}

function CaseActionPanel({ caseItem, mode }) {
  if (!caseItem) {
    return (
      <aside className="case-action-panel">
        <span>Seleccione un caso</span>
        <p>No hay casos de decisión disponibles.</p>
      </aside>
    );
  }

  if (mode === "brief") {
    return (
      <aside className="case-action-panel" aria-label="Vista de brief de confianza">
        <span>Brief compacto</span>
        <h3>{caseItem.decision_label}: {caseItem.node_display_name}</h3>
        <div className="case-brief-preview">
          <p>{caseItem.decision_action}</p>
          <p>{caseItem.recommended_workflow}</p>
        </div>
        <dl className="case-panel-facts">
          <CaseDataPair label="Fecha" value={caseItem.date} />
          <CaseDataPair label="Prioridad" value={caseItem.priority_level} />
          <CaseDataPair label="Campo" value={caseItem.field_verification_status} />
        </dl>
        <p className="case-panel-limit">{caseItem.claim_firewall}</p>
      </aside>
    );
  }

  if (mode === "verification") {
    return (
      <aside className="case-action-panel" aria-label="Solicitud de verificación">
        <span>Verificación territorial</span>
        <h3>Solicitud preparada, no persistida</h3>
        <p>
          Este flujo documenta que el caso requiere revisión territorial. No guarda
          datos, no abre backend y no reemplaza la autoridad técnica.
        </p>
        <dl className="case-panel-facts">
          <CaseDataPair label="Nodo" value={caseItem.node_display_name || caseItem.node_id} />
          <CaseDataPair label="Fecha" value={caseItem.date} />
          <CaseDataPair label="Estado" value={caseItem.field_verification_status} />
          <CaseDataPair label="Laboratorio" value={caseItem.lab_escalation_status} />
        </dl>
        <p className="case-panel-limit">{LAB_ESCALATION_COPY}</p>
      </aside>
    );
  }

  return (
    <aside className="case-action-panel" aria-label="Evidencia del caso">
      <span>Evidencia del caso</span>
      <h3>{caseItem.node_display_name || caseItem.node_id}</h3>
      <dl className="case-panel-facts">
        <CaseDataPair label="Fecha" value={caseItem.date} />
        <CaseDataPair
          label="Sentinel-2"
          value={`${caseItem.primary_confidence_class || "pendiente"} · ${formatCasePercent(
            caseItem.primary_validPercent,
          )}`}
        />
        <CaseDataPair label="Exposure" value={caseItem.exposure_status} />
        <CaseDataPair label="HydroClimate" value={caseItem.hydroclimate_status} />
        <CaseDataPair label="Ledger" value={caseItem.ledger_status} />
      </dl>
      <div className="case-panel-gaps">
        <strong>Brechas</strong>
        <ul>
          {splitEvidenceGaps(caseItem.evidence_gaps).map((gap) => (
            <li key={gap}>{gap}</li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

function CaseFact({ label, value }) {
  return (
    <div className="case-fact">
      <span>{label}</span>
      <strong>{value || "pendiente"}</strong>
    </div>
  );
}

function CaseDataPair({ label, value }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value || "pendiente"}</dd>
    </div>
  );
}

function TechnicalDashboard({
  availableDates,
  comparisonRecords,
  record,
  ledger,
  selectedDate,
  setSelectedDate,
  sarContext,
  sarLoadState,
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

      <ConfidenceThresholdVisual record={record} compact />
      <TerritorialMap record={record} state={state} variant="technical" />
      <ComparisonSection records={comparisonRecords} />
      <MetricsSection record={record} />
      <SarTechnicalNote data={sarContext} loadState={sarLoadState} />
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

function SarTechnicalNote({ data, loadState }) {
  const ready = loadState.status === "ready" && data;
  const note = ready
    ? data.claim_limit || SAR_LIMITS
    : "Sentinel-1 SAR no está disponible en este corte y no se usa como evidencia principal.";
  return (
    <p className="sar-technical-note" aria-label="Nota técnica Sentinel-1 SAR">
      {note}
    </p>
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

function findHydroContextForRecord(payload, record) {
  const observations = Array.isArray(payload?.observations)
    ? payload.observations
    : [];
  const sameDateRows = observations.filter((row) => row.date === record.date);
  const exactNodeRows = sameDateRows.filter(
    (row) => row.node_id === record.aoi || row.node_display_name === record.aoi,
  );
  const candidates = exactNodeRows.length ? exactNodeRows : sameDateRows;
  return (
    candidates
      .filter(isHydroReviewContext)
      .sort((a, b) => hydroContextScore(b) - hydroContextScore(a))[0] ?? null
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

function normalizeWatchPayload(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    ...payload,
    nodes: Array.isArray(payload.nodes)
      ? payload.nodes.map(normalizeRecord)
      : [],
    dates: Array.isArray(payload.dates)
      ? payload.dates.map((date) =>
          typeof date === "string" ? repairMojibake(date) : date,
        )
      : [],
    observations: Array.isArray(payload.observations)
      ? payload.observations.map(normalizeRecord)
      : [],
    summary_by_node: Array.isArray(payload.summary_by_node)
      ? payload.summary_by_node.map(normalizeRecord)
      : [],
  };
}

function normalizeSarPayload(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    ...payload,
    nodes: Array.isArray(payload.nodes)
      ? payload.nodes.map(normalizeRecord)
      : [],
    dates: Array.isArray(payload.dates)
      ? payload.dates.map((date) =>
          typeof date === "string" ? repairMojibake(date) : date,
        )
      : [],
    observations: Array.isArray(payload.observations)
      ? payload.observations.map(normalizeRecord)
      : [],
    summary_by_node: Array.isArray(payload.summary_by_node)
      ? payload.summary_by_node.map(normalizeRecord)
      : [],
  };
}

function normalizeHydroClimatePayload(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    ...payload,
    nodes: Array.isArray(payload.nodes)
      ? payload.nodes.map(normalizeRecord)
      : [],
    dates: Array.isArray(payload.dates)
      ? payload.dates.map((date) =>
          typeof date === "string" ? repairMojibake(date) : date,
        )
      : [],
    observations: Array.isArray(payload.observations)
      ? payload.observations.map(normalizeRecord)
      : [],
    summary_by_node: Array.isArray(payload.summary_by_node)
      ? payload.summary_by_node.map(normalizeRecord)
      : [],
  };
}

function normalizeDecisionCasesPayload(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    ...payload,
    claim_firewall:
      typeof payload.claim_firewall === "string"
        ? repairMojibake(payload.claim_firewall)
        : payload.claim_firewall,
    decision_principle:
      typeof payload.decision_principle === "string"
        ? repairMojibake(payload.decision_principle)
        : payload.decision_principle,
    nodes: Array.isArray(payload.nodes)
      ? payload.nodes.map(normalizeRecord)
      : [],
    dates: Array.isArray(payload.dates)
      ? payload.dates.map((date) =>
          typeof date === "string" ? repairMojibake(date) : date,
        )
      : [],
    cases: Array.isArray(payload.cases)
      ? payload.cases.map(normalizeRecord)
      : [],
    summary:
      payload.summary && typeof payload.summary === "object"
        ? normalizeRecord(payload.summary)
        : {},
  };
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

function formatRainMm(value) {
  if (value === undefined || value === null || value === "") return "sin dato";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "sin dato";
  return `${formatNumber(numeric, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} mm`;
}

function isHydroReviewContext(row) {
  const status = row?.hydroclimate_status;
  return status === "heavy_rain_context" || status === "antecedent_rain";
}

function hydroContextScore(row) {
  const status = row?.hydroclimate_status;
  const severity =
    status === "heavy_rain_context" ? 3 : status === "antecedent_rain" ? 2 : 0;
  return severity * 10000 + Number(row?.rain_7d_mm ?? 0);
}

function hydroStatusTone(status) {
  if (status === "heavy_rain_context") return "heavy";
  if (status === "antecedent_rain") return "antecedent";
  if (status === "data_unavailable") return "unavailable";
  if (status === "dry_or_low_rain") return "dry";
  return "normal";
}

function sortHydroObservation(a, b) {
  const nodeCompare = String(a.node_id ?? "").localeCompare(String(b.node_id ?? ""));
  if (nodeCompare !== 0) return nodeCompare;
  return String(a.date ?? "").localeCompare(String(b.date ?? ""));
}

function sortDecisionCase(a, b) {
  const priorityCompare = decisionPriorityRank(a) - decisionPriorityRank(b);
  if (priorityCompare !== 0) return priorityCompare;
  const dateCompare = String(a.date ?? "").localeCompare(String(b.date ?? ""));
  if (dateCompare !== 0) return dateCompare;
  return String(a.node_id ?? "").localeCompare(String(b.node_id ?? ""));
}

function decisionPriorityRank(caseItem) {
  const label = String(caseItem?.decision_label ?? "").toUpperCase();
  if (label === "NO INFERIR") return 0;
  if (label === "REVISAR") return 1;
  const priority = String(caseItem?.priority_level ?? "").toLowerCase();
  if (priority === "alta") return 2;
  if (priority === "media-alta") return 3;
  if (priority === "media") return 4;
  return 5;
}

function decisionCaseTone(caseItem) {
  const label = String(caseItem?.decision_label ?? "").toUpperCase();
  if (label === "NO INFERIR") return "stop";
  if (label === "REVISAR") return "review";
  return "usable";
}

function canRequestVerification(caseItem) {
  const label = String(caseItem?.decision_label ?? "").toUpperCase();
  return label === "NO INFERIR" || label === "REVISAR";
}

function splitEvidenceGaps(value) {
  if (!value) return ["Sin brechas registradas."];
  return String(value)
    .split("|")
    .map((gap) => gap.trim())
    .filter(Boolean);
}

function formatCasePercent(value) {
  if (value === undefined || value === null || value === "") return "pendiente";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  return formatPercent(numeric);
}

function formatNumber(value, options) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return new Intl.NumberFormat("es-PA", options).format(Number(value));
}

function displayValue(value) {
  if (value === undefined || value === null || value === "") return "no disponible";
  return String(value);
}

function formatPassportPercent(value) {
  if (value === undefined || value === null || value === "") return null;
  return formatPercent(value);
}

function formatPassportInteger(value) {
  if (value === undefined || value === null || value === "") return null;
  return formatInteger(value);
}

function clampPercentage(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.min(100, Math.max(0, numeric));
}
