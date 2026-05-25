"""Confidence state definitions for Sentinel observation usability."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any


USABLE = "usable"
LOW_CONFIDENCE = "low_confidence"
DO_NOT_INFER = "do_not_infer"

DECISION_STATES = (USABLE, LOW_CONFIDENCE, DO_NOT_INFER)

RECOMMENDED_ACTIONS = {
    USABLE: "Use for exploratory hydro-sedimentary interpretation with stated limits.",
    LOW_CONFIDENCE: "Review cautiously and consider field verification.",
    DO_NOT_INFER: (
        "Do not make a satellite-based inference; wait for a new acquisition "
        "or request field verification."
    ),
}

DECISIONS = {
    USABLE: "interpret",
    LOW_CONFIDENCE: "review",
    DO_NOT_INFER: "do_not_infer",
}


@dataclass(frozen=True)
class ConfidenceDecision:
    """Minimal decision record for future observation classifiers."""

    state: str
    reason: str


def classify_confidence(
    valid_percent: float,
    sample_count: int | None = None,
    no_data_count: int | None = None,
) -> dict[str, str]:
    """Classify a Sentinel observation by valid observation percentage."""

    if _is_invalid_input(valid_percent, sample_count, no_data_count):
        return _build_confidence_result(
            DO_NOT_INFER,
            "Invalid input or valid percentage is below 10 percent.",
        )

    if valid_percent < 10:
        return _build_confidence_result(
            DO_NOT_INFER,
            "Valid percentage is below 10 percent.",
        )

    if valid_percent < 30:
        return _build_confidence_result(
            LOW_CONFIDENCE,
            "Valid percentage is at least 10 percent and below 30 percent.",
        )

    return _build_confidence_result(
        USABLE,
        "Valid percentage is at least 30 percent.",
    )


def _is_invalid_input(
    valid_percent: Any,
    sample_count: int | None,
    no_data_count: int | None,
) -> bool:
    if isinstance(valid_percent, bool) or not isinstance(valid_percent, int | float):
        return True

    if not math.isfinite(valid_percent) or valid_percent < 0 or valid_percent > 100:
        return True

    for count in (sample_count, no_data_count):
        if count is None:
            continue
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            return True

    return False


def _build_confidence_result(confidence_class: str, reason: str) -> dict[str, str]:
    return {
        "confidence_class": confidence_class,
        "decision": DECISIONS[confidence_class],
        "reason": reason,
        "recommended_action": RECOMMENDED_ACTIONS[confidence_class],
    }


def classify_observation(
    *,
    valid_pixel_fraction: float | None,
    cloud_fraction: float | None,
    has_required_bands: bool,
) -> ConfidenceDecision:
    """Classify whether a Sentinel observation supports limited inference."""

    if not has_required_bands:
        return ConfidenceDecision(DO_NOT_INFER, "Required Sentinel bands are missing.")

    if valid_pixel_fraction is None or cloud_fraction is None:
        return ConfidenceDecision(DO_NOT_INFER, "Required quality metrics are missing.")

    if valid_pixel_fraction < 0.5 or cloud_fraction > 0.6:
        return ConfidenceDecision(DO_NOT_INFER, "Observation quality is insufficient.")

    if valid_pixel_fraction < 0.8 or cloud_fraction > 0.3:
        return ConfidenceDecision(LOW_CONFIDENCE, "Observation quality is limited.")

    return ConfidenceDecision(USABLE, "Observation quality supports limited interpretation.")


if __name__ == "__main__":
    for percent in (47.72, 0.00, 13.24, 58.34, 34.94):
        print(json.dumps(classify_confidence(percent), sort_keys=True))
