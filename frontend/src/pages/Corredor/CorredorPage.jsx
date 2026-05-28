import React, { useMemo } from "react";
import AzueroLens from "../../components/AzueroLens/AzueroLens.jsx";
import "./CorredorPage.css";

const CORRIDOR_NODE_ORDER = [
  "la_villa_oeste",
  "la_villa_central",
  "la_villa_este",
];

const STATE_CLASS = {
  USABLE: "usable",
  REVISAR: "revisar",
  NO_INFERIR: "no-inferir",
  MISSING: "missing",
};

export default function CorredorPage({
  data,
  loadState,
  selectedDate,
}) {
  const ready = loadState?.status === "ready" && data;
  const nodes = useMemo(() => {
    if (!ready) return [];
    return orderNodes(data.nodes ?? [], data.observations ?? []);
  }, [data, ready]);
  const dates = ready ? data.dates ?? [] : [];
  const observations = ready ? data.observations ?? [] : [];
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
  const activeDate = dates.includes(selectedDate) ? selectedDate : dates[0];
  const lensNodes = useMemo(
    () =>
      nodes
        .map((node) => {
          const observation = observationMap.get(`${node.node_id}|${activeDate}`);
          if (!observation) return null;
          return {
            id: node.node_id,
            name: node.display_name || observation.node_display_name || node.node_id,
            state: getDecisionState(observation),
            validPercent: observation.validPercent,
            date: observation.date,
          };
        })
        .filter(Boolean),
    [activeDate, nodes, observationMap],
  );

  if (!ready) {
    return (
      <section className="corredor-page" aria-label="Corredor">
        <article className="corredor-page__empty">
          <p className="section-label">CORREDOR</p>
          <h1 className="display-heading">Patrón regional de confianza</h1>
          <p>
            {loadState?.message ||
              "El corredor estará disponible cuando se exporte kairos_watch.json."}
          </p>
        </article>
      </section>
    );
  }

  return (
    <section className="corredor-page" aria-label="Corredor">
      <div className="corredor-page__hero">
        <AzueroLens nodes={lensNodes} />
      </div>

      <section className="corredor-page__matrix-section" aria-label="Matriz regional">
        <div className="corredor-page__matrix-heading">
          <p className="section-label">MATRIZ REGIONAL</p>
          <p>
            Tres nodos del Río La Villa por cinco fechas Sentinel-2. Cada celda conserva
            la decisión oficial de confianza de observación.
          </p>
        </div>

        <div className="corredor-page__matrix" role="table" aria-label="Matriz regional de confianza">
          {nodes.map((node) => (
            <div className="corredor-page__matrix-row" role="row" key={node.node_id}>
              <div className="corredor-page__node-label" role="rowheader">
                <strong>{node.display_name || node.node_id}</strong>
                <span>{node.node_id}</span>
              </div>
              <div className="corredor-page__date-cells">
                {dates.map((date) => {
                  const observation = observationMap.get(`${node.node_id}|${date}`);
                  const state = getDecisionState(observation);
                  const stateClass = STATE_CLASS[state] ?? STATE_CLASS.MISSING;
                  const tooltip = observation
                    ? `${formatPercent(observation.validPercent)} evidencia válida`
                    : "sin dato Sentinel-2";

                  return (
                    <span
                      className={`corredor-page__cell corredor-page__cell--${stateClass}`}
                      data-tooltip={tooltip}
                      key={`${node.node_id}-${date}`}
                      role="cell"
                      tabIndex="0"
                    >
                      <span className="corredor-page__state-dot" aria-hidden="true" />
                      <span className="corredor-page__cell-date">{date}</span>
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}

function orderNodes(nodes, observations) {
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

function getDecisionState(observation) {
  if (!observation) return "MISSING";
  const label = String(observation.confidence_label_es || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  if (label === "USABLE" || observation.confidence_class === "usable") {
    return "USABLE";
  }
  if (label === "REVISAR" || observation.confidence_class === "low_confidence") {
    return "REVISAR";
  }
  if (label === "NO_INFERIR" || observation.confidence_class === "do_not_infer") {
    return "NO_INFERIR";
  }
  return "MISSING";
}

function formatPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "sin dato";
  return `${numeric.toFixed(2)}%`;
}
