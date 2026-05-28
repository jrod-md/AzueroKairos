import React from "react";

const VIEWBOX_WIDTH = 720;
const VIEWBOX_HEIGHT = 120;
const NODE_RADIUS = 12;
const DEFAULT_GATES = [
  { id: "api", label: "API", result: "PENDIENTE", state: "pending" },
  { id: "quality", label: "CALIDAD", result: "PENDIENTE", state: "pending" },
  { id: "inference", label: "INFERENCIA", result: "PENDIENTE", state: "pending" },
  { id: "action", label: "ACCIÓN", result: "PENDIENTE", state: "pending" },
];

const NODE_POSITIONS = [
  { x: 72, y: 38 },
  { x: 264, y: 28 },
  { x: 456, y: 46 },
  { x: 648, y: 34 },
];

export default function GateChain({ gates = DEFAULT_GATES }) {
  const normalizedGates = normalizeGates(gates);
  const connectors = normalizedGates.slice(0, -1).map((gate, index) => ({
    id: `${gate.id}-${normalizedGates[index + 1].id}`,
    path: buildConnectorPath(NODE_POSITIONS[index], NODE_POSITIONS[index + 1], index),
    broken: gate.state === "passed" && normalizedGates[index + 1].state === "failed",
  }));

  return (
    <svg
      aria-label="Cadena de decisión territorial"
      role="img"
      viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
      preserveAspectRatio="xMidYMid meet"
      style={{
        display: "block",
        width: "100%",
        height: 120,
        overflow: "visible",
      }}
    >
      <g aria-hidden="true">
        {connectors.map((connector) => (
          <path
            key={connector.id}
            d={connector.path}
            fill="none"
            stroke="var(--border)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={connector.broken ? "4 4" : undefined}
          />
        ))}
      </g>

      {normalizedGates.map((gate, index) => {
        const position = NODE_POSITIONS[index];
        const visual = getGateVisual(gate.state);

        return (
          <g key={gate.id} transform={`translate(${position.x} ${position.y})`}>
            <circle
              r={NODE_RADIUS}
              fill={visual.fill}
              stroke={visual.stroke}
              strokeWidth="2"
            />
            {gate.state === "failed" ? (
              <text
                x="0"
                y="0"
                textAnchor="middle"
                dominantBaseline="central"
                fill="var(--bg-surface)"
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 16,
                  fontWeight: 800,
                }}
              >
                ×
              </text>
            ) : null}
            <text
              className="section-label"
              x="0"
              y="39"
              textAnchor="middle"
              fill="var(--text-muted)"
              style={{
                fontFamily: "var(--font-ui)",
                fontSize: 11,
                fontWeight: 800,
                letterSpacing: "0.12em",
              }}
            >
              {gate.label}
            </text>
            <text
              x="0"
              y="58"
              textAnchor="middle"
              fill={visual.resultFill}
              style={{
                fontFamily: "var(--font-ui)",
                fontSize: 11,
                fontWeight: 760,
                letterSpacing: "0.02em",
              }}
            >
              {gate.result}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function normalizeGates(gates) {
  const gateList = Array.isArray(gates) ? gates : [];

  return DEFAULT_GATES.map((defaultGate, index) => {
    const gate = gateList[index] ?? {};
    return {
      id: String(gate.id || defaultGate.id),
      label: String(gate.label || defaultGate.label).toUpperCase(),
      result: String(gate.result || defaultGate.result).toUpperCase(),
      state: normalizeState(gate.state || defaultGate.state),
    };
  });
}

function normalizeState(state) {
  return ["passed", "failed", "pending"].includes(state) ? state : "pending";
}

function getGateVisual(state) {
  if (state === "passed") {
    return {
      fill: "var(--state-usable)",
      stroke: "var(--state-usable)",
      resultFill: "var(--text-primary)",
    };
  }

  if (state === "failed") {
    return {
      fill: "var(--state-no-inferir)",
      stroke: "var(--state-no-inferir)",
      resultFill: "var(--state-no-inferir)",
    };
  }

  return {
    fill: "var(--bg-surface)",
    stroke: "var(--border)",
    resultFill: "var(--text-secondary)",
  };
}

function buildConnectorPath(start, end, index) {
  const startX = start.x + NODE_RADIUS;
  const endX = end.x - NODE_RADIUS;
  const wave = index % 2 === 0 ? -18 : 20;
  const controlOne = {
    x: startX + (endX - startX) * 0.34,
    y: start.y + wave,
  };
  const controlTwo = {
    x: startX + (endX - startX) * 0.66,
    y: end.y - wave,
  };

  return [
    "M",
    round(startX),
    round(start.y),
    "C",
    round(controlOne.x),
    round(controlOne.y),
    round(controlTwo.x),
    round(controlTwo.y),
    round(endX),
    round(end.y),
  ].join(" ");
}

function round(value) {
  return Number(value.toFixed(2));
}
