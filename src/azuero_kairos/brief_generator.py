"""Confidence Brief generation scaffold."""

from __future__ import annotations

from collections.abc import Mapping

from azuero_kairos.confidence_engine import ConfidenceDecision


SCIENTIFIC_LIMITS_NOTICE = (
    "This system does not detect contamination, pesticides, atrazine, "
    "pathogens, heavy metals, dissolved chemical contamination, or safe water."
)


def generate_confidence_brief(
    *,
    decision: ConfidenceDecision,
    evidence: Mapping[str, object],
) -> str:
    """Generate a minimal Markdown Confidence Brief from a decision record."""

    evidence_lines = "\n".join(
        f"- {key}: {value}" for key, value in sorted(evidence.items())
    )

    return "\n".join(
        [
            "# Confidence Brief",
            "",
            f"Decision state: `{decision.state}`",
            "",
            f"Reason: {decision.reason}",
            "",
            "## Evidence",
            "",
            evidence_lines or "- No evidence metrics supplied.",
            "",
            "## Scientific Limits",
            "",
            SCIENTIFIC_LIMITS_NOTICE,
            "",
        ]
    )
