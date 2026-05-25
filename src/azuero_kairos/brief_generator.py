"""Markdown Confidence Brief generation for Azuero Kairós."""

from __future__ import annotations

from pathlib import Path
from typing import Any


SCIENTIFIC_LIMITS_NOTICE = (
    "This brief does not detect pesticides, atrazine, pathogens, heavy metals, "
    "dissolved chemical contamination, or safe water. Laboratory or authorized "
    "field verification is required for chemical or sanitary claims."
)


def generate_confidence_brief(
    record: dict,
    output_path: str | Path | None = None,
) -> str:
    """Generate a deterministic Markdown Confidence Brief from one record."""

    brief = "\n".join(
        [
            "# Azuero Kairós Confidence Brief",
            "",
            "## 1. Executive decision",
            "",
            f"- Confidence class: `{_value(record, 'confidence_class')}`",
            f"- Decision: `{_value(record, 'decision')}`",
            f"- Reason: {_value(record, 'reason')}",
            "",
            "## 2. Observation metadata",
            "",
            f"- Date: {_value(record, 'date')}",
            f"- AOI: {_value(record, 'aoi')}",
            f"- Resolution: {_value(record, 'resolution_m')} m",
            "",
            "## 3. Evidence quality",
            "",
            f"- Sample count: {_value(record, 'sampleCount')}",
            f"- No-data count: {_value(record, 'noDataCount')}",
            f"- Valid percent: {_value(record, 'validPercent')}%",
            "",
            "## 4. Satellite indicators",
            "",
            f"- MNDWI mean: {_value(record, 'mndwi_mean')}",
            f"- NDTI mean: {_value(record, 'ndti_mean')}",
            "",
            "## 5. Responsible interpretation",
            "",
            (
                "This brief supports only confidence classification for cautious "
                "exploratory hydro-sedimentary interpretation. Use the decision "
                "state together with the evidence quality metrics and stated limits."
            ),
            "",
            "## 6. What cannot be inferred",
            "",
            SCIENTIFIC_LIMITS_NOTICE,
            "",
            "## 7. Recommended next action",
            "",
            _value(record, "recommended_action"),
            "",
            "## 8. Evidence traceability",
            "",
            f"- Raw JSON path: {_value(record, 'raw_json_path')}",
            "",
        ]
    )

    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(brief, encoding="utf-8")

    return brief


def _value(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if value is None:
        return "not provided"
    return str(value)


if __name__ == "__main__":
    sample_record = {
        "date": "2025-06-10",
        "aoi": "corridor_wide",
        "resolution_m": 10,
        "mndwi_mean": None,
        "ndti_mean": None,
        "sampleCount": 0,
        "noDataCount": 0,
        "validPercent": 0.00,
        "confidence_class": "do_not_infer",
        "decision": "do_not_infer",
        "reason": "No valid satellite evidence after cloud/no-data filtering.",
        "recommended_action": (
            "Do not make a satellite-based inference; wait for a new acquisition "
            "or request field verification."
        ),
        "raw_json_path": "outputs/raw_json/2025-06-10_corridor_wide.json",
    }

    output = Path("outputs/briefs/2025-06-10_corridor_wide_confidence_brief.md")
    print(generate_confidence_brief(sample_record, output))
