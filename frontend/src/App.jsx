import React, { useEffect, useMemo, useState } from "react";
import { formatDate, formatPercent, loadPublicData, stateOf } from "./lib/data.js";
import { InkFilter } from "./components/ui.jsx";
import Observacion from "./pages/Observacion.jsx";
import Accion from "./pages/Accion.jsx";
import Registro from "./pages/Registro.jsx";
import Acerca from "./pages/Acerca.jsx";

const DEFAULT_DATE = "2025-06-10";

const PAGES = [
  { id: "observacion", label: "Observación" },
  { id: "accion", label: "Acción" },
  { id: "registro", label: "Registro" },
];

// Older links keep working after the move from eight tabs to three.
const HASH_TO_PAGE = {
  "": "observacion",
  "#observacion": "observacion",
  "#decision": "observacion",
  "#corredor": "observacion",
  "#accion": "accion",
  "#campo": "accion",
  "#registro": "registro",
  "#passport": "registro",
  "#evidencia": "registro",
  "#acerca": "acerca",
  "#sistema": "acerca",
  "#impacto": "acerca",
};

const DEMO_STEPS = [
  {
    page: "observacion",
    date: "2025-06-10",
    title: "La API respondió. La escena no alcanza.",
    text: "El 10 de junio solo 2.26% de la escena era válido. La regla queda bajo la marca de 10% y Kairós bloquea la inferencia.",
  },
  {
    page: "observacion",
    date: "2025-06-30",
    title: "Veinte días después: USABLE.",
    text: "Kairós no bloquea por defecto. Con 71.06% de cobertura válida, la misma regla permite una lectura con límites.",
  },
  {
    page: "observacion",
    date: "2025-06-10",
    anchor: "nodos",
    title: "Tres nodos, la misma brecha.",
    text: "Radar, lluvia y cobertura del suelo dan contexto a cada nodo. Ninguna de esas capas cambia la clasificación de Sentinel-2.",
  },
  {
    page: "accion",
    date: "2025-06-10",
    caseId: "case_la_villa_este_2025-06-10",
    title: "De la brecha a la acción.",
    text: "Cada caso dice qué hacer, por qué y qué falta. La verificación de campo se prepara aquí; no se registra.",
  },
  {
    page: "registro",
    date: "2025-06-10",
    title: "Un comprobante que se puede verificar.",
    text: "El Passport reúne decisión, eventos enlazados, hash y límites. Certifica la trazabilidad del paquete, no el territorio.",
  },
  {
    page: "acerca",
    title: "Lo que Kairós no afirma.",
    text: "Una regla, un ciclo y sus límites. La respuesta responsable a veces es esperar una mejor observación.",
  },
];

function pageFromHash() {
  return HASH_TO_PAGE[window.location.hash.toLowerCase()] ?? "observacion";
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(pageFromHash);
  const [date, setDate] = useState(DEFAULT_DATE);
  const [caseId, setCaseId] = useState(null);
  const [scopeId, setScopeId] = useState(null);
  const [demoIndex, setDemoIndex] = useState(null);

  useEffect(() => {
    let active = true;
    loadPublicData()
      .then((payload) => {
        if (!active) return;
        setData(payload);
        if (!payload.observations.some((row) => row.date === DEFAULT_DATE)) {
          setDate(payload.observations[0].date);
        }
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "No se pudo cargar la data pública.");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const onHash = () => setPage(pageFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const record = useMemo(
    () => data?.observations.find((row) => row.date === date) ?? data?.observations[0] ?? null,
    [data, date],
  );

  if (error) {
    return (
      <main className="boot">
        <h1>Azuero Kairós</h1>
        <p>{error}</p>
      </main>
    );
  }

  if (!data || !record) {
    return (
      <main className="boot" aria-busy="true">
        <p className="mono">Abriendo la bitácora</p>
      </main>
    );
  }

  const casesForDate = data.cases.filter((item) => item.date === date);
  const activeCase =
    casesForDate.find((item) => item.case_id === caseId) ?? casesForDate[0] ?? null;
  const scopeCase = casesForDate.find((item) => item.case_id === scopeId) ?? null;
  const state = stateOf(record.confidence_class);

  function go(nextPage, { top = true } = {}) {
    setPage(nextPage);
    const hash = `#${nextPage}`;
    if (window.location.hash !== hash) window.location.hash = hash;
    if (top) window.scrollTo({ top: 0 });
  }

  function selectCase(id) {
    const item = data.cases.find((entry) => entry.case_id === id);
    if (!item) return;
    setDate(item.date);
    setCaseId(id);
  }

  function openCase(id) {
    selectCase(id);
    go("accion");
  }

  function openRegistro(id) {
    const item = id ? data.cases.find((entry) => entry.case_id === id) : null;
    if (item) setDate(item.date);
    setScopeId(item ? id : null);
    go("registro");
  }

  function openObservacion(nextDate) {
    setDate(nextDate);
    go("observacion");
  }

  function openDemoStep(index) {
    const step = DEMO_STEPS[index];
    if (!step) {
      setDemoIndex(null);
      return;
    }
    setDemoIndex(index);
    if (step.date) setDate(step.date);
    if (step.caseId) setCaseId(step.caseId);
    setScopeId(null);
    go(step.page, { top: !step.anchor });
    if (step.anchor) {
      window.requestAnimationFrame(() => {
        document.getElementById(step.anchor)?.scrollIntoView({ block: "start" });
      });
    }
  }

  const demoStep = demoIndex === null ? null : DEMO_STEPS[demoIndex];

  return (
    <>
      <InkFilter />
      <a className="skip" href="#contenido">
        Saltar al contenido
      </a>

      <header className="top">
        <div className="top__bar">
          <button className="brand" type="button" onClick={() => go("observacion")}>
            <span className="brand__name">Azuero Kairós</span>
            <span className="brand__sub mono">Río La Villa, Panamá</span>
          </button>

          <nav className="tabs" aria-label="Secciones">
            {PAGES.map((item) => (
              <button
                className={`tabs__tab${page === item.id ? " is-active" : ""}`}
                key={item.id}
                type="button"
                aria-current={page === item.id ? "page" : undefined}
                onClick={() => go(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div className="top__side">
            <button
              className={`tabs__tab${page === "acerca" ? " is-active" : ""}`}
              type="button"
              aria-current={page === "acerca" ? "page" : undefined}
              onClick={() => go("acerca")}
            >
              Acerca
            </button>
            <button className="btn btn--small" type="button" onClick={() => openDemoStep(0)}>
              Demo guiada
            </button>
          </div>
        </div>

        {page !== "acerca" ? (
          <div className="ctx">
            <span className="ctx__label">Fecha observada</span>
            <div className="ctx__dates" role="group" aria-label="Fecha observada">
              {data.observations.map((row) => (
                <button
                  className={`ctx__date tone-${stateOf(row.confidence_class).tone}${
                    row.date === date ? " is-active" : ""
                  }`}
                  key={row.date}
                  type="button"
                  aria-pressed={row.date === date}
                  onClick={() => setDate(row.date)}
                >
                  <span className="ctx__dot" aria-hidden="true" />
                  <span className="mono">{formatDate(row.date)}</span>
                </button>
              ))}
            </div>
            <span className={`ctx__verdict tone-${state.tone}`}>
              <b>{state.label}</b>
              <span className="mono">{formatPercent(record.validPercent)} válido</span>
            </span>
            <span className="ctx__source mono">Sentinel-2 L2A, 20 m, 2025</span>
          </div>
        ) : null}
      </header>

      <main className="sheet" id="contenido">
        {page === "observacion" ? (
          <Observacion
            data={data}
            date={date}
            record={record}
            setDate={setDate}
            onOpenCase={openCase}
            onOpenRegistro={openRegistro}
          />
        ) : page === "accion" ? (
          <Accion
            activeCase={activeCase}
            data={data}
            date={date}
            onOpenObservacion={openObservacion}
            onOpenRegistro={openRegistro}
            onSelectCase={selectCase}
          />
        ) : page === "registro" ? (
          <Registro data={data} date={date} record={record} scopeCase={scopeCase} setScope={setScopeId} />
        ) : (
          <Acerca data={data} />
        )}
      </main>

      <footer className="foot">
        <p>
          Kairós evalúa la confianza de una observación satelital. No detecta sustancias, no
          certifica agua y no reemplaza laboratorio, verificación de campo ni autoridad competente.
        </p>
        <p className="mono">
          Demostración con datos exportados de Copernicus CDSE. No es un monitoreo en vivo.{" "}
          <button className="link" type="button" onClick={() => go("acerca")}>
            Límites completos
          </button>
        </p>
      </footer>

      {demoStep ? (
        <aside className="demo" aria-label="Demo guiada">
          <div className="demo__progress" aria-hidden="true">
            {DEMO_STEPS.map((step, index) => (
              <i className={index <= demoIndex ? "is-done" : undefined} key={step.title} />
            ))}
          </div>
          <div className="demo__copy" aria-live="polite">
            <span className="mono">
              Paso {demoIndex + 1} de {DEMO_STEPS.length}
            </span>
            <strong>{demoStep.title}</strong>
            <p>{demoStep.text}</p>
          </div>
          <div className="demo__actions">
            {demoIndex > 0 ? (
              <button className="btn btn--small btn--onink" type="button" onClick={() => openDemoStep(demoIndex - 1)}>
                Anterior
              </button>
            ) : null}
            <button
              className="btn btn--small btn--paper"
              type="button"
              onClick={() => openDemoStep(demoIndex + 1)}
            >
              {demoIndex >= DEMO_STEPS.length - 1 ? "Terminar" : "Siguiente"}
            </button>
            <button className="demo__close" type="button" onClick={() => setDemoIndex(null)} aria-label="Cerrar demo">
              ×
            </button>
          </div>
        </aside>
      ) : null}
    </>
  );
}
