import React, { useMemo, useState } from "react";
import {
  NODES,
  accent,
  exposureFor,
  formatDate,
  formatNumber,
  formatPercent,
  hydroFor,
  priorityLabel,
  sarFor,
  sortCases,
  splitList,
  stateOf,
} from "../lib/data.js";
import { Fact, Section, Stamp, StateTag, ThresholdBar } from "../components/ui.jsx";

const FILTERS = [
  { id: "all", label: "Todos" },
  { id: "verify", label: "Verificación recomendada" },
  { id: "usable", label: "Usables" },
];

const FIELD_CHECKLIST = [
  "Confirmar acceso y punto de observación dentro del nodo.",
  "Registrar fecha, hora y nubosidad al llegar.",
  "Describir la condición visible del cauce sin interpretar causas.",
  "Anotar lluvia reciente reportada por personas del lugar.",
  "Tomar referencia fotográfica fuera de esta interfaz.",
  "Si hace falta laboratorio o autoridad, derivar por el canal competente.",
];

export default function Accion({ data, date, activeCase, onSelectCase, onOpenRegistro, onOpenObservacion }) {
  const [filter, setFilter] = useState("all");
  const cases = useMemo(() => sortCases(data.cases), [data.cases]);
  const visible = cases.filter((item) => {
    if (filter === "verify") return item.field_verification_status === "recomendada";
    if (filter === "usable") return item.primary_confidence_class === "usable";
    return true;
  });
  const caseDates = Array.from(new Set(cases.map((item) => item.date))).sort();

  return (
    <div className="page page--accion">
      <header className="page__head">
        <h1>Cola de acción</h1>
        <p>
          Cinco casos curados de nodo y fecha. El orden indica qué revisar primero; no es un puntaje
          de riesgo ambiental.
        </p>
      </header>

      <div className="split">
        <nav className="queue" aria-label="Casos">
          <div className="chips" role="group" aria-label="Filtrar casos">
            {FILTERS.map((item) => (
              <button
                className={`chip${filter === item.id ? " is-active" : ""}`}
                key={item.id}
                type="button"
                aria-pressed={filter === item.id}
                onClick={() => setFilter(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <ol className="queue__list">
            {visible.map((item, index) => {
              const selected = activeCase?.case_id === item.case_id;
              return (
                <li key={item.case_id}>
                  <button
                    className={`queue__item${selected ? " is-selected" : ""}`}
                    type="button"
                    aria-current={selected ? "true" : undefined}
                    onClick={() => onSelectCase(item.case_id)}
                  >
                    <span className="queue__rank mono">{String(index + 1).padStart(2, "0")}</span>
                    <span className="queue__body">
                      <span className="queue__title">
                        {NODES[item.node_id]?.name ?? item.node_display_name}
                      </span>
                      <span className="queue__meta mono">
                        {formatDate(item.date, { year: true })}
                        <span aria-hidden="true"> / </span>
                        {formatPercent(item.primary_validPercent)}
                      </span>
                      <span className="queue__tags">
                        <StateTag confidenceClass={item.primary_confidence_class} />
                        <span className={`prio prio--${item.priority_level}`}>
                          {priorityLabel(item.priority_level)}
                        </span>
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
          {!visible.length ? <p className="muted">Ningún caso coincide con este filtro.</p> : null}
        </nav>

        {activeCase ? (
          <CaseDetail
            caseItem={activeCase}
            data={data}
            key={activeCase.case_id}
            onOpenObservacion={onOpenObservacion}
            onOpenRegistro={onOpenRegistro}
          />
        ) : (
          <div className="empty">
            <h2>No hay casos curados para el {formatDate(date)}.</h2>
            <p>
              La cola pública cubre {caseDates.map((item) => formatDate(item)).join(", ")}. Elige un
              caso de la lista o cambia la fecha.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function CaseDetail({ caseItem, data, onOpenObservacion, onOpenRegistro }) {
  const state = stateOf(caseItem.primary_confidence_class);
  const sar = sarFor(data, caseItem.node_id, caseItem.date);
  const hydro = hydroFor(data, caseItem.node_id, caseItem.date);
  const exposure = exposureFor(data, caseItem.node_id);
  const gaps = splitList(caseItem.evidence_gaps);
  const recommended = caseItem.field_verification_status === "recomendada";

  return (
    <article className="case" aria-label={`Caso ${caseItem.node_display_name} ${caseItem.date}`}>
      <header className="case__head">
        <div>
          <p className="eyebrow">
            {NODES[caseItem.node_id]?.name ?? caseItem.node_display_name}{" "}
            <span aria-hidden="true">/</span> {formatDate(caseItem.date, { year: true })}{" "}
            <span aria-hidden="true">/</span> {priorityLabel(caseItem.priority_level)}
          </p>
          <h2>{accent(caseItem.title)}</h2>
        </div>
        <Stamp confidenceClass={caseItem.primary_confidence_class} size="md" />
      </header>

      <div className="case__meter">
        <span className="mono case__pct">{formatPercent(caseItem.primary_validPercent)}</span>
        <ThresholdBar
          value={caseItem.primary_validPercent}
          confidenceClass={caseItem.primary_confidence_class}
          labels
        />
      </div>

      <div className="next next--wide">
        <span className="next__k">Qué hacer</span>
        <p>{accent(caseItem.recommended_action)}</p>
      </div>

      <div className="case__cols">
        <div>
          <h3>Por qué</h3>
          <p>{accent(caseItem.decision_rationale)}</p>
          <p className="muted">{accent(caseItem.evidence_summary)}</p>
        </div>
        <div>
          <h3>Brechas de evidencia</h3>
          <ul className="ticks">
            {gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      </div>

      <Section number="A" title="Contexto auxiliar" note="No cambia la decisión de Sentinel-2.">
        <dl className="facts facts--row">
          <Fact label="Radar Sentinel-1">
            {sar?.matched_acquisition_date
              ? `Adquisición del ${formatDate(sar.matched_acquisition_date)}, ${formatPercent(sar.validPercent, 0)} válido`
              : "Sin adquisición en la ventana"}
          </Fact>
          <Fact label="Lluvia antecedente">
            {hydro
              ? `${formatNumber(hydro.rain_72h_mm, 1)} mm en 72 h, ${formatNumber(hydro.rain_7d_mm, 1)} mm en 7 d${
                  hydro.context_status === "antecedent_rain_review" ? ". Priorizar revisión." : ""
                }`
              : "Sin dato exportado"}
          </Fact>
          <Fact label="Cobertura del suelo">
            {exposure
              ? `${formatPercent(exposure.tree_vegetation_pct, 0)} vegetación, ${formatPercent(exposure.cropland_agriculture_pct, 1)} cultivo (CLMS 2020)`
              : "Sin dato exportado"}
          </Fact>
        </dl>
      </Section>

      <Section
        number="B"
        title={`Verificación de campo ${recommended ? "recomendada" : "opcional"}`}
        note="Lista de preparación. Las marcas viven solo en esta sesión: aquí no se guardan notas, fotos ni resultados."
      >
        <FieldChecklist />
        <p className="case__lab">
          <b>Laboratorio:</b> {accent(caseItem.lab_escalation_status)}.
        </p>
      </Section>

      <footer className="case__actions">
        <button className="btn btn--primary" type="button" onClick={() => onOpenRegistro(caseItem.case_id)}>
          Abrir el registro del caso
        </button>
        <button className="btn" type="button" onClick={() => onOpenObservacion(caseItem.date)}>
          Ver la fecha en el corredor
        </button>
        <span className={`case__state tone-${state.tone}`}>{state.rule}</span>
      </footer>
    </article>
  );
}

function FieldChecklist() {
  const [checked, setChecked] = useState({});
  const done = Object.values(checked).filter(Boolean).length;

  return (
    <div className="checklist">
      <ul>
        {FIELD_CHECKLIST.map((item, index) => (
          <li key={item}>
            <label>
              <input
                type="checkbox"
                checked={Boolean(checked[index])}
                onChange={(event) => setChecked((prev) => ({ ...prev, [index]: event.target.checked }))}
              />
              <span>{item}</span>
            </label>
          </li>
        ))}
      </ul>
      <p className="checklist__count mono" aria-live="polite">
        {done} de {FIELD_CHECKLIST.length} preparados
      </p>
    </div>
  );
}
