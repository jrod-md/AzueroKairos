import React, { useEffect, useMemo, useState } from "react";
import DecisionStamp from "../../components/DecisionStamp/DecisionStamp.jsx";
import "./PassportPage.css";

const PASSPORT_STAGES = [
  {
    eventType: "raw_observation_received",
    label: "Observación cruda",
    shortLabel: "RAW",
  },
  {
    eventType: "processed_metrics_created",
    label: "Métricas procesadas",
    shortLabel: "CSV",
  },
  {
    eventType: "confidence_decision_computed",
    label: "Decisión de confianza",
    shortLabel: "DEC",
  },
  {
    eventType: "brief_generated",
    label: "Brief de evidencia",
    shortLabel: "BRF",
  },
  {
    eventType: "public_export_sanitized",
    label: "Exportación pública",
    shortLabel: "PUB",
  },
  {
    eventType: "evidence_case_registered",
    label: "Caso relacionado",
    shortLabel: "CAS",
  },
];

const CLAIM_LIMIT =
  "No certifica contaminación, potabilidad, salud pública, aptitud de uso ni respuesta institucional.";
const TRUST_LIMIT_COPY =
  "La capa Trust no certifica condiciones químicas, sanitarias ni operativas; verifica la trazabilidad del paquete de evidencia.";

export default function PassportPage({
  availableDates = [],
  decisionCases,
  ledger,
  ledgerRows = [],
  onNavigate,
  record,
  selectedDate,
  setSelectedDate,
}) {
  const [copyState, setCopyState] = useState("idle");
  const [trustCopyState, setTrustCopyState] = useState("idle");
  const [trustVerification, setTrustVerification] = useState({
    reportStatus: "pendiente",
    status: "loading",
    verificationHash: "",
  });
  const passport = useMemo(
    () => buildPassport({ decisionCases, ledger, ledgerRows, record }),
    [decisionCases, ledger, ledgerRows, record],
  );
  const trustPath = useMemo(() => buildTrustPassportPath(passport.id), [passport.id]);

  useEffect(() => {
    let active = true;

    async function loadTrustVerification() {
      setTrustVerification({
        reportStatus: "pendiente",
        status: "loading",
        verificationHash: "",
      });
      try {
        const [passportResponse, reportResponse] = await Promise.all([
          fetch(trustPath),
          fetch("/trust/v1/validation_report.json"),
        ]);
        const passportPayload = passportResponse.ok ? await passportResponse.json() : null;
        const reportPayload = reportResponse.ok ? await reportResponse.json() : null;
        if (!active) return;

        setTrustVerification({
          reportStatus: reportPayload?.status || "no disponible",
          status: passportResponse.ok ? "ready" : "missing",
          verificationHash: passportPayload?.verification_hash || "",
        });
      } catch {
        if (!active) return;
        setTrustVerification({
          reportStatus: "no disponible",
          status: "error",
          verificationHash: "",
        });
      }
    }

    loadTrustVerification();
    return () => {
      active = false;
    };
  }, [trustPath]);

  async function copyPassportPacket() {
    const packet = buildPortablePacket(passport);
    if (!navigator?.clipboard?.writeText) {
      setCopyState("unavailable");
      return;
    }

    try {
      await navigator.clipboard.writeText(packet);
      setCopyState("copied");
    } catch {
      setCopyState("blocked");
    }
  }

  async function copyTrustPath() {
    if (!navigator?.clipboard?.writeText) {
      setTrustCopyState("unavailable");
      return;
    }

    try {
      await navigator.clipboard.writeText(trustPath);
      setTrustCopyState("copied");
    } catch {
      setTrustCopyState("blocked");
    }
  }

  function printPassport() {
    window.print();
  }

  return (
    <section className="passport-page" aria-label="Passport Kairós v1">
      <header className="passport-hero">
        <div className="passport-hero__copy">
          <p className="small-label">Passport Kairós v1</p>
          <h1>Comprobante público de evidencia, listo para auditoría.</h1>
          <p>
            Un paquete compacto que reúne decisión, fecha, ledger, hashes,
            artefactos y límites de uso. Sirve para compartir qué sostiene la
            observación, y qué no debe inferirse.
          </p>
        </div>

        <div className="passport-hero__controls">
          <label>
            <span>Fecha</span>
            <select
              value={selectedDate}
              onChange={(event) => setSelectedDate(event.target.value)}
            >
              {availableDates.map((date) => (
                <option key={date} value={date}>
                  {date}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={copyPassportPacket}>
            {getCopyButtonLabel(copyState)}
          </button>
          <button type="button" onClick={printPassport}>
            Imprimir
          </button>
        </div>
      </header>

      <div className="passport-layout">
        <article className={`passport-card tone-${passport.tone}`}>
          <div className="passport-card__topline">
            <span>Passport ID</span>
            <code>{passport.id}</code>
          </div>

          <div className="passport-card__stamp">
            <DecisionStamp animated={false} scale={0.86} state={passport.stateLabel} />
          </div>

          <dl className="passport-card__facts">
            <PassportFact label="Fecha" value={passport.date} />
            <PassportFact label="AOI" value={passport.aoi} />
            <PassportFact label="Evidencia válida" value={formatPercent(passport.validPercent)} />
            <PassportFact label="API CDSE" value={passport.apiStatus} />
            <PassportFact label="Ledger" value={passport.ledgerStatus} />
            <PassportFact label="Resolución" value={`${passport.resolutionM} m`} />
          </dl>

          <div className="passport-card__hash">
            <span>Huella pública</span>
            <strong>{passport.chainHashShort}</strong>
            <p>{passport.hashMethod}</p>
          </div>
        </article>

        <aside className="passport-control-panel" aria-label="Cobertura documental">
          <div
            className="passport-completeness"
            style={{ "--passport-complete": `${passport.coveragePercent}%` }}
          >
            <span>{passport.coverageAvailable}/{passport.coverageTotal}</span>
            <strong>Cobertura documental</strong>
          </div>

          <div className="passport-control-panel__copy">
            <p className="small-label">Uso responsable</p>
            <h2>Portable, pero no expansivo.</h2>
            <p>{passport.claimLimit}</p>
          </div>

          <div className="passport-actions">
            <button type="button" onClick={() => onNavigate("technical")}>
              Ver evidencia
            </button>
            <button type="button" onClick={() => onNavigate("cases")}>
              Ver acción
            </button>
          </div>

          <TrustVerificationPanel
            copyState={trustCopyState}
            onCopy={copyTrustPath}
            passportId={passport.id}
            trustPath={trustPath}
            verification={trustVerification}
          />
        </aside>
      </div>

      <section className="passport-verifier" aria-label="Verificador visual">
        <div className="passport-verifier__copy">
          <p className="small-label">Checksum visual</p>
          <h2>La lectura humana empieza por la huella.</h2>
          <p>
            Los bloques son fragmentos de la cadena de hashes del ledger público.
            No reemplazan una verificación criptográfica, pero hacen visible si
            el passport corresponde al paquete seleccionado.
          </p>
        </div>
        <div className="passport-hash-grid" aria-label="Fragmentos de hash">
          {passport.hashTiles.map((tile, index) => (
            <span key={`${tile}-${index}`}>{tile}</span>
          ))}
        </div>
      </section>

      <section className="passport-timeline" aria-label="Cadena de auditoría">
        <div className="passport-section-head">
          <p className="small-label">Cadena de auditoría</p>
          <h2>Del JSON crudo al comprobante compartible.</h2>
        </div>
        <ol className="passport-timeline__list">
          {passport.timeline.map((event) => (
            <li className={event.available ? "is-available" : ""} key={event.key}>
              <span>{event.shortLabel}</span>
              <div>
                <strong>{event.label}</strong>
                <p>{event.artifact}</p>
              </div>
              <code>{event.hashShort}</code>
            </li>
          ))}
        </ol>
      </section>

      <section className="passport-scope-grid" aria-label="Alcance del passport">
        <article>
          <span>Permite</span>
          <h3>Compartir confianza de observación</h3>
          <p>
            Fecha, AOI, porcentaje válido, decisión Sentinel-2, artefactos y
            hashes públicos de auditoría.
          </p>
        </article>
        <article>
          <span>No permite</span>
          <h3>No convierte evidencia en autoridad</h3>
          <p>{CLAIM_LIMIT}</p>
        </article>
        <article>
          <span>Siguiente paso</span>
          <h3>{passport.nextActionTitle}</h3>
          <p>{passport.nextAction}</p>
        </article>
      </section>

      <section className="passport-case" aria-label="Caso enlazado">
        <div>
          <p className="small-label">Caso enlazado</p>
          <h2>{passport.caseTitle}</h2>
          <p>{passport.caseSummary}</p>
        </div>
        <ul>
          {passport.caseGaps.map((gap) => (
            <li key={gap}>{gap}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

function PassportFact({ label, value }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value || "pendiente"}</dd>
    </div>
  );
}

function TrustVerificationPanel({ copyState, onCopy, passportId, trustPath, verification }) {
  return (
    <section className="passport-trust" aria-label="Verificación Trust">
      <div className="passport-trust__header">
        <p className="small-label">Verificación Trust</p>
        <span className={`passport-trust__status tone-${getTrustTone(verification.status)}`}>
          {getTrustStatusLabel(verification)}
        </span>
      </div>

      <dl className="passport-trust__facts">
        <div>
          <dt>Passport ID</dt>
          <dd>{passportId}</dd>
        </div>
        <div>
          <dt>Hash</dt>
          <dd>{verification.verificationHash || "pendiente"}</dd>
        </div>
        <div>
          <dt>Validación</dt>
          <dd>{verification.reportStatus}</dd>
        </div>
      </dl>

      <label className="passport-trust__path">
        <span>Ruta pública</span>
        <input readOnly value={trustPath} />
      </label>
      <button className="passport-trust__copy" type="button" onClick={onCopy}>
        {getTrustCopyLabel(copyState)}
      </button>
      <p>{TRUST_LIMIT_COPY}</p>
    </section>
  );
}

function buildPassport({ decisionCases, ledger, ledgerRows, record }) {
  const rows = normalizeLedgerRows(ledgerRows, ledger);
  const decisionRow = pickLedgerRow(rows, "confidence_decision_computed") || ledger || rows[0];
  const caseItem = pickCaseForRecord(decisionCases, record);
  const stateLabel = getStateLabel(record);
  const passportHash =
    decisionRow?.event_hash ||
    decisionRow?.artifact_hash ||
    ledger?.event_hash ||
    `${record?.date || "sin-fecha"}-${record?.aoi || "sin-aoi"}`;
  const id = `KAIROS-P1-${String(record?.date || "0000-00-00").replaceAll("-", "")}-${shortHash(passportHash, 8)}`;
  const chainHash = rows
    .map((row) => row.event_hash || row.artifact_hash || row.hash_short)
    .filter(Boolean)
    .join("");
  const timeline = buildTimeline(rows);
  const coverage = buildCoverage({ caseItem, decisionCases, record, rows });
  const nextAction =
    caseItem?.recommended_workflow ||
    record?.recommended_action_es ||
    "Mantener el passport junto al ledger y revisar una nueva adquisición.";

  return {
    id,
    aoi: record?.aoi || "corridor_wide",
    apiStatus: record?.api_status || "pendiente",
    caseGaps: splitGaps(caseItem?.evidence_gaps),
    caseSummary:
      caseItem?.evidence_summary ||
      "No hay caso territorial enlazado para esta fecha. El passport conserva la evidencia de observación disponible.",
    caseTitle: caseItem?.title || "Sin caso territorial enlazado",
    chainHashShort: shortHash(chainHash || passportHash, 16),
    claimLimit: decisionCases?.claim_firewall || caseItem?.claim_firewall || CLAIM_LIMIT,
    coverageAvailable: coverage.available,
    coveragePercent: coverage.percent,
    coverageTotal: coverage.total,
    date: record?.date || "sin fecha",
    hashMethod: decisionRow?.hash_method || "hash público del ledger",
    hashTiles: buildHashTiles(chainHash || passportHash || id),
    ledgerStatus: ledger?.evidence_status || decisionRow?.status || "sin registro",
    nextAction,
    nextActionTitle: stateLabel === "NO INFERIR" ? "Revisar antes de interpretar" : "Conservar trazabilidad",
    resolutionM: record?.resolution_m || 20,
    stateLabel,
    timeline,
    tone: stateTone(stateLabel),
    validPercent: record?.validPercent,
  };
}

function buildPortablePacket(passport) {
  return [
    `Passport: ${passport.id}`,
    `Fecha: ${passport.date}`,
    `AOI: ${passport.aoi}`,
    `Decisión: ${passport.stateLabel}`,
    `Evidencia válida: ${formatPercent(passport.validPercent)}`,
    `Ledger: ${passport.ledgerStatus}`,
    `Huella pública: ${passport.chainHashShort}`,
    `Límite: ${passport.claimLimit}`,
    `Siguiente paso: ${passport.nextAction}`,
  ].join("\n");
}

function normalizeLedgerRows(ledgerRows, ledger) {
  if (Array.isArray(ledgerRows) && ledgerRows.length) return ledgerRows;
  return ledger ? [ledger] : [];
}

function buildTimeline(rows) {
  return PASSPORT_STAGES.map((stage) => {
    const row = pickLedgerRow(rows, stage.eventType);
    return {
      key: stage.eventType,
      artifact:
        row?.artifact_ref ||
        row?.brief_path ||
        row?.processed_csv_path ||
        row?.raw_json_path ||
        "pendiente en ledger público",
      available: Boolean(row),
      hashShort: row ? shortHash(row.event_hash || row.artifact_hash || row.hash_short, 12) : "pendiente",
      label: row?.event_label || stage.label,
      shortLabel: stage.shortLabel,
    };
  });
}

function buildCoverage({ caseItem, decisionCases, record, rows }) {
  const checks = [
    Boolean(record),
    Boolean(record?.raw_json_path),
    Boolean(record?.brief_path || pickLedgerRow(rows, "brief_generated")),
    Boolean(pickLedgerRow(rows, "confidence_decision_computed")),
    Boolean(pickLedgerRow(rows, "public_export_sanitized")),
    Boolean(rows.some((row) => row.event_hash || row.artifact_hash)),
    Boolean(caseItem),
    Boolean(decisionCases?.claim_firewall || caseItem?.claim_firewall),
  ];
  const available = checks.filter(Boolean).length;
  return {
    available,
    total: checks.length,
    percent: Math.round((available / checks.length) * 100),
  };
}

function pickLedgerRow(rows, eventType) {
  return rows.find((row) => row.event_type === eventType) || null;
}

function pickCaseForRecord(decisionCases, record) {
  const cases = Array.isArray(decisionCases?.cases) ? decisionCases.cases : [];
  if (!cases.length) return null;
  const sameDate = cases.filter((caseItem) => caseItem.date === record?.date);
  const candidates = sameDate.length ? sameDate : cases;
  return [...candidates].sort(compareCases)[0] || null;
}

function compareCases(left, right) {
  const rank = caseRank(left) - caseRank(right);
  if (rank !== 0) return rank;
  return String(left.node_id || "").localeCompare(String(right.node_id || ""));
}

function caseRank(caseItem) {
  const label = String(caseItem?.decision_label || "").toUpperCase();
  if (label === "NO INFERIR") return 0;
  const priority = stripAccents(caseItem?.priority_level || "").toLowerCase();
  if (priority === "alta") return 1;
  if (priority === "media-alta") return 2;
  return 3;
}

function splitGaps(value) {
  if (!value) return ["Sin brechas adicionales registradas para el caso enlazado."];
  return String(value)
    .split("|")
    .map((gap) => gap.trim())
    .filter(Boolean);
}

function buildHashTiles(value) {
  const normalized = String(value || "passport").replace(/[^a-zA-Z0-9]/g, "");
  const seed = (normalized + normalized + normalized).slice(0, 48).padEnd(48, "0");
  return seed.match(/.{1,4}/g) || ["0000"];
}

function getStateLabel(record) {
  const label = String(record?.confidence_label_es || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, " ");
  if (label) return label;
  if (record?.confidence_class === "usable") return "USABLE";
  if (record?.confidence_class === "low_confidence") return "REVISAR";
  return "NO INFERIR";
}

function stateTone(label) {
  if (label === "USABLE") return "usable";
  if (label === "REVISAR") return "review";
  return "stop";
}

function getCopyButtonLabel(state) {
  if (state === "copied") return "Copiado";
  if (state === "blocked") return "Permiso requerido";
  if (state === "unavailable") return "No disponible";
  return "Copiar paquete";
}

function getTrustCopyLabel(state) {
  if (state === "copied") return "Ruta copiada";
  if (state === "blocked") return "Permiso requerido";
  if (state === "unavailable") return "No disponible";
  return "Copiar ruta Trust";
}

function getTrustStatusLabel(verification) {
  if (verification.status === "ready") return "Trust disponible";
  if (verification.status === "missing") return "Trust pendiente";
  if (verification.status === "error") return "Trust no disponible";
  return "Cargando Trust";
}

function getTrustTone(status) {
  if (status === "ready") return "ready";
  if (status === "missing") return "pending";
  if (status === "error") return "error";
  return "loading";
}

function buildTrustPassportPath(passportId) {
  return `/trust/v1/passports/${encodeURIComponent(passportId)}.json`;
}

function shortHash(value, length) {
  const normalized = String(value || "sin-hash").replace(/[^a-zA-Z0-9]/g, "");
  return normalized.slice(0, length) || "sin-hash";
}

function formatPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "pendiente";
  return `${new Intl.NumberFormat("es-PA", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(numeric)}%`;
}

function stripAccents(value) {
  return String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}
