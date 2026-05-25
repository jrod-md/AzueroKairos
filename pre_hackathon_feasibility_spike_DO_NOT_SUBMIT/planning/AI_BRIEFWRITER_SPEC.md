# AI BriefWriter Spec

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

## Purpose

The AI BriefWriter does not calculate risk. It does not decide confidence state. It does not change thresholds. It only translates structured results into audience-specific language.

If AI is unavailable or blocked by the Claim Firewall, local templates must be used.

## Provider Strategy

Provider-agnostic:
- `none`
- `gemini`
- `openrouter`

Environment variables:
- `LLM_PROVIDER`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `LLM_MODEL`

Suggested models:
- Gemini Flash or Flash-Lite for low-cost short text if available.
- OpenRouter as optional fallback if credit is available.

No key is printed. No key is saved. No key is included in logs.

## Functions To Design During Official Build

Do not implement before the official window.

```python
def build_brief_input(row, audience):
    """Convert one processed observation row into structured JSON."""

def generate_brief_with_llm(input_json):
    """Generate short audience text using configured provider."""

def generate_brief_with_template(input_json):
    """Generate safe local fallback text."""

def run_claim_firewall(text):
    """Return passed/blocked status and safe replacement if needed."""

def return_safe_brief(input_json, audience):
    """Use AI if available, then firewall; otherwise template."""
```

## Input Contract

The model receives only structured JSON:
- date.
- aoi_label.
- confidence_state.
- risk_state.
- validPercent.
- MNDWI summary.
- NDTI summary.
- recommendation_code.
- limitations.

No hidden data. No raw credentials. No free-form scientific speculation.

## Guardrails

- Max output: 80 words for producer, 120 words for technical/institutional.
- Include limitations.
- No chemical claims.
- No mandatory recommendations.
- No crisis validation.
- No real-time claim.
- Pass through Claim Firewall before display.

## Producer Template

Summary sentence:
“Para esta fecha, la evidencia satelital sobre el corredor agrícola se clasifica como {confidence_state}.”

Evidence sentence:
“La lectura usa evidencia Copernicus disponible para MNDWI y NDTI sobre el AOI {aoi_label}, con {validPercent}% de píxeles válidos.”

Confidence sentence:
“{confidence_sentence}”

Recommendation sentence:
“Recomendación: {recommendation}.”

Limitation sentence:
“Esta lectura no detecta químicos ni reemplaza muestreo local; solo resume evidencia Copernicus disponible.”

Complete template:
“Para esta fecha, la evidencia satelital sobre el corredor agrícola se clasifica como {confidence_state}. La lectura usa evidencia Copernicus disponible para MNDWI y NDTI sobre el AOI {aoi_label}, con {validPercent}% de píxeles válidos. {confidence_sentence} Recomendación: {recommendation}. Esta lectura no detecta químicos ni reemplaza muestreo local; solo resume evidencia Copernicus disponible.”

## Technical Operator Template

Summary sentence:
“Observation {date} for {aoi_label} is classified as {confidence_state} with risk state {risk_state}.”

Evidence sentence:
“MNDWI mean={mndwi_mean}, MNDWI stDev={mndwi_stdev}, NDTI mean={ndti_mean}, NDTI stDev={ndti_stdev}, validPercent={validPercent}%.”

Confidence sentence:
“The rule basis is: {explanation_rules}.”

Recommendation sentence:
“Operational note: {recommendation}; review cache/live source mode before interpreting.”

Limitation sentence:
“This is hydro-sedimentary exploratory screening, not chemical detection and not laboratory validation.”

Complete template:
“Observation {date} for {aoi_label} is classified as {confidence_state} with risk state {risk_state}. MNDWI mean={mndwi_mean}, MNDWI stDev={mndwi_stdev}, NDTI mean={ndti_mean}, NDTI stDev={ndti_stdev}, validPercent={validPercent}%. The rule basis is: {explanation_rules}. Operational note: {recommendation}; review cache/live source mode before interpreting. This is hydro-sedimentary exploratory screening, not chemical detection and not laboratory validation.”

## Jury Template

Summary sentence:
“AgroShield separates satellite confidence from risk interpretation for {aoi_label} on {date}.”

Evidence sentence:
“The state is based on Copernicus-derived Sentinel-2 statistics, valid pixels, MNDWI, and NDTI.”

Confidence sentence:
“The system is allowed to say {confidence_state}; if evidence is insufficient, it must say do not infer.”

Recommendation sentence:
“The product recommendation is {recommendation}, framed as decision support.”

Limitation sentence:
“The MVP does not validate a crisis, detect chemicals, or replace field verification.”

Complete template:
“AgroShield separates satellite confidence from risk interpretation for {aoi_label} on {date}. The state is based on Copernicus-derived Sentinel-2 statistics, valid pixels, MNDWI, and NDTI. The system is allowed to say {confidence_state}; if evidence is insufficient, it must say do not infer. The product recommendation is {recommendation}, framed as decision support. The MVP does not validate a crisis, detect chemicals, or replace field verification.”

## Institutional Policy Template

Summary sentence:
“This brief provides a cautious Copernicus-derived screening for {aoi_label} on {date}.”

Evidence sentence:
“The evidence state is {confidence_state}, using validPercent={validPercent}% and exploratory MNDWI/NDTI indicators.”

Confidence sentence:
“The result should be used to prioritize review, not to certify water safety.”

Recommendation sentence:
“Recommended institutional action: {recommendation}, with local verification where relevant.”

Limitation sentence:
“This is not legal, laboratory, or operational closure advice.”

Complete template:
“This brief provides a cautious Copernicus-derived screening for {aoi_label} on {date}. The evidence state is {confidence_state}, using validPercent={validPercent}% and exploratory MNDWI/NDTI indicators. The result should be used to prioritize review, not to certify water safety. Recommended institutional action: {recommendation}, with local verification where relevant. This is not legal, laboratory, or operational closure advice.”

## Recommendation Sentence Mapping

- `DO_NOT_INFER`: “No inferir riesgo para esta fecha; esperar otra adquisición o verificar localmente.”
- `WATCH_NEXT_ACQUISITION`: “Mantener observación y comparar con la próxima adquisición Sentinel-2 útil.”
- `LOCAL_REVIEW_RECOMMENDED`: “Revisar localmente el corredor antes de tomar decisiones sensibles.”
- `NO_ACTION`: “No hay señal suficiente para elevar el estado, mantener monitoreo regular.”
