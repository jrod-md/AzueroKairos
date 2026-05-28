import React from "react";

const STATE_CONFIG = {
  USABLE: {
    label: "USABLE",
    color: "var(--state-usable)",
    background: "var(--state-usable-bg)",
    rotation: "0deg",
    fontSize: "clamp(2.35rem, 6vw, 3rem)",
    pulse: false,
  },
  REVISAR: {
    label: "REVISAR",
    color: "var(--state-revisar)",
    background: "var(--state-revisar-bg)",
    rotation: "-1deg",
    fontSize: "clamp(2.25rem, 5.5vw, 2.85rem)",
    pulse: false,
  },
  NO_INFERIR: {
    label: "NO INFERIR",
    color: "var(--state-no-inferir)",
    background: "var(--state-no-inferir-bg)",
    rotation: "-1deg",
    fontSize: "clamp(2rem, 5vw, 2.45rem)",
    pulse: true,
  },
};

const STAMP_STYLES = `
  @keyframes decision-stamp-enter {
    from {
      transform: scale(0.85) rotate(var(--rotation));
      opacity: 0;
    }

    to {
      transform: scale(1) rotate(var(--rotation));
      opacity: 1;
    }
  }

  @keyframes decision-stamp-pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(184, 76, 44, 0.3);
    }

    70%,
    100% {
      box-shadow: 0 0 0 8px rgba(184, 76, 44, 0);
    }
  }

  .decision-stamp {
    position: relative;
    isolation: isolate;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: fit-content;
    max-width: 100%;
    border: 3px solid currentColor;
    border-radius: 4px;
    padding: 12px 24px;
    color: var(--stamp-color);
    background: var(--stamp-background);
    font-family: var(--font-display);
    font-size: var(--stamp-font-size);
    font-weight: 800;
    line-height: 1;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    transform: rotate(var(--rotation));
    animation: decision-stamp-enter var(--transition-stamp, 300ms ease);
    animation-fill-mode: both;
  }

  .decision-stamp::before {
    content: "";
    position: absolute;
    inset: 7px;
    border: 1px solid currentColor;
    border-radius: 2px;
    opacity: 0.76;
    pointer-events: none;
  }

  .decision-stamp::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background:
      linear-gradient(90deg, transparent 0 18%, currentColor 18% 19%, transparent 19% 100%),
      linear-gradient(0deg, transparent 0 44%, currentColor 44% 45%, transparent 45% 100%);
    opacity: 0.025;
    mix-blend-mode: multiply;
    pointer-events: none;
  }

  .decision-stamp--pulse {
    animation:
      decision-stamp-enter var(--transition-stamp, 300ms ease),
      decision-stamp-pulse 3s ease-out infinite;
  }

  .decision-stamp--small {
    padding: 8px 14px;
    font-size: clamp(1rem, 2.1vw, 1.28rem);
    letter-spacing: 0.05em;
  }

  .decision-stamp--small::before {
    inset: 5px;
  }
`;

export default function DecisionStamp({ state, size = "default" }) {
  const normalizedState = normalizeState(state);
  const config = STATE_CONFIG[normalizedState];
  const sizeClass = size === "small" ? " decision-stamp--small" : "";

  return (
    <>
      <style>{STAMP_STYLES}</style>
      <div
        key={normalizedState}
        className={`decision-stamp${sizeClass}${config.pulse ? " decision-stamp--pulse" : ""}`}
        style={{
          "--rotation": config.rotation,
          "--stamp-background": config.background,
          "--stamp-color": config.color,
          "--stamp-font-size": config.fontSize,
        }}
      >
        {config.label}
      </div>
    </>
  );
}

function normalizeState(state) {
  const normalized = String(state ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  return STATE_CONFIG[normalized] ? normalized : "NO_INFERIR";
}
