import React from "react";

const STATE_COLORS = {
  USABLE: "var(--state-usable)",
  REVISAR: "var(--state-revisar)",
  NO_INFERIR: "var(--state-no-inferir)",
};

export default function StatusBar({ activeState }) {
  const state = normalizeState(activeState);

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        left: 0,
        zIndex: 100,
        height: 3,
        background: STATE_COLORS[state],
        transition: "background-color var(--transition-status, 400ms ease)",
        pointerEvents: "none",
      }}
    />
  );
}

function normalizeState(state) {
  const normalized = String(state ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  return STATE_COLORS[normalized] ? normalized : "NO_INFERIR";
}
