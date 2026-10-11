import React from "react";
import {
  NODES,
  NODE_ORDER,
  THRESHOLDS,
  daysBetween,
  decisionEvent,
  exposureFor,
  findContrast,
  formatCount,
  formatDate,
  formatNumber,
  formatPercent,
  hydroFor,
  ledgerForDate,
  nodeObservation,
  sarFor,
  stateOf,
} from "../lib/data.js";
import { Fact, Section, Stamp, StateTag, ThresholdBar } from "../components/ui.jsx";

export default function Observacion({ data, date, record, setDate, onOpenCase, onOpenRegistro }) {
  const state = stateOf(record.confidence_class);
  const ledgerRows = ledgerForDate(data.ledger, date);
  const decision = decisionEvent(ledgerRows);
  const contrast = findContrast(data.observations);
  const validPixels = Number(record.sampleCount) - Number(record.noDataCount);
  const blocked = record.confidence_class === "do_not_infer";

  return (
    <div className="page page--observacion">
      <h1 className="sr-only">
        Observación del {formatDate(date, { year: true })}: {state.label}
      </h1>

      <div className="lead">
        <div className="lead__gauge">
          <header className="lead__head">
            <h2>Cobertura válida de Sentinel-2 por adquisición</h2>
            <p>
              Cada regla es una escena oficial del corredor. Las tres barras finas son los nodos
              Oeste, Centro y Este en la misma fecha.
            </p>
          </header>

          <EvidenceGauge data={data} date={date} setDate={setDate} />

          {contrast ? (
            <p className="lead__reading">
              <span className="lead__reading-mark" aria-hidden="true">
                Lectura
              </span>
              El {formatDate(contrast.weak.date)} la API respondió, pero solo{" "}
              <b className="mono">{formatPercent(contrast.weak.validPercent)}</b> de la escena era
              válida. {contrast.days} días después, la cobertura fue{" "}
              <b className="mono">{formatPercent(contrast.strong.validPercent)}</b>. La respuesta
              responsable fue esperar.
            </p>
          ) : null}
        </div>

        <aside className="verdict" aria-label="Decisión de la fecha seleccionada">
          <p className="eyebrow">
            Corredor completo <span aria-hidden="true">/</span> {formatDate(date, { year: true })}
          </p>
          <Stamp key={date} confidenceClass={record.confidence_class} />
          <p className="verdict__reason">{record.reason_es || state.reason}</p>

          <ol className="gate" aria-label="Compuerta de decisión">
            <li className={record.api_status === "OK" ? "gate__step is-pass" : "gate__step is-fail"}>
              <span className="gate__k">API CDSE</span>
              <span className="gate__v">{record.api_status === "OK" ? "Respondió" : "Sin respuesta"}</span>
            </li>
            <li className={`gate__step is-${state.tone}`}>
              <span className="gate__k">Cobertura válida</span>
              <span className="gate__v mono">{formatPercent(record.validPercent)}</span>
            </li>
            <li className={`gate__step is-${state.tone}`}>
              <span className="gate__k">Inferencia</span>
              <span className="gate__v">{state.inference}</span>
            </li>
          </ol>

          <ThresholdBar value={record.validPercent} confidenceClass={record.confidence_class} labels />

          <div className="next">
            <span className="next__k">Siguiente paso</span>
            <p>{record.recommended_action_es || state.action}</p>
          </div>

          <dl className="facts">
            <Fact label="Píxeles válidos" mono>
              {formatCount(validPixels)} de {formatCount(record.sampleCount)}
            </Fact>
            <Fact label="Resolución" mono>
              {record.resolution_m} m
            </Fact>
            <Fact label="MNDWI / NDTI medio" mono>
              <span className={blocked ? "is-void" : undefined}>
                {formatNumber(record.mndwi_mean)} / {formatNumber(record.ndti_mean)}
              </span>
              {blocked ? <em className="void-note">no interpretar</em> : null}
            </Fact>
            <Fact label="Evento de decisión" mono>
              {decision?.hash_short ? `#${decision.hash_short}` : "sin registro"}
            </Fact>
          </dl>

          <button className="btn btn--primary" type="button" onClick={() => onOpenRegistro(null)}>
            Abrir el registro de esta fecha
          </button>
        </aside>
      </div>

      <Section
        id="nodos"
        number="02"
        title={`Los tres nodos el ${formatDate(date)}`}
        note="Sentinel-2 decide. Radar, lluvia y cobertura del suelo dan contexto y no cambian la clasificación."
      >
        <NodeTable data={data} date={date} onOpenCase={onOpenCase} />
      </Section>
    </div>
  );
}

function EvidenceGauge({ data, date, setDate }) {
  return (
    <div className="gauge">
      <div className="gauge__plot">
        <div className="gauge__axis" aria-hidden="true">
          {[0, 10, 30, 50, 100].map((tick) => (
            <span key={tick} style={{ bottom: `${tick}%` }}>
              {tick}
            </span>
          ))}
        </div>
        <div className="gauge__field">
          <div className="gauge__zone gauge__zone--stop" style={{ height: `${THRESHOLDS.review}%` }} />
          <div
            className="gauge__zone gauge__zone--review"
            style={{ bottom: `${THRESHOLDS.review}%`, height: `${THRESHOLDS.usable - THRESHOLDS.review}%` }}
          />
          <div className="gauge__line gauge__line--usable" style={{ bottom: `${THRESHOLDS.usable}%` }}>
            <span>{THRESHOLDS.usable}% mínimo para interpretar</span>
          </div>
          <div className="gauge__line gauge__line--review" style={{ bottom: `${THRESHOLDS.review}%` }}>
            <span>{THRESHOLDS.review}% bajo esta marca no se infiere</span>
          </div>

          <div className="gauge__cols">
            {data.observations.map((row, index) => {
              const state = stateOf(row.confidence_class);
              const selected = row.date === date;
              return (
                <button
                  className={`staff tone-${state.tone}${selected ? " is-selected" : ""}`}
                  key={row.date}
                  type="button"
                  aria-pressed={selected}
                  aria-label={`${formatDate(row.date, { year: true })}: ${state.label}, ${formatPercent(row.validPercent)} de cobertura válida`}
                  onClick={() => setDate(row.date)}
                  style={{ "--i": index }}
                >
                  <span className="staff__plot">
                    <span className="staff__main">
                      <span className="staff__fill" style={{ height: `${row.validPercent}%` }} />
                      <span className="staff__value mono" style={{ bottom: `${row.validPercent}%` }}>
                        {formatPercent(row.validPercent)}
                      </span>
                    </span>
                    <span className="staff__nodes">
                      {NODE_ORDER.map((nodeId) => {
                        const node = nodeObservation(data, nodeId, row.date);
                        const nodeState = stateOf(node?.confidence_class);
                        return (
                          <span className={`staff__node tone-${nodeState.tone}`} key={nodeId}>
                            <span
                              className="staff__node-fill"
                              style={{ height: `${Number(node?.validPercent) || 0}%` }}
                            />
                          </span>
                        );
                      })}
                    </span>
                  </span>
                  <span className="staff__foot">
                    <span className="staff__letters mono" aria-hidden="true">
                      {NODE_ORDER.map((nodeId) => (
                        <span key={nodeId}>{NODES[nodeId].letter}</span>
                      ))}
                    </span>
                    <span className="staff__date mono">{formatDate(row.date)}</span>
                    <span className="staff__state">{state.label}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      <p className="gauge__caption">
        Porcentaje de píxeles válidos, escala lineal de 0 a 100. Adquisiciones de 2025. Selecciona
        una regla para cambiar la fecha en toda la bitácora.
      </p>
    </div>
  );
}

function NodeTable({ data, date, onOpenCase }) {
  return (
    <div className="nodes">
      <div className="nodes__row nodes__row--head" aria-hidden="true">
        <span>Nodo</span>
        <span>Sentinel-2, cobertura válida</span>
        <span>Radar Sentinel-1</span>
        <span>Lluvia antecedente (CHIRPS)</span>
        <span>Cobertura del suelo (CLMS 2020)</span>
      </div>

      {NODE_ORDER.map((nodeId) => {
        const node = nodeObservation(data, nodeId, date);
        const sar = sarFor(data, nodeId, date);
        const hydro = hydroFor(data, nodeId, date);
        const exposure = exposureFor(data, nodeId);
        const caseItem = data.cases.find((item) => item.node_id === nodeId && item.date === date);

        return (
          <article className="nodes__row" key={nodeId}>
            <div className="nodes__name">
              <h3>{NODES[nodeId].name}</h3>
              {caseItem ? (
                <button className="link" type="button" onClick={() => onOpenCase(caseItem.case_id)}>
                  Ver caso
                </button>
              ) : null}
            </div>

            <div className="nodes__primary">
              {node ? (
                <>
                  <div className="nodes__reading">
                    <span className="mono nodes__pct">{formatPercent(node.validPercent)}</span>
                    <StateTag confidenceClass={node.confidence_class} />
                  </div>
                  <ThresholdBar value={node.validPercent} confidenceClass={node.confidence_class} />
                </>
              ) : (
                <span className="muted">Sin observación exportada.</span>
              )}
            </div>

            <div className="nodes__aux">
              <SarCell row={sar} date={date} />
            </div>

            <div className="nodes__aux">
              <RainCell row={hydro} />
            </div>

            <div className="nodes__aux">
              <LandCell row={exposure} />
            </div>
          </article>
        );
      })}

      <ul className="legend" aria-label="Leyenda de cobertura del suelo">
        <li>
          <i className="land land--veg" /> Vegetación
        </li>
        <li>
          <i className="land land--crop" /> Cultivo
        </li>
        <li>
          <i className="land land--water" /> Agua y humedal
        </li>
        <li>
          <i className="land land--built" /> Construido y otros
        </li>
      </ul>
    </div>
  );
}

function SarCell({ row, date }) {
  if (!row) return <span className="muted">Sin dato exportado.</span>;
  if (!row.matched_acquisition_date) {
    return (
      <>
        <span className="aux__main">Sin adquisición</span>
        <span className="aux__sub">
          Ventana {formatDate(row.sar_window_start)} a {formatDate(row.sar_window_end)}
        </span>
      </>
    );
  }
  const offset = daysBetween(date, row.matched_acquisition_date);
  const when =
    offset === 0
      ? "el mismo día"
      : `${Math.abs(offset)} ${Math.abs(offset) === 1 ? "día" : "días"} ${offset < 0 ? "antes" : "después"}`;
  return (
    <>
      <span className="aux__main mono">{formatDate(row.matched_acquisition_date)}</span>
      <span className="aux__sub">
        {when}, {formatPercent(row.validPercent, 0)} válido
      </span>
    </>
  );
}

function RainCell({ row }) {
  if (!row) return <span className="muted">Sin dato exportado.</span>;
  const review = row.context_status === "antecedent_rain_review";
  return (
    <>
      <span className="aux__main mono">
        {formatNumber(row.rain_72h_mm, 1)} mm <small>72 h</small>
        <span className="aux__sep" aria-hidden="true" />
        {formatNumber(row.rain_7d_mm, 1)} mm <small>7 d</small>
      </span>
      <span className={`aux__sub${review ? " aux__sub--flag" : ""}`}>
        {review ? "Lluvia antecedente: priorizar revisión" : "Contexto normal"}
      </span>
    </>
  );
}

function LandCell({ row }) {
  if (!row) return <span className="muted">Sin dato exportado.</span>;
  const parts = [
    ["veg", row.tree_vegetation_pct],
    ["crop", row.cropland_agriculture_pct],
    ["water", row.water_wetland_pct],
    ["built", row.built_bare_other_pct],
  ];
  return (
    <>
      <span
        className="landbar"
        role="img"
        aria-label={`Vegetación ${formatPercent(row.tree_vegetation_pct, 1)}, cultivo ${formatPercent(row.cropland_agriculture_pct, 1)}, agua y humedal ${formatPercent(row.water_wetland_pct, 1)}, construido y otros ${formatPercent(row.built_bare_other_pct, 1)}`}
      >
        {parts.map(([key, value]) => (
          <i className={`land land--${key}`} key={key} style={{ flexGrow: Number(value) || 0 }} />
        ))}
      </span>
      <span className="aux__sub">
        {formatPercent(row.tree_vegetation_pct, 0)} vegetación,{" "}
        {formatPercent(row.cropland_agriculture_pct, 1)} cultivo,{" "}
        {formatCount(Math.round(row.total_area_ha))} ha
      </span>
    </>
  );
}
