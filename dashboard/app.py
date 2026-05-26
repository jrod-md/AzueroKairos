"""Streamlit decision console for the Azuero Kairós MVP."""

from __future__ import annotations

import csv
from html import escape
import math
from pathlib import Path
import sys
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from azuero_kairos.brief_generator import generate_confidence_brief
from azuero_kairos.confidence_engine import (
    CONFIDENCE_LABELS_ES,
    DECISION_LABELS_ES as DECISION_LABELS_BY_CONFIDENCE_ES,
    REASONS_ES,
    RECOMMENDED_ACTIONS_ES,
)


DATES = ["2025-06-02", "2025-06-10", "2025-06-15", "2025-06-30", "2025-07-15"]
AOIS = ["corridor_wide", "river"]
DEFAULT_DATE = "2025-06-10"
DEFAULT_AOI = "corridor_wide"
PROCESSED_DIR = PROJECT_ROOT / "outputs" / "processed_csv"
BRIEF_DIR = PROJECT_ROOT / "outputs" / "briefs"
LEDGER_PATH = PROJECT_ROOT / "outputs" / "ledger" / "evidence_ledger.csv"

CONFIDENCE_DISPLAY = {
    "usable": "USABLE",
    "low_confidence": "BAJA CONFIANZA",
    "do_not_infer": "NO INFERIR",
}

WHAT_NOW = {
    "usable": "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
    "low_confidence": "Revisar con cautela y considerar evidencia territorial.",
    "do_not_infer": (
        "No usar esta observación para afirmar condiciones del territorio; "
        "esperar nueva adquisición o pedir verificación local."
    ),
}

STATE_STYLE = {
    "usable": {
        "class": "usable",
        "label": "USABLE",
        "tone": "usable",
    },
    "low_confidence": {
        "class": "low-confidence",
        "label": "BAJA CONFIANZA",
        "tone": "low_confidence",
    },
    "do_not_infer": {
        "class": "do-not-infer",
        "label": "NO INFERIR",
        "tone": "do_not_infer",
    },
}

PREVIEW_RECORDS = [
    {
        "date": "2025-06-02",
        "aoi": "corridor_wide",
        "resolution_m": 20,
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": None,
        "noDataCount": None,
        "validPercent": 47.72,
        "confidence_class": "usable",
        "decision": "interpret",
        "reason": "La observación tiene suficiente porcentaje válido para interpretación exploratoria.",
        "recommended_action": "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
        "raw_json_path": "pending official run",
        "source": "preview",
    },
    {
        "date": "2025-06-10",
        "aoi": "corridor_wide",
        "resolution_m": 20,
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": None,
        "noDataCount": None,
        "validPercent": 0.00,
        "confidence_class": "do_not_infer",
        "decision": "do_not_infer",
        "reason": "No hay suficiente evidencia satelital válida para una inferencia responsable.",
        "recommended_action": "Esperar una nueva adquisición o solicitar verificación territorial.",
        "raw_json_path": "pending official run",
        "source": "preview",
    },
    {
        "date": "2025-06-15",
        "aoi": "corridor_wide",
        "resolution_m": 20,
        "mndwi_mean": None,
        "ndti_mean": None,
        "noDataCount": None,
        "sampleCount": None,
        "validPercent": 13.24,
        "confidence_class": "low_confidence",
        "decision": "review",
        "reason": "La observación conserva señal parcial, pero la evidencia válida es limitada.",
        "recommended_action": "Revisar con cautela y considerar evidencia territorial.",
        "raw_json_path": "pending official run",
        "source": "preview",
    },
    {
        "date": "2025-06-30",
        "aoi": "corridor_wide",
        "resolution_m": 20,
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": None,
        "noDataCount": None,
        "validPercent": 58.34,
        "confidence_class": "usable",
        "decision": "interpret",
        "reason": "La observación tiene suficiente porcentaje válido para interpretación exploratoria.",
        "recommended_action": "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
        "raw_json_path": "pending official run",
        "source": "preview",
    },
    {
        "date": "2025-07-15",
        "aoi": "corridor_wide",
        "resolution_m": 20,
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": None,
        "noDataCount": None,
        "validPercent": 34.94,
        "confidence_class": "usable",
        "decision": "interpret",
        "reason": "La observación tiene suficiente porcentaje válido para interpretación exploratoria.",
        "recommended_action": "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos.",
        "raw_json_path": "pending official run",
        "source": "preview",
    },
]

SCIENTIFIC_LIMITS = (
    "Azuero Kairós no detecta pesticidas, atrazina, patógenos, metales pesados, "
    "contaminación química disuelta ni agua segura. Las afirmaciones químicas o "
    "sanitarias requieren laboratorio o verificación autorizada."
)


st.set_page_config(page_title="Azuero Kairós", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ak-bg: #f5ecdc;
          --ak-bg-soft: #fbf6ec;
          --ak-surface: #fffaf0;
          --ak-surface-strong: #fff6e6;
          --ak-text: #122d3d;
          --ak-muted: #6d7780;
          --ak-border: rgba(18, 45, 61, 0.13);
          --ak-border-strong: rgba(18, 45, 61, 0.22);
          --ak-river: #0c4868;
          --ak-river-soft: #d7e9ec;
          --ak-terracotta: #9b443d;
          --ak-terracotta-soft: #f2ded7;
          --ak-amber: #b97721;
          --ak-amber-soft: #f5e4c8;
          --ak-green: #24775e;
          --ak-green-soft: #dcebe1;
          --ak-shadow: 0 18px 46px rgba(42, 39, 34, 0.10);
        }

        .stApp {
          background:
            radial-gradient(circle at 9% -10%, rgba(12, 72, 104, 0.12), transparent 24rem),
            radial-gradient(circle at 88% 4%, rgba(155, 68, 61, 0.10), transparent 22rem),
            linear-gradient(135deg, var(--ak-bg) 0%, var(--ak-bg-soft) 53%, #ecdec8 100%);
          color: var(--ak-text);
        }

        .block-container {
          max-width: 1340px;
          padding: 1.05rem 1.55rem 2.3rem;
        }

        h1, h2, h3, p, li, div, label, span {
          letter-spacing: 0;
        }

        h1, h2, h3 {
          color: var(--ak-river);
        }

        h2, h3 {
          margin-top: 0;
        }

        p {
          margin-bottom: 0.35rem;
        }

        div[data-testid="stVerticalBlock"] {
          gap: 0.62rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
          border: 1px solid var(--ak-border);
          background: rgba(255, 250, 240, 0.92);
          border-radius: 8px;
          box-shadow: var(--ak-shadow);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
          padding: 0.72rem 0.82rem;
        }

        div[data-testid="stButton"] button {
          border: 0;
          border-radius: 8px;
          background: var(--ak-river);
          color: #fffaf0;
          font-weight: 760;
          padding: 0.68rem 1rem;
          box-shadow: 0 10px 22px rgba(12, 72, 104, 0.18);
        }

        div[data-testid="stButton"] button:hover {
          background: #0f5878;
          color: #fffaf0;
        }

        div[data-baseweb="select"] > div {
          background: #fffaf0;
          border-color: var(--ak-border-strong);
          border-radius: 8px;
          min-height: 2.4rem;
        }

        div[data-testid="stMetric"] {
          background: transparent;
          border: 0;
          padding: 0;
          min-height: auto;
        }

        div[data-testid="stMetricLabel"] p {
          color: var(--ak-muted);
          font-size: 0.72rem;
          font-weight: 760;
          text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
          color: var(--ak-text);
          font-size: 1.05rem;
          font-weight: 820;
        }

        label, div[data-testid="stCaptionContainer"] {
          color: var(--ak-muted);
        }

        .ak-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 1rem;
          margin-bottom: 0.55rem;
        }

        .ak-kicker {
          color: var(--ak-muted);
          font-size: 0.74rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .ak-title {
          margin: 0.05rem 0 0.2rem;
          color: var(--ak-river);
          font-size: 2.45rem;
          line-height: 0.96;
          font-weight: 860;
        }

        .ak-subtitle {
          margin: 0;
          color: #25495b;
          font-size: 1.03rem;
          font-weight: 680;
        }

        .ak-risk {
          align-self: center;
          max-width: 24rem;
          border: 1px solid rgba(155, 68, 61, 0.22);
          background: var(--ak-terracotta-soft);
          color: var(--ak-terracotta);
          border-radius: 8px;
          padding: 0.68rem 0.82rem;
          font-size: 0.92rem;
          font-weight: 760;
        }

        .ak-control-label {
          color: var(--ak-muted);
          font-size: 0.72rem;
          font-weight: 800;
          text-transform: uppercase;
          margin-bottom: 0.15rem;
        }

        .ak-source-value {
          color: var(--ak-text);
          font-size: 0.9rem;
          font-weight: 740;
          overflow-wrap: anywhere;
        }

        .ak-source-note {
          color: var(--ak-muted);
          font-size: 0.76rem;
          margin-top: 0.1rem;
        }

        .ak-hero {
          min-height: 19.2rem;
          border: 1px solid var(--ak-border);
          border-radius: 8px;
          padding: 1.15rem;
          background:
            linear-gradient(160deg, rgba(255, 250, 240, 0.98), rgba(255, 246, 230, 0.96)),
            var(--ak-surface);
          box-shadow: var(--ak-shadow);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }

        .ak-hero-top {
          display: flex;
          justify-content: space-between;
          gap: 0.75rem;
          color: var(--ak-muted);
          font-size: 0.8rem;
          font-weight: 760;
        }

        .ak-state {
          margin-top: 0.55rem;
          font-size: 3.4rem;
          line-height: 0.92;
          font-weight: 900;
        }

        .ak-state.do-not-infer {
          color: var(--ak-terracotta);
        }

        .ak-state.low-confidence {
          color: var(--ak-amber);
        }

        .ak-state.usable {
          color: var(--ak-green);
        }

        .ak-evidence {
          display: inline-flex;
          align-items: baseline;
          gap: 0.42rem;
          margin-top: 0.55rem;
          color: var(--ak-river);
        }

        .ak-evidence strong {
          font-size: 2.05rem;
          line-height: 1;
          font-weight: 880;
        }

        .ak-evidence span {
          color: var(--ak-muted);
          font-size: 0.96rem;
          font-weight: 720;
        }

        .ak-hero-action {
          margin: 0.9rem 0 0;
          max-width: 42rem;
          color: var(--ak-text);
          font-size: 1.07rem;
          font-weight: 760;
        }

        .ak-hero-next {
          margin-top: 0.32rem;
          color: #41515c;
          font-size: 0.94rem;
        }

        .ak-side-panel,
        .ak-visual-card,
        .ak-compare-card,
        .ak-metric-card,
        .ak-flow-card,
        .ak-limits-card {
          border: 1px solid var(--ak-border);
          background: rgba(255, 250, 240, 0.94);
          border-radius: 8px;
          box-shadow: 0 12px 30px rgba(42, 39, 34, 0.08);
        }

        .ak-side-panel {
          padding: 1rem;
        }

        .ak-side-panel h3,
        .ak-visual-card h3,
        .ak-section-title {
          margin: 0;
          color: var(--ak-river);
          font-size: 1.02rem;
          font-weight: 840;
        }

        .ak-side-panel p {
          color: #3b4b55;
          font-size: 0.94rem;
          line-height: 1.48;
        }

        .ak-next-action {
          margin-top: 0.75rem;
          border: 1px solid rgba(12, 72, 104, 0.15);
          background: var(--ak-river-soft);
          border-radius: 8px;
          padding: 0.72rem;
          color: #17384a;
          font-weight: 720;
        }

        .ak-visual-card {
          padding: 1rem;
        }

        .ak-river-visual {
          position: relative;
          min-height: 8.5rem;
          margin-top: 0.75rem;
          border: 1px solid rgba(12, 72, 104, 0.16);
          border-radius: 8px;
          background:
            linear-gradient(135deg, rgba(215, 233, 236, 0.78), rgba(255, 246, 230, 0.95)),
            repeating-linear-gradient(90deg, rgba(18, 45, 61, 0.04) 0 1px, transparent 1px 18px);
          overflow: hidden;
        }

        .ak-river-visual svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }

        .ak-river-label {
          position: absolute;
          left: 0.75rem;
          top: 0.65rem;
          color: var(--ak-river);
          font-size: 0.78rem;
          font-weight: 820;
        }

        .ak-river-badge {
          position: absolute;
          right: 0.75rem;
          bottom: 0.65rem;
          border: 1px solid rgba(12, 72, 104, 0.16);
          background: rgba(255, 250, 240, 0.88);
          border-radius: 8px;
          padding: 0.4rem 0.55rem;
          color: #314754;
          font-size: 0.74rem;
          font-weight: 760;
        }

        .ak-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 0.38rem;
          margin-top: 0.72rem;
        }

        .ak-tag {
          border: 1px solid rgba(18, 45, 61, 0.13);
          background: rgba(255, 246, 230, 0.72);
          color: #39505e;
          border-radius: 999px;
          padding: 0.32rem 0.55rem;
          font-size: 0.74rem;
          font-weight: 760;
        }

        .ak-status-chip {
          border-radius: 999px;
          padding: 0.34rem 0.58rem;
          font-size: 0.74rem;
          font-weight: 860;
        }

        .ak-status-chip.do-not-infer {
          background: var(--ak-terracotta-soft);
          color: var(--ak-terracotta);
        }

        .ak-status-chip.low-confidence {
          background: var(--ak-amber-soft);
          color: #80500c;
        }

        .ak-status-chip.usable {
          background: var(--ak-green-soft);
          color: var(--ak-green);
        }

        .ak-section-title {
          margin: 0.2rem 0 0.45rem;
        }

        .ak-compare-card {
          padding: 0.82rem;
          min-height: 10.4rem;
        }

        .ak-compare-top {
          display: flex;
          justify-content: space-between;
          gap: 0.7rem;
          align-items: center;
        }

        .ak-date {
          color: var(--ak-muted);
          font-size: 0.78rem;
          font-weight: 820;
        }

        .ak-compare-value {
          margin-top: 0.72rem;
          color: var(--ak-river);
          font-size: 1.65rem;
          line-height: 1;
          font-weight: 880;
        }

        .ak-compare-label,
        .ak-mini-label {
          color: var(--ak-muted);
          font-size: 0.72rem;
          font-weight: 780;
          text-transform: uppercase;
        }

        .ak-compare-message {
          margin-top: 0.66rem;
          color: #3c4b55;
          font-size: 0.86rem;
          line-height: 1.42;
        }

        .ak-compare-mini {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.45rem;
          margin-top: 0.65rem;
        }

        .ak-mini-value {
          color: var(--ak-text);
          font-weight: 820;
          font-size: 0.88rem;
        }

        .ak-insight {
          margin-top: 0.55rem;
          border: 1px solid rgba(12, 72, 104, 0.14);
          background: rgba(215, 233, 236, 0.58);
          color: #17384a;
          border-radius: 8px;
          padding: 0.64rem 0.76rem;
          font-size: 0.9rem;
          font-weight: 740;
        }

        .ak-metric-grid {
          display: grid;
          grid-template-columns: repeat(6, minmax(0, 1fr));
          gap: 0.55rem;
          margin-top: 0.4rem;
        }

        .ak-metric-card {
          padding: 0.72rem;
          min-height: 5rem;
        }

        .ak-metric-value {
          color: var(--ak-text);
          font-size: 1.1rem;
          font-weight: 850;
          margin-top: 0.26rem;
          overflow-wrap: anywhere;
        }

        .ak-flow-card {
          padding: 0.8rem;
        }

        .ak-flow {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 0.42rem;
          margin-top: 0.35rem;
        }

        .ak-flow span {
          color: #31505f;
          font-size: 0.84rem;
          font-weight: 790;
        }

        .ak-flow-step {
          border: 1px solid rgba(18, 45, 61, 0.13);
          background: #fffaf0;
          border-radius: 999px;
          padding: 0.38rem 0.58rem;
        }

        .ak-flow-arrow {
          color: rgba(12, 72, 104, 0.52) !important;
        }

        .ak-limits-card {
          padding: 0.82rem;
          color: #4b5860;
          font-size: 0.86rem;
          line-height: 1.45;
        }

        .ak-preview-note {
          border: 1px solid rgba(185, 119, 33, 0.24);
          background: var(--ak-amber-soft);
          color: #6f470e;
          border-radius: 8px;
          padding: 0.66rem 0.78rem;
          font-size: 0.88rem;
          font-weight: 700;
        }

        .stMarkdown p {
          line-height: 1.52;
        }

        @media (max-width: 980px) {
          .block-container {
            padding: 0.8rem 0.78rem 1.8rem;
          }

          .ak-header {
            display: block;
          }

          .ak-risk {
            margin-top: 0.6rem;
          }

          .ak-title {
            font-size: 2.1rem;
          }

          .ak-state {
            font-size: 2.7rem;
          }

          .ak-metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def newest_processed_csv() -> Path | None:
    if not PROCESSED_DIR.exists():
        return None
    csv_files = [path for path in PROCESSED_DIR.glob("*.csv") if path.is_file()]
    if not csv_files:
        return None
    return max(csv_files, key=lambda path: path.stat().st_mtime)


@st.cache_data(show_spinner=False)
def load_records(csv_path: str | None) -> tuple[list[dict[str, Any]], str | None]:
    if csv_path is None:
        return PREVIEW_RECORDS, None

    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    for record in records:
        record["source"] = "official"
    return records, str(path)


def get_record(records: list[dict[str, Any]], selected_date: str, selected_aoi: str) -> dict[str, Any] | None:
    for record in records:
        if str(record.get("date")) == selected_date and str(record.get("aoi")) == selected_aoi:
            return record
    return None


def value_is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    value_text = str(value).strip()
    return value_text == "" or value_text.lower() in {"none", "nan", "pending official run"}


def parse_float(value: Any) -> float | None:
    if value_is_missing(value):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def display_value(value: Any, *, suffix: str = "", missing: str = "pendiente") -> str:
    if value_is_missing(value):
        return missing
    parsed = parse_float(value)
    if parsed is not None and suffix == "%":
        return f"{parsed:.2f}{suffix}"
    return f"{value}{suffix}"


def display_percent(value: Any) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "pendiente"
    return f"{parsed:.2f}%"


def display_count(value: Any) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "pendiente"
    return f"{int(parsed):,}"


def display_decimal(value: Any) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "pendiente"
    return f"{parsed:.2f}"


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized.setdefault("resolution_m", 20)
    normalized.setdefault("mndwi_mean", None)
    normalized.setdefault("ndti_mean", None)
    normalized.setdefault("sampleCount", None)
    normalized.setdefault("noDataCount", None)
    normalized.setdefault("validPercent", None)
    normalized.setdefault("raw_json_path", "pending official run")
    add_localized_display_fields(normalized)
    return normalized


def add_localized_display_fields(record: dict[str, Any]) -> None:
    confidence_class = str(record.get("confidence_class", ""))
    localized_defaults = {
        "confidence_label_es": CONFIDENCE_LABELS_ES.get(confidence_class),
        "decision_label_es": DECISION_LABELS_BY_CONFIDENCE_ES.get(confidence_class),
        "reason_es": REASONS_ES.get(confidence_class),
        "recommended_action_es": RECOMMENDED_ACTIONS_ES.get(confidence_class),
    }
    for key, value in localized_defaults.items():
        if value is not None and value_is_missing(record.get(key)):
            record[key] = value


def localized_value(record: dict[str, Any], localized_key: str, fallback_key: str) -> str:
    localized = record.get(localized_key)
    if not value_is_missing(localized):
        return str(localized)

    fallback = record.get(fallback_key)
    if not value_is_missing(fallback):
        return str(fallback)

    return "no proporcionado"


def safe(value: Any) -> str:
    return escape(str(value), quote=True)


def relative_path(path_value: str | Path | None) -> str:
    if path_value is None:
        return "No disponible"
    path = Path(path_value)
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def render_html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def state_style(record: dict[str, Any]) -> dict[str, str]:
    confidence = str(record.get("confidence_class", "do_not_infer"))
    return STATE_STYLE.get(confidence, STATE_STYLE["do_not_infer"])


def state_label(record: dict[str, Any]) -> str:
    return localized_value(record, "confidence_label_es", "confidence_class")


def hero_action_text(record: dict[str, Any]) -> tuple[str, str]:
    confidence = str(record.get("confidence_class", "do_not_infer"))
    if confidence == "do_not_infer":
        return (
            "No usar esta observación para afirmar condiciones del territorio.",
            "Siguiente acción: esperar nueva adquisición o solicitar verificación territorial.",
        )
    if confidence == "low_confidence":
        return (
            "Revisar esta observación con cautela antes de cualquier lectura territorial.",
            "Siguiente acción: considerar verificación territorial o una nueva adquisición.",
        )
    return (
        "Usar esta observación para lectura exploratoria con límites explícitos.",
        "Siguiente acción: interpretar con cautela y conservar la trazabilidad.",
    )


def render_header() -> None:
    render_html(
        """
        <div class="ak-header">
          <div>
            <div class="ak-kicker">Consola de decisión territorial</div>
            <h1 class="ak-title">Azuero Kairós</h1>
            <p class="ak-subtitle">Semáforo de confianza satelital para decisiones agrícolas</p>
          </div>
          <div class="ak-risk">Una mala inferencia también es un riesgo.</div>
        </div>
        """
    )


def render_input_panel(selected_date: str, selected_aoi: str, source_path: str | None) -> tuple[str, str]:
    ledger_status = (
        f"Ledger activo: {relative_path(LEDGER_PATH)}"
        if LEDGER_PATH.exists()
        else "Ledger pendiente"
    )
    source_label = relative_path(source_path) if source_path else "UI preview only, not official evidence"

    with st.container(border=True):
        col_date, col_aoi, col_source, col_ledger = st.columns(
            [0.92, 0.78, 1.6, 1.08],
            vertical_alignment="bottom",
            gap="small",
        )
        with col_date:
            next_date = st.selectbox(
                "Fecha",
                DATES,
                index=DATES.index(selected_date),
            )
        with col_aoi:
            next_aoi = st.selectbox(
                "AOI",
                AOIS,
                index=AOIS.index(selected_aoi),
            )
        with col_source:
            render_html(
                f"""
                <div class="ak-control-label">Fuente de datos</div>
                <div class="ak-source-value">{safe(source_label)}</div>
                <div class="ak-source-note">CSV oficial cuando está disponible</div>
                """
            )
        with col_ledger:
            render_html(
                f"""
                <div class="ak-control-label">Estado ledger</div>
                <div class="ak-source-value">{safe(ledger_status)}</div>
                <div class="ak-source-note">Trazabilidad de evidencia</div>
                """
            )
    return next_date, next_aoi


def render_preview_notice(using_preview: bool) -> None:
    if not using_preview:
        return
    render_html(
        """
        <div class="ak-preview-note">
          No official processed CSV found yet. Showing UI preview data only.
          Ejecuta el batch oficial Sentinel-2 para reemplazar esta vista previa con evidencia oficial.
        </div>
        """
    )


def render_hero_card(record: dict[str, Any]) -> None:
    style = state_style(record)
    primary_action, next_action = hero_action_text(record)
    valid_percent = display_percent(record.get("validPercent"))
    label = state_label(record)

    render_html(
        f"""
        <section class="ak-hero">
          <div>
            <div class="ak-hero-top">
              <span>Decisión actual</span>
              <span>{safe(record.get("date"))} · {safe(record.get("aoi"))}</span>
            </div>
            <div class="ak-state {safe(style["class"])}">{safe(label)}</div>
            <div class="ak-evidence">
              <strong>{safe(valid_percent)}</strong>
              <span>evidencia válida</span>
            </div>
          </div>
          <div>
            <p class="ak-hero-action">{safe(primary_action)}</p>
            <p class="ak-hero-next">{safe(next_action)}</p>
          </div>
        </section>
        """
    )


def render_meaning_panel(record: dict[str, Any]) -> None:
    reason = localized_value(record, "reason_es", "reason")
    action = localized_value(record, "recommended_action_es", "recommended_action")
    if action == "no proporcionado":
        action = WHAT_NOW.get(str(record.get("confidence_class")), WHAT_NOW["do_not_infer"])

    render_html(
        f"""
        <section class="ak-side-panel">
          <h3>Qué significa esto</h3>
          <p>{safe(reason)}</p>
          <div class="ak-next-action">
            <div class="ak-mini-label">Siguiente acción</div>
            <div>{safe(action)}</div>
          </div>
        </section>
        """
    )


def render_territory_card(record: dict[str, Any]) -> None:
    style = state_style(record)
    label = state_label(record)
    render_html(
        f"""
        <section class="ak-visual-card">
          <h3>Corredor Río La Villa</h3>
          <div class="ak-river-visual" aria-label="Visual abstracto del corredor Río La Villa">
            <div class="ak-river-label">Corredor agrícola-ripario</div>
            <svg viewBox="0 0 360 150" role="img" aria-label="Línea abstracta tipo río">
              <path d="M-8 102 C 44 58, 82 132, 132 82 S 221 36, 270 77 S 329 120, 370 63"
                    fill="none" stroke="#0c4868" stroke-width="14" stroke-linecap="round" opacity="0.24" />
              <path d="M-8 102 C 44 58, 82 132, 132 82 S 221 36, 270 77 S 329 120, 370 63"
                    fill="none" stroke="#176c84" stroke-width="5" stroke-linecap="round" opacity="0.82" />
            </svg>
            <div class="ak-river-badge">{safe(label)}</div>
          </div>
          <div class="ak-tags">
            <span class="ak-tag">AOI corridor_wide</span>
            <span class="ak-tag">Sentinel-2</span>
            <span class="ak-tag">{safe(display_value(record.get("resolution_m"), suffix=" m"))}</span>
            <span class="ak-status-chip {safe(style["class"])}">{safe(label)}</span>
          </div>
        </section>
        """
    )


def render_demo_comparison(records: list[dict[str, Any]], using_preview: bool) -> None:
    first_record = get_record(records, "2025-06-10", "corridor_wide")
    second_record = get_record(records, "2025-06-30", "corridor_wide")
    comparison_available = (
        not using_preview
        and first_record is not None
        and second_record is not None
        and first_record.get("source") == "official"
        and second_record.get("source") == "official"
    )

    render_html('<h3 class="ak-section-title">Comparación de decisión</h3>')

    if not comparison_available:
        render_html(
            """
            <div class="ak-compare-card">
              Comparación disponible cuando el CSV oficial contiene 2025-06-10 y 2025-06-30.
            </div>
            """
        )
        return

    left, right = st.columns(2, gap="small")
    with left:
        render_comparison_card(
            normalize_record(first_record),
            message="Evidencia insuficiente para inferencia responsable.",
        )
    with right:
        render_comparison_card(
            normalize_record(second_record),
            message="Evidencia suficiente para lectura exploratoria con límites explícitos.",
        )

    render_html(
        """
        <div class="ak-insight">
          El valor del sistema no es forzar alertas, sino decidir cuándo la evidencia Copernicus puede usarse y cuándo no.
        </div>
        """
    )


def render_comparison_card(record: dict[str, Any], *, message: str) -> None:
    style = state_style(record)
    label = state_label(record)
    render_html(
        f"""
        <article class="ak-compare-card">
          <div class="ak-compare-top">
            <span class="ak-date">{safe(record.get("date"))}</span>
            <span class="ak-status-chip {safe(style["class"])}">{safe(label)}</span>
          </div>
          <div class="ak-compare-value">{safe(display_percent(record.get("validPercent")))}</div>
          <div class="ak-compare-label">validPercent</div>
          <div class="ak-compare-mini">
            <div>
              <div class="ak-mini-label">sampleCount</div>
              <div class="ak-mini-value">{safe(display_count(record.get("sampleCount")))}</div>
            </div>
            <div>
              <div class="ak-mini-label">noDataCount</div>
              <div class="ak-mini-value">{safe(display_count(record.get("noDataCount")))}</div>
            </div>
          </div>
          <div class="ak-compare-message">Mensaje: {safe(message)}</div>
        </article>
        """
    )


def render_metrics(record: dict[str, Any]) -> None:
    metrics = [
        ("validPercent", display_percent(record.get("validPercent"))),
        ("sampleCount", display_count(record.get("sampleCount"))),
        ("noDataCount", display_count(record.get("noDataCount"))),
        ("MNDWI", display_decimal(record.get("mndwi_mean"))),
        ("NDTI", display_decimal(record.get("ndti_mean"))),
        ("resolution_m", display_value(record.get("resolution_m"), suffix=" m")),
    ]
    cards = "\n".join(
        f"""
        <div class="ak-metric-card">
          <div class="ak-mini-label">{safe(label)}</div>
          <div class="ak-metric-value">{safe(value)}</div>
        </div>
        """
        for label, value in metrics
    )
    render_html(
        f"""
        <h3 class="ak-section-title">Métricas críticas</h3>
        <div class="ak-metric-grid">{cards}</div>
        """
    )


def render_workflow() -> None:
    steps = ["CDSE", "JSON", "CSV", "Confianza", "Brief", "Ledger"]
    pieces: list[str] = []
    for index, step in enumerate(steps):
        if index:
            pieces.append('<span class="ak-flow-arrow">&rarr;</span>')
        pieces.append(f'<span class="ak-flow-step">{safe(step)}</span>')
    render_html(
        f"""
        <section class="ak-flow-card">
          <h3 class="ak-section-title">Flujo de evidencia</h3>
          <div class="ak-flow">{"".join(pieces)}</div>
        </section>
        """
    )


def brief_output_path(record: dict[str, Any]) -> Path:
    date_value = str(record.get("date", "unknown_date"))
    aoi_value = str(record.get("aoi", "unknown_aoi"))
    safe_name = f"{date_value}_{aoi_value}_confidence_brief.md".replace("/", "_").replace("\\", "_")
    return BRIEF_DIR / safe_name


def record_for_brief(record: dict[str, Any]) -> dict[str, Any]:
    prepared = normalize_record(record)
    if value_is_missing(prepared.get("mndwi_mean")):
        prepared["mndwi_mean"] = "pending official run"
    if value_is_missing(prepared.get("ndti_mean")):
        prepared["ndti_mean"] = "pending official run"
    return prepared


def generate_brief(record: dict[str, Any], is_preview: bool, state_key: str) -> None:
    generated_key = f"brief_generated_{state_key}"
    markdown_key = f"brief_markdown_{state_key}"
    path_key = f"brief_path_{state_key}"

    output_path = brief_output_path(record)
    brief_markdown = generate_confidence_brief(record_for_brief(record))
    if is_preview:
        brief_markdown = "UI preview only, not official evidence.\n\n" + brief_markdown

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(brief_markdown, encoding="utf-8")

    st.session_state[generated_key] = True
    st.session_state[markdown_key] = brief_markdown
    st.session_state[path_key] = str(output_path)


def render_brief_panel(record: dict[str, Any], is_preview: bool, state_key: str) -> None:
    generated_key = f"brief_generated_{state_key}"
    markdown_key = f"brief_markdown_{state_key}"
    path_key = f"brief_path_{state_key}"

    with st.container(border=True):
        st.subheader("Informe de Confianza")
        if st.button("Generar Informe de Confianza", use_container_width=False):
            generate_brief(record, is_preview, state_key)

        if st.session_state.get(generated_key):
            st.caption(f"Guardado en: {st.session_state[path_key]}")
            st.markdown(st.session_state[markdown_key])
        else:
            st.caption("El informe se genera bajo demanda para mantener trazabilidad explícita.")


def render_limits() -> None:
    render_html(
        f"""
        <section class="ak-limits-card">
          <strong>Límites científicos.</strong> {safe(SCIENTIFIC_LIMITS)}
        </section>
        """
    )


def render_no_record(selected_date: str, selected_aoi: str) -> None:
    render_html(
        f"""
        <section class="ak-side-panel">
          <h3>Sin registro para la selección</h3>
          <p>No hay registro para {safe(selected_date)} / {safe(selected_aoi)}. No se inventa evidencia oficial.</p>
        </section>
        """
    )
    render_workflow()
    render_limits()


def main() -> None:
    inject_css()

    csv_path = newest_processed_csv()
    records, source_path = load_records(str(csv_path) if csv_path else None)
    using_preview = source_path is None

    render_header()
    selected_date, selected_aoi = render_input_panel(DEFAULT_DATE, DEFAULT_AOI, source_path)
    render_preview_notice(using_preview)

    raw_record = get_record(records, selected_date, selected_aoi)
    if raw_record is None:
        render_no_record(selected_date, selected_aoi)
        return

    record = normalize_record(raw_record)
    is_preview = record.get("source") == "preview"
    state_key = f"{record.get('source')}_{selected_date}_{selected_aoi}"

    main_col, side_col = st.columns([1.45, 0.88], gap="medium")
    with main_col:
        render_hero_card(record)
        render_demo_comparison(records, using_preview)
    with side_col:
        render_meaning_panel(record)
        render_territory_card(record)

    render_metrics(record)
    render_workflow()
    render_limits()
    render_brief_panel(record, is_preview, state_key)


if __name__ == "__main__":
    main()
