from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from azuero_kairos.confidence_engine import classify_confidence


class ConfidenceEngineTests(unittest.TestCase):
    def test_classifies_usable_at_30_percent_and_above(self) -> None:
        result = classify_confidence(30.0)

        self.assertEqual(
            result,
            {
                "confidence_class": "usable",
                "decision": "interpret",
                "reason": "Valid percentage is at least 30 percent.",
                "recommended_action": (
                    "Use for exploratory hydro-sedimentary interpretation with stated limits."
                ),
            },
        )

    def test_classifies_low_confidence_from_10_to_below_30_percent(self) -> None:
        result = classify_confidence(13.24)

        self.assertEqual(result["confidence_class"], "low_confidence")
        self.assertEqual(result["decision"], "review")
        self.assertEqual(
            result["recommended_action"],
            "Review cautiously and consider field verification.",
        )

    def test_classifies_do_not_infer_below_10_percent(self) -> None:
        result = classify_confidence(0.0)

        self.assertEqual(result["confidence_class"], "do_not_infer")
        self.assertEqual(result["decision"], "do_not_infer")
        self.assertEqual(
            result["recommended_action"],
            "Do not make a satellite-based inference; wait for a new acquisition "
            "or request field verification.",
        )

    def test_classifies_invalid_input_as_do_not_infer(self) -> None:
        invalid_values = (None, "47.72", True, -1.0, 101.0, math.nan, math.inf)

        for value in invalid_values:
            result = classify_confidence(value)  # type: ignore[arg-type]
            self.assertEqual(result["confidence_class"], "do_not_infer")
            self.assertEqual(result["decision"], "do_not_infer")

    def test_classifies_invalid_counts_as_do_not_infer(self) -> None:
        self.assertEqual(
            classify_confidence(47.72, sample_count=-1)["confidence_class"],
            "do_not_infer",
        )
        self.assertEqual(
            classify_confidence(47.72, no_data_count=-1)["confidence_class"],
            "do_not_infer",
        )
        self.assertEqual(
            classify_confidence(47.72, sample_count=True)["confidence_class"],
            "do_not_infer",
        )


if __name__ == "__main__":
    unittest.main()
