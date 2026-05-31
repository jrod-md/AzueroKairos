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
  const [idCopyState, setIdCopyState] = useState("idle");
  const [pathCopyState, setPathCopyState] = useState("idle");
  const [downloadState, setDownloadState] = useState("idle");
  const [trustVerification, setTrustVerification] = useState({
    passport: null,
    reportStatus: "pendiente",
    status: "loading",
    verificationHash: "",
  });
  const passport = useMemo(
    () => buildPassport({ decisionCases, ledger, ledgerRows, record }),
    [decisionCases, ledger, ledgerRows, record],
  );
  const trustPath = useMemo(() => buildTrustPassportPath(passport.id), [passport.id]);
  const trustDetails = useMemo(
    () => buildTrustDetails({ fallbackPassport: passport, trustPassport: trustVerification.passport }),
    [passport, trustVerification.passport],
  );
  const checklist = useMemo(() => buildTrustChecklist(trustDetails), [trustDetails]);

  useEffect(() => {
    let active = true;

    async function loadTrustVerification() {
      setTrustVerification({
        passport: null,
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
          passport: passportPayload,
          reportStatus: reportPayload?.status || "no disponible",
          status: passportResponse.ok ? "ready" : "missing",
          verificationHash: passportPayload?.verification_hash || "",
        });
      } catch {
        if (!active) return;
        setTrustVerification({
          passport: null,
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

  async function copyPassportId() {
    if (!navigator?.clipboard?.writeText) {
      setIdCopyState("unavailable");
      return;
    }

    try {
      await navigator.clipboard.writeText(passport.id);
      setIdCopyState("copied");
    } catch {
      setIdCopyState("blocked");
    }
  }

  async function copyTrustPath() {
    if (!navigator?.clipboard?.writeText) {
      setPathCopyState("unavailable");
      return;
    }

    try {
      await navigator.clipboard.writeText(trustPath);
      setPathCopyState("copied");
    } catch {
      setPathCopyState("blocked");
    }
  }

  function downloadTrustJson() {
    const payload = trustVerification.passport || buildPortableTrustPayload(trustDetails);
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${passport.id}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setDownloadState("downloaded");
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
          <button type="button" onClick={copyPassportId}>
            {getIdCopyLabel(idCopyState)}
          </button>
          <button type="button" onClick={copyTrustPath}>
            {getPathCopyLabel(pathCopyState)}
          </button>
          <button type="button" onClick={downloadTrustJson}>
            {getDownloadLabel(downloadState)}
          </button>
          <button type="button" onClick={printPassport}>
            Imprimir Passport
          </button>
        </div>
      </header>

      <div className="passport-layout">
        <article className={`passport-card tone-${passport.tone}`}>
          <div className="passport-card__topline">
            <span>Passport ID</span>
            <code>{passport.id}</code>
          </div>

          <div className="passport-card__identity">
            <div className="passport-card__stamp">
              <DecisionStamp animated={false} scale={0.86} state={passport.stateLabel} />
            </div>
            <div className="passport-verification-code" aria-label="Código de verificación">
              <span>Código</span>
              <strong>{trustDetails.verificationCode}</strong>
              <p>Verificable en {trustPath}</p>
            </div>
          </div>

          <dl className="passport-card__facts">
            <PassportFact label="Decision ID" value={trustDetails.decisionId} />
            <PassportFact label="Fecha objetivo" value={trustDetails.targetDate} />
            <PassportFact label={trustDetails.scopeLabel} value={trustDetails.scopeValue} />
            <PassportFact label="Confianza" value={trustDetails.confidenceClass} />
            <PassportFact label="Evidencia válida" value={formatPercent(trustDetails.validPercent)} />
            <PassportFact label="API CDSE" value={trustDetails.apiStatus} />
            <PassportFact label="Capa primaria" value={trustDetails.primaryLayer} />
            <PassportFact label="Ledger hash" value={trustDetails.ledgerHash} />
            <PassportFact label="Trust hash" value={trustDetails.verificationHash} />
          </dl>

          <div className="passport-limits-strip">
            <span>Límite de uso</span>
            <p>{trustDetails.claimLimit}</p>
          </div>

          <div className="passport-artifacts" aria-label="Referencias de artefactos">
            <span>Referencias</span>
            <ul>
              {trustDetails.artifactRefs.map((artifact) => (
                <li key={`${artifact.label}-${artifact.path}`}>
                  <strong>{artifact.label}</strong>
                  <code>{artifact.path}</code>
                </li>
              ))}
            </ul>
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
            checklist={checklist}
            copyState={pathCopyState}
            details={trustDetails}
            onCopy={copyTrustPath}
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

function TrustVerificationPanel({ checklist, copyState, details, onCopy, trustPath, verification }) {
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
          <dd>{details.passportId}</dd>
        </div>
        <div>
          <dt>Decision ID</dt>
          <dd>{details.decisionId}</dd>
        </div>
        <div>
          <dt>Trust hash</dt>
          <dd>{details.verificationHash || "pendiente"}</dd>
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
        {getPathCopyLabel(copyState)}
      </button>
      <p>Verificable en {trustPath}</p>

      <ul className="passport-checklist" aria-label="Checklist Trust">
        {checklist.map((item) => (
          <li className={item.ready ? "is-ready" : ""} key={item.label}>
            <span aria-hidden="true">{item.ready ? "✓" : "·"}</span>
            {item.label}
          </li>
        ))}
      </ul>

      <div className="passport-aux-summary">
        <span>Contexto auxiliar</span>
        <p>{details.auxiliarySummary}</p>
      </div>

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

function buildTrustDetails({ fallbackPassport, trustPassport }) {
  const auxiliaryLayers = trustPassport?.auxiliary_layers || {};
  const ledgerRefs = Array.isArray(trustPassport?.ledger_refs)
    ? trustPassport.ledger_refs
    : [];
  const artifactRefs = normalizeArtifactRefs(trustPassport?.artifact_refs);
  const ledgerHash =
    ledgerRefs.find((row) => row.event_type === "confidence_decision_computed")?.hash ||
    ledgerRefs[0]?.hash ||
    fallbackPassport.chainHashShort;
  const verificationHash = trustPassport?.verification_hash || "";
  const scopeValue =
    trustPassport?.node_name ||
    trustPassport?.node_id ||
    trustPassport?.aoi ||
    fallbackPassport.aoi;

  return {
    apiStatus: trustPassport?.api_status || fallbackPassport.apiStatus,
    artifactRefs,
    auxiliaryLayers,
    auxiliarySummary: summarizeAuxiliaryLayers(auxiliaryLayers),
    claimLimit: trustPassport?.claim_limit || fallbackPassport.claimLimit,
    confidenceClass: trustPassport?.confidence_class || fallbackPassport.stateLabel,
    decisionId: trustPassport?.decision_id || "pendiente",
    ledgerHash,
    passportId: trustPassport?.passport_id || fallbackPassport.id,
    primaryLayer: trustPassport?.primary_layer || "Sentinel-2",
    scopeLabel: "AOI / Nodo",
    scopeValue,
    targetDate: trustPassport?.target_date || fallbackPassport.date,
    validPercent: trustPassport?.validPercent ?? fallbackPassport.validPercent,
    verificationCode: shortHash(verificationHash || ledgerHash || fallbackPassport.id, 12).toUpperCase(),
    verificationHash,
  };
}

function buildTrustChecklist(details) {
  return [
    {
      label: "Sentinel-2 decision present",
      ready: details.primaryLayer === "Sentinel-2" && Boolean(details.confidenceClass),
    },
    {
      label: "Ledger linked",
      ready: Boolean(details.ledgerHash && details.ledgerHash !== "pendiente"),
    },
    {
      label: "Trust hash generated",
      ready: Boolean(details.verificationHash),
    },
    {
      label: "Auxiliary context listed",
      ready: details.auxiliarySummary !== "sin contexto auxiliar listado",
    },
    {
      label: "Limits included",
      ready: Boolean(details.claimLimit),
    },
  ];
}

function buildPortableTrustPayload(details) {
  return {
    passport_id: details.passportId,
    decision_id: details.decisionId,
    target_date: details.targetDate,
    scope: details.scopeValue,
    confidence_class: details.confidenceClass,
    validPercent: details.validPercent,
    api_status: details.apiStatus,
    primary_layer: details.primaryLayer,
    ledger_hash: details.ledgerHash,
    verification_hash: details.verificationHash,
    claim_limit: details.claimLimit,
  };
}

function normalizeArtifactRefs(value) {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value)
    .map(([label, path]) => ({
      label,
      path: String(path || "").trim(),
    }))
    .filter((item) => item.path);
}

function summarizeAuxiliaryLayers(layers) {
  const entries = ["sar", "clms", "hydroclimate"]
    .map((key) => {
      const layer = layers?.[key];
      if (!layer) return "";
      const status = layer.status || (layer.available ? "available" : "not listed");
      return `${key.toUpperCase()}: ${status}`;
    })
    .filter(Boolean);
  return entries.join(" · ") || "sin contexto auxiliar listado";
}

function getIdCopyLabel(state) {
  if (state === "copied") return "Copiado";
  if (state === "blocked") return "Permiso requerido";
  if (state === "unavailable") return "No disponible";
  return "Copiar ID";
}

function getPathCopyLabel(state) {
  if (state === "copied") return "Ruta copiada";
  if (state === "blocked") return "Permiso requerido";
  if (state === "unavailable") return "No disponible";
  return "Copiar ruta Trust";
}

function getDownloadLabel(state) {
  if (state === "downloaded") return "JSON descargado";
  return "Descargar JSON";
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
