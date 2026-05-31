import React, { useMemo, useState } from "react";

const VIEWBOX_WIDTH = 1600;
const VIEWBOX_HEIGHT = 500;
const NODE_POSITIONS = [
  { x: 400, y: 246 },
  { x: 800, y: 230 },
  { x: 1200, y: 246 },
];

const LAYERS = [
  { id: "s2", label: "S-2 DECISIÓN", helper: "capa primaria" },
  { id: "s1", label: "S-1 SAR", helper: "contexto auxiliar" },
  { id: "clms", label: "CLMS", helper: "contexto auxiliar" },
  { id: "hydro", label: "HYDRO", helper: "contexto auxiliar" },
];

const STATE_COLORS = {
  USABLE: "var(--state-usable)",
  REVISAR: "var(--state-revisar)",
  NO_INFERIR: "var(--state-no-inferir)",
};

const LENS_STYLES = `
  @keyframes azuero-lens-sonar {
    0% {
      opacity: 0.4;
      transform: scale(1);
    }

    100% {
      opacity: 0;
      transform: scale(2);
    }
  }

  .az-lens {
    width: 100%;
  }

  .az-lens__controls {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-sm);
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .az-lens__toggle {
    min-height: 30px;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0 12px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-ui);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    transition:
      background-color var(--transition-fast),
      color var(--transition-fast),
      border-color var(--transition-fast),
      transform var(--transition-fast);
  }

  .az-lens__toggle:active {
    transform: translateY(1px);
  }

  .az-lens__toggle.is-active {
    border-color: var(--text-primary);
    background: var(--text-primary);
    color: var(--bg-surface);
  }

  .az-lens__aux-badge {
    border: 1px solid color-mix(in oklch, var(--state-revisar) 32%, var(--border));
    border-radius: 999px;
    padding: 6px 10px;
    background: var(--state-revisar-bg);
    color: var(--state-revisar);
    font-family: var(--font-ui);
    font-size: 11px;
    font-weight: 820;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .az-lens__context-control {
    display: grid;
    gap: 4px;
    margin-left: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 7px 10px;
    background: color-mix(in oklch, var(--bg-surface) 72%, transparent);
  }

  .az-lens__context-row {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
    color: var(--text-secondary);
    font-family: var(--font-ui);
    font-size: 10px;
    font-weight: 780;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .az-lens__context-row input {
    width: 118px;
    accent-color: var(--state-usable);
    cursor: pointer;
  }

  .az-lens__context-note {
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: 10px;
    font-weight: 680;
  }

  .az-lens__stage {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 5;
    overflow: hidden;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    background: var(--bg-archive);
  }

  .az-lens__stage::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 0;
    background-image: url("/img/aerial-view.png");
    background-position: center;
    background-size: cover;
    opacity: var(--territory-opacity, 0.08);
    transition: opacity 150ms ease-out;
    pointer-events: none;
  }

  .az-lens__svg {
    position: relative;
    z-index: 1;
    display: block;
    width: 100%;
    height: 100%;
  }

  .az-lens__node {
    color: var(--node-color);
    outline: none;
    cursor: default;
  }

  .az-lens__node:focus-visible .az-lens__node-core {
    stroke: var(--bg-surface);
    stroke-width: 3;
  }

  .az-lens__node-sonar {
    transform-box: fill-box;
    transform-origin: center;
    animation: azuero-lens-sonar 4s ease-out infinite;
  }

  .az-lens__node-label {
    font-family: var(--font-data);
    font-size: 11px;
    font-weight: 720;
    letter-spacing: 0.04em;
    fill: var(--text-primary);
    text-shadow: 0 1px 3px rgba(29, 53, 87, 0.4);
  }

  .az-lens__sun {
    filter: drop-shadow(0 0 12px rgba(232, 146, 46, 0.5));
  }

  .az-lens__field-card {
    position: absolute;
    z-index: 3;
    min-width: 190px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 12px;
    background: color-mix(in oklch, var(--bg-surface) 94%, transparent);
    box-shadow: 0 16px 34px color-mix(in oklch, var(--text-primary) 18%, transparent);
    color: var(--text-primary);
    pointer-events: none;
    transform: translate(-50%, calc(-100% - 24px));
  }

  .az-lens__field-card::after {
    content: "";
    position: absolute;
    left: 50%;
    bottom: -7px;
    width: 12px;
    height: 12px;
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    background: color-mix(in oklch, var(--bg-surface) 94%, transparent);
    transform: translateX(-50%) rotate(45deg);
  }

  .az-lens__field-card h3 {
    margin: 0;
    color: var(--text-primary);
    font-family: var(--font-display);
    font-size: 1.02rem;
    line-height: 1.05;
  }

  .az-lens__field-card dl {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr);
    gap: 6px 10px;
    margin: 10px 0 0;
  }

  .az-lens__field-card dt {
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .az-lens__field-card dd {
    min-width: 0;
    margin: 0;
    color: var(--text-primary);
    font-family: var(--font-data);
    font-size: 11px;
    font-weight: 720;
    overflow-wrap: anywhere;
  }

  .az-lens__field-card .az-lens__state-value {
    color: var(--node-color);
  }

  .az-lens__card-badge {
    display: inline-flex;
    width: fit-content;
    margin-top: 10px;
    border-radius: 999px;
    padding: 5px 8px;
    background: var(--state-revisar-bg);
    color: var(--state-revisar);
    font-family: var(--font-ui);
    font-size: 10px;
    font-weight: 820;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .az-lens__disclaimer {
    position: absolute;
    z-index: 2;
    right: var(--space-md);
    bottom: var(--space-sm);
    left: var(--space-md);
    margin: 0;
    text-align: center;
  }

  @media (max-width: 760px) {
    .az-lens__context-control {
      width: 100%;
      margin-left: 0;
    }

    .az-lens__field-card {
      min-width: 170px;
      transform: translate(-50%, calc(-100% - 18px));
    }
  }
`;

export default function AzueroLens({ nodes = [] }) {
  const [activeLayer, setActiveLayer] = useState("s2");
  const [territoryOpacity, setTerritoryOpacity] = useState(0.08);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const lensNodes = useMemo(() => normalizeNodes(nodes), [nodes]);
  const hoveredNode = lensNodes.find((node) => node.id === hoveredNodeId);
  const activeLayerMeta = LAYERS.find((layer) => layer.id === activeLayer) ?? LAYERS[0];
  const showingAuxiliaryLayer = activeLayer !== "s2";

  return (
    <section className="az-lens" aria-label="Azuero Lens">
      <style>{LENS_STYLES}</style>
      <div className="az-lens__controls" aria-label="Capas del Azuero Lens">
        {LAYERS.map((layer) => (
          <button
            key={layer.id}
            type="button"
            aria-pressed={activeLayer === layer.id}
            className={`az-lens__toggle${activeLayer === layer.id ? " is-active" : ""}`}
            onClick={() => setActiveLayer(layer.id)}
          >
            {layer.label}
          </button>
        ))}
        {showingAuxiliaryLayer ? (
          <span className="az-lens__aux-badge">{activeLayerMeta.helper}</span>
        ) : null}
        <label className="az-lens__context-control">
          <span className="section-label">Contexto territorial</span>
          <span className="az-lens__context-row">
            <span>Esquema</span>
            <input
              type="range"
              min="0"
              max="0.1"
              step="0.01"
              value={territoryOpacity}
              aria-label="Opacidad de referencia territorial"
              onChange={(event) => {
                const nextOpacity = Number(event.target.value);
                setTerritoryOpacity(Math.min(0.1, Math.max(0, nextOpacity)));
              }}
            />
            <span>{Math.round(territoryOpacity * 100)}%</span>
          </span>
          <span className="az-lens__context-note">Referencia visual no satelital.</span>
        </label>
      </div>

      <div
        className="az-lens__stage"
        style={{ "--territory-opacity": territoryOpacity.toFixed(2) }}
      >
        <svg
          className="az-lens__svg"
          viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
          role="img"
          aria-label="Vista esquemática ilustrada del corredor Río La Villa"
          focusable="false"
        >
          <defs>
            <linearGradient
              id="azueroLensSky"
              gradientUnits="userSpaceOnUse"
              x1="0"
              y1="0"
              x2="0"
              y2="190"
            >
              <stop offset="0%" stopColor="var(--text-primary)" stopOpacity="0.15" />
              <stop offset="100%" stopColor="var(--text-primary)" stopOpacity="0" />
            </linearGradient>
            <radialGradient id="azueroLensVignette" cx="50%" cy="48%" r="72%">
              <stop offset="0%" stopColor="var(--bg-archive)" stopOpacity="0" />
              <stop offset="72%" stopColor="var(--text-primary)" stopOpacity="0.02" />
              <stop offset="100%" stopColor="var(--text-primary)" stopOpacity="0.22" />
            </radialGradient>
          </defs>

          <rect width={VIEWBOX_WIDTH} height={VIEWBOX_HEIGHT} fill="transparent" />

          <rect width={VIEWBOX_WIDTH} height="190" fill="url(#azueroLensSky)" pointerEvents="none" />
          <path
            d="M-44 118 C98 74 226 74 358 102 C492 130 594 78 732 92 C874 108 990 66 1154 78 C1326 88 1484 130 1644 104 C1630 132 1580 164 1478 172 C1350 184 1256 164 1138 178 C1006 194 904 154 760 172 C602 190 476 158 326 176 C184 194 58 168 -44 184 Z"
            fill="var(--text-primary)"
            opacity="0.35"
            pointerEvents="none"
          />
          <path
            d="M-44 154 C86 104 220 114 360 134 C510 156 620 112 766 124 C924 138 1042 110 1190 116 C1348 124 1490 154 1644 132 C1592 168 1508 198 1390 204 C1264 212 1158 188 1048 196 C902 206 806 176 674 190 C516 206 430 180 288 184 C154 188 42 204 -44 216 Z"
            fill="var(--text-primary)"
            opacity="0.55"
            pointerEvents="none"
          />
          <path
            d="M-42 356 C118 268 236 318 368 276 C508 232 584 310 702 294 C820 278 886 222 1008 246 C1138 272 1226 342 1368 294 C1482 256 1550 284 1642 236 L1642 532 L-42 532 Z"
            fill="var(--state-no-inferir)"
            opacity="0.7"
          />
          <path
            d="M-34 430 C104 380 210 398 326 352 C472 294 574 364 704 334 C844 302 912 372 1054 340 C1208 306 1328 232 1640 262 L1640 532 L-34 532 Z"
            fill="var(--state-revisar)"
            opacity="0.35"
          />
          <path
            d="M910 314 C1028 242 1122 286 1228 232 C1346 172 1458 218 1640 160 L1640 532 L880 532 C820 438 812 374 910 314 Z"
            fill="var(--state-revisar)"
            opacity="0.6"
          />
          <path
            d="M-24 224 C104 156 200 186 310 142 C438 92 560 148 666 116 C748 90 820 94 882 132 C950 174 1040 152 1138 118 C1270 72 1396 112 1624 70"
            fill="none"
            stroke="var(--border-subtle)"
            strokeWidth="1"
            opacity="0.72"
          />
          <path
            d="M-36 284 C150 218 276 292 410 246 C548 198 640 160 800 230 C942 292 1056 282 1200 246 C1356 206 1460 228 1636 176"
            fill="none"
            stroke="var(--state-usable)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M-36 284 C150 218 276 292 410 246 C548 198 640 160 800 230 C942 292 1056 282 1200 246 C1356 206 1460 228 1636 176"
            fill="none"
            stroke="var(--bg-surface)"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.42"
          />

          <circle
            className="az-lens__sun"
            cx="1476"
            cy="88"
            r="20"
            fill="var(--state-revisar)"
            opacity="0.92"
          />

          {lensNodes.map((node, index) => {
            const position = NODE_POSITIONS[index];
            return (
              <g
                key={node.id}
                className="az-lens__node"
                tabIndex="0"
                role="group"
                aria-label={`${node.name}, ${formatPercent(node.validPercent)}, ${node.state}`}
                transform={`translate(${position.x} ${position.y})`}
                style={{ "--node-color": node.color }}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onFocus={() => setHoveredNodeId(node.id)}
                onBlur={() => setHoveredNodeId(null)}
              >
                <circle
                  className="az-lens__node-sonar"
                  r="16"
                  fill="none"
                  stroke="var(--node-color)"
                  strokeWidth="1.5"
                  opacity="0.4"
                  style={{ animationDelay: `${index * 1.4}s` }}
                />
                <circle
                  className="az-lens__node-core"
                  r="8"
                  fill="var(--node-color)"
                />
                <text
                  className="az-lens__node-label"
                  x="0"
                  y="-24"
                  textAnchor="middle"
                >
                  {node.name}
                </text>
              </g>
            );
          })}

          <rect
            width={VIEWBOX_WIDTH}
            height={VIEWBOX_HEIGHT}
            fill="url(#azueroLensVignette)"
            pointerEvents="none"
          />
        </svg>

        {hoveredNode ? (
          <FieldCard
            node={hoveredNode}
            activeLayerLabel={activeLayerMeta.label}
            showAuxiliaryBadge={showingAuxiliaryLayer}
          />
        ) : null}

        <p className="section-label az-lens__disclaimer">
          Vista esquemática de evidencia territorial. No es imagen satelital ni mapa exacto.
        </p>
      </div>
    </section>
  );
}

function FieldCard({ node, activeLayerLabel, showAuxiliaryBadge }) {
  const position = node.position;

  return (
    <article
      className="az-lens__field-card"
      style={{
        left: `${(position.x / VIEWBOX_WIDTH) * 100}%`,
        top: `${(position.y / VIEWBOX_HEIGHT) * 100}%`,
        "--node-color": node.color,
      }}
    >
      <h3>{node.name}</h3>
      <dl>
        <dt>Fecha</dt>
        <dd>{node.date || "sin fecha"}</dd>
        <dt>Valid%</dt>
        <dd>{formatPercent(node.validPercent)}</dd>
        <dt>Decisión</dt>
        <dd className="az-lens__state-value">{node.stateLabel}</dd>
      </dl>
      {showAuxiliaryBadge ? (
        <span className="az-lens__card-badge">{activeLayerLabel} contexto auxiliar</span>
      ) : null}
    </article>
  );
}

function normalizeNodes(nodes) {
  if (!Array.isArray(nodes)) return [];

  return nodes.slice(0, NODE_POSITIONS.length).map((node, index) => {
    const state = normalizeState(node.state);
    return {
      id: String(node.id || `node-${index + 1}`),
      name: String(node.name || node.id || "Sin nombre"),
      state,
      stateLabel: state.replace("_", " "),
      color: STATE_COLORS[state],
      validPercent: safeNumber(node.validPercent),
      date: String(node.date || ""),
      position: NODE_POSITIONS[index],
    };
  });
}

function normalizeState(state) {
  const normalized = String(state ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  return STATE_COLORS[normalized] ? normalized : "NO_INFERIR";
}

function safeNumber(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.min(100, Math.max(0, numeric));
}

function formatPercent(value) {
  return `${safeNumber(value).toFixed(2)}%`;
}
