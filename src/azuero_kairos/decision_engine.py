"""Decision-case composition for Azuero Kairos context layers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


CLAIM_FIREWALL = (
    "No detecta pesticidas, metales pesados, patógenos, contaminación química "
    "disuelta ni agua segura."
)

LAB_ESCALATION_STATUS = (
    "solo si verificación territorial o autoridad competente lo justifica"
)

DECISION_CASE_FIELDNAMES = [
    "case_id",
    "node_id",
    "node_display_name",
    "date",
    "primary_confidence_class",
    "primary_validPercent",
    "decision_label",
    "decision_action",
    "priority_level",
    "recommended_workflow",
    "evidence_gaps",
    "claim_firewall",
    "field_verification_status",
    "lab_escalation_status",
    "sar_context_status",
    "exposure_status",
    "hydroclimate_status",
    "ledger_status",
]

BASE_DECISIONS = {
    "do_not_infer": {
        "decision_label": "NO INFERIR",
        "decision_action": (
            "No usar esta observación para afirmar condiciones del territorio."
        ),
        "priority_level": "alta",
        "recommended_workflow": (
            "Solicitar verificación territorial o esperar nueva adquisición."
        ),
        "field_verification_status": "recomendada",
    },
    "low_confidence": {
        "decision_label": "REVISAR",
        "decision_action": (
            "Revisar con cautela y considerar verificación territorial."
        ),
        "priority_level": "media",
        "recommended_workflow": (
            "Revisar datos técnicos y considerar verificación territorial según contexto."
        ),
        "field_verification_status": "opcional/recomendada según contexto",
    },
    "usable": {
        "decision_label": "USABLE",
        "decision_action": (
            "Usar para lectura hidro-sedimentaria exploratoria con límites explícitos."
        ),
        "priority_level": "normal",
        "recommended_workflow": (
            "Interpretar con límites explícitos y mantener trazabilidad."
        ),
        "field_verification_status": "opcional",
    },
}

PRIORITY_ORDER = ["normal", "media", "media-alta", "alta"]

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(client_secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(access_token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(refresh_token\s*[:=]\s*)[^\s,;]+"),
]


def build_decision_cases(
    *,
    sentinel2_rows: Iterable[dict[str, Any]],
    sar_rows: Iterable[dict[str, Any]] | None = None,
    exposure_rows: Iterable[dict[str, Any]] | None = None,
    hydroclimate_rows: Iterable[dict[str, Any]] | None = None,
    ledger_rows: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Compose node/date decision cases from primary and auxiliary layers."""

    sar_index = index_by_node_date(sar_rows or [])
    hydro_index = index_by_node_date(hydroclimate_rows or [])
    exposure_index = index_by_node(exposure_rows or [])
    ledger_exact, ledger_by_date = build_ledger_indexes(ledger_rows or [])

    cases: list[dict[str, Any]] = []
    for row in sentinel2_rows:
        node_id = clean(row.get("node_id") or row.get("aoi"))
        target_date = clean(row.get("date"))
        if not node_id or not target_date:
            continue

        confidence_class = clean(row.get("confidence_class"))
        base = BASE_DECISIONS.get(confidence_class, BASE_DECISIONS["do_not_infer"])
        sar_row = sar_index.get((node_id, target_date))
        hydro_row = hydro_index.get((node_id, target_date))
        exposure_row = exposure_index.get(node_id)

        sar_status = derive_sar_context_status(sar_row)
        exposure_status = derive_exposure_status(exposure_row)
        hydro_status = context_status(
            hydro_row,
            field="hydroclimate_status",
            missing_value="data_unavailable",
        )
        ledger_status = derive_ledger_status(
            ledger_exact=ledger_exact,
            ledger_by_date=ledger_by_date,
            row=row,
        )

        priority_level = derive_priority(
            confidence_class=confidence_class,
            base_priority=base["priority_level"],
            sar_status=sar_status,
            exposure_status=exposure_status,
            hydro_status=hydro_status,
        )
        evidence_gaps = build_evidence_gaps(
            sar_status=sar_status,
            exposure_status=exposure_status,
            hydro_status=hydro_status,
        )

        cases.append(
            {
                "case_id": build_case_id(node_id=node_id, target_date=target_date),
                "node_id": node_id,
                "node_display_name": clean(row.get("node_display_name") or node_id),
                "date": target_date,
                "primary_confidence_class": confidence_class,
                "primary_validPercent": clean(row.get("validPercent")),
                "decision_label": base["decision_label"],
                "decision_action": base["decision_action"],
                "priority_level": priority_level,
                "recommended_workflow": base["recommended_workflow"],
                "evidence_gaps": evidence_gaps,
                "claim_firewall": CLAIM_FIREWALL,
                "field_verification_status": base["field_verification_status"],
                "lab_escalation_status": LAB_ESCALATION_STATUS,
                "sar_context_status": sar_status,
                "exposure_status": exposure_status,
                "hydroclimate_status": hydro_status,
                "ledger_status": ledger_status,
            }
        )

    return sorted(cases, key=lambda item: (item["node_id"], item["date"]))


def derive_priority(
    *,
    confidence_class: str,
    base_priority: str,
    sar_status: str,
    exposure_status: str,
    hydro_status: str,
) -> str:
    priority = base_priority

    if confidence_class == "do_not_infer" and has_missing_context(
        sar_status=sar_status,
        exposure_status=exposure_status,
        hydro_status=hydro_status,
    ):
        priority = "media-alta"

    if (
        confidence_class in {"do_not_infer", "low_confidence"}
        and hydro_status in {"antecedent_rain", "heavy_rain_context"}
    ):
        priority = raise_priority(priority)

    return priority


def has_missing_context(*, sar_status: str, exposure_status: str, hydro_status: str) -> bool:
    return (
        sar_status in {"data_unavailable", "sar_error", "sar_low_observation"}
        or exposure_status in {"data_pending", "data_unavailable"}
        or hydro_status == "data_unavailable"
    )


def raise_priority(priority: str) -> str:
    try:
        index = PRIORITY_ORDER.index(priority)
    except ValueError:
        return priority
    return PRIORITY_ORDER[min(index + 1, len(PRIORITY_ORDER) - 1)]


def build_evidence_gaps(
    *,
    sar_status: str,
    exposure_status: str,
    hydro_status: str,
) -> str:
    gaps: list[str] = []

    if sar_status in {"sar_low_observation", "sar_error", "data_unavailable"}:
        gaps.append("SAR context no disponible para priorización.")
    if exposure_status == "data_pending":
        gaps.append("Exposición agrícola pendiente de CLMS; no se usa para priorización.")
    elif exposure_status == "data_unavailable":
        gaps.append("Exposición agrícola no disponible; no se usa para priorización.")
    if hydro_status == "data_unavailable":
        gaps.append("Contexto hidroclimático no disponible; no se usa para priorización.")

    return " | ".join(gaps) if gaps else "sin brechas críticas"


def derive_sar_context_status(row: dict[str, Any] | None) -> str:
    status = context_status(row, field="context_status", missing_value="data_unavailable")
    if status == "sar_context_available":
        return "SAR context available"
    return status


def derive_exposure_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "data_unavailable"
    agricultural_status = clean(row.get("agricultural_exposure_status"))
    riparian_status = clean(row.get("riparian_context_status"))
    if "exposure_available" in {agricultural_status, riparian_status}:
        return "exposure_available"
    if "data_pending" in {agricultural_status, riparian_status}:
        return "data_pending"
    return "data_unavailable"


def derive_ledger_status(
    *,
    ledger_exact: dict[tuple[str, str], dict[str, Any]],
    ledger_by_date: dict[str, list[dict[str, Any]]],
    row: dict[str, Any],
) -> str:
    aoi = clean(row.get("aoi") or row.get("node_id"))
    target_date = clean(row.get("date"))
    exact = ledger_exact.get((aoi, target_date))
    if exact:
        return clean(exact.get("evidence_status") or exact.get("api_status") or "available")
    if ledger_by_date.get(target_date):
        return "regional_ledger_available"
    return "not_available"


def context_status(
    row: dict[str, Any] | None,
    *,
    field: str,
    missing_value: str,
) -> str:
    if not row:
        return missing_value
    return clean(row.get(field)) or missing_value


def index_by_node_date(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        node_id = clean(row.get("node_id") or row.get("aoi"))
        target_date = clean(row.get("date"))
        if node_id and target_date:
            index[(node_id, target_date)] = row
    return index


def index_by_node(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        node_id = clean(row.get("node_id") or row.get("aoi"))
        if node_id:
            index[node_id] = row
    return index


def build_ledger_indexes(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    exact: dict[tuple[str, str], dict[str, Any]] = {}
    by_date: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        aoi = clean(row.get("aoi"))
        target_date = clean(row.get("date"))
        if aoi and target_date:
            exact[(aoi, target_date)] = row
            by_date.setdefault(target_date, []).append(row)
    return exact, by_date


def build_case_id(*, node_id: str, target_date: str) -> str:
    return f"case_{safe_slug(node_id)}_{safe_slug(target_date)}"


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())


def clean(value: Any) -> str:
    if value is None:
        return ""
    return sanitize_text(str(value))


def sanitize_text(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "[redacted]", text)
    return " ".join(text.split())
