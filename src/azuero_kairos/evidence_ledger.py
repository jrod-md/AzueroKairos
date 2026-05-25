"""Evidence ledger helpers for reproducible confidence decisions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from azuero_kairos.confidence_engine import ConfidenceDecision


def build_ledger_record(
    *,
    observation_id: str,
    decision: ConfidenceDecision,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Build a JSON-serializable ledger record for a classified observation."""

    return {
        "observation_id": observation_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "decision_state": decision.state,
        "decision_reason": decision.reason,
        "evidence": evidence,
    }


def append_jsonl_record(path: Path, record: dict[str, Any]) -> None:
    """Append one record to a JSON Lines evidence ledger."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
