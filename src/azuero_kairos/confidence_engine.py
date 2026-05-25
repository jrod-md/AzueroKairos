"""Confidence state definitions for Sentinel observation usability."""

from __future__ import annotations

from dataclasses import dataclass


USABLE = "usable"
LOW_CONFIDENCE = "low_confidence"
DO_NOT_INFER = "do_not_infer"

DECISION_STATES = (USABLE, LOW_CONFIDENCE, DO_NOT_INFER)


@dataclass(frozen=True)
class ConfidenceDecision:
    """Minimal decision record for future observation classifiers."""

    state: str
    reason: str


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
