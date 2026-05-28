import React, { useId } from "react";

const DEFAULT_SIZE = 280;
const VIEWBOX_SIZE = 280;
const CENTER = VIEWBOX_SIZE / 2;
const ARC_RADIUS = 94;
const OUTER_RING_RADIUS = 122;
const TICK_INNER_RADIUS = 112;
const TICK_OUTER_RADIUS = 128;
const ARC_START_DEGREES = 135;
const ARC_SWEEP_DEGREES = 270;
const ARC_END_DEGREES = ARC_START_DEGREES + ARC_SWEEP_DEGREES;
const TICK_VALUES = [0, 25, 50, 75, 100];

const arcPath = describeArc(CENTER, CENTER, ARC_RADIUS, ARC_START_DEGREES, ARC_END_DEGREES);
const tickMarks = TICK_VALUES.map((value) => {
  const angle = percentToAngle(value);
  return {
    value,
    inner: polarToCartesian(CENTER, CENTER, TICK_INNER_RADIUS, angle),
    outer: polarToCartesian(CENTER, CENTER, TICK_OUTER_RADIUS, angle),
  };
});

export default function ConfidenceCompass({ validPercent, size = DEFAULT_SIZE }) {
  const gradientId = `confidence-compass-paper-${useId().replace(/:/g, "")}`;
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
        <radialGradient id={gradientId} cx="48%" cy="38%" r="72%">
          <stop offset="0%" stopColor="var(--bg-surface)" />
          <stop offset="100%" stopColor="var(--bg-base)" />
        </radialGradient>
      </defs>

      <circle
        cx={CENTER}
        cy={CENTER}
        r={OUTER_RING_RADIUS}
        fill={`url(#${gradientId})`}
        stroke="var(--border-subtle)"
        strokeWidth="1"
      />
      <circle
        cx={CENTER}
        cy={CENTER}
        r="104"
        fill="none"
        stroke="var(--border-subtle)"
        strokeWidth="1"
        strokeDasharray="2 7"
      />
      <circle
        cx={CENTER}
        cy={CENTER}
        r="70"
        fill="none"
        stroke="var(--border-subtle)"
        strokeWidth="1"
        opacity="0.55"
      />

      <g aria-hidden="true">
        {tickMarks.map((tick) => (
          <line
            key={tick.value}
            x1={tick.inner.x}
            y1={tick.inner.y}
            x2={tick.outer.x}
            y2={tick.outer.y}
            stroke="var(--text-secondary)"
            strokeWidth={tick.value === 50 ? 2 : 1.4}
            strokeLinecap="round"
            opacity={tick.value === 50 ? 0.72 : 0.5}
          />
        ))}
      </g>

      <path
        d={arcPath}
        fill="none"
        stroke="var(--border)"
        strokeWidth="9"
        strokeLinecap="round"
        pathLength="100"
        opacity="0.7"
      />
      <path
        d={arcPath}
        fill="none"
        stroke={strokeColor}
        strokeWidth="11"
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
        y={CENTER - 4}
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--text-primary)"
        style={{
          fontFamily: "var(--font-data)",
          fontSize: 48,
          fontWeight: 650,
          letterSpacing: 0,
        }}
      >
        {displayPercent}
      </text>
      <text
        x={CENTER}
        y={CENTER + 38}
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--text-secondary)"
        style={{
          fontFamily: "var(--font-ui)",
          fontSize: 12,
          fontWeight: 700,
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
