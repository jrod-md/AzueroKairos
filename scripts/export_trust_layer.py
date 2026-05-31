"""Export static public-safe Kairos Trust Layer v1 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_ROOT / "frontend/public/data"
TRUST_DIR = PROJECT_ROOT / "frontend/public/trust/v1"

SCHEMA_VERSION = "kairos.trust.v1"
VERIFICATION_PAYLOAD_VERSION = "kairos-trust-payload-v1"
PILOT_NAME = "Azuero Kairos - Rio La Villa"
PRIMARY_LAYER = "Sentinel-2"
TRUST_CLAIM_LIMIT = (
    "La capa Trust no certifica condiciones quimicas, sanitarias ni operativas; "
    "verifica la trazabilidad del paquete de evidencia."
)
PUBLIC_DATASETS = {
    "observations": "observations.json",
    "kairos_watch": "kairos_watch.json",
    "decision_cases": "decision_cases.json",
    "evidence_ledger": "evidence_ledger.json",
    "sar_context": "sar_context.json",
    "exposure_context": "exposure_context.json",
    "hydroclimate_context": "hydroclimate_context.json",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate static read-only Trust Layer v1 JSON from public data."
    )
    parser.add_argument("--data-dir", default=str(PUBLIC_DATA_DIR))
    parser.add_argument("--output-dir", default=str(TRUST_DIR))
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    if not data_dir.exists():
        print(f"Missing public data dir: {display_path(data_dir)}", file=sys.stderr)
        return 1

    public_data = load_public_data(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reset_generated_dirs(output_dir)

    ledger_rows = as_list(public_data.get("evidence_ledger"))
    observations = as_list(public_data.get("observations"))
    cases = get_cases(public_data.get("decision_cases"))

    ledger_by_date_aoi = group_ledger_by_date_aoi(ledger_rows)
    auxiliary_indexes = build_auxiliary_indexes(public_data)

    decisions: list[dict[str, Any]] = []
    passports: list[dict[str, Any]] = []

    for record in observations:
        bundle = build_official_bundle(
            record=record,
            ledger_rows=ledger_by_date_aoi.get(
                date_aoi_key(record.get("date"), record.get("aoi")), []
            ),
            auxiliary_indexes=auxiliary_indexes,
        )
        decisions.append(bundle["decision"])
        passports.append(bundle["passport"])

    for case in cases:
        bundle = build_case_bundle(
            case=case,
            ledger_rows=ledger_by_date_aoi.get(
                date_aoi_key(case.get("date"), "corridor_wide"), []
            ),
            auxiliary_indexes=auxiliary_indexes,
        )
        decisions.append(bundle["decision"])
        passports.append(bundle["passport"])

    ledger_artifacts = build_ledger_artifacts(
        ledger_rows=ledger_rows,
        decisions=decisions,
        passports=passports,
    )

    write_collection(output_dir / "decisions", decisions, "decision_id")
    write_collection(output_dir / "passports", passports, "passport_id")
    write_collection(output_dir / "ledger", ledger_artifacts, "event_id")

    index = build_index(
        output_dir=output_dir,
        public_data=public_data,
        decisions=decisions,
        passports=passports,
        ledger_artifacts=ledger_artifacts,
    )
    write_json(output_dir / "index.json", index)
    write_json(output_dir / "openapi.json", build_contract(index=index))
    write_json(output_dir / "validation_report.json", build_pending_validation_report(index=index))

    print(f"Trust Layer output: {display_path(output_dir)}")
    print(f"Passports: {len(passports)}")
    print(f"Decisions: {len(decisions)}")
    print(f"Ledger events: {len(ledger_artifacts)}")
    print(f"Collections: {', '.join(index['available_collections'])}")
    return 0


def load_public_data(data_dir: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, filename in PUBLIC_DATASETS.items():
        path = data_dir / filename
        if not path.exists():
            payload[key] = None
            continue
        payload[key] = read_json(path)
    return payload


def reset_generated_dirs(output_dir: Path) -> None:
    for name in ("passports", "decisions", "ledger"):
        path = output_dir / name
        if path.exists():
            if not path.resolve().is_relative_to(output_dir.resolve()):
                raise RuntimeError(f"Refusing to remove outside trust dir: {path}")
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)


def build_official_bundle(
    *,
    record: dict[str, Any],
    ledger_rows: list[dict[str, Any]],
    auxiliary_indexes: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    target_date = clean(record.get("date"))
    aoi = clean(record.get("aoi")) or "corridor_wide"
    decision_id = f"decision-official-{slug(aoi)}-{slug(target_date)}"
    passport_id = official_passport_id(record=record, ledger_rows=ledger_rows)
    ledger_refs = build_ledger_refs(ledger_rows)

    decision = {
        "schema_version": SCHEMA_VERSION,
        "decision_id": decision_id,
        "target_date": target_date,
        "scope_type": "official_observation",
        "aoi": aoi,
        "confidence_class": clean(record.get("confidence_class")),
        "confidence_label": clean(record.get("confidence_label_es")),
        "validPercent": as_number(record.get("validPercent")),
        "api_status": clean(record.get("api_status")),
        "decision_reason": clean(record.get("reason_es") or record.get("reason")),
        "recommended_action": clean(
            record.get("recommended_action_es") or record.get("recommended_action")
        ),
        "primary_layer": PRIMARY_LAYER,
        "auxiliary_context_available": auxiliary_availability(
            target_date=target_date,
            node_id="",
            indexes=auxiliary_indexes,
        ),
        "passport_id": passport_id,
        "claim_limit": TRUST_CLAIM_LIMIT,
    }
    decision["verification_hash"] = verification_hash(decision)

    passport = {
        "schema_version": SCHEMA_VERSION,
        "passport_id": passport_id,
        "decision_id": decision_id,
        "scope_type": "official_observation",
        "aoi": aoi,
        "target_date": target_date,
        "confidence_class": clean(record.get("confidence_class")),
        "confidence_label": clean(record.get("confidence_label_es")),
        "validPercent": as_number(record.get("validPercent")),
        "api_status": clean(record.get("api_status")),
        "primary_layer": PRIMARY_LAYER,
        "auxiliary_layers": summarize_auxiliary_layers(
            target_date=target_date,
            node_id="",
            indexes=auxiliary_indexes,
        ),
        "ledger_refs": ledger_refs,
        "artifact_refs": official_artifact_refs(
            decision_id=decision_id,
            passport_id=passport_id,
        ),
        "claim_limit": TRUST_CLAIM_LIMIT,
        "verification_payload_version": VERIFICATION_PAYLOAD_VERSION,
    }
    passport["verification_hash"] = verification_hash(passport)
    return {"decision": decision, "passport": passport}


def build_case_bundle(
    *,
    case: dict[str, Any],
    ledger_rows: list[dict[str, Any]],
    auxiliary_indexes: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    target_date = clean(case.get("date"))
    node_id = clean(case.get("node_id"))
    node_name = clean(case.get("node_display_name") or case.get("node_name"))
    decision_id = f"decision-case-{slug(node_id)}-{slug(target_date)}"
    passport_id = case_passport_id(case)
    ledger_refs = build_ledger_refs(ledger_rows)

    decision = {
        "schema_version": SCHEMA_VERSION,
        "decision_id": decision_id,
        "target_date": target_date,
        "scope_type": "node_date_case",
        "node_id": node_id,
        "node_name": node_name,
        "confidence_class": clean(case.get("primary_confidence_class")),
        "confidence_label": clean(case.get("decision_label")),
        "validPercent": as_number(case.get("primary_validPercent")),
        "api_status": "OK",
        "decision_reason": clean(case.get("decision_rationale")),
        "recommended_action": clean(
            case.get("recommended_action") or case.get("recommended_workflow")
        ),
        "primary_layer": PRIMARY_LAYER,
        "auxiliary_context_available": auxiliary_availability(
            target_date=target_date,
            node_id=node_id,
            indexes=auxiliary_indexes,
        ),
        "passport_id": passport_id,
        "claim_limit": TRUST_CLAIM_LIMIT,
    }
    decision["verification_hash"] = verification_hash(decision)

    passport = {
        "schema_version": SCHEMA_VERSION,
        "passport_id": passport_id,
        "decision_id": decision_id,
        "scope_type": "node_date_case",
        "node_id": node_id,
        "node_name": node_name,
        "target_date": target_date,
        "confidence_class": clean(case.get("primary_confidence_class")),
        "confidence_label": clean(case.get("decision_label")),
        "validPercent": as_number(case.get("primary_validPercent")),
        "api_status": "OK",
        "primary_layer": PRIMARY_LAYER,
        "auxiliary_layers": summarize_auxiliary_layers(
            target_date=target_date,
            node_id=node_id,
            indexes=auxiliary_indexes,
        ),
        "ledger_refs": ledger_refs,
        "artifact_refs": case_artifact_refs(
            decision_id=decision_id,
            passport_id=passport_id,
        ),
        "claim_limit": TRUST_CLAIM_LIMIT,
        "verification_payload_version": VERIFICATION_PAYLOAD_VERSION,
    }
    passport["verification_hash"] = verification_hash(passport)
    return {"decision": decision, "passport": passport}


def build_ledger_artifacts(
    *,
    ledger_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    passports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decision_lookup = {
        date_aoi_key(item.get("target_date"), item.get("aoi") or "corridor_wide"): item
        for item in decisions
        if item.get("scope_type") == "official_observation"
    }
    passport_lookup = {item["decision_id"]: item for item in passports}

    artifacts: list[dict[str, Any]] = []
    for index, row in enumerate(ledger_rows, start=1):
        event_hash = clean(row.get("event_hash") or row.get("hash") or row.get("hash_short"))
        event_id = f"ledger-{slug(row.get('date'))}-{slug(row.get('aoi') or 'corridor_wide')}-{index:03d}"
        decision = decision_lookup.get(date_aoi_key(row.get("date"), row.get("aoi")))
        passport = passport_lookup.get(clean(decision.get("decision_id")) if decision else "")
        artifact_ref = safe_public_ref(row.get("artifact_ref"))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "event_id": event_id,
            "event_type": clean(row.get("event_type")),
            "event_label": clean(row.get("event_label") or row.get("event_label_es")),
            "timestamp": clean(row.get("generated_at_utc")),
            "artifact_ref": artifact_ref,
            "artifact_ref_status": "public" if artifact_ref else "not_public_in_trust_layer",
            "status": clean(row.get("status")),
            "hash": event_hash,
            "hash_method": clean(row.get("hash_method")),
            "decision_id": clean(decision.get("decision_id")) if decision else "",
            "passport_id": clean(passport.get("passport_id")) if passport else "",
        }
        payload["verification_hash"] = verification_hash(payload)
        artifacts.append(payload)
    return artifacts


def build_auxiliary_indexes(public_data: dict[str, Any]) -> dict[str, Any]:
    sar_rows = as_list((public_data.get("sar_context") or {}).get("rows"))
    hydro_rows = as_list((public_data.get("hydroclimate_context") or {}).get("rows")) or as_list(
        (public_data.get("hydroclimate_context") or {}).get("observations")
    )
    exposure_rows = as_list((public_data.get("exposure_context") or {}).get("observations"))

    return {
        "sar_by_node_date": index_rows(sar_rows, "node_id", "target_date"),
        "sar_by_date": group_rows(sar_rows, "target_date"),
        "sar_summary": public_data.get("sar_context") or {},
        "hydro_by_node_date": index_rows(hydro_rows, "node_id", "target_date"),
        "hydro_by_date": group_rows(hydro_rows, "target_date"),
        "hydro_summary": public_data.get("hydroclimate_context") or {},
        "clms_by_node": {clean(row.get("node_id")): row for row in exposure_rows},
        "clms_summary": public_data.get("exposure_context") or {},
    }


def auxiliary_availability(
    *,
    target_date: str,
    node_id: str,
    indexes: dict[str, Any],
) -> dict[str, bool]:
    return {
        "sar": bool(select_aux_row(indexes, "sar", target_date, node_id)),
        "clms": bool(indexes["clms_by_node"].get(node_id))
        if node_id
        else bool(indexes["clms_by_node"]),
        "hydroclimate": bool(select_aux_row(indexes, "hydro", target_date, node_id)),
    }


def summarize_auxiliary_layers(
    *,
    target_date: str,
    node_id: str,
    indexes: dict[str, Any],
) -> dict[str, Any]:
    sar = select_aux_row(indexes, "sar", target_date, node_id)
    hydro = select_aux_row(indexes, "hydro", target_date, node_id)
    clms = indexes["clms_by_node"].get(node_id) if node_id else None
    clms_rows = list(indexes["clms_by_node"].values())

    return {
        "sar": {
            "available": bool(sar),
            "status": clean(sar.get("context_status")) if sar else aggregate_status(indexes["sar_by_date"].get(target_date, [])),
            "matched_rows": len(indexes["sar_by_date"].get(target_date, [])),
            "claim_limit": clean((sar or indexes["sar_summary"]).get("claim_limit")),
        },
        "clms": {
            "available": bool(clms or clms_rows),
            "status": clean((clms or {}).get("exposure_status"))
            if clms
            else "node_context_available"
            if clms_rows
            else "",
            "matched_nodes": len(clms_rows),
            "reference_year": as_number((clms or indexes["clms_summary"]).get("reference_year")),
            "claim_limit": clean((clms or indexes["clms_summary"]).get("claim_limit")),
        },
        "hydroclimate": {
            "available": bool(hydro),
            "status": clean(hydro.get("context_status")) if hydro else aggregate_status(indexes["hydro_by_date"].get(target_date, [])),
            "matched_rows": len(indexes["hydro_by_date"].get(target_date, [])),
            "claim_limit": clean((hydro or indexes["hydro_summary"]).get("claim_limit")),
        },
        "limits": (
            "Auxiliary layers are context only and do not modify the Sentinel-2 "
            "confidence classification."
        ),
    }


def select_aux_row(
    indexes: dict[str, Any],
    layer: str,
    target_date: str,
    node_id: str,
) -> dict[str, Any] | None:
    if layer == "sar":
        if node_id:
            row = indexes["sar_by_node_date"].get((node_id, target_date))
            if row:
                return row
        rows = indexes["sar_by_date"].get(target_date, [])
    else:
        if node_id:
            row = indexes["hydro_by_node_date"].get((node_id, target_date))
            if row:
                return row
        rows = indexes["hydro_by_date"].get(target_date, [])
    return rows[0] if rows else None


def build_index(
    *,
    output_dir: Path,
    public_data: dict[str, Any],
    decisions: list[dict[str, Any]],
    passports: list[dict[str, Any]],
    ledger_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    example_passport = passports[0]["passport_id"] if passports else ""
    example_decision = decisions[0]["decision_id"] if decisions else ""
    example_ledger = ledger_artifacts[0]["event_id"] if ledger_artifacts else ""
    available_data = sorted(key for key, payload in public_data.items() if payload is not None)
    counts = {
        "official_observations": len(as_list(public_data.get("observations"))),
        "kairos_watch_observations": len(as_list((public_data.get("kairos_watch") or {}).get("observations"))),
        "decision_cases": len(get_cases(public_data.get("decision_cases"))),
        "evidence_ledger_events": len(as_list(public_data.get("evidence_ledger"))),
        "trust_passports": len(passports),
        "trust_decisions": len(decisions),
        "trust_ledger_events": len(ledger_artifacts),
        "sar_rows": len(as_list((public_data.get("sar_context") or {}).get("rows"))),
        "clms_nodes": len(as_list((public_data.get("exposure_context") or {}).get("observations"))),
        "hydroclimate_rows": len(as_list((public_data.get("hydroclimate_context") or {}).get("rows"))),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": now_utc(),
        "pilot_name": PILOT_NAME,
        "public_safe": True,
        "primary_layer": PRIMARY_LAYER,
        "claim_limit": TRUST_CLAIM_LIMIT,
        "counts": counts,
        "source_public_data": available_data,
        "available_collections": [
            "index",
            "passports",
            "decisions",
            "ledger",
            "openapi",
            "validation_report",
        ],
        "example_verification_paths": {
            "index": "/trust/v1/index.json",
            "passport": f"/trust/v1/passports/{example_passport}.json"
            if example_passport
            else "",
            "decision": f"/trust/v1/decisions/{example_decision}.json"
            if example_decision
            else "",
            "ledger": f"/trust/v1/ledger/{example_ledger}.json" if example_ledger else "",
            "validation_report": "/trust/v1/validation_report.json",
            "contract": "/trust/v1/openapi.json",
        },
        "generated_files_root": trust_public_path(output_dir),
    }


def build_contract(*, index: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "title": "Kairos Trust Layer v1 static contract",
        "generated_at_utc": now_utc(),
        "read_only": True,
        "public_safe": True,
        "base_path": "/trust/v1",
        "primary_layer": PRIMARY_LAYER,
        "claim_limit": TRUST_CLAIM_LIMIT,
        "limits": [
            "Static JSON only; no database and no external API call is required.",
            "Trust Layer verifies traceability of the evidence packet.",
            "Auxiliary layers never modify the Sentinel-2 confidence classification.",
            "No chemical, sanitary, water-safety, operational-readiness, or authority-level certification is provided.",
        ],
        "collections": {
            "index": {
                "path": "/trust/v1/index.json",
                "fields": [
                    "schema_version",
                    "generated_at_utc",
                    "pilot_name",
                    "public_safe",
                    "counts",
                    "available_collections",
                    "example_verification_paths",
                ],
            },
            "passports": {
                "path": "/trust/v1/passports/{passport_id}.json",
                "id_field": "passport_id",
                "fields": [
                    "passport_id",
                    "decision_id",
                    "scope_type",
                    "node_id",
                    "aoi",
                    "target_date",
                    "confidence_class",
                    "validPercent",
                    "primary_layer",
                    "auxiliary_layers",
                    "ledger_refs",
                    "artifact_refs",
                    "claim_limit",
                    "verification_hash",
                ],
            },
            "decisions": {
                "path": "/trust/v1/decisions/{decision_id}.json",
                "id_field": "decision_id",
                "fields": [
                    "decision_id",
                    "target_date",
                    "node_id",
                    "aoi",
                    "confidence_class",
                    "validPercent",
                    "decision_reason",
                    "recommended_action",
                    "primary_layer",
                    "passport_id",
                    "verification_hash",
                ],
            },
            "ledger": {
                "path": "/trust/v1/ledger/{event_id}.json",
                "id_field": "event_id",
                "fields": [
                    "event_id",
                    "event_type",
                    "event_label",
                    "timestamp",
                    "artifact_ref",
                    "status",
                    "hash",
                    "decision_id",
                    "passport_id",
                ],
            },
            "validation_report": {
                "path": "/trust/v1/validation_report.json",
                "fields": ["status", "generated_at_utc", "checks", "summary"],
            },
        },
        "examples": index.get("example_verification_paths", {}),
    }


def build_pending_validation_report(*, index: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": now_utc(),
        "status": "pending_validation",
        "summary": {
            "message": "Run scripts/validate_public_demo.py to refresh validation gates.",
            "counts": index.get("counts", {}),
        },
        "checks": [],
    }


def official_artifact_refs(*, decision_id: str, passport_id: str) -> dict[str, str]:
    return {
        "observations": "/data/observations.json",
        "evidence_ledger": "/data/evidence_ledger.json",
        "decision": f"/trust/v1/decisions/{decision_id}.json",
        "passport": f"/trust/v1/passports/{passport_id}.json",
    }


def case_artifact_refs(*, decision_id: str, passport_id: str) -> dict[str, str]:
    return {
        "kairos_watch": "/data/kairos_watch.json",
        "decision_cases": "/data/decision_cases.json",
        "decision": f"/trust/v1/decisions/{decision_id}.json",
        "passport": f"/trust/v1/passports/{passport_id}.json",
    }


def build_ledger_refs(ledger_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs = []
    for row in ledger_rows:
        event_hash = clean(row.get("event_hash") or row.get("hash_short"))
        if not event_hash:
            continue
        refs.append(
            {
                "event_type": clean(row.get("event_type")),
                "hash": event_hash,
                "hash_short": clean(row.get("hash_short")) or event_hash[:12],
            }
        )
    return refs


def write_collection(path: Path, rows: list[dict[str, Any]], id_field: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for row in rows:
        write_json(path / f"{row[id_field]}.json", row)


def official_passport_id(*, record: dict[str, Any], ledger_rows: list[dict[str, Any]]) -> str:
    decision_row = next(
        (row for row in ledger_rows if clean(row.get("event_type")) == "confidence_decision_computed"),
        None,
    )
    passport_hash = clean(
        (decision_row or {}).get("event_hash")
        or (decision_row or {}).get("artifact_hash")
        or clean(record.get("date")) + "-" + clean(record.get("aoi"))
    )
    return f"KAIROS-P1-{clean(record.get('date')).replace('-', '')}-{short_hash(passport_hash, 8)}"


def case_passport_id(case: dict[str, Any]) -> str:
    date_part = clean(case.get("date")).replace("-", "") or "00000000"
    seed = clean(case.get("case_id")) or f"{case.get('node_id')}-{case.get('date')}"
    return f"KAIROS-P1-{date_part}-{short_hash(stable_digest(seed), 8)}"


def verification_hash(payload: dict[str, Any]) -> str:
    stable = {key: value for key, value in payload.items() if key != "verification_hash"}
    return f"sha256:{stable_digest(stable)}"


def stable_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def short_hash(value: Any, length: int) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]", "", clean(value))
    return (normalized[:length] or "sinhash").lower()


def safe_public_ref(value: Any) -> str:
    text = clean(value).replace("\\", "/")
    if not text:
        return ""
    if re.match(r"^[A-Za-z]:/", text) or text.startswith("/"):
        return ""
    if text.startswith("frontend/public/"):
        return "/" + text.removeprefix("frontend/public/").lstrip("/")
    if text.startswith("public/"):
        return "/" + text.removeprefix("public/").lstrip("/")
    if text.startswith("/data/") or text.startswith("/trust/"):
        return text
    return ""


def trust_public_path(path: Path) -> str:
    try:
        rel = path.resolve().relative_to((PROJECT_ROOT / "frontend/public").resolve())
    except ValueError:
        return ""
    return "/" + rel.as_posix()


def group_ledger_by_date_aoi(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(date_aoi_key(row.get("date"), row.get("aoi")), []).append(row)
    return grouped


def index_rows(rows: list[dict[str, Any]], id_field: str, date_field: str) -> dict[tuple[str, str], dict[str, Any]]:
    return {(clean(row.get(id_field)), clean(row.get(date_field))): row for row in rows}


def group_rows(rows: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(clean(row.get(field)), []).append(row)
    return grouped


def aggregate_status(rows: list[dict[str, Any]]) -> str:
    statuses = [clean(row.get("context_status")) for row in rows if clean(row.get("context_status"))]
    if not statuses:
        return ""
    counts = Counter(statuses)
    return counts.most_common(1)[0][0]


def date_aoi_key(date: Any, aoi: Any) -> tuple[str, str]:
    return (clean(date), clean(aoi) or "corridor_wide")


def get_cases(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return as_list(payload.get("cases") or payload.get("rows"))
    return as_list(payload)


def as_list(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def as_number(value: Any) -> int | float | str:
    if isinstance(value, int | float):
        return value
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def slug(value: Any) -> str:
    text = clean(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
