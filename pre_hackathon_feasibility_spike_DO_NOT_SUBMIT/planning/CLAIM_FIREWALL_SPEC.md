# Claim Firewall Spec

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

## Purpose

The Claim Firewall is a deterministic text validator. It protects the MVP from unsafe claims in AI output, templates, recommendations, labels, and export text.

It must run after any AI BriefWriter output and before display. It should also be used in tests against local template strings.

## Blocked Claim Categories

- chemical detection.
- atrazine detection.
- pesticide detection.
- water safe / safe drinking water.
- real-time operation.
- automatic closure.
- mandatory irrigation suspension.
- validated crisis.
- guaranteed prediction.
- operational system ready.

## Suggested Regex / Patterns

Use case-insensitive matching.

```text
\bdetect(?:amos|ed|a|s|ing)?\s+(?:atrazina|atrazine)\b
\bdetect(?:amos|ed|a|s|ing)?\s+(?:pesticid|pesticide|plaguicida)
\b(?:chemical|quimic|química|químico)\s+(?:detection|detect|contamination|contaminación)
\bagua\s+segura\b
\bwater\s+safe\b
\bcalidad\s+h[ií]drica\s+completa\b
\bcomplete\s+water\s+quality\b
\breal[-\s]?time\b
\btiempo\s+real\b
\bcierre\s+autom[aá]tico\b
\bautomatic\s+closure\b
\bsuspensi[oó]n\s+obligatoria\s+de\s+riego\b
\bvalidated?\s+(?:crisis|event)\b
\bvalidamos\s+la\s+crisis\b
\bpredicci[oó]n\s+garantizada\b
\bguaranteed\s+prediction\b
\bsistema\s+operacional\s+listo\b
\boperational\s+system\s+ready\b
```

## Behavior

1. Receive text and source label.
2. Normalize case and accents if practical.
3. Match against blocked patterns.
4. If no match: return original text with `claim_firewall_status=passed`.
5. If match: return fallback safe text with `claim_firewall_status=blocked_replaced`.
6. Save a local `blocked_claims` log with timestamp, pattern id, source label, and safe replacement. Do not log secrets.

## Safe Replacement

“This output was replaced because it contained an unsupported claim. AgroShield only provides Copernicus-derived satellite confidence and hydro-sedimentary exploratory screening. It does not detect chemicals, validate crises, or replace field/laboratory verification.”

## Blocked Examples

Blocked:
“Detectamos atrazina en el corredor.”

Corrected:
“La evidencia Sentinel-2 muestra una señal satelital exploratoria que puede justificar revisión local; no detecta atrazina ni otros químicos.”

Blocked:
“El agua es segura para riego.”

Corrected:
“La evidencia satelital disponible es usable para screening, pero no certifica seguridad del agua ni reemplaza verificación local.”

Blocked:
“El sistema valida la crisis de junio 2025.”

Corrected:
“El sistema no valida la crisis de junio 2025; solo permite comparar evidencia satelital exploratoria con incertidumbre explícita.”

Blocked:
“Cerrar automáticamente la toma.”

Corrected:
“Revisión local recomendada antes de cualquier decisión operativa.”

## Test Cases Required During Official Build

- Every forbidden phrase above must fail.
- Every allowed phrase must pass.
- AI generated text must be firewalled.
- Local templates must be firewalled.
- Recommendations must be firewalled.
