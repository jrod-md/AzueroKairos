# Azuero Kairós - Decision Rules

This document defines how layers combine into actions. The Sentinel-2 confidence engine remains the main decision source. Auxiliary layers may add context, priority, or uncertainty, but they must not create unsupported claims.

## Primary Decision States

### Sentinel-2 `usable`

**Action:** interpret with limits.

Use the observation for cautious exploratory interpretation. Keep scientific limits visible. Do not convert "usable" into a claim about contamination, safe water, pesticides, pathogens, heavy metals, or crisis validation.

Allowed decision language:

- "Usar para interpretación exploratoria con límites explícitos."
- "Evidencia suficiente para lectura cautelosa."

### Sentinel-2 `low_confidence`

**Action:** review / consider field verification.

The observation has some evidence but not enough for a clean interpretation. Review technical context, compare dates, and consider territorial verification.

Allowed decision language:

- "Revisar antes de interpretar."
- "Considerar verificación territorial."

### Sentinel-2 `do_not_infer`

**Action:** do not infer / field verification recommended.

The observation does not have sufficient valid evidence for a responsible inference. Do not use the scene to claim territorial conditions. Recommend waiting for a new acquisition or requesting field verification.

Allowed decision language:

- "No inferir."
- "Verificación territorial recomendada."
- "Esperar nueva adquisición."

## Auxiliary Context Rules

### SAR Context Available

**Rule:** add context only.

Sentinel-1 SAR context may provide physical context, especially under cloud conditions. It never overrides Sentinel-2 confidence and never validates a contamination or water-safety claim.

Allowed effect:

- show a context badge
- show technical SAR metrics
- explain physical context

Forbidden effect:

- changing `do_not_infer` to `usable`
- claiming validated sensor fusion
- claiming contamination detection

### Exposure `data_pending`

**Rule:** evidence gap only.

When exposure is `data_pending`, the system may state that an exposure layer is designed but awaiting official CLMS land-cover pull. It must never produce a risk claim.

Allowed effect:

- show pending status
- note missing land-cover context
- preserve uncertainty

Forbidden effect:

- inventing crop types
- claiming farm boundaries
- identifying producers
- assigning exposure risk

### HydroClimate Antecedent Rain

**Rule:** can raise verification priority, not contamination claim.

Antecedent rainfall can help explain runoff-sensitive context or increase the priority of review when Sentinel-2 confidence is low or `do_not_infer`.

Allowed effect:

- "Lluvia antecedente: revisar contexto territorial."
- increase field verification priority
- explain uncertainty around runoff or sediment context

Forbidden effect:

- claiming contamination
- claiming unsafe water
- declaring crop loss
- overriding Sentinel-2 confidence

### Field Visible Condition

**Rule:** visible condition documentation only.

A field observation can document visible conditions such as turbidity, visible discharge, erosion, sediment, or anomalous color. It cannot validate chemical conditions by itself.

Allowed effect:

- document visible condition
- attach a note, role, date, and coordinates
- recommend review or lab escalation

Forbidden effect:

- confirming pesticides
- confirming pathogens
- confirming heavy metals
- declaring water safe

### Lab Escalation

**Rule:** recommendation only unless external lab results exist.

Kairós may recommend laboratory escalation when satellite confidence is weak, field conditions are visible, or context layers suggest higher review priority. The system must not invent lab outcomes.

Allowed effect:

- "Requiere laboratorio."
- "Escalar a análisis autorizado."
- "No concluir sin laboratorio."

Forbidden effect:

- automatic contamination conclusion
- chemical validation without results
- safe-water declaration

## Decision Combination Examples

### Usable Sentinel-2 + SAR Context

Interpret with limits. Mention SAR only as auxiliary physical context.

### Do Not Infer Sentinel-2 + Antecedent Rain

Do not infer. Raise field verification priority because rainfall may explain runoff-sensitive context.

### Low Confidence Sentinel-2 + Field Visible Condition

Review and document the visible condition. Recommend territorial verification or laboratory escalation if appropriate. Do not claim chemical validation.

### Exposure Pending + Any Sentinel-2 State

Treat exposure as an evidence gap. Do not change the decision state.

## Final Guardrail

If a layer does not change the decision, change the priority, or explain uncertainty, it should not alter the user-facing action.
