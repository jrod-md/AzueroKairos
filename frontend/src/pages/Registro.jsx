import React, { useEffect, useMemo, useState } from "react";
import {
  NODES,
  accent,
  fetchJson,
  formatDate,
  formatPercent,
  ledgerForDate,
  statusLabel,
} from "../lib/data.js";
import {
  ASSISTANT_LENSES,
  assistantStatusLabel,
  buildDeterministicBrief,
  buildEvidencePacket,
  requestEvidenceBrief,
} from "../lib/assistant.js";
import { Fact, Section, Stamp, StateTag } from "../components/ui.jsx";

const CHECK_LABELS = {
  official_observations: "Existen las cinco observaciones oficiales",
  contrast_dates: "Existen las fechas de contraste (10 y 30 de junio)",
  evidence_uplift: "El contraste de cobertura se puede calcular",
  kairos_watch_rows: "La matriz tiene 15 observaciones de nodo y fecha",
  sar_context_rows: "El contexto de radar tiene las filas esperadas",
  clms_node_coverage: "CLMS cubre los tres nodos",
  hydroclimate_rows: "El contexto de lluvia tiene las filas esperadas",
  ledger_hashes: "Los eventos del ledger tienen hashes distintos",
  trust_passport_hashes: "Cada Passport tiene hash de verificación",
  public_safety_scan: "Sin secretos, tokens ni rutas locales en lo publicado",
  mojibake_scan: "Sin texto corrupto en los artefactos",
  positive_claim_scan: "Sin afirmaciones prohibidas en la capa Trust",
};

const AUX_LAYERS = [
  ["sar", "Radar Sentinel-1"],
  ["clms", "Cobertura del suelo CLMS"],
  ["hydroclimate", "Lluvia antecedente"],
];

function decisionPath(date, caseItem) {
  if (caseItem) {
    return `/trust/v1/decisions/decision-case-${caseItem.node_id.replaceAll("_", "-")}-${date}.json`;
  }
  return `/trust/v1/decisions/decision-official-corridor-wide-${date}.json`;
}

export default function Registro({ data, date, record, scopeCase, setScope }) {
  const scopes = data.cases.filter((item) => item.date === date);
  const ledgerRows = useMemo(() => ledgerForDate(data.ledger, date), [data.ledger, date]);
  const [showAll, setShowAll] = useState(false);
  const allRows = useMemo(
    () => [...data.ledger].sort((a, b) => Number(a.event_index) - Number(b.event_index)),
    [data.ledger],
  );

  return (
    <div className="page page--registro">
      <header className="page__head">
        <h1>Registro verificable</h1>
        <p>
          El comprobante, la cadena de eventos y el resumen del paquete para el{" "}
          {formatDate(date, { year: true })}. Verifica la trazabilidad del paquete, no el territorio.
        </p>
      </header>

      <div className="chips" role="group" aria-label="Alcance del registro">
        <button
          className={`chip${!scopeCase ? " is-active" : ""}`}
          type="button"
          aria-pressed={!scopeCase}
          onClick={() => setScope(null)}
        >
          Corredor completo
        </button>
        {scopes.map((item) => (
          <button
            className={`chip${scopeCase?.case_id === item.case_id ? " is-active" : ""}`}
            key={item.case_id}
            type="button"
            aria-pressed={scopeCase?.case_id === item.case_id}
            onClick={() => setScope(item.case_id)}
          >
            {NODES[item.node_id]?.name ?? item.node_display_name}
          </button>
        ))}
      </div>

      <Passport
        caseItem={scopeCase}
        date={date}
        key={`${date}-${scopeCase?.case_id ?? "corridor"}`}
        ledgerRows={ledgerRows}
        record={record}
      />

      <Section
        id="ledger"
        number="02"
        title="Cadena de eventos"
        note="Seis eventos por observación oficial. Las horas ordenan eventos generados por el exportador; no son capturas independientes de cada operación."
      >
        <LedgerTable rows={showAll ? allRows : ledgerRows} showDate={showAll} />
        <button className="link" type="button" onClick={() => setShowAll((value) => !value)}>
          {showAll ? `Ver solo el ${formatDate(date)}` : `Ver los ${data.ledger.length} eventos del piloto`}
        </button>
      </Section>

      <Section
        id="resumen"
        number="03"
        title="Resumen del paquete"
        note="El asistente ordena evidencia ya auditada. No crea observaciones ni cambia la clasificación."
      >
        <Assistant data={data} date={date} ledgerRows={ledgerRows} record={record} />
      </Section>

      <Section
        id="validacion"
        number="04"
        title="Validación de la exportación"
        note="Comprobaciones automáticas sobre los archivos públicos. No es una certificación de producción."
      >
        <Validation report={data.validation} index={data.trustIndex} />
      </Section>
    </div>
  );
}

function Passport({ caseItem, date, ledgerRows, record }) {
  const [trust, setTrust] = useState({ status: "loading", decision: null, passport: null });
  const [copied, setCopied] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      const decision = await fetchJson(decisionPath(date, caseItem));
      const passport = decision?.passport_id
        ? await fetchJson(`/trust/v1/passports/${encodeURIComponent(decision.passport_id)}.json`)
        : null;
      if (!active) return;
      setTrust({ status: passport ? "ready" : "missing", decision, passport });
    })();
    return () => {
      active = false;
    };
  }, [caseItem, date]);

  const passport = trust.passport;
  const confidenceClass =
    passport?.confidence_class ?? caseItem?.primary_confidence_class ?? record.confidence_class;
  const validPercent = passport?.validPercent ?? caseItem?.primary_validPercent ?? record.validPercent;
  const scopeName = caseItem
    ? NODES[caseItem.node_id]?.name ?? caseItem.node_display_name
    : "Corredor completo";
  const passportPath = passport ? `/trust/v1/passports/${passport.passport_id}.json` : "";
  const hash = String(passport?.verification_hash ?? "").replace(/^sha256:/, "");
  const ledgerRefs = Array.isArray(passport?.ledger_refs) ? passport.ledger_refs : [];
  const eventLabels = Object.fromEntries(ledgerRows.map((row) => [row.event_type, row.event_label]));
  const artifacts = Object.entries(passport?.artifact_refs ?? {}).filter(([, path]) =>
    /^\/(data|trust)\//.test(String(path)),
  );

  async function copy(kind, text) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
    } catch {
      setCopied(`${kind}-error`);
    }
  }

  function download() {
    const blob = new Blob([JSON.stringify(passport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${passport.passport_id}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  if (trust.status === "loading") {
    return <div className="passport passport--loading" aria-busy="true" />;
  }

  if (!passport) {
    return (
      <div className="empty">
        <h2>No hay Passport publicado para este alcance.</h2>
        <p>
          La capa Trust no contiene un comprobante para {scopeName} el {formatDate(date)}. La
          decisión sigue disponible en Observación.
        </p>
      </div>
    );
  }

  return (
    <article className="passport" aria-label={`Passport ${passport.passport_id}`}>
      <header className="passport__head">
        <div>
          <p className="eyebrow">Passport Kairós v1</p>
          <h2 className="mono passport__id">{passport.passport_id}</h2>
          <p className="passport__scope">
            {scopeName} <span aria-hidden="true">/</span> {formatDate(passport.target_date, { year: true })}
          </p>
        </div>
        <Stamp confidenceClass={confidenceClass} size="md" />
      </header>

      <dl className="facts facts--grid">
        <Fact label="Cobertura válida" mono>
          {formatPercent(validPercent)}
        </Fact>
        <Fact label="Capa que decide">{passport.primary_layer}</Fact>
        <Fact label="API CDSE" mono>
          {passport.api_status}
        </Fact>
        <Fact label="Decisión" mono>
          {passport.decision_id}
        </Fact>
      </dl>

      <div className="passport__cols">
        <div>
          <h3>Contexto auxiliar listado</h3>
          <ul className="plain">
            {AUX_LAYERS.map(([key, label]) => {
              const layer = passport.auxiliary_layers?.[key];
              return (
                <li key={key}>
                  <span>{label}</span>
                  <span className="muted">{layer ? statusLabel(layer.status) : "No listado"}</span>
                </li>
              );
            })}
          </ul>
        </div>
        <div>
          <h3>Eventos enlazados</h3>
          {ledgerRefs.length ? (
            <ul className="plain">
              {ledgerRefs.map((ref) => (
                <li key={ref.hash}>
                  <span>{eventLabels[ref.event_type] ?? statusLabel(ref.event_type)}</span>
                  <span className="mono muted">#{ref.hash_short}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">Este comprobante no enlaza eventos individuales.</p>
          )}
        </div>
      </div>

      <div className="passport__hash">
        <div>
          <h3>Hash de verificación (SHA-256)</h3>
          <p className="mono passport__hashtext">{hash || "pendiente"}</p>
        </div>
        <HashStrip hash={hash} />
      </div>

      {artifacts.length ? (
        <ul className="artifacts" aria-label="Artefactos públicos">
          {artifacts.map(([label, path]) => (
            <li key={label}>
              <a className="mono" href={path} target="_blank" rel="noreferrer">
                {path}
              </a>
            </li>
          ))}
        </ul>
      ) : null}

      <p className="passport__limit">{accent(passport.claim_limit)}</p>

      <footer className="passport__actions">
        <button className="btn btn--primary" type="button" onClick={download}>
          Descargar JSON
        </button>
        <button className="btn" type="button" onClick={() => copy("id", passport.passport_id)}>
          {copied === "id" ? "ID copiado" : "Copiar ID"}
        </button>
        <button className="btn" type="button" onClick={() => copy("path", passportPath)}>
          {copied === "path" ? "Ruta copiada" : "Copiar ruta Trust"}
        </button>
        <button className="btn" type="button" onClick={() => window.print()}>
          Imprimir
        </button>
        {copied.endsWith("-error") ? (
          <span className="muted" role="status">
            El navegador bloqueó el portapapeles.
          </span>
        ) : null}
      </footer>
    </article>
  );
}

// A visual fingerprint: one bar per hex digit of the verification hash.
function HashStrip({ hash }) {
  if (!hash) return null;
  return (
    <span className="hashstrip" aria-hidden="true">
      {hash.split("").map((char, index) => (
        <i key={index} style={{ height: `${20 + (parseInt(char, 16) || 0) * 5}%` }} />
      ))}
    </span>
  );
}

function LedgerTable({ rows, showDate }) {
  if (!rows.length) return <p className="muted">No hay eventos de ledger para esta fecha.</p>;
  return (
    <div className="table-wrap">
      <table className="ledger">
        <thead>
          <tr>
            <th scope="col">N.º</th>
            {showDate ? <th scope="col">Fecha</th> : null}
            <th scope="col">Evento</th>
            <th scope="col">Artefacto</th>
            <th scope="col">Estado</th>
            <th scope="col">Hash</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.event_hash ?? row.event_index}>
              <td className="mono">{String(row.event_index).padStart(2, "0")}</td>
              {showDate ? (
                <td className="mono">
                  <StateTag confidenceClass={row.confidence_class} /> {formatDate(row.date)}
                </td>
              ) : null}
              <td>
                {row.event_label}
                <span className="ledger__type mono">{row.event_type}</span>
              </td>
              <td className="mono">
                {/^\/(data|trust)\//.test(String(row.artifact_ref)) ? row.artifact_ref : "metadata pública"}
              </td>
              <td>{statusLabel(row.status)}</td>
              <td className="mono">#{row.hash_short}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Assistant({ data, date, ledgerRows, record }) {
  const [lens, setLens] = useState("brief");
  const [state, setState] = useState({ brief: null, mode: "fallback", reason: "", status: "idle" });
  const packet = useMemo(
    () => buildEvidencePacket({ data, ledgerRows, lens, record }),
    [data, ledgerRows, lens, record],
  );
  const deterministic = useMemo(() => buildDeterministicBrief(packet), [packet]);
  const brief = state.brief ?? deterministic;

  useEffect(() => {
    setState({ brief: null, mode: "fallback", reason: "", status: "idle" });
  }, [date, lens]);

  async function prepare() {
    setState({ brief: null, mode: "fallback", reason: "", status: "loading" });
    const result = await requestEvidenceBrief(packet);
    if (result.mode === "ai" && result.brief) {
      setState({ brief: result.brief, mode: "ai", reason: "", status: "ready" });
      return;
    }
    setState({ brief: null, mode: "fallback", reason: result.reason || "fallback", status: "ready" });
  }

  return (
    <div className="brief">
      <div className="brief__bar">
        <div className="chips" role="group" aria-label="Formato del resumen">
          {ASSISTANT_LENSES.map((item) => (
            <button
              className={`chip${lens === item.id ? " is-active" : ""}`}
              key={item.id}
              type="button"
              aria-pressed={lens === item.id}
              onClick={() => setLens(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <span className="brief__status mono" role="status">
          {assistantStatusLabel(state)}
        </span>
        <button className="btn" type="button" onClick={prepare} disabled={state.status === "loading"}>
          {state.status === "loading" ? "Preparando" : "Pedir redacción asistida"}
        </button>
      </div>

      <p className="brief__summary">{accent(brief.decision_summary)}</p>
      <div className="next next--wide">
        <span className="next__k">Acción</span>
        <p>{accent(brief.recommended_action)}</p>
      </div>

      <div className="brief__cols">
        <BriefList title="Evidencia usada" items={brief.evidence_used} />
        <BriefList title="Brechas" items={brief.evidence_gaps} />
        <BriefList title="Límites" items={brief.limits} />
        <BriefList title="Artefactos" items={brief.artifact_refs} mono />
      </div>
    </div>
  );
}

function BriefList({ title, items, mono = false }) {
  return (
    <div>
      <h3>{title}</h3>
      <ul className={`ticks${mono ? " mono" : ""}`}>
        {items.map((item) => (
          <li key={item}>{mono ? item : accent(item)}</li>
        ))}
      </ul>
    </div>
  );
}

function Validation({ report, index }) {
  if (!report) return <p className="muted">El reporte de validación no está disponible.</p>;
  const checks = Array.isArray(report.checks) ? report.checks : [];
  const counts = index?.counts ?? report.summary?.counts ?? {};

  return (
    <div className="validation">
      <dl className="facts facts--grid">
        <Fact label="Comprobaciones aprobadas" mono>
          {report.summary?.passed ?? 0} de {report.summary?.total_checks ?? checks.length}
        </Fact>
        <Fact label="Generado" mono>
          {formatDate(report.generated_at_utc, { year: true })}
        </Fact>
        <Fact label="Passports publicados" mono>
          {counts.trust_passports ?? "sin dato"}
        </Fact>
        <Fact label="Eventos de ledger" mono>
          {counts.trust_ledger_events ?? counts.evidence_ledger_events ?? "sin dato"}
        </Fact>
      </dl>
      <details className="validation__details">
        <summary>Ver las {checks.length} comprobaciones</summary>
        <ul className="plain">
          {checks.map((check) => (
            <li key={check.id}>
              <span>{CHECK_LABELS[check.id] ?? check.label}</span>
              <span className={check.status === "pass" ? "ok" : "warn"}>{statusLabel(check.status)}</span>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
