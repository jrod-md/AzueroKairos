import React, { useId } from "react";

const DEFAULT_SIZE = 280;
const VIEWBOX_SIZE = 280;
const CENTER = VIEWBOX_SIZE / 2;
const ARC_RADIUS = 94;
const ARC_STROKE_WIDTH = 14;
const ARC_OUTER_EDGE_RADIUS = ARC_RADIUS + ARC_STROKE_WIDTH / 2;
const OUTER_RING_RADIUS = ARC_RADIUS + 20;
const TICK_INNER_RADIUS = ARC_OUTER_EDGE_RADIUS + 2;
const CARDINAL_LABEL_RADIUS = OUTER_RING_RADIUS + 13;
const ARC_START_DEGREES = 135;
const ARC_SWEEP_DEGREES = 270;
const ARC_END_DEGREES = ARC_START_DEGREES + ARC_SWEEP_DEGREES;
const TICK_VALUES = [0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100];
const MAJOR_TICK_VALUES = [0, 25, 50, 75, 100];

const arcPath = describeArc(CENTER, CENTER, ARC_RADIUS, ARC_START_DEGREES, ARC_END_DEGREES);
const tickMarks = TICK_VALUES.map((value) => {
  const angle = percentToAngle(value);
  const isMajor = MAJOR_TICK_VALUES.includes(value);
  const tickLength = isMajor ? 12 : 6;
  return {
    value,
    isMajor,
    inner: polarToCartesian(CENTER, CENTER, TICK_INNER_RADIUS, angle),
    outer: polarToCartesian(CENTER, CENTER, TICK_INNER_RADIUS + tickLength, angle),
  };
});
const cardinalLabels = [0, 100].map((value) => ({
  value,
  position: polarToCartesian(CENTER, CENTER, CARDINAL_LABEL_RADIUS, percentToAngle(value)),
}));

export default function ConfidenceCompass({ validPercent, size = DEFAULT_SIZE }) {
  const gradientId = `confidence-compass-vellum-${useId().replace(/:/g, "")}`;
  const percent = clampPercent(validPercent);
  const displayPercent = `${percent.toFixed(2)}%`;
  const renderedSize = normalizeSize(size);
  const strokeColor = getZoneColor(percent);

  return (
    <svg
      aria-label={`${displayPercent} evidencia válida`}
      role="img"
      width={renderedSize}
      height={renderedSize}
      viewBox={`0 0 ${VIEWBOX_SIZE} ${VIEWBOX_SIZE}`}
      style={{
        display: "block",
        maxWidth: "100%",
        overflow: "visible",
      }}
    >
      <defs>
        <radialGradient id={gradientId} cx="50%" cy="42%" r="70%">
          <stop offset="0%" stopColor="rgba(245, 238, 221, 1)" />
          <stop offset="100%" stopColor="rgba(224, 212, 184, 0.6)" />
        </radialGradient>
      </defs>

      <circle
        cx={CENTER}
        cy={CENTER}
        r={ARC_OUTER_EDGE_RADIUS}
        fill={`url(#${gradientId})`}
      />
      <circle
        cx={CENTER}
        cy={CENTER}
        r={OUTER_RING_RADIUS}
        fill="none"
        stroke="var(--border)"
        strokeWidth="1"
        opacity="0.4"
      />

      <g aria-hidden="true">
        {tickMarks.map((tick) => (
          <line
            key={tick.value}
            x1={tick.inner.x}
            y1={tick.inner.y}
            x2={tick.outer.x}
            y2={tick.outer.y}
            stroke={tick.isMajor ? "var(--text-muted)" : "var(--border)"}
            strokeWidth={tick.isMajor ? 2 : 1}
            strokeLinecap="round"
          />
        ))}
      </g>

      <g aria-hidden="true">
        {cardinalLabels.map((label) => (
          <text
            key={label.value}
            x={label.position.x}
            y={label.position.y}
            textAnchor="middle"
            dominantBaseline="central"
            fill="var(--text-muted)"
            style={{
              fontFamily: "var(--font-data)",
              fontSize: 9,
              fontWeight: 700,
            }}
          >
            {label.value}
          </text>
        ))}
      </g>

      <path
        d={arcPath}
        fill="none"
        stroke="var(--border)"
        strokeWidth={ARC_STROKE_WIDTH}
        strokeLinecap="round"
        pathLength="100"
        opacity="0.6"
      />
      <path
        d={arcPath}
        fill="none"
        stroke={strokeColor}
        strokeWidth={ARC_STROKE_WIDTH}
        strokeLinecap="round"
        pathLength="100"
        style={{
          strokeDasharray: 100,
          strokeDashoffset: 100 - percent,
          transition: "stroke-dashoffset var(--transition-compass, 600ms ease-out)",
        }}
      />

      <text
        x={CENTER}
        y={CENTER - 8}
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--text-primary)"
        style={{
          fontFamily: "var(--font-data)",
          fontSize: 52,
          fontWeight: 600,
          letterSpacing: "-0.02em",
        }}
      >
        {displayPercent}
      </text>
      <line
        x1={CENTER - VIEWBOX_SIZE * 0.2}
        y1={CENTER + 27}
        x2={CENTER + VIEWBOX_SIZE * 0.2}
        y2={CENTER + 27}
        stroke="var(--border)"
        strokeWidth="1"
      />
      <text
        x={CENTER}
        y={CENTER + 48}
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--text-muted)"
        style={{
          fontFamily: "var(--font-ui)",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
        }}
      >
        evidencia válida
      </text>
    </svg>
  );
}

function clampPercent(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return 0;
  return Math.min(100, Math.max(0, numericValue));
}

function normalizeSize(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue) || numericValue <= 0) return DEFAULT_SIZE;
  return numericValue;
}

function getZoneColor(percent) {
  if (percent <= 30) return "var(--state-no-inferir)";
  if (percent < 60) return "var(--state-revisar)";
  return "var(--state-usable)";
}

function percentToAngle(percent) {
  return ARC_START_DEGREES + ARC_SWEEP_DEGREES * (percent / 100);
}

function describeArc(centerX, centerY, radius, startAngle, endAngle) {
  const start = polarToCartesian(centerX, centerY, radius, startAngle);
  const end = polarToCartesian(centerX, centerY, radius, endAngle);
  const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;

  return [
    "M",
    roundCoordinate(start.x),
    roundCoordinate(start.y),
    "A",
    radius,
    radius,
    0,
    largeArcFlag,
    1,
    roundCoordinate(end.x),
    roundCoordinate(end.y),
  ].join(" ");
}

function polarToCartesian(centerX, centerY, radius, angleDegrees) {
  const angleRadians = (angleDegrees * Math.PI) / 180;
  return {
    x: roundCoordinate(centerX + radius * Math.cos(angleRadians)),
    y: roundCoordinate(centerY + radius * Math.sin(angleRadians)),
  };
}

function roundCoordinate(value) {
  return Number(value.toFixed(3));
}
