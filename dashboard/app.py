"""Streamlit decision console for the Azuero Kairós MVP."""

from __future__ import annotations

import csv
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

CONFIDENCE_DISPLAY = {
    "usable": "USABLE",
    "low_confidence": "BAJA CONFIANZA",
    "do_not_infer": "NO INFERIR",
}

DECISION_DISPLAY = {
    "interpret": "Interpretar con cautela",
    "review": "Revisar / verificar",
    "do_not_infer": "No inferir",
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
        "streamlit_state": "success",
        "label": "USABLE",
        "decision": "Interpretar con cautela",
    },
    "low_confidence": {
        "streamlit_state": "warning",
        "label": "BAJA CONFIANZA",
        "decision": "Revisar / verificar",
    },
    "do_not_infer": {
        "streamlit_state": "error",
        "label": "NO INFERIR",
        "decision": "No inferir",
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
        "recommended_action": (
            "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos."
        ),
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
        "recommended_action": (
            "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos."
        ),
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
        "recommended_action": (
            "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos."
        ),
        "raw_json_path": "pending official run",
        "source": "preview",
    },
]

SCIENTIFIC_LIMITS = (
    "Azuero Kairós no detecta pesticidas, atrazina, patógenos, metales pesados, "
    "contaminación química disuelta ni agua segura. La salida es una evaluación "
    "de confianza satelital para lectura hidro-sedimentaria exploratoria. "
    "Las afirmaciones químicas o sanitarias requieren laboratorio o verificación autorizada."
)


st.set_page_config(page_title="Azuero Kairós", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ak-bg: #f4ecde;
          --ak-surface: #fffaf1;
          --ak-surface-2: #f8efe0;
          --ak-text: #17232e;
          --ak-muted: #66727e;
          --ak-river: #0d4666;
          --ak-river-2: #176c84;
          --ak-amber: #b97824;
          --ak-red-muted: #8a3f3b;
          --ak-green: #1f7a62;
          --ak-border: rgba(23, 35, 46, 0.14);
          --ak-border-strong: rgba(13, 70, 102, 0.22);
          --ak-shadow: 0 18px 46px rgba(38, 43, 47, 0.10);
        }

        .stApp {
          background:
            radial-gradient(circle at 8% 0%, rgba(23, 108, 132, 0.10), transparent 28%),
            linear-gradient(135deg, var(--ak-bg) 0%, #f8f2e8 56%, #eadcc8 100%);
          color: var(--ak-text);
        }

        .block-container {
          max-width: 1180px;
          padding: 1.1rem 1.55rem 2.2rem;
        }

        h1, h2, h3, p, li, div, label {
          letter-spacing: 0;
        }

        h1 {
          color: var(--ak-river);
          font-size: 2.65rem;
          line-height: 0.98;
          margin-bottom: 0.15rem;
        }

        h2, h3 {
          color: var(--ak-river);
        }

        h3 {
          margin-top: 0.15rem;
          margin-bottom: 0.35rem;
        }

        p {
          margin-bottom: 0.45rem;
        }

        div[data-testid="stVerticalBlock"] {
          gap: 0.62rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
          border-color: var(--ak-border);
          background: rgba(255, 250, 241, 0.90);
          border-radius: 8px;
          box-shadow: var(--ak-shadow);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
          padding: 0.82rem 0.95rem;
        }

        div[data-testid="stMetric"] {
          background: var(--ak-surface);
          border: 1px solid var(--ak-border);
          border-radius: 8px;
          padding: 0.74rem 0.85rem;
          min-height: 82px;
          box-shadow: 0 8px 24px rgba(38, 43, 47, 0.06);
        }

        div[data-testid="stMetricLabel"] p {
          color: #40505c;
          font-size: 0.78rem;
          font-weight: 780;
          text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
          color: var(--ak-text);
          font-size: 1.18rem;
          font-weight: 820;
        }

        div[data-testid="stAlert"] {
          border-radius: 8px;
          padding: 0.6rem 0.75rem;
          border: 1px solid var(--ak-border);
        }

        div[data-testid="stButton"] button {
          border: 0;
          border-radius: 8px;
          background: var(--ak-river);
          color: #fffaf1;
          font-weight: 780;
          padding: 0.72rem 1rem;
        }

        div[data-testid="stButton"] button:hover {
          background: #0f5578;
          color: #fffaf1;
        }

        div[data-baseweb="select"] > div {
          border-radius: 8px;
          border-color: var(--ak-border-strong);
          background-color: #fffaf1;
        }

        label, div[data-testid="stCaptionContainer"] {
          color: #5f6a72;
        }

        .stMarkdown p {
          line-height: 1.58;
        }

        @media (max-width: 900px) {
          .block-container {
            padding: 0.8rem 0.85rem 1.8rem;
          }

          h1 {
            font-size: 2.15rem;
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
    if str(value).strip() == "":
        return True
    return False


def display_value(value: Any, *, suffix: str = "", missing: str = "pendiente") -> str:
    if value_is_missing(value):
        return missing
    if isinstance(value, float):
        rendered = f"{value:.2f}"
    else:
        rendered = str(value)
    return f"{rendered}{suffix}"


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


def render_header() -> None:
    st.title("Azuero Kairós")
    st.markdown("#### Semáforo de confianza satelital para decisiones agrícolas")
    st.write(
        "Azuero Kairós evalúa si una observación Sentinel tiene evidencia suficiente "
        "para interpretar, revisar o no inferir."
    )


def render_input_panel(selected_date: str, selected_aoi: str, source_path: str | None) -> tuple[str, str]:
    with st.container(border=True):
        st.caption("Panel de control")
        col_date, col_aoi, col_source = st.columns([0.9, 0.75, 1.45], vertical_alignment="bottom")
        with col_date:
            next_date = st.selectbox(
                "Fecha de observación",
                DATES,
                index=DATES.index(selected_date),
            )
        with col_aoi:
            next_aoi = st.selectbox(
                "Área de interés",
                AOIS,
                index=AOIS.index(selected_aoi),
            )
        with col_source:
            st.markdown("**Fuente de datos**")
            st.caption(source_path or "Vista previa hasta ejecutar el batch oficial Sentinel-2")
    return next_date, next_aoi


def render_preview_notice(using_preview: bool) -> None:
    if not using_preview:
        return
    with st.container(border=True):
        col_status, col_action = st.columns([1.0, 1.9], vertical_alignment="center")
        with col_status:
            st.markdown("**Vista previa de interfaz**")
            st.caption("UI preview only, not official evidence.")
        with col_action:
            st.write("No official processed CSV found yet. Showing UI preview data only.")
            st.caption("Ejecuta el batch oficial Sentinel-2 para reemplazar esta vista previa con evidencia oficial.")


def render_hero_card(record: dict[str, Any]) -> None:
    confidence = str(record.get("confidence_class", "do_not_infer"))
    style = STATE_STYLE.get(confidence, STATE_STYLE["do_not_infer"])
    state_label = localized_value(record, "confidence_label_es", "confidence_class")
    decision_label = localized_value(record, "decision_label_es", "decision")
    reason = localized_value(record, "reason_es", "reason")
    action = localized_value(record, "recommended_action_es", "recommended_action")

    with st.container(border=True):
        top_left, top_right = st.columns([0.85, 1.55], vertical_alignment="center")
        with top_left:
            st.caption(f"{record.get('date')} · {record.get('aoi')}")
            st.markdown(f"## {state_label}")
            if style["streamlit_state"] == "success":
                st.success(decision_label)
            elif style["streamlit_state"] == "warning":
                st.warning(decision_label)
            else:
                st.error(decision_label)
        with top_right:
            st.caption("Decisión responsable")
            st.markdown(f"**{reason}**")
            st.write(f"**Siguiente acción:** {action}")
            st.info("Insight de producto: Una mala inferencia también es un riesgo.")


def render_metrics(record: dict[str, Any]) -> None:
    st.subheader("Métricas críticas")
    row_one = st.columns(4)
    row_one[0].metric("Porcentaje válido", display_value(record.get("validPercent"), suffix="%"))
    row_one[1].metric("Muestras", display_value(record.get("sampleCount")))
    row_one[2].metric("Sin datos", display_value(record.get("noDataCount")))
    row_one[3].metric("Resolución", display_value(record.get("resolution_m"), suffix=" m"))

    row_two = st.columns(2)
    row_two[0].metric("Promedio MNDWI", display_value(record.get("mndwi_mean")))
    row_two[1].metric("Promedio NDTI", display_value(record.get("ndti_mean")))


def render_what_now(record: dict[str, Any]) -> None:
    confidence = str(record.get("confidence_class", "do_not_infer"))
    action = localized_value(record, "recommended_action_es", "recommended_action")
    if action == "no proporcionado":
        action = WHAT_NOW.get(confidence, WHAT_NOW["do_not_infer"])
    with st.container(border=True):
        col_label, col_action = st.columns([0.72, 2.1], vertical_alignment="center")
        with col_label:
            st.subheader("Qué hacer ahora")
        with col_action:
            st.markdown(f"**{action}**")


def workflow_steps(record_exists: bool, confidence_class: str, brief_generated: bool) -> list[tuple[str, str]]:
    needs_human_review = confidence_class in {"low_confidence", "do_not_infer"}
    first_status = "completo" if record_exists else "pendiente"
    brief_status = "completo" if brief_generated else "pendiente"
    verification_status = "pendiente" if needs_human_review else "pendiente"
    human_status = "requiere decisión humana" if needs_human_review else "pendiente"
    final_status = "completo" if brief_generated else "pendiente"

    return [
        ("Adquisición Sentinel", first_status),
        ("Estadísticas del AOI", first_status),
        ("Clasificación de confianza", first_status),
        ("Informe generado", brief_status),
        ("Verificación territorial si aplica", verification_status),
        ("Confirmación humana", human_status),
        ("Informe final", final_status),
    ]


def render_workflow(record: dict[str, Any] | None, brief_generated: bool) -> None:
    confidence = str(record.get("confidence_class", "do_not_infer")) if record else "do_not_infer"
    steps = workflow_steps(record is not None, confidence, brief_generated)

    with st.container(border=True):
        st.subheader("Flujo de evidencia")
        columns = st.columns(7, gap="small")
        for index, ((name, status), column) in enumerate(zip(steps, columns), start=1):
            with column:
                st.caption(f"{index}. {name}")
                st.markdown(f"**{status}**")


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
    with st.container(border=True):
        st.subheader("Límites científicos")
        st.caption(SCIENTIFIC_LIMITS)


def render_no_record(selected_date: str, selected_aoi: str) -> None:
    with st.container(border=True):
        st.subheader("Sin registro para la selección")
        st.write(f"No hay registro para {selected_date} / {selected_aoi}. No se inventa evidencia oficial.")
    render_workflow(None, brief_generated=False)
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
    brief_generated = bool(st.session_state.get(f"brief_generated_{state_key}", False))

    render_hero_card(record)
    render_what_now(record)
    render_metrics(record)
    render_workflow(record, brief_generated)
    render_limits()
    render_brief_panel(record, is_preview, state_key)


if __name__ == "__main__":
    main()
