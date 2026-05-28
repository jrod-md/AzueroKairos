import React from "react";

const NAV_ITEMS = [
  { id: "decision", label: "Decisión" },
  { id: "watch", label: "Corredor" },
  { id: "cases", label: "Acción" },
  { id: "technical", label: "Evidencia" },
];

const STATE_COLORS = {
  USABLE: "var(--state-usable)",
  REVISAR: "var(--state-revisar)",
  NO_INFERIR: "var(--state-no-inferir)",
};

const NAVIGATION_STYLES = `
  @keyframes az-navigation-dot-pulse {
    0%,
    100% {
      opacity: 0.35;
      transform: scale(1);
    }

    50% {
      opacity: 1;
      transform: scale(1.9);
    }
  }

  .az-navigation {
    display: inline-flex;
    max-width: 100%;
  }

  .az-navigation__pill {
    display: inline-flex;
    max-width: 100%;
    align-items: center;
    gap: var(--space-sm);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 5px;
    background: var(--bg-archive);
    box-shadow: 0 14px 34px color-mix(in oklch, var(--text-primary) 12%, transparent);
  }

  .az-navigation__tabs {
    display: inline-flex;
    gap: 3px;
  }

  .az-navigation__tab {
    min-height: 34px;
    border: 0;
    border-radius: 999px;
    padding: 0 14px;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-ui);
    font-size: 13px;
    font-weight: 760;
    cursor: pointer;
    transition:
      background-color var(--transition-fast),
      color var(--transition-fast),
      transform var(--transition-fast);
  }

  .az-navigation__tab:active {
    transform: translateY(1px);
  }

  .az-navigation__tab.is-active {
    background: var(--text-primary);
    color: var(--bg-surface);
  }

  .az-navigation__status {
    display: inline-flex;
    min-height: 30px;
    align-items: center;
    gap: 8px;
    border-left: 1px solid var(--border-subtle);
    padding: 0 11px 0 13px;
    color: var(--text-muted);
    font-family: var(--font-data);
    font-size: 11px;
    font-weight: 680;
    letter-spacing: 0.04em;
    white-space: nowrap;
  }

  .az-navigation__dot {
    width: 2px;
    height: 2px;
    border-radius: 999px;
    background: var(--state-usable);
    animation: az-navigation-dot-pulse 2.4s ease-out infinite;
  }

  @media (max-width: 760px) {
    .az-navigation,
    .az-navigation__pill {
      width: 100%;
    }

    .az-navigation__pill {
      align-items: stretch;
      flex-direction: column;
      border-radius: var(--radius-lg);
    }

    .az-navigation__tabs {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .az-navigation__status {
      justify-content: center;
      border-top: 1px solid var(--border-subtle);
      border-left: 0;
      padding: 8px 10px 4px;
      white-space: normal;
      text-align: center;
    }
  }
`;

export default function Navigation({
  activeState,
  activePage = "decision",
  onNavigate = () => {},
}) {
  const state = normalizeState(activeState);

  return (
    <header
      className="az-navigation"
      data-active-state={state}
      style={{ "--navigation-state-color": STATE_COLORS[state] }}
    >
      <style>{NAVIGATION_STYLES}</style>
      <nav className="az-navigation__pill" aria-label="Navegación principal">
        <div className="az-navigation__tabs">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`az-navigation__tab${activePage === item.id ? " is-active" : ""}`}
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="az-navigation__status" aria-label="Estado oficial del ledger">
          <span className="az-navigation__dot" aria-hidden="true" />
          <span>COPERNICUS OFICIAL · LEDGER OK</span>
        </div>
      </nav>
    </header>
  );
}

function normalizeState(state) {
  const normalized = String(state ?? "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_");

  return STATE_COLORS[normalized] ? normalized : "NO_INFERIR";
}
