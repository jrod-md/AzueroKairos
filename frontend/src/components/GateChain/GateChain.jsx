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

const CHAIN_STYLES = `
  @keyframes gate-chain-node-reveal {
    0% {
      opacity: 0.28;
      transform: scale(0.72);
    }

    72% {
      opacity: 1;
      transform: scale(1.08);
    }

    100% {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes gate-chain-path-reveal {
    0% {
      opacity: 0.25;
      stroke-dashoffset: 18;
    }

    100% {
      opacity: 1;
      stroke-dashoffset: 0;
    }
  }

  .gate-chain__connector {
    animation: gate-chain-path-reveal 420ms ease-out both;
    animation-delay: calc(var(--gate-step, 0) * 150ms);
  }

  .gate-chain__node-inner {
    transform-box: fill-box;
    transform-origin: center;
    animation: gate-chain-node-reveal 360ms cubic-bezier(0.34, 1.56, 0.64, 1) both;
    animation-delay: calc(var(--gate-step, 0) * 150ms);
  }
`;

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
      <style>{CHAIN_STYLES}</style>
      <g aria-hidden="true">
        {connectors.map((connector, index) => (
          <path
            key={connector.id}
            className="gate-chain__connector"
            d={connector.path}
            fill="none"
            stroke="var(--border)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={connector.broken ? "4 4" : undefined}
            style={{ "--gate-step": index + 1 }}
          />
        ))}
      </g>

      {normalizedGates.map((gate, index) => {
        const position = NODE_POSITIONS[index];
        const visual = getGateVisual(gate.state);

        return (
          <g key={gate.id} transform={`translate(${position.x} ${position.y})`}>
            <g className="gate-chain__node-inner" style={{ "--gate-step": index }}>
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
