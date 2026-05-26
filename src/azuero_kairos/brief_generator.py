"""Markdown Confidence Brief generation for Azuero Kairós."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .confidence_engine import (
    CONFIDENCE_LABELS_ES,
    DECISION_LABELS_ES,
    REASONS_ES,
    RECOMMENDED_ACTIONS_ES,
)


SCIENTIFIC_LIMITS_NOTICE = (
    "Este informe no detecta pesticidas, atrazina, patógenos, metales pesados, "
    "contaminación química disuelta ni agua segura. Las afirmaciones químicas "
    "o sanitarias requieren laboratorio o verificación autorizada."
)


def generate_confidence_brief(
    record: dict,
    output_path: str | Path | None = None,
) -> str:
    """Generate a deterministic Spanish Markdown Confidence Brief from one record."""

    confidence_class = _value(record, "confidence_class")
    confidence_label = _localized_by_confidence(
        record,
        "confidence_label_es",
        "confidence_class",
        CONFIDENCE_LABELS_ES,
    )
    decision_label = _localized_by_confidence(
        record,
        "decision_label_es",
        "decision",
        DECISION_LABELS_ES,
    )
    reason = _localized_by_confidence(record, "reason_es", "reason", REASONS_ES)
    recommended_action = _localized_by_confidence(
        record,
        "recommended_action_es",
        "recommended_action",
        RECOMMENDED_ACTIONS_ES,
    )

    brief = "\n".join(
        [
            "# Azuero Kairós - Informe de Confianza",
            "",
            "## 1. Decisión ejecutiva",
            "",
            f"- Clase de confianza: `{confidence_label}` (`{confidence_class}`)",
            f"- Decisión: `{decision_label}`",
            f"- Razón: {reason}",
            "",
            "## 2. Metadatos de observación",
            "",
            f"- Fecha: {_value(record, 'date')}",
            f"- AOI: {_value(record, 'aoi')}",
            f"- Resolución: {_value(record, 'resolution_m')} m",
            "",
            "## 3. Calidad de evidencia",
            "",
            f"- Muestras evaluadas: {_value(record, 'sampleCount')}",
            f"- Muestras sin datos: {_value(record, 'noDataCount')}",
            f"- Porcentaje válido: {_value(record, 'validPercent')}%",
            "",
            "## 4. Indicadores satelitales",
            "",
            f"- Promedio MNDWI: {_value(record, 'mndwi_mean')}",
            f"- Promedio NDTI: {_value(record, 'ndti_mean')}",
            "",
            "## 5. Interpretación responsable",
            "",
            (
                "Este informe clasifica la confianza de una observación Sentinel para "
                "lectura hidro-sedimentaria exploratoria. La decisión debe interpretarse "
                "junto con la calidad de evidencia y los límites científicos declarados."
            ),
            "",
            "## 6. Qué no puede inferirse",
            "",
            SCIENTIFIC_LIMITS_NOTICE,
            "",
            "## 7. Siguiente acción recomendada",
            "",
            recommended_action,
            "",
            "## 8. Trazabilidad de evidencia",
            "",
            f"- Ruta del JSON crudo: {_value(record, 'raw_json_path')}",
            "",
        ]
    )

    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(brief, encoding="utf-8")

    return brief


def _localized_by_confidence(
    record: dict[str, Any],
    localized_key: str,
    fallback_key: str,
    values_by_confidence: dict[str, str],
) -> str:
    localized_value = record.get(localized_key)
    if not _is_missing(localized_value):
        return str(localized_value)

    confidence_class = str(record.get("confidence_class", ""))
    mapped_value = values_by_confidence.get(confidence_class)
    if mapped_value:
        return mapped_value

    return _value(record, fallback_key)


def _value(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if _is_missing(value):
        return "no proporcionado"
    return str(value)


def _is_missing(value: Any) -> bool:
    return value is None or str(value).strip() == ""


if __name__ == "__main__":
    sample_record = {
        "date": "2025-06-10",
        "aoi": "corridor_wide",
        "resolution_m": 20,
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": 0,
        "noDataCount": 0,
        "validPercent": 0.00,
        "confidence_class": "do_not_infer",
        "decision": "do_not_infer",
        "reason_es": "La observación no tiene suficiente evidencia válida para una inferencia responsable.",
        "recommended_action_es": (
            "No usar esta observación para afirmar condiciones del territorio; esperar una "
            "nueva adquisición o solicitar verificación territorial."
        ),
        "raw_json_path": "outputs/raw_json/2025-06-10_corridor_wide.json",
    }

    output = Path("outputs/briefs/2025-06-10_corridor_wide_confidence_brief.md")
    print(generate_confidence_brief(sample_record, output))
