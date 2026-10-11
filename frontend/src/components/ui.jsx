import React from "react";
import { THRESHOLDS, formatPercent, stateOf } from "../lib/data.js";

// Ink roughness for the decision stamp. Rendered once at the app root.
export function InkFilter() {
  return (
    <svg className="ink-defs" aria-hidden="true" focusable="false" width="0" height="0">
      <filter id="kairos-ink" x="-5%" y="-10%" width="110%" height="120%">
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3" result="grain" />
        <feDisplacementMap in="SourceGraphic" in2="grain" scale="2.4" result="rough" />
        <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" seed="11" result="blot" />
        <feColorMatrix
          in="blot"
          type="matrix"
          values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 2"
          result="wear"
        />
        <feComposite in="rough" in2="wear" operator="in" />
      </filter>
    </svg>
  );
}

export function Stamp({ confidenceClass, size = "lg" }) {
  const state = stateOf(confidenceClass);
  return (
    <span className={`stamp stamp--${size} tone-${state.tone}`} key={state.id}>
      {state.label}
    </span>
  );
}

export function StateTag({ confidenceClass }) {
  const state = stateOf(confidenceClass);
  return (
    <span className={`state-tag tone-${state.tone}`}>
      <span className="state-tag__dot" aria-hidden="true" />
      {state.label}
    </span>
  );
}

// The decision rule drawn to scale: marks at 10% and 30%.
export function ThresholdBar({ value, confidenceClass, labels = false }) {
  const state = stateOf(confidenceClass);
  const numeric = Number(value);
  const width = Number.isFinite(numeric) ? Math.max(0, Math.min(100, numeric)) : 0;

  return (
    <span
      className={`tbar tone-${state.tone}${labels ? " tbar--labels" : ""}`}
      role="img"
      aria-label={`${formatPercent(value)} de cobertura válida. Umbrales en ${THRESHOLDS.review}% y ${THRESHOLDS.usable}%.`}
    >
      <span className="tbar__track">
        <span className="tbar__fill" style={{ width: `${width}%` }} />
        <span className="tbar__mark" style={{ left: `${THRESHOLDS.review}%` }} />
        <span className="tbar__mark" style={{ left: `${THRESHOLDS.usable}%` }} />
      </span>
      {labels ? (
        <span className="tbar__scale" aria-hidden="true">
          <span style={{ left: 0 }}>0</span>
          <span style={{ left: `${THRESHOLDS.review}%` }}>{THRESHOLDS.review}</span>
          <span style={{ left: `${THRESHOLDS.usable}%` }}>{THRESHOLDS.usable}</span>
          <span style={{ left: "100%" }}>100%</span>
        </span>
      ) : null}
    </span>
  );
}

export function Section({ number, title, note, children, id, className = "" }) {
  return (
    <section className={`sec ${className}`} id={id} aria-labelledby={id ? `${id}-title` : undefined}>
      <header className="sec__head">
        <span className="sec__num" aria-hidden="true">
          {number}
        </span>
        <h2 className="sec__title" id={id ? `${id}-title` : undefined}>
          {title}
        </h2>
        {note ? <p className="sec__note">{note}</p> : null}
      </header>
      <div className="sec__body">{children}</div>
    </section>
  );
}

export function Fact({ label, children, mono = false }) {
  return (
    <div className="fact">
      <dt>{label}</dt>
      <dd className={mono ? "mono" : undefined}>{children}</dd>
    </div>
  );
}
