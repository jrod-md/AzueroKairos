import React from "react";
import { STATES, THRESHOLDS, findContrast, formatDate, formatPercent } from "../lib/data.js";
import { Section, StateTag, ThresholdBar } from "../components/ui.jsx";

const CYCLE = [
  ["Observa", "Registra escenas Sentinel-2 oficiales del corredor piloto vía Copernicus CDSE."],
  ["Calibra", "Mide qué fracción de la escena es evidencia válida antes de interpretar."],
  ["Decide", "Convierte esa fracción en USABLE, REVISAR o NO INFERIR con una regla fija."],
  ["Contextualiza", "Suma radar, lluvia y cobertura del suelo sin tocar la clasificación."],
  ["Prioriza", "Ordena qué caso revisar primero según la brecha de evidencia."],
  ["Verifica", "Prepara la visita de campo y separa laboratorio y autoridad competente."],
  ["Emite", "Empaqueta decisión, hashes y límites en un Passport portable."],
  ["Audita", "Conserva la cadena de eventos desde la observación hasta la exportación."],
];

const AUDIENCES = [
  {
    profile: "Gobierno",
    output: "Prioridad de verificación y estado de inferencia por nodo.",
    next: "Asignar revisión territorial donde la evidencia es más débil.",
    never: "No ordena cierre, sanción ni acto de autoridad.",
  },
  {
    profile: "Cooperativa",
    output: "Mensaje de cautela para técnicos y miembros.",
    next: "Comunicar límites y esperar evidencia usable cuando haga falta.",
    never: "No confirma verdad de campo ni reemplaza revisión local.",
  },
  {
    profile: "Crédito y seguro",
    output: "Preevaluación de si la evidencia alcanza para revisión.",
    next: "Enviar a revisión documental o pedir evidencia adicional.",
    never: "Nunca decide un pago ni una cobertura.",
  },
  {
    profile: "Laboratorio y autoridad",
    output: "Ruta de escalamiento con evidencia trazable.",
    next: "Solicitar muestra, visita o acto formal por el canal competente.",
    never: "No produce resultado de laboratorio ni decisión institucional.",
  },
];

const LIMITS = [
  "No detecta plaguicidas, patógenos, metales ni sustancias disueltas.",
  "No certifica agua potable ni agua segura.",
  "No reemplaza laboratorio, verificación de campo ni autoridad competente.",
  "Los umbrales de 10% y 30% son reglas del MVP, no un estándar ambiental validado.",
  "Los datos son una exportación estática del piloto, no un monitoreo en vivo.",
];

export default function Acerca({ data }) {
  const contrast = findContrast(data.observations);
  const blocked = data.observations.filter((row) => row.confidence_class === "do_not_infer").length;
  const counts = data.trustIndex?.counts ?? {};

  return (
    <div className="page page--acerca">
      <header className="about">
        <div className="about__copy">
          <h1>Una API que responde no es una escena que se pueda leer.</h1>
          <p>
            Azuero Kairós evalúa si una observación satelital del río La Villa tiene suficiente
            evidencia válida para sostener una lectura cautelosa. Cuando no la tiene, lo dice y
            recomienda esperar.
          </p>
        </div>
        <figure className="about__figure">
          <img src="/img/aerial-view.png" alt="" loading="lazy" />
          <figcaption>Imagen ilustrativa. No es una escena satelital ni un mapa.</figcaption>
        </figure>
      </header>

      <Section id="regla" number="01" title="La regla" note="Una sola medida decide: el porcentaje de píxeles válidos de Sentinel-2.">
        <div className="rule">
          {[STATES.do_not_infer, STATES.low_confidence, STATES.usable].map((state) => (
            <div className="rule__band" key={state.id}>
              <StateTag confidenceClass={state.id} />
              <p className="rule__range">{state.rule}</p>
              <p className="muted">{state.reason}</p>
            </div>
          ))}
        </div>
        {contrast ? (
          <div className="contrast">
            {[contrast.weak, contrast.strong].map((row) => (
              <div className="contrast__row" key={row.date}>
                <span className="mono">{formatDate(row.date, { year: true })}</span>
                <ThresholdBar value={row.validPercent} confidenceClass={row.confidence_class} />
                <span className="mono contrast__pct">{formatPercent(row.validPercent)}</span>
                <StateTag confidenceClass={row.confidence_class} />
              </div>
            ))}
            <p className="muted">
              Marcas en {THRESHOLDS.review}% y {THRESHOLDS.usable}%. La diferencia es de cobertura
              de observación; no mide calidad del agua ni resultados en el territorio.
            </p>
          </div>
        ) : null}
      </Section>

      <Section id="ciclo" number="02" title="El ciclo" note="De la observación a la auditoría, en ocho pasos.">
        <ol className="cycle">
          {CYCLE.map(([label, text], index) => (
            <li key={label}>
              <span className="cycle__n mono">{String(index + 1).padStart(2, "0")}</span>
              <span className="cycle__label">{label}</span>
              <span className="cycle__text">{text}</span>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="piloto" number="03" title="El piloto en cifras" note="Conteos de los archivos públicos de esta demostración.">
        <dl className="tally">
          <div>
            <dt>Observaciones oficiales</dt>
            <dd className="mono">{data.observations.length}</dd>
          </div>
          <div>
            <dt>Con API OK y bloqueadas</dt>
            <dd className="mono">{blocked}</dd>
          </div>
          <div>
            <dt>Observaciones nodo y fecha</dt>
            <dd className="mono">{data.watch.length}</dd>
          </div>
          <div>
            <dt>Casos curados</dt>
            <dd className="mono">{data.cases.length}</dd>
          </div>
          <div>
            <dt>Eventos de ledger</dt>
            <dd className="mono">{data.ledger.length}</dd>
          </div>
          <div>
            <dt>Passports publicados</dt>
            <dd className="mono">{counts.trust_passports ?? "sin dato"}</dd>
          </div>
        </dl>
      </Section>

      <Section id="usos" number="04" title="Quién lo usa y qué no decide" note="Cuatro lecturas del mismo paquete de evidencia. No son roles ni productos separados.">
        <div className="table-wrap">
          <table className="audiences">
            <thead>
              <tr>
                <th scope="col">Perfil</th>
                <th scope="col">Qué obtiene</th>
                <th scope="col">Siguiente paso</th>
                <th scope="col">Lo que Kairós no decide</th>
              </tr>
            </thead>
            <tbody>
              {AUDIENCES.map((row) => (
                <tr key={row.profile}>
                  <th scope="row">{row.profile}</th>
                  <td>{row.output}</td>
                  <td>{row.next}</td>
                  <td>{row.never}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="limites" number="05" title="Límites" note="Lo que esta interfaz no afirma, dicho una vez.">
        <ul className="ticks ticks--wide">
          {LIMITS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Section>
    </div>
  );
}
