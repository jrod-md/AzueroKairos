"""Validate public Kairos demo data and generated Trust Layer artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_ROOT / "frontend/public/data"
TRUST_DIR = PROJECT_ROOT / "frontend/public/trust/v1"
DOCS_REPORT = PROJECT_ROOT / "docs/demo_quality_report.md"

SCHEMA_VERSION = "kairos.trust.validation.v1"
EXPECTED_OFFICIAL_DATES = {
    "2025-06-02",
    "2025-06-10",
    "2025-06-15",
    "2025-06-30",
    "2025-07-15",
}
CONTRAST_DATES = ("2025-06-10", "2025-06-30")
EXPECTED_NODE_DATE_ROWS = 15
EXPECTED_NODE_COVERAGE = 3
MOJIBAKE_PATTERN = re.compile("[\u00c3\u00c2\u00e2\ufffd]")
UNSAFE_PATTERNS = [
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")),
    ("authorization header", re.compile(r"(?i)\bauthorization\s*[:=]")),
    ("request cookie", re.compile(r"(?i)\bcookie\s*:")),
    ("api key", re.compile(r"(?i)\b(api[_-]?key|x-api-key)\b")),
    ("client secret", re.compile(r"(?i)\bclient[_-]?secret\b")),
    ("access token", re.compile(r"(?i)\b(access|refresh)[_-]?token\b")),
    ("windows absolute path", re.compile(r"(?i)\b[A-Z]:\\[A-Za-z0-9_ .\\/-]+")),
    ("posix user path", re.compile(r"(?i)(/users/|/home/)")),
    ("raw output payload", re.compile(r"(?i)outputs/(raw_json|raw|payloads)")),
]
PROHIBITED_CLAIM_TERMS = [
    "contamination detection",
    "chemical detection",
    "sanitary validation",
    "water safety",
    "potability",
    "crisis validation",
    "operational readiness",
    "automatic closure",
    "mandatory suspension",
    "authority-level decisions",
    "yield prediction",
    "measured crop loss reduction",
    "detecta contaminacion",
    "deteccion de contaminacion",
    "detecta quim",
    "validacion sanitaria",
    "agua segura",
    "potabilidad",
    "crisis",
    "cierre automatico",
    "suspension obligatoria",
    "decision de autoridad",
    "prediccion de rendimiento",
    "reduccion medida de perdidas",
]
NEGATION_MARKERS = (
    " no ",
    " not ",
    " never ",
    " does not ",
    " do not ",
    " sin ",
    " ni ",
    " no certifica ",
    " no hace ",
    " no detecta ",
    " no modifica ",
    " not used ",
    " certification is provided",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate public demo data, Trust Layer artifacts, and claim limits."
    )
    parser.add_argument("--data-dir", default=str(PUBLIC_DATA_DIR))
    parser.add_argument("--trust-dir", default=str(TRUST_DIR))
    parser.add_argument("--docs-report", default=str(DOCS_REPORT))
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    trust_dir = Path(args.trust_dir)
    docs_report = Path(args.docs_report)

    context = {
        "data_dir": data_dir,
        "trust_dir": trust_dir,
        "observations": read_json_if_exists(data_dir / "observations.json", []),
        "kairos_watch": read_json_if_exists(data_dir / "kairos_watch.json", None),
        "decision_cases": read_json_if_exists(data_dir / "decision_cases.json", None),
        "evidence_ledger": read_json_if_exists(data_dir / "evidence_ledger.json", []),
        "sar_context": read_json_if_exists(data_dir / "sar_context.json", None),
        "exposure_context": read_json_if_exists(data_dir / "exposure_context.json", None),
        "hydroclimate_context": read_json_if_exists(data_dir / "hydroclimate_context.json", None),
        "trust_index": read_json_if_exists(trust_dir / "index.json", None),
        "trust_passports": read_trust_collection(trust_dir / "passports"),
        "trust_decisions": read_trust_collection(trust_dir / "decisions"),
        "trust_ledger": read_trust_collection(trust_dir / "ledger"),
    }

    checks = [
        check_official_observations(context),
        check_contrast_dates(context),
        check_evidence_uplift(context),
        check_kairos_watch(context),
        check_sar_context(context),
        check_clms_context(context),
        check_hydroclimate_context(context),
        check_ledger_hashes(context),
        check_trust_passport_hashes(context),
        check_exposure_safety(data_dir, trust_dir),
        check_mojibake(data_dir, trust_dir, docs_report),
        check_positive_claims(trust_dir),
    ]
    report = build_report(checks=checks, context=context)
    write_json(trust_dir / "validation_report.json", report)
    write_docs_report(docs_report, report)

    print(f"Validation status: {report['status']}")
    print(f"Checks passed: {report['summary']['passed']}/{report['summary']['total_checks']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Failures: {report['summary']['failed']}")
    print(f"Trust report: {display_path(trust_dir / 'validation_report.json')}")
    print(f"Docs report: {display_path(docs_report)}")
    return 0 if report["summary"]["failed"] == 0 else 1


def check_official_observations(context: dict[str, Any]) -> dict[str, Any]:
    rows = as_list(context["observations"])
    dates = {clean(row.get("date")) for row in rows}
    missing = sorted(EXPECTED_OFFICIAL_DATES - dates)
    return check(
        "official_observations",
        "Expected official observations exist",
        "pass" if not missing else "fail",
        f"{len(rows)} official observations; missing dates: {', '.join(missing) or 'none'}",
        {"count": len(rows), "dates": sorted(dates), "expected": sorted(EXPECTED_OFFICIAL_DATES)},
    )


def check_contrast_dates(context: dict[str, Any]) -> dict[str, Any]:
    rows = rows_by_date(as_list(context["observations"]))
    missing = [date for date in CONTRAST_DATES if date not in rows]
    return check(
        "contrast_dates",
        "2025-06-10 and 2025-06-30 contrast exists",
        "pass" if not missing else "fail",
        f"Contrast dates present: {', '.join(date for date in CONTRAST_DATES if date in rows)}",
        {"missing": missing},
    )


def check_evidence_uplift(context: dict[str, Any]) -> dict[str, Any]:
    rows = rows_by_date(as_list(context["observations"]))
    weak = rows.get(CONTRAST_DATES[0])
    usable = rows.get(CONTRAST_DATES[1])
    weak_value = to_float((weak or {}).get("validPercent"))
    usable_value = to_float((usable or {}).get("validPercent"))
    if weak_value <= 0 or usable_value <= 0:
        return check(
            "evidence_uplift",
            "Evidence uplift can be computed",
            "fail",
            "validPercent missing or zero for contrast dates",
            {"from_date": CONTRAST_DATES[0], "to_date": CONTRAST_DATES[1]},
        )
    ratio = round(usable_value / weak_value, 2)
    delta = round(usable_value - weak_value, 2)
    return check(
        "evidence_uplift",
        "Evidence uplift can be computed",
        "pass",
        f"{CONTRAST_DATES[0]} -> {CONTRAST_DATES[1]}: {ratio}x valid evidence",
        {
            "from_date": CONTRAST_DATES[0],
            "from_validPercent": weak_value,
            "to_date": CONTRAST_DATES[1],
            "to_validPercent": usable_value,
            "uplift_ratio": ratio,
            "uplift_delta_points": delta,
        },
    )


def check_kairos_watch(context: dict[str, Any]) -> dict[str, Any]:
    payload = context["kairos_watch"]
    if not payload:
        return check(
            "kairos_watch_rows",
            "Kairos Watch has node-date observations if available",
            "warn",
            "kairos_watch.json not available",
        )
    rows = as_list(payload.get("observations"))
    status = "pass" if len(rows) == EXPECTED_NODE_DATE_ROWS else "fail"
    return check(
        "kairos_watch_rows",
        "Kairos Watch has 15 node-date observations",
        status,
        f"{len(rows)} node-date rows",
        {"expected": EXPECTED_NODE_DATE_ROWS, "count": len(rows)},
    )


def check_sar_context(context: dict[str, Any]) -> dict[str, Any]:
    payload = context["sar_context"]
    if not payload:
        return check("sar_context_rows", "SAR context row count if available", "warn", "sar_context.json not available")
    rows = as_list(payload.get("rows"))
    summary = {
        "rows_total": payload.get("rows_total"),
        "available": payload.get("sar_context_available_count"),
        "no_acquisition": payload.get("sar_no_acquisition_count"),
        "low_observation": payload.get("sar_low_observation_count"),
        "api_error": payload.get("sar_api_error_count"),
    }
    status = "pass" if len(rows) == EXPECTED_NODE_DATE_ROWS else "fail"
    return check(
        "sar_context_rows",
        "SAR context has expected row count and availability summary",
        status,
        f"{len(rows)} SAR rows; summary available",
        {"expected": EXPECTED_NODE_DATE_ROWS, "count": len(rows), "summary": summary},
    )


def check_clms_context(context: dict[str, Any]) -> dict[str, Any]:
    payload = context["exposure_context"]
    if not payload:
        return check("clms_node_coverage", "CLMS node coverage if available", "warn", "exposure_context.json not available")
    rows = as_list(payload.get("observations"))
    nodes = {clean(row.get("node_id")) for row in rows if clean(row.get("node_id"))}
    status = "pass" if len(nodes) >= EXPECTED_NODE_COVERAGE else "fail"
    return check(
        "clms_node_coverage",
        "CLMS has expected node coverage",
        status,
        f"{len(nodes)} CLMS nodes covered",
        {"expected_minimum": EXPECTED_NODE_COVERAGE, "nodes": sorted(nodes)},
    )


def check_hydroclimate_context(context: dict[str, Any]) -> dict[str, Any]:
    payload = context["hydroclimate_context"]
    if not payload:
        return check("hydroclimate_rows", "HydroClimate row coverage if available", "warn", "hydroclimate_context.json not available")
    rows = as_list(payload.get("rows") or payload.get("observations"))
    status = "pass" if len(rows) == EXPECTED_NODE_DATE_ROWS else "fail"
    return check(
        "hydroclimate_rows",
        "HydroClimate has expected row coverage",
        status,
        f"{len(rows)} HydroClimate rows",
        {"expected": EXPECTED_NODE_DATE_ROWS, "count": len(rows)},
    )


def check_ledger_hashes(context: dict[str, Any]) -> dict[str, Any]:
    rows = as_list(context["evidence_ledger"])
    hashes = [clean(row.get("event_hash") or row.get("hash")) for row in rows]
    hashes = [value for value in hashes if value]
    unique_hashes = set(hashes)
    status = "pass" if len(unique_hashes) > 1 and len(unique_hashes) == len(hashes) else "fail"
    return check(
        "ledger_hashes",
        "Evidence ledger has non-identical hashes for visible events",
        status,
        f"{len(hashes)} visible hashes; {len(unique_hashes)} unique",
        {"hash_count": len(hashes), "unique_hash_count": len(unique_hashes)},
    )


def check_trust_passport_hashes(context: dict[str, Any]) -> dict[str, Any]:
    passports = as_list(context["trust_passports"])
    missing = [
        clean(item.get("passport_id")) or f"passport_{index}"
        for index, item in enumerate(passports, start=1)
        if not clean(item.get("verification_hash")).startswith("sha256:")
    ]
    status = "pass" if passports and not missing else "fail"
    return check(
        "trust_passport_hashes",
        "Generated Trust passports have verification_hash values",
        status,
        f"{len(passports)} Trust passports checked; missing: {len(missing)}",
        {"passport_count": len(passports), "missing": missing},
    )


def check_exposure_safety(data_dir: Path, trust_dir: Path) -> dict[str, Any]:
    matches = []
    for scan_root in (data_dir, trust_dir):
        for path, text in iter_text_files(scan_root):
            for label, pattern in UNSAFE_PATTERNS:
                if pattern.search(text):
                    matches.append({"file": display_path(path), "pattern": label})
    return check(
        "public_safety_scan",
        "No secrets, tokens, headers, local paths, or raw ignored payloads are exposed in public data or Trust",
        "pass" if not matches else "fail",
        f"{len(matches)} unsafe exposure matches",
        {"matches": matches[:25], "match_count": len(matches)},
    )


def check_mojibake(data_dir: Path, trust_dir: Path, docs_report: Path) -> dict[str, Any]:
    matches = []
    scan_roots = [data_dir, trust_dir]
    if docs_report.exists():
        scan_roots.append(docs_report)
    for root in scan_roots:
        for path, text in iter_text_files(root):
            if MOJIBAKE_PATTERN.search(text):
                matches.append(display_path(path))
    return check(
        "mojibake_scan",
        "No mojibake in generated public artifacts",
        "pass" if not matches else "fail",
        f"{len(matches)} files with mojibake",
        {"files": sorted(set(matches))},
    )


def check_positive_claims(trust_dir: Path) -> dict[str, Any]:
    matches = []
    for path, text in iter_text_files(trust_dir):
        for line_number, line in enumerate(text.splitlines(), start=1):
            normalized = f" {strip_accents(line).lower()} "
            for term in PROHIBITED_CLAIM_TERMS:
                if term in normalized and not has_negation(normalized):
                    matches.append(
                        {
                            "file": display_path(path),
                            "line": line_number,
                            "term": term,
                        }
                    )
    return check(
        "positive_claim_scan",
        "Generated Trust Layer has no prohibited positive claims",
        "pass" if not matches else "fail",
        f"{len(matches)} prohibited positive claim matches",
        {"matches": matches[:25], "match_count": len(matches)},
    )


def build_report(*, checks: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    passed = sum(1 for item in checks if item["status"] == "pass")
    warnings = sum(1 for item in checks if item["status"] == "warn")
    failed = sum(1 for item in checks if item["status"] == "fail")
    status = "passed" if failed == 0 and warnings == 0 else "warning" if failed == 0 else "failed"
    uplift = next((item.get("metrics") for item in checks if item["id"] == "evidence_uplift"), {})
    counts = {
        "official_observations": len(as_list(context["observations"])),
        "kairos_watch_observations": len(as_list((context["kairos_watch"] or {}).get("observations"))),
        "decision_cases": len(get_cases(context["decision_cases"])),
        "evidence_ledger_events": len(as_list(context["evidence_ledger"])),
        "trust_passports": len(as_list(context["trust_passports"])),
        "trust_decisions": len(as_list(context["trust_decisions"])),
        "trust_ledger_events": len(as_list(context["trust_ledger"])),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": now_utc(),
        "status": status,
        "summary": {
            "total_checks": len(checks),
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "counts": counts,
            "evidence_uplift": uplift,
        },
        "checks": checks,
    }


def write_docs_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Kairos demo quality report",
        "",
        f"Generated UTC: {report['generated_at_utc']}",
        f"Overall status: {report['status']}",
        "",
        "## Summary",
        "",
        f"- Total checks: {report['summary']['total_checks']}",
        f"- Passed: {report['summary']['passed']}",
        f"- Warnings: {report['summary']['warnings']}",
        f"- Failed: {report['summary']['failed']}",
        f"- Trust passports: {report['summary']['counts']['trust_passports']}",
        f"- Trust decisions: {report['summary']['counts']['trust_decisions']}",
        f"- Trust ledger events: {report['summary']['counts']['trust_ledger_events']}",
        "",
        "## Evidence uplift",
        "",
    ]
    uplift = report["summary"].get("evidence_uplift") or {}
    if uplift.get("uplift_ratio"):
        lines.extend(
            [
                f"- From date: {uplift.get('from_date')}",
                f"- To date: {uplift.get('to_date')}",
                f"- Uplift ratio: {uplift.get('uplift_ratio')}x",
                f"- Delta points: {uplift.get('uplift_delta_points')}",
            ]
        )
    else:
        lines.append("- Not available.")
    lines.extend(["", "## Checks", ""])
    for item in report["checks"]:
        lines.append(f"- [{item['status'].upper()}] {item['id']}: {item['detail']}")
    lines.extend(
        [
            "",
            "## Claim limit",
            "",
            (
                "The Trust Layer verifies traceability of evidence packets. It does not "
                "certify chemical, sanitary, operational, water-safety, or authority-level conditions."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def check(
    check_id: str,
    label: str,
    status: str,
    detail: str,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "detail": detail,
        "metrics": metrics or {},
    }


def read_trust_collection(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for file_path in sorted(path.glob("*.json")):
        payload = read_json_if_exists(file_path, None)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def iter_text_files(root: Path) -> list[tuple[Path, str]]:
    if root.is_file():
        paths = [root]
    elif root.exists():
        paths = [path for path in root.rglob("*") if path.is_file()]
    else:
        paths = []
    files = []
    for path in paths:
        if path.suffix.lower() not in {".json", ".md", ".txt", ".jsx", ".js", ".css", ".py"}:
            continue
        try:
            files.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            files.append((path, path.read_text(encoding="utf-8", errors="replace")))
    return files


def rows_by_date(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("date")): row for row in rows}


def get_cases(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return as_list(payload.get("cases") or payload.get("rows"))
    return as_list(payload)


def has_negation(line: str) -> bool:
    return any(marker in line for marker in NEGATION_MARKERS)


def strip_accents(value: str) -> str:
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "ü": "u",
    }
    text = value.lower()
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def read_json_if_exists(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def as_list(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
