import React, { useId } from "react";

const STATE_CONFIG = {
  USABLE: {
    label: "USABLE",
    color: "var(--state-usable)",
    background: "var(--state-usable-bg)",
    rotation: "0deg",
    shadow: "none",
  },
  REVISAR: {
    label: "REVISAR",
    color: "var(--state-revisar)",
    background: "var(--state-revisar-bg)",
    rotation: "-0.8deg",
    shadow: "none",
  },
  NO_INFERIR: {
    label: "NO INFERIR",
    color: "var(--state-no-inferir)",
    background: "var(--state-no-inferir-bg)",
    rotation: "1.2deg",
    shadow: "0 0 20px rgba(184, 76, 44, 0.15)",
  },
};

const STAMP_STYLES = `
  @keyframes stampDrop {
    0% {
      transform: translateY(-10px) rotate(var(--stamp-rotate)) scale(calc(var(--stamp-scale, 1) * 1.45));
      opacity: 0;
      filter: blur(2px);
    }

    48% {
      transform: translateY(1px) rotate(var(--stamp-rotate)) scale(calc(var(--stamp-scale, 1) * 0.96));
      opacity: 1;
      filter: blur(0);
    }

    72% {
      transform: translateY(0) rotate(var(--stamp-rotate)) scale(calc(var(--stamp-scale, 1) * 1.035));
      filter: blur(0);
    }

    100% {
      transform: translateY(0) rotate(var(--stamp-rotate)) scale(var(--stamp-scale, 1));
      opacity: 1;
      filter: blur(0);
    }
  }

  .decision-stamp {
    position: relative;
    isolation: isolate;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: min(100%, 300px);
    aspect-ratio: 16 / 5;
    max-width: 100%;
    color: var(--stamp-color);
    background: transparent;
    box-shadow: var(--stamp-shadow);
    transform: rotate(var(--stamp-rotate)) scale(var(--stamp-scale, 1));
    animation: stampDrop 420ms cubic-bezier(0.25, 1, 0.5, 1);
    animation-fill-mode: both;
    transform-origin: center;
    will-change: transform, opacity, filter;
  }

  .decision-stamp--static {
    animation: none;
    opacity: 1;
    transform: rotate(var(--stamp-rotate)) scale(var(--stamp-scale, 1));
  }

  .decision-stamp__frame {
    position: absolute;
    inset: 0;
    display: block;
    width: 100%;
    height: 100%;
    overflow: visible;
    pointer-events: none;
  }

  .decision-stamp__text {
    position: relative;
    z-index: 1;
    padding: 0 22px;
    color: currentColor;
    font-family: var(--font-display);
    font-size: clamp(1.6rem, 3vw, 2.2rem);
    font-weight: 700;
    line-height: 0.95;
    letter-spacing: 0.08em;
    text-align: center;
    text-transform: uppercase;
    text-wrap: balance;
    opacity: 0.94;
    mix-blend-mode: multiply;
    text-shadow: 0 1px 0 color-mix(in oklch, currentColor 12%, transparent);
  }

  .decision-stamp__outer {
    fill: none;
  }

  .decision-stamp__outer,
  .decision-stamp__inner {
    stroke: currentColor;
    vector-effect: non-scaling-stroke;
  }

  .decision-stamp--small {
    width: min(100%, 190px);
  }

  .decision-stamp--small .decision-stamp__text {
    padding: 0 14px;
    font-size: clamp(0.95rem, 1.65vw, 1.18rem);
    letter-spacing: 0.07em;
  }
`;

export default function DecisionStamp({
  state,
  size = "default",
  animated = true,
  scale = 1,
}) {
  const textureId = `stamp-texture-${useId().replace(/:/g, "")}`;
  const normalizedState = normalizeState(state);
  const config = STATE_CONFIG[normalizedState];
  const sizeClass = size === "small" ? " decision-stamp--small" : "";

  return (
    <>
      <style>{STAMP_STYLES}</style>
      <div
        key={normalizedState}
        className={`decision-stamp${sizeClass}${animated ? "" : " decision-stamp--static"}`}
        style={{
          "--stamp-color": config.color,
          "--stamp-rotate": config.rotation,
          "--stamp-scale": scale,
          "--stamp-shadow": config.shadow,
        }}
      >
        <svg
          className="decision-stamp__frame"
          viewBox="0 0 320 100"
          preserveAspectRatio="none"
          aria-hidden="true"
          focusable="false"
        >
          <defs>
            <filter id={textureId} colorInterpolationFilters="sRGB">
              <feTurbulence
                type="turbulence"
                baseFrequency="0.045"
                numOctaves="2"
                seed="7"
                result="distortion"
              />
              <feDisplacementMap
                in="SourceGraphic"
                in2="distortion"
                scale="1.7"
                xChannelSelector="R"
                yChannelSelector="G"
              />
            </filter>
          </defs>
          <rect
            className="decision-stamp__outer"
            x="3"
            y="3"
            width="314"
            height="94"
            rx="3"
            ry="3"
            strokeWidth="3"
            filter={`url(#${textureId})`}
          />
          <rect
            className="decision-stamp__inner"
            x="11"
            y="11"
            width="298"
            height="78"
            rx="3"
            ry="3"
            strokeWidth="1.5"
            fill={config.background}
            fillOpacity="0.6"
          />
        </svg>
        <span className="decision-stamp__text">{config.label}</span>
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
