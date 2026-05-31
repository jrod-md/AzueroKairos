import React, { useEffect, useMemo, useState } from "react";
import StatusBar from "./components/StatusBar/StatusBar.jsx";
import DecisionStamp from "./components/DecisionStamp/DecisionStamp.jsx";
import DecisionPage from "./pages/Decision/DecisionPage.jsx";
import EvidenciaPage from "./pages/Evidencia/EvidenciaPage.jsx";
import PassportPage from "./pages/Passport/PassportPage.jsx";

const DEFAULT_DATE = "2025-06-10";
const COMPARISON_DATES = ["2025-06-10", "2025-06-30"];
const CORRIDOR_NODE_ORDER = [
  "la_villa_oeste",
  "la_villa_central",
  "la_villa_este",
];

const NAV_ITEMS = [
  { id: "system", label: "Sistema" },
  { id: "impact", label: "Impacto" },
  { id: "decision", label: "Decisión" },
  { id: "watch", label: "Corredor" },
  { id: "cases", label: "Acción" },
  { id: "passport", label: "Passport" },
  { id: "technical", label: "Evidencia" },
];

const KAIROS_CYCLE_STEPS = [
  {
    id: "observa",
    label: "Observa",
    proof: "Copernicus CDSE",
    text: "Registra escenas Sentinel-2 oficiales para el corredor piloto.",
  },
  {
    id: "calibra",
    label: "Calibra",
    proof: "ValidPercent",
    text: "Mide si la escena tiene evidencia válida suficiente antes de interpretar.",
  },
  {
    id: "decide",
    label: "Decide",
    proof: "USABLE / NO INFERIR",
    text: "Convierte calidad de observación en una decisión proporcional.",
  },
  {
    id: "contextualiza",
    label: "Contextualiza",
    proof: "SAR / CLMS / HYDRO",
    text: "Agrega capas auxiliares sin cambiar la clasificación primaria.",
  },
  {
    id: "prioriza",
    label: "Prioriza",
    proof: "Cola de casos",
    text: "Ordena revisión y verificación territorial según brecha de evidencia.",
  },
  {
    id: "verifica",
    label: "Verifica",
    proof: "Campo / autoridad",
    text: "Separa observación visible, laboratorio y autoridad competente.",
  },
  {
    id: "emite",
    label: "Emite",
    proof: "Passport",
    text: "Prepara un comprobante de confianza con decisión, hashes y límites.",
  },
  {
    id: "audita",
    label: "Audita",
    proof: "Ledger",
    text: "Conserva trazabilidad desde JSON crudo hasta auditoría de evidencia.",
  },
];

const IMPACT_CONTRAST_DATES = {
  weak: "2025-06-10",
  usable: "2025-06-30",
};

const WORKBENCH_LAYERS = [
  { id: "s2", label: "S-2 DECISIÓN" },
  { id: "sar", label: "S-1 SAR" },
  { id: "clms", label: "CLMS" },
  { id: "hydro", label: "HYDRO" },
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

const CASES_INSIGHT =
  "Cada caso traduce capas de evidencia en una acción responsable.";

const LAB_ESCALATION_COPY =
  "Requiere verificación territorial o autoridad competente.";

export default function App() {
  const [observations, setObservations] = useState([]);
  const [ledgerRows, setLedgerRows] = useState([]);
  const [watchData, setWatchData] = useState(null);
  const [sarContext, setSarContext] = useState(null);
  const [hydroClimate, setHydroClimate] = useState(null);
  const [decisionCases, setDecisionCases] = useState(null);
  const [exposureContext, setExposureContext] = useState(null);
  const [selectedDate, setSelectedDate] = useState(DEFAULT_DATE);
  const [activePage, setActivePage] = useState(getInitialPage);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [casePanelMode, setCasePanelMode] = useState("evidence");
  const [workbenchNodeId, setWorkbenchNodeId] = useState(CORRIDOR_NODE_ORDER[0]);
  const [workbenchLayer, setWorkbenchLayer] = useState("s2");
  const [decisionBarVisible, setDecisionBarVisible] = useState(false);
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
  const [exposureLoadState, setExposureLoadState] = useState({
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
          exposureResult,
        ] = await Promise.all([
          fetch("/data/observations.json"),
          fetch("/data/evidence_ledger.json"),
          loadWatchData(),
          loadSarContext(),
          loadHydroClimateContext(),
          loadDecisionCases(),
          loadExposureContext(),
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
        setExposureContext(exposureResult.payload);
        setExposureLoadState({
          status: exposureResult.status,
          message: exposureResult.message,
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
          message: "No se pudo cargar Corredor.",
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
          message: "No se pudo cargar Accion.",
        });
        setExposureLoadState({
          status: "error",
          message: "Contexto CLMS no disponible para esta demo.",
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

  useEffect(() => {
    let frame = 0;

    function handleScroll() {
      if (frame) window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => {
        setDecisionBarVisible(window.scrollY > 150);
      });
    }

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      if (frame) window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const selectedRecord = useMemo(() => {
    return (
      observations.find((record) => record.date === selectedDate) ??
      observations[0] ??
      null
    );
  }, [observations, selectedDate]);

  const selectedLedgerRows = useMemo(() => {
    if (!selectedRecord) return [];
    return findLedgerRowsForRecord(ledgerRows, selectedRecord);
  }, [ledgerRows, selectedRecord]);

  const selectedLedger = useMemo(
    () => (selectedRecord ? findLedgerForRecord(ledgerRows, selectedRecord) : null),
    [ledgerRows, selectedRecord],
  );

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

  const impactMetrics = useMemo(
    () =>
      buildImpactMetrics({
        observations,
        ledgerRows,
        watchData,
        sarContext,
        hydroClimate,
        decisionCases,
        exposureContext,
      }),
    [
      observations,
      ledgerRows,
      watchData,
      sarContext,
      hydroClimate,
      decisionCases,
      exposureContext,
    ],
  );

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
  const selectedState = getStateMeta(selectedRecord);

  return (
    <main className="app-shell">
      <StatusBar activeState={selectedState.label} />
      <Header
        activePage={activePage}
        activeState={selectedState.label}
        setActivePage={setPageAndHash}
      />

      <StickyDecisionBar
        ledger={selectedLedger}
        onOpenEvidence={() => setPageAndHash("technical")}
        record={selectedRecord}
        state={selectedState}
        visible={decisionBarVisible}
      />

      {activePage === "system" ? (
        <KairosCycle metrics={impactMetrics} onNavigate={setPageAndHash} />
      ) : activePage === "impact" ? (
        <ImpactLab metrics={impactMetrics} />
      ) : activePage === "decision" ? (
        <DecisionPage
          observations={observations}
          comparisonRecords={comparisonRecords}
          record={selectedRecord}
          ledger={selectedLedger}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
        />
      ) : activePage === "watch" ? (
        <CorredorWorkbench
          data={watchData}
          exposureContext={exposureContext}
          hydroClimate={hydroClimate}
          loadState={watchLoadState}
          onNavigate={setPageAndHash}
          sarContext={sarContext}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          selectedLayer={workbenchLayer}
          selectedNodeId={workbenchNodeId}
          setSelectedLayer={setWorkbenchLayer}
          setSelectedNodeId={setWorkbenchNodeId}
        />
      ) : activePage === "cases" ? (
        <KairosCases
          data={decisionCases}
          loadState={decisionCasesLoadState}
          activeCaseId={activeCaseId}
          setActiveCaseId={setActiveCaseId}
          casePanelMode={casePanelMode}
          setCasePanelMode={setCasePanelMode}
          exposureContext={exposureContext}
        />
      ) : activePage === "passport" ? (
        <PassportPage
          availableDates={availableDates}
          decisionCases={decisionCases}
          ledger={selectedLedger}
          ledgerRows={selectedLedgerRows}
          onNavigate={setPageAndHash}
          record={selectedRecord}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
        />
      ) : (
        <EvidenciaPage
          availableDates={availableDates}
          comparisonRecords={comparisonRecords}
          record={selectedRecord}
          ledger={selectedLedger}
          ledgerRows={ledgerRows}
          hydroClimateContext={selectedHydroClimateContext}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          sarContext={sarContext}
          sarLoadState={sarLoadState}
          exposureContext={exposureContext}
          exposureLoadState={exposureLoadState}
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
          "Corredor estara disponible cuando exista /data/kairos_watch.json.",
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
          "Accion estara disponible cuando exista /data/decision_cases.json.",
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

async function loadExposureContext() {
  try {
    const response = await fetch("/data/exposure_context.json");
    if (!response.ok) {
      return {
        status: "missing",
        message: "Contexto CLMS no disponible para esta demo.",
        payload: null,
      };
    }

    return {
      status: "ready",
      message: "",
      payload: normalizeExposurePayload(await response.json()),
    };
  } catch {
    return {
      status: "error",
      message: "Contexto CLMS no disponible para esta demo.",
      payload: null,
    };
  }
}

function setPageAndHash(page) {
  const nextHash =
    page === "system"
      ? "#sistema"
      : page === "decision"
      ? "#decision"
      : page === "impact"
      ? "#impacto"
      : page === "technical"
      ? "#evidencia"
      : page === "passport"
      ? "#passport"
      : page === "watch"
        ? "#corredor"
        : page === "cases"
          ? "#accion"
        : "#sistema";
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash;
    return;
  }
}

function getInitialPage() {
  const hash =
    typeof window !== "undefined" ? window.location.hash.toLowerCase() : "";
  if (hash === "" || hash === "#sistema" || hash === "#ciclo") {
    return "system";
  }
  if (hash === "#decision" || hash === "#decision-ejecutiva") {
    return "decision";
  }
  if (hash === "#impacto" || hash === "#impact") {
    return "impact";
  }
  if (hash === "#datos-tecnicos" || hash === "#technical" || hash === "#evidencia") {
    return "technical";
  }
  if (hash === "#passport" || hash === "#pasaporte") {
    return "passport";
  }
  if (hash === "#kairos-watch" || hash === "#corredor") {
    return "watch";
  }
  if (hash === "#kairos-cases" || hash === "#accion") {
    return "cases";
  }
  return "system";
}

function Header({ activePage, activeState, setActivePage }) {
  const normalizedState = String(activeState ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  return (
    <header className="top-nav">
      <button
        className="brand-button"
        type="button"
        onClick={() => setActivePage("system")}
        aria-label="Ir al ciclo Kairós"
      >
        Azuero Kairós
      </button>

      <nav
        className="az-navigation"
        aria-label="Navegación principal"
        data-active-state={normalizedState}
      >
        <div className="az-navigation__pill">
          <div className="az-navigation__tabs">
            {NAV_ITEMS.map((item) => (
              <button
                className={`az-navigation__tab${
                  activePage === item.id ? " is-active" : ""
                }`}
                key={item.id}
                onClick={() => setActivePage(item.id)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="az-navigation__status" aria-label="Estado oficial del ledger">
            <span className="az-navigation__dot" aria-hidden="true" />
            <span>COPERNICUS OFICIAL · LEDGER OK</span>
          </div>
        </div>
      </nav>
    </header>
  );
}

function KairosCycle({ metrics, onNavigate }) {
  const proofCards = [
    {
      label: "Contraste piloto",
      value: `${formatMultiplier(metrics.evidenceUpliftRatio)}x`,
      text: "Más evidencia válida al esperar una adquisición usable.",
    },
    {
      label: "Escenas oficiales",
      value: `${metrics.apiOkBlockedCount}/${metrics.officialObservationCount}`,
      text: "API OK bloqueada de inferencia cuando la evidencia no alcanza.",
    },
    {
      label: "Corredor regional",
      value: `${metrics.nodeCount} x ${metrics.dateCount}`,
      text: `${metrics.regionalObservationCount} observaciones nodo-fecha en la matriz pública.`,
    },
    {
      label: "Ledger público",
      value: formatInteger(metrics.ledgerEventCount),
      text: "Eventos trazables desde evidencia cruda hasta decisión.",
    },
  ];
  const auxiliaryRows = [
    ["SAR", metrics.auxiliaryCoverage.sar],
    ["CLMS", metrics.auxiliaryCoverage.clms],
    ["HydroClimate", metrics.auxiliaryCoverage.hydro],
  ];
  const routeButtons = [
    ["Impacto", "impact"],
    ["Decisión", "decision"],
    ["Corredor", "watch"],
    ["Acción", "cases"],
    ["Passport", "passport"],
    ["Evidencia", "technical"],
  ];

  return (
    <section className="kairos-system" aria-label="Sistema Kairós">
      <div className="kairos-system__hero">
        <div className="kairos-system__copy">
          <p className="small-label">Sistema Kairós</p>
          <h1>Ciclo de evidencia responsable.</h1>
          <p>
            Del satélite a la decisión: interpretar, revisar o no inferir según
            la evidencia disponible.
          </p>
          <div className="kairos-system__actions" aria-label="Entradas del sistema">
            {routeButtons.map(([label, page]) => (
              <button key={page} type="button" onClick={() => onNavigate(page)}>
                {label}
              </button>
            ))}
          </div>
        </div>

        <aside className="kairos-system__pilot" aria-label="Caso piloto Río La Villa">
          <div className="kairos-system__pilot-photo" aria-hidden="true" />
          <div className="kairos-system__pilot-facts">
            <span>Río La Villa</span>
            <strong>{metrics.nodeCount} nodos, {metrics.dateCount} fechas</strong>
            <p>
              Una escena con API OK y {formatMaybePercent(metrics.weakContrast?.validPercent)}
              {" "}de evidencia válida fue bloqueada de inferencia.
            </p>
          </div>
        </aside>
      </div>

      <section className="kairos-system__proof" aria-label="Prueba del ciclo">
        {proofCards.map((card) => (
          <article className="kairos-proof-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.text}</p>
          </article>
        ))}
      </section>

      <section className="kairos-cycle-board" aria-label="Ciclo operativo">
        <div className="kairos-cycle-board__head">
          <p className="small-label">Ciclo operativo</p>
          <h2>La evidencia entra solo si cambia decisión, prioridad o incertidumbre.</h2>
        </div>
        <ol className="kairos-cycle-list">
          {KAIROS_CYCLE_STEPS.map((step, index) => (
            <li className={`kairos-cycle-step step-${step.id}`} key={step.id}>
              <span className="kairos-cycle-step__index">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <strong>{step.label}</strong>
                <em>{step.proof}</em>
                <p>{step.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="kairos-system__ledger" aria-label="Cobertura y límites">
        <div className="kairos-ledger-copy">
          <p className="small-label">Frontera científica</p>
          <h2>No inferir es una salida válida del sistema.</h2>
          <p>
            Kairós no detecta contaminación ni declara agua segura. Produce una
            decisión de confianza de observación y deja la cadena lista para
            auditoría, verificación territorial o autoridad competente.
          </p>
        </div>
        <dl className="kairos-aux-ledger">
          {auxiliaryRows.map(([label, coverage]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>
                {coverage.available}/{coverage.total}
              </dd>
            </div>
          ))}
          <div>
            <dt>Casos curados</dt>
            <dd>{metrics.decisionCaseCount}</dd>
          </div>
        </dl>
      </section>
    </section>
  );
}

function ImpactLab({ metrics }) {
  const [badInferenceCostUnits, setBadInferenceCostUnits] = useState(100);
  const [verificationCostUnits, setVerificationCostUnits] = useState(22);
  const criticalCases = metrics.regionalReviewCount;
  const baselineRiskUnits = criticalCases * Number(badInferenceCostUnits || 0);
  const kairosReviewUnits = criticalCases * Number(verificationCostUnits || 0);
  const relativeExposureReductionPercent =
    baselineRiskUnits > 0
      ? ((baselineRiskUnits - kairosReviewUnits) / baselineRiskUnits) * 100
      : 0;

  const realMetricCards = [
    {
      label: "EVIDENCIA VALIDADA",
      value: `${formatMultiplier(metrics.evidenceUpliftRatio)}x`,
      text: `${formatMultiplier(
        metrics.evidenceUpliftRatio,
      )}x más evidencia válida al esperar una adquisición usable.`,
    },
    {
      label: "API OK NO BASTA",
      value: `${metrics.apiOkBlockedCount} de ${metrics.officialObservationCount}`,
      text: `${metrics.apiOkBlockedCount} de ${
        metrics.officialObservationCount
      } observaciones oficiales ${
        metrics.apiOkBlockedCount === 1 ? "bloqueada" : "bloqueadas"
      } de inferencia aunque la API estaba OK`,
    },
    {
      label: "CARGA REGIONAL",
      value: `${metrics.regionalReviewCount} de ${metrics.regionalObservationCount}`,
      text: `${metrics.regionalReviewCount} de ${
        metrics.regionalObservationCount
      } casos regionales ${
        metrics.regionalReviewCount === 1 ? "enviado" : "enviados"
      } a revisión antes de interpretación`,
    },
  ];

  return (
    <section className="impact-lab" aria-label="Kairós Impact Lab">
      <div className="impact-hero">
        <div className="impact-hero__copy">
          <p className="small-label">Kairós Impact Lab</p>
          <h1>Impacto del piloto: evitar inferencias débiles, no prometer certezas falsas.</h1>
          <p>API OK no basta: Kairós exige evidencia válida antes de interpretar.</p>
        </div>

        <article className="impact-hero__instrument" aria-label="Evidencia valida al esperar">
          <span>Contraste oficial Sentinel-2</span>
          <strong>{formatMultiplier(metrics.evidenceUpliftRatio)}x</strong>
          <p>más evidencia válida al esperar una adquisición usable.</p>
          <dl>
            <div>
              <dt>{metrics.weakContrast?.date || IMPACT_CONTRAST_DATES.weak}</dt>
              <dd>{formatMaybePercent(metrics.weakContrast?.validPercent)}</dd>
            </div>
            <div>
              <dt>{metrics.usableContrast?.date || IMPACT_CONTRAST_DATES.usable}</dt>
              <dd>{formatMaybePercent(metrics.usableContrast?.validPercent)}</dd>
            </div>
          </dl>
        </article>
      </div>

      <div className="impact-pilot-grid" aria-label="Caso piloto">
        <article className="impact-pilot-panel">
          <p className="small-label">Caso piloto</p>
          <h2>Río La Villa, Azuero, Panamá</h2>
          <ul>
            <li>{metrics.nodeCount} nodos</li>
            <li>{metrics.dateCount} fechas Sentinel-2</li>
            <li>{metrics.regionalObservationCount} observaciones regionales</li>
            <li>Contraste crítico: 2025-06-10 vs 2025-06-30</li>
          </ul>
        </article>

        <div className="impact-metric-grid">
          {realMetricCards.map((card) => (
            <article className="impact-metric-card" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <p>{card.text}</p>
            </article>
          ))}
        </div>
      </div>

      <section className="impact-contrast-panel" aria-label="Contraste oficial">
        <div className="impact-section-heading">
          <p className="small-label">Contraste oficial</p>
          <h2>La diferencia no es la API, es la evidencia válida.</h2>
        </div>
        <div className="impact-contrast-grid">
          <ImpactContrastCard
            label="Bloqueo responsable"
            record={metrics.weakContrast}
            fallbackDate={IMPACT_CONTRAST_DATES.weak}
          />
          <ImpactContrastCard
            label="Adquisición usable"
            record={metrics.usableContrast}
            fallbackDate={IMPACT_CONTRAST_DATES.usable}
          />
        </div>
      </section>

      <section className="impact-aux-strip" aria-label="Cobertura auxiliar">
        <div>
          <p className="small-label">Cobertura auxiliar</p>
          <h2>Contexto disponible, no motor de decisión.</h2>
        </div>
        <ImpactCoverageItem label="SAR" coverage={metrics.auxiliaryCoverage.sar} />
        <ImpactCoverageItem label="CLMS" coverage={metrics.auxiliaryCoverage.clms} />
        <ImpactCoverageItem label="HydroClimate" coverage={metrics.auxiliaryCoverage.hydro} />
      </section>

      <section className="impact-simulation" aria-label="Simulación de sensibilidad">
        <div className="impact-section-heading">
          <p className="small-label">Opcional</p>
          <h2>Simulación de sensibilidad: costo relativo de inferir mal</h2>
          <p>
            Simulación, no resultado medido. Los supuestos pueden ajustarse. No estima
            pérdidas agrícolas reales; estima exposición relativa a decisiones basadas en
            evidencia insuficiente.
          </p>
        </div>

        <div className="impact-calculator">
          <label>
            <span>Costo relativo de inferir mal</span>
            <input
              min="0"
              onChange={(event) => setBadInferenceCostUnits(Number(event.target.value))}
              type="number"
              value={badInferenceCostUnits}
            />
          </label>
          <label>
            <span>Costo relativo de verificación</span>
            <input
              min="0"
              onChange={(event) => setVerificationCostUnits(Number(event.target.value))}
              type="number"
              value={verificationCostUnits}
            />
          </label>
          <div className="impact-formula-card">
            <span>Casos críticos regionales</span>
            <strong>{criticalCases}</strong>
          </div>
          <div className="impact-formula-card primary">
            <span>Reducción relativa simulada</span>
            <strong>{formatPercent(relativeExposureReductionPercent)}</strong>
          </div>
        </div>

        <code className="impact-formula">
          (({formatInteger(baselineRiskUnits)} - {formatInteger(kairosReviewUnits)}) /{" "}
          {formatInteger(baselineRiskUnits)}) * 100
        </code>
      </section>

      <aside className="impact-limits-strip">
        <strong>Límites del impacto público</strong>
        <p>
          Kairós reporta límites de evidencia, no resultados territoriales medidos ni
          acciones obligatorias. La pantalla muestra cuándo la evidencia Sentinel-2 sostiene
          o bloquea una interpretación responsable.
        </p>
      </aside>
    </section>
  );
}

function ImpactContrastCard({ label, record, fallbackDate }) {
  const state = getStateMeta(record ?? { confidence_class: "do_not_infer" });

  return (
    <article className={`impact-contrast-card tone-${state.tone}`}>
      <span>{label}</span>
      <h3>{record?.date || fallbackDate}</h3>
      <strong>{formatMaybePercent(record?.validPercent)}</strong>
      <p>{record?.confidence_label_es || state.label}</p>
    </article>
  );
}

function ImpactCoverageItem({ label, coverage }) {
  return (
    <article className="impact-coverage-item">
      <span>{label}</span>
      <strong>
        {coverage.available}/{coverage.total}
      </strong>
      <p>{coverage.note}</p>
    </article>
  );
}

function CorredorWorkbench({
  data,
  exposureContext,
  hydroClimate,
  loadState,
  onNavigate,
  sarContext,
  selectedDate,
  selectedLayer,
  selectedNodeId,
  setSelectedDate,
  setSelectedLayer,
  setSelectedNodeId,
}) {
  const ready = loadState.status === "ready" && data;
  const observations = ready ? data.observations ?? data.rows ?? [] : [];
  const dates = ready ? data.dates ?? [] : [];
  const nodes = useMemo(
    () => orderCorridorNodes(ready ? data.nodes ?? [] : [], observations),
    [data, observations, ready],
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

  if (!ready) {
    return (
      <section className="corredor-workbench empty" aria-label="Corredor">
        <div className="corredor-workbench__empty">
          <p className="small-label">Corredor</p>
          <h1>Banco de evidencia territorial</h1>
          <p>
            {loadState.message ||
              "El corredor estará disponible cuando exista kairos_watch.json."}
          </p>
        </div>
      </section>
    );
  }

  const activeDate = dates.includes(selectedDate)
    ? selectedDate
    : dates[0] ?? selectedDate;
  const activeNode = nodes.find((node) => node.node_id === selectedNodeId) ?? nodes[0];
  const activeNodeId = activeNode?.node_id ?? "";
  const selectedObservation = observationMap.get(`${activeNodeId}|${activeDate}`);
  const selectedState = selectedObservation
    ? getStateMeta(selectedObservation)
    : {
        label: "SIN DATO",
        tone: "review",
        action: "Seleccionar otro nodo o fecha con observación pública.",
      };
  const sarRow = findSarLensRow(sarContext, activeNodeId, activeDate);
  const clmsRow = findClmsLensRow(exposureContext, activeNodeId);
  const hydroRow = findHydroLensRow(hydroClimate, activeNodeId, activeDate);
  const inspector = buildWorkbenchInspector({
    clmsRow,
    hydroRow,
    layer: selectedLayer,
    observation: selectedObservation,
    sarRow,
    state: selectedState,
  });
  const evidenceGaps = buildWorkbenchEvidenceGaps({
    clmsRow,
    hydroRow,
    observation: selectedObservation,
    sarRow,
  });
  const nextAction = buildWorkbenchNextAction(selectedObservation);

  function selectWorkbenchCell(nodeId, date) {
    setSelectedNodeId(nodeId);
    setSelectedDate(date);
  }

  return (
    <section className="corredor-workbench" aria-label="Corredor Layer Workbench">
      <div className="corredor-workbench__hero">
        <div>
          <p className="small-label">Corredor</p>
          <h1>Layer Workbench del Río La Villa</h1>
          <p>
            Selecciona un nodo, una fecha y una capa. Cada control cambia la evidencia
            visible en el inspector.
          </p>
        </div>
        <aside className="corredor-workbench__legend" aria-label="Leyenda compacta">
          <span>
            <b>Sentinel-2</b> capa primaria de decisión.
          </span>
          <span>
            <b>SAR / CLMS / HydroClimate</b> contexto auxiliar.
          </span>
        </aside>
      </div>

      <div className="corredor-layer-tabs" aria-label="Capas de evidencia">
        {WORKBENCH_LAYERS.map((layer) => (
          <button
            aria-pressed={selectedLayer === layer.id}
            className={selectedLayer === layer.id ? "is-active" : ""}
            key={layer.id}
            onClick={() => setSelectedLayer(layer.id)}
            type="button"
          >
            {layer.label}
          </button>
        ))}
      </div>

      <div className="corredor-workbench__grid">
        <section className="corredor-map-panel" aria-label="Esquema del corredor">
          <div className="corredor-map-panel__surface">
            <svg
              className="corredor-map-svg"
              viewBox="0 0 920 300"
              role="img"
              aria-label="Vista esquemática del Río La Villa con tres nodos"
            >
              <path
                className="corredor-map-mountains far"
                d="M20 92 C95 42 168 80 230 55 C314 22 390 72 470 48 C570 18 666 68 742 40 C818 17 872 52 900 34 L900 118 L20 118 Z"
              />
              <path
                className="corredor-map-mountains near"
                d="M20 128 C104 94 168 128 254 92 C348 56 424 126 522 88 C620 50 694 118 784 78 C838 54 878 80 900 68 L900 146 L20 146 Z"
              />
              <path
                className="corredor-map-terrain left"
                d="M30 216 C112 154 198 184 274 140 C344 100 418 142 398 210 C370 274 250 252 180 264 C98 278 50 258 30 216 Z"
              />
              <path
                className="corredor-map-terrain right"
                d="M500 202 C586 136 664 168 736 126 C816 80 900 130 882 206 C860 286 740 256 660 270 C574 284 506 262 500 202 Z"
              />
              <path
                className="corredor-map-river-shadow"
                d="M56 190 C162 116 270 230 402 160 C542 84 650 136 864 104"
              />
              <path
                className="corredor-map-river"
                d="M56 190 C162 116 270 230 402 160 C542 84 650 136 864 104"
              />
            </svg>

            <div className="corredor-node-buttons">
              {nodes.map((node, index) => {
                const observation = observationMap.get(`${node.node_id}|${activeDate}`);
                const state = observation ? getStateMeta(observation) : selectedState;
                const layerSummary = buildWorkbenchNodeLayerSummary({
                  clmsRow: findClmsLensRow(exposureContext, node.node_id),
                  hydroRow: findHydroLensRow(hydroClimate, node.node_id, activeDate),
                  layer: selectedLayer,
                  observation,
                  sarRow: findSarLensRow(sarContext, node.node_id, activeDate),
                  state,
                });
                const selected = node.node_id === activeNodeId;
                return (
                  <button
                    className={`corredor-node-button tone-${state.tone}${
                      selected ? " is-selected" : ""
                    }`}
                    key={node.node_id}
                    onClick={() => setSelectedNodeId(node.node_id)}
                    style={{ "--node-left": `${[18, 50, 82][index] ?? 50}%` }}
                    type="button"
                  >
                    <span className="corredor-node-button__dot" aria-hidden="true" />
                    <b>{node.display_name || node.node_id}</b>
                    <em>{layerSummary}</em>
                  </button>
                );
              })}
            </div>
          </div>

          <p className="corredor-disclaimer">
            Vista esquemática de evidencia territorial. No es imagen satelital ni mapa
            geoespacial exacto.
          </p>
        </section>

        <WorkbenchInspector
          activeDate={activeDate}
          activeNode={activeNode}
          evidenceGaps={evidenceGaps}
          inspector={inspector}
          nextAction={nextAction}
          onNavigate={onNavigate}
          selectedLayer={selectedLayer}
          state={selectedState}
        />
      </div>

      <section className="corredor-matrix-section" aria-label="Matriz regional">
        <div className="section-heading compact">
          <div>
            <p className="small-label">Matriz regional</p>
            <h2>Haz clic en una celda para inspeccionar nodo y fecha.</h2>
          </div>
          <p>
            La matriz cambia la selección del banco de trabajo; la capa activa decide
            qué evidencia se ve en el inspector.
          </p>
        </div>

        <div className="corredor-matrix-wrap">
          <table className="corredor-matrix">
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
                    <strong>{node.display_name || node.node_id}</strong>
                    <span>{node.node_id}</span>
                  </th>
                  {dates.map((date) => {
                    const observation = observationMap.get(`${node.node_id}|${date}`);
                    const state = observation
                      ? getStateMeta(observation)
                      : { label: "SIN DATO", tone: "review" };
                    const selected = node.node_id === activeNodeId && date === activeDate;
                    return (
                      <td key={`${node.node_id}-${date}`}>
                        <button
                          className={`corredor-matrix-cell tone-${state.tone}${
                            selected ? " is-selected" : ""
                          }`}
                          onClick={() => selectWorkbenchCell(node.node_id, date)}
                          title={
                            observation
                              ? `${formatPercent(observation.validPercent)} evidencia válida`
                              : "Sin observación pública"
                          }
                          type="button"
                        >
                          <span>{state.label}</span>
                          <strong>
                            {observation
                              ? formatPercent(observation.validPercent)
                              : "sin dato"}
                          </strong>
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}

function WorkbenchInspector({
  activeDate,
  activeNode,
  evidenceGaps,
  inspector,
  nextAction,
  onNavigate,
  selectedLayer,
  state,
}) {
  return (
    <aside className={`workbench-inspector tone-${state.tone}`} aria-label="Inspector de evidencia">
      <div className="workbench-inspector__header">
        <p className="small-label">Inspector</p>
        <h2>{activeNode?.display_name || activeNode?.node_id || "Nodo sin dato"}</h2>
        <span>{activeDate}</span>
      </div>

      <div className="workbench-inspector__state">
        <span>{workbenchLayerLabel(selectedLayer)}</span>
        <strong>{inspector.headline}</strong>
        <p>{inspector.summary}</p>
      </div>

      <dl className="workbench-inspector__readings">
        {inspector.items.map((item) => (
          <div key={item.label}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>

      <div className="workbench-question-block">
        <span>Brechas de evidencia</span>
        <ul>
          {evidenceGaps.map((gap) => (
            <li key={gap}>{gap}</li>
          ))}
        </ul>
      </div>

      <div className="workbench-question-block next">
        <span>Siguiente paso</span>
        <p>{nextAction.text}</p>
        {nextAction.page ? (
          <button type="button" onClick={() => onNavigate(nextAction.page)}>
            {nextAction.button}
          </button>
        ) : null}
      </div>
    </aside>
  );
}

function StickyDecisionBar({ record, ledger, state, visible, onOpenEvidence }) {
  if (!visible) return null;

  const apiLabel = record.api_status === "OK" ? "API OK" : record.api_status || "API pendiente";
  const ledgerLabel = ledger?.evidence_status ? "Ledger OK" : "Ledger pendiente";

  return (
    <aside className={`sticky-decision-bar tone-${state.tone}`} aria-label="Decision fija">
      <div className="sticky-decision-main">
        <span>{record.date}</span>
        <strong>{state.label}</strong>
      </div>
      <div className="sticky-decision-meta">
        <span>{formatPercent(record.validPercent)} valido</span>
        <span>{apiLabel}</span>
        <span>{ledgerLabel}</span>
      </div>
      <button type="button" onClick={onOpenEvidence}>
        Ver evidencia
      </button>
    </aside>
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

function findSarLensRow(data, nodeId, selectedDate) {
  return getSarRows(data).find(
    (row) => row.node_id === nodeId && row.target_date === selectedDate,
  );
}

function findHydroLensRow(data, nodeId, selectedDate) {
  const rows = Array.isArray(data?.rows)
    ? data.rows
    : Array.isArray(data?.observations)
      ? data.observations
      : [];
  return rows.find(
    (row) =>
      row.node_id === nodeId &&
      (row.target_date === selectedDate || row.date === selectedDate),
  );
}

function findClmsLensRow(data, nodeId) {
  const rows = Array.isArray(data?.summary_by_node)
    ? data.summary_by_node
    : Array.isArray(data?.nodes)
      ? data.nodes
      : [];
  return rows.find((row) => row.node_id === nodeId);
}

function KairosCases({
  data,
  loadState,
  activeCaseId,
  setActiveCaseId,
  casePanelMode,
  setCasePanelMode,
  exposureContext,
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
      <section className="cases-screen" aria-label="Accion">
        <div className="cases-hero">
          <div>
            <p className="small-label">Accion</p>
            <h1>Cola de decision territorial</h1>
            <p>{CASES_INSIGHT}</p>
          </div>
          <article className="cases-empty-card">
            <span>Casos no disponibles</span>
            <p>
              {loadState.message ||
                "Accion estara disponible cuando se exporte decision_cases.json."}
            </p>
          </article>
        </div>
      </section>
    );
  }

  return (
    <section className="cases-screen" aria-label="Accion">
      <div className="cases-hero">
        <div>
          <p className="small-label">Accion</p>
          <h1>Cola de decision territorial</h1>
          <p>{CASES_INSIGHT}</p>
        </div>
        <article className="cases-insight-card">
          <span>Cola de decision</span>
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
              <p className="small-label">Cola de casos</p>
              <h2>Acciones recomendadas por nodo y fecha</h2>
            </div>
            <p>Corredor conserva el panorama regional. Esta vista organiza la accion.</p>
          </div>

          <div className="case-queue-list">
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

        <CaseActionPanel
          caseItem={selectedCase}
          exposureContext={exposureContext}
          mode={casePanelMode}
        />
      </div>

      <section className="cases-limit-note" aria-label="Limite cientifico de Accion">
        <span>Limite de alcance</span>
        <p>
          {data.claim_firewall ||
            "No extiende la interfaz a conclusiones fuera de confianza observacional ni a respuesta institucional."}
        </p>
      </section>
    </section>
  );
}

function DecisionCaseCard({ caseItem, isActive, onSelect }) {
  const tone = decisionCaseTone(caseItem);
  const priority = casePriorityBadge(caseItem);
  const stampState = decisionCaseStampState(caseItem);
  const actionText = caseItem.recommended_action || caseItem.recommended_workflow;

  return (
    <article className={`case-card case-queue-row tone-${tone} ${isActive ? "active" : ""}`}>
      <span className="case-priority-pill">{priority}</span>

      <div className="case-card-row case-card-row--top">
        <div className="case-card-identity">
          <h3>{caseItem.node_display_name || caseItem.node_id}</h3>
          <span>{caseItem.date}</span>
        </div>

        <div className="case-card-state">
          <span className="case-row-stamp">
            <DecisionStamp
              animated={false}
              scale={0.65}
              size="small"
              state={stampState}
            />
          </span>
          <strong className="case-row-percent">
            {formatCasePercent(caseItem.primary_validPercent)}
          </strong>
        </div>
      </div>

      <div className="case-card-row case-card-row--bottom">
        <p className="case-row-action">{actionText}</p>
        <div className="case-actions" aria-label="Acciones del caso">
          <button type="button" onClick={() => onSelect(caseItem, "evidence")}>
            Ver evidencia
          </button>
        </div>
      </div>
      <p className="case-lab-copy">{LAB_ESCALATION_COPY}</p>
    </article>
  );
}

function CaseActionPanel({ caseItem, exposureContext, mode }) {
  const exposureLabel =
    exposureContext?.data_status === "exposure_available"
      ? "CLMS disponible"
      : caseItem?.exposure_status || "pendiente";
  const evidenceGaps = caseEvidenceGaps(caseItem, exposureContext);

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
      <aside className="case-action-panel" aria-label="Vista de verificacion territorial">
        <span>Verificación territorial</span>
        <h3>Ficha de verificacion, no persistida</h3>
        <p>
          Este flujo documenta que el caso requiere revisión territorial. No guarda
          datos, no abre backend y no reemplaza la autoridad técnica.
        </p>
        <dl className="case-panel-facts">
          <CaseDataPair label="Nodo" value={caseItem.node_display_name || caseItem.node_id} />
          <CaseDataPair label="Fecha" value={caseItem.date} />
          <CaseDataPair label="Estado" value={caseItem.field_verification_status} />
          <CaseDataPair label="Limite externo" value={caseItem.lab_escalation_status} />
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
          value={`${caseItem.primary_confidence_class || "pendiente"} - ${formatCasePercent(
            caseItem.primary_validPercent,
          )}`}
        />
        <CaseDataPair label="Contexto CLMS" value={exposureLabel} />
        <CaseDataPair
          label="HydroClimate"
          value={translateHydroStatus(caseItem.hydroclimate_status)}
        />
        <CaseDataPair label="Ledger" value={caseItem.ledger_status} />
      </dl>
      <div className="case-panel-gaps">
        <strong>Brechas</strong>
        <ul>
          {evidenceGaps.map((gap) => (
            <li key={gap}>{gap}</li>
          ))}
        </ul>
      </div>
    </aside>
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

function getStateMeta(record) {
  const base = STATE_META[record.confidence_class] ?? STATE_META.do_not_infer;
  return {
    ...base,
    label: base.label,
    decision: record.decision_label_es || base.decision,
    action: record.recommended_action_es || base.action,
  };
}

function buildImpactMetrics({
  observations,
  ledgerRows,
  watchData,
  sarContext,
  hydroClimate,
  decisionCases,
  exposureContext,
}) {
  const officialObservations = Array.isArray(observations) ? observations : [];
  const weakContrast = findOfficialContrastRecord(
    officialObservations,
    IMPACT_CONTRAST_DATES.weak,
  );
  const usableContrast = findOfficialContrastRecord(
    officialObservations,
    IMPACT_CONTRAST_DATES.usable,
  );
  const weakValidPercent = Number(weakContrast?.validPercent);
  const usableValidPercent = Number(usableContrast?.validPercent);
  const evidenceUpliftRatio =
    Number.isFinite(weakValidPercent) &&
    weakValidPercent > 0 &&
    Number.isFinite(usableValidPercent)
      ? usableValidPercent / weakValidPercent
      : 0;
  const apiOkBlockedCount = officialObservations.filter(
    (record) => isApiOk(record) && isDoNotInfer(record),
  ).length;

  const regionalRows = getRegionalRows(watchData);
  const regionalObservationCount =
    regionalRows.length || getRegionalNodeCount(watchData, regionalRows) * getRegionalDateCount(watchData, regionalRows);
  const regionalReviewCount = regionalRows.filter(isDoNotInfer).length;

  return {
    weakContrast,
    usableContrast,
    evidenceUpliftRatio,
    officialObservationCount: officialObservations.length,
    apiOkBlockedCount,
    regionalObservationCount,
    regionalReviewCount,
    ledgerEventCount: Array.isArray(ledgerRows) ? ledgerRows.length : 0,
    decisionCaseCount: getDecisionCaseRows(decisionCases).length,
    nodeCount: getRegionalNodeCount(watchData, regionalRows),
    dateCount: getRegionalDateCount(watchData, regionalRows),
    auxiliaryCoverage: {
      sar: buildSarCoverage(sarContext),
      clms: buildClmsCoverage(exposureContext),
      hydro: buildHydroCoverage(hydroClimate),
    },
  };
}

function findOfficialContrastRecord(records, date) {
  return (
    records.find((record) => record.date === date && record.aoi === "corridor_wide") ??
    records.find((record) => record.date === date) ??
    null
  );
}

function getRegionalRows(watchData) {
  if (Array.isArray(watchData?.observations)) return watchData.observations;
  if (Array.isArray(watchData?.rows)) return watchData.rows;
  return [];
}

function getDecisionCaseRows(decisionCases) {
  if (Array.isArray(decisionCases?.cases)) return decisionCases.cases;
  if (Array.isArray(decisionCases?.rows)) return decisionCases.rows;
  if (Array.isArray(decisionCases)) return decisionCases;
  return [];
}

function getRegionalNodeCount(watchData, rows) {
  if (Array.isArray(watchData?.nodes) && watchData.nodes.length) {
    return watchData.nodes.length;
  }
  return new Set(rows.map((row) => row.node_id).filter(Boolean)).size;
}

function getRegionalDateCount(watchData, rows) {
  if (Array.isArray(watchData?.dates) && watchData.dates.length) {
    return watchData.dates.length;
  }
  return new Set(rows.map((row) => row.date || row.target_date).filter(Boolean)).size;
}

function buildSarCoverage(sarContext) {
  const rows = getSarRows(sarContext);
  const total = asCount(sarContext?.rows_total) || rows.length;
  const available =
    asCount(sarContext?.sar_context_available_count) ||
    rows.filter((row) => row.context_status === "sar_context_available").length;

  return {
    available,
    total,
    note: "Cobertura auxiliar reportada, separada de la decisión Sentinel-2.",
  };
}

function buildClmsCoverage(exposureContext) {
  const nodes = Array.isArray(exposureContext?.nodes) ? exposureContext.nodes : [];
  const total = nodes.length;
  const available = nodes.filter(
    (node) => node.exposure_status === "exposure_available",
  ).length;

  return {
    available,
    total,
    note: "Cobertura por nodo para contexto territorial auxiliar.",
  };
}

function buildHydroCoverage(hydroClimate) {
  const summary = hydroClimate?.summary ?? {};
  const counts = summary.context_status_counts ?? {};
  const rows = Array.isArray(hydroClimate?.rows) ? hydroClimate.rows : [];
  const total = asCount(summary.rows_total) || rows.length;
  const unavailable = asCount(counts.data_unavailable) + asCount(counts.api_error);

  return {
    available: Math.max(0, total - unavailable),
    total,
    note: "Filas de lluvia antecedente como contexto auxiliar.",
  };
}

function buildWorkbenchInspector({
  clmsRow,
  hydroRow,
  layer,
  observation,
  sarRow,
  state,
}) {
  if (layer === "sar") {
    return buildSarWorkbenchInspector(sarRow);
  }
  if (layer === "clms") {
    return buildClmsWorkbenchInspector(clmsRow);
  }
  if (layer === "hydro") {
    return buildHydroWorkbenchInspector(hydroRow);
  }
  return buildS2WorkbenchInspector(observation, state);
}

function buildS2WorkbenchInspector(observation, state) {
  return {
    headline: state.label,
    summary:
      observation?.reason_es ||
      state.explanation ||
      "Sentinel-2 es la capa primaria de decisión pública.",
    items: [
      ["Decisión", observation?.decision_label_es || state.decision || state.label],
      ["Evidencia válida", formatMaybePercent(observation?.validPercent)],
      ["API CDSE", observation?.api_status || "sin dato"],
      ["Clasificación", observation?.confidence_label_es || state.label],
      ["Acción", observation?.recommended_action_es || state.action || "sin dato"],
    ].map(([label, value]) => ({ label, value })),
  };
}

function buildSarWorkbenchInspector(row) {
  const status = translateSarStatus(row?.context_status);
  return {
    headline: row ? status : "SAR sin fila pública",
    summary: row
      ? "Continuidad radar reportada como contexto auxiliar para el nodo y fecha seleccionados."
      : "No existe fila SAR pública para esta selección.",
    items: [
      ["Estado", status],
      ["Fecha SAR", row?.matched_acquisition_date || "sin adquisición"],
      [
        "Ventana",
        row?.sar_window_start && row?.sar_window_end
          ? `${row.sar_window_start} a ${row.sar_window_end}`
          : "sin ventana",
      ],
      ["Ancho ventana", row?.window_days ? `+/-${row.window_days} días` : "sin dato"],
      ["API", row?.api_status || "sin dato"],
    ].map(([label, value]) => ({ label, value })),
  };
}

function buildClmsWorkbenchInspector(row) {
  return {
    headline: row?.exposure_status === "exposure_available" ? "CLMS disponible" : "CLMS sin nodo público",
    summary: row
      ? "Composición territorial del nodo como contexto auxiliar."
      : "No existe contexto CLMS público para este nodo.",
    items: [
      ["Referencia", row?.reference_year || "sin dato"],
      ["Cultivo/agricultura", formatMaybePercent(row?.cropland_agriculture_pct)],
      ["Árbol/vegetación", formatMaybePercent(row?.tree_vegetation_pct)],
      ["Agua/humedal", formatMaybePercent(row?.water_wetland_pct)],
      ["Urbano/suelo", formatMaybePercent(row?.built_bare_other_pct)],
    ].map(([label, value]) => ({ label, value })),
  };
}

function buildHydroWorkbenchInspector(row) {
  const status = formatWorkbenchHydroStatus(row?.context_status || row?.hydroclimate_status);
  return {
    headline: row ? status : "HydroClimate sin fila pública",
    summary: row
      ? "Lluvia antecedente reportada como contexto auxiliar para priorizar revisión."
      : "No existe fila HydroClimate pública para esta selección.",
    items: [
      ["Estado", status],
      ["24h", formatRainMm(row?.rain_24h_mm)],
      ["72h", formatRainMm(row?.rain_72h_mm)],
      ["7 días", formatRainMm(row?.rain_7d_mm)],
      ["14 días", formatRainMm(row?.rain_14d_mm)],
    ].map(([label, value]) => ({ label, value })),
  };
}

function buildWorkbenchEvidenceGaps({ clmsRow, hydroRow, observation, sarRow }) {
  const gaps = [];
  if (!observation) {
    gaps.push("No hay observación Sentinel-2 pública para esta selección.");
  } else if (isDoNotInfer(observation)) {
    gaps.push("Sentinel-2 no alcanza evidencia válida suficiente para interpretar.");
  } else if (observation.confidence_class === "low_confidence") {
    gaps.push("Sentinel-2 requiere revisión antes de interpretar.");
  }

  if (!sarRow || sarRow.context_status !== "sar_context_available") {
    gaps.push("SAR auxiliar no aporta contexto disponible para esta ventana.");
  }
  if (!clmsRow || clmsRow.exposure_status !== "exposure_available") {
    gaps.push("CLMS auxiliar no está disponible para este nodo.");
  }
  if (!hydroRow) {
    gaps.push("HydroClimate auxiliar no tiene fila pública para este nodo/fecha.");
  }

  return gaps.length
    ? gaps
    : ["Los JSON públicos no registran brecha auxiliar adicional para esta selección."];
}

function buildWorkbenchNextAction(observation) {
  if (!observation) {
    return {
      text: "Cambiar nodo o fecha hasta encontrar una observación pública.",
      button: "",
      page: "",
    };
  }
  if (isDoNotInfer(observation)) {
    return {
      text:
        observation.recommended_action_es ||
        "Esperar una nueva adquisición o solicitar verificación territorial.",
      button: "Ver Acción",
      page: "cases",
    };
  }
  if (observation.confidence_class === "low_confidence") {
    return {
      text: "Revisar evidencia auxiliar y abrir trazabilidad antes de interpretar.",
      button: "Ver Evidencia",
      page: "technical",
    };
  }
  return {
    text: "Abrir trazabilidad para ver la cadena pública de evidencia.",
    button: "Ver Evidencia",
    page: "technical",
  };
}

function buildWorkbenchNodeLayerSummary({
  clmsRow,
  hydroRow,
  layer,
  observation,
  sarRow,
  state,
}) {
  if (layer === "sar") {
    return sarRow ? translateSarStatus(sarRow.context_status) : "SAR sin fila";
  }
  if (layer === "clms") {
    return clmsRow?.exposure_status === "exposure_available"
      ? `CLMS ${formatMaybePercent(clmsRow.water_wetland_pct)} agua/humedal`
      : "CLMS sin dato";
  }
  if (layer === "hydro") {
    return hydroRow
      ? formatWorkbenchHydroStatus(hydroRow.context_status || hydroRow.hydroclimate_status)
      : "Hydro sin fila";
  }
  return observation
    ? `${state.label} · ${formatPercent(observation.validPercent)}`
    : "sin Sentinel-2";
}

function workbenchLayerLabel(layer) {
  return WORKBENCH_LAYERS.find((item) => item.id === layer)?.label || "S-2 DECISIÓN";
}

function formatWorkbenchHydroStatus(status) {
  const labels = {
    normal_context: "contexto normal",
    antecedent_rain_review: "revisión por lluvia antecedente",
    antecedent_rain: "lluvia antecedente",
    heavy_rain_context: "lluvia alta antecedente",
    dry_or_low_rain: "lluvia baja",
    data_unavailable: "datos pendientes",
    api_error: "error API",
  };
  return labels[status] || status || "sin dato";
}

function isApiOk(record) {
  return String(record?.api_status ?? "").toUpperCase() === "OK";
}

function isDoNotInfer(record) {
  const normalizedClass = String(record?.confidence_class ?? record?.decision ?? "")
    .trim()
    .toLowerCase();
  const normalizedLabel = String(record?.confidence_label_es ?? record?.decision_label ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  return normalizedClass === "do_not_infer" || normalizedLabel === "NO_INFERIR";
}

function findLedgerForRecord(rows, record) {
  return pickPreferredLedgerRow(findLedgerRowsForRecord(rows, record));
}

function findLedgerRowsForRecord(rows, record) {
  if (!record) return [];
  return rows.filter(
    (row) =>
      row.date === record.date &&
      row.aoi === record.aoi &&
      Number(row.resolution_m) === Number(record.resolution_m),
  );
}

function pickPreferredLedgerRow(rows) {
  if (!Array.isArray(rows) || !rows.length) return null;
  const preferredEventOrder = [
    "confidence_decision_computed",
    "brief_generated",
    "processed_metrics_created",
    "raw_observation_received",
  ];
  return (
    preferredEventOrder
      .map((eventType) => rows.find((row) => row.event_type === eventType))
      .find(Boolean) ?? rows[0]
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
    rows: Array.isArray(payload.rows)
      ? payload.rows.map(normalizeRecord)
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
    rows: Array.isArray(payload.rows)
      ? payload.rows.map(normalizeRecord)
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

function normalizeExposurePayload(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    ...payload,
    nodes: Array.isArray(payload.nodes)
      ? payload.nodes.map(normalizeRecord)
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
  if (!/[\u00c3\u00c2\u00e2]/.test(value) || typeof TextDecoder === "undefined") {
    return value;
  }

  try {
    const bytes = Uint8Array.from(Array.from(value), (char) =>
      char.charCodeAt(0),
    );
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return value
      .replaceAll("\u00c3\u00b3", "\u00f3")
      .replaceAll("\u00c3\u00a1", "\u00e1")
      .replaceAll("\u00c3\u00a9", "\u00e9")
      .replaceAll("\u00c3\u00ad", "\u00ed")
      .replaceAll("\u00c3\u00ba", "\u00fa")
      .replaceAll("\u00c3\u00b1", "\u00f1")
      .replaceAll("\u00c3\u00bc", "\u00fc")
      .replaceAll("\u00c2", "");
  }
}

function formatPercent(value) {
  return `${formatNumber(value, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function formatMaybePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "pendiente";
  return formatPercent(numeric);
}

function formatMultiplier(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "0.0";
  return formatNumber(numeric, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatInteger(value) {
  if (value === undefined || value === null || value === "") return "pendiente";
  return new Intl.NumberFormat("es-PA", { maximumFractionDigits: 0 }).format(
    Number(value),
  );
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

function getSarRows(data) {
  if (Array.isArray(data?.rows)) return data.rows;
  if (Array.isArray(data?.observations)) return data.observations;
  return [];
}

function asCount(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
}

function translateSarStatus(status) {
  const labels = {
    sar_context_available: "contexto disponible",
    sar_low_observation: "observacion baja",
    sar_no_acquisition: "sin adquisicion",
    sar_api_error: "error API",
    sar_error: "error API",
  };
  return labels[status] || status || "sin dato";
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

function translateHydroStatus(status) {
  const labels = {
    normal_context: "contexto normal",
    antecedent_rain: "lluvia antecedente",
    heavy_rain_context: "lluvia alta antecedente",
    dry_or_low_rain: "lluvia baja",
    data_unavailable: "datos pendientes",
  };
  return labels[status] || status || "sin dato";
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

function decisionCaseStampState(caseItem) {
  const label = String(caseItem?.decision_label ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");
  if (label === "NO_INFERIR") return "NO_INFERIR";
  if (label === "REVISAR") return "REVISAR";
  return "USABLE";
}

function casePriorityBadge(caseItem) {
  const priority = stripAccents(String(caseItem?.priority_level ?? "")).toLowerCase();
  return priority === "alta" ? "ALTA" : "MEDIA";
}

function caseEvidenceGaps(caseItem, exposureContext) {
  const gaps = splitEvidenceGaps(caseItem?.evidence_gaps);
  if (exposureContext?.data_status !== "exposure_available") {
    return gaps;
  }

  return gaps.map((gap) => {
    const normalized = stripAccents(gap).toLowerCase();
    if (normalized.includes("exposicion") || normalized.includes("clms")) {
      return "CLMS disponible como contexto territorial auxiliar.";
    }
    return gap;
  });
}

function splitEvidenceGaps(value) {
  if (!value) return ["Sin brechas registradas."];
  return String(value)
    .split("|")
    .map((gap) => gap.trim())
    .filter(Boolean);
}

function stripAccents(value) {
  return String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "");
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

