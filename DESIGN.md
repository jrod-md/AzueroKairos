# Azuero Kairós - DESIGN.md

## Direction

**Design direction:** Atlas de decisión territorial.

Azuero Kairós is not a generic agricultural dashboard. It is a decision system for Azuero that turns Copernicus evidence into a clear operational answer:

- interpret
- review
- do not infer

The product should feel like an editorial atlas, a living technical file, and a premium institutional startup tool. It must be warm, rigorous, and territorial, not decorative.

## Product Posture

Decision first, evidence second.

The first screen must answer whether the observation is usable for a cautious interpretation. Technical data belongs behind the decision or in supporting sections. More data is not better unless it changes a decision, changes a priority, or explains uncertainty.

Azuero Kairós must never look like a data scraper, an agricultural stock template, a generic SaaS dashboard, or a pile of charts searching for a conclusion.

## Audience

Primary users:

- technical reviewers
- institutions
- territorial decision makers
- food security stakeholders
- hackathon judges

Secondary users:

- producers
- territorial technicians
- non-specialist local actors who need a clear next step

The interface must be readable for producers and credible for technical evaluators.

## Visual Character

The UI should feel:

- premium
- institutional
- scientific
- calm
- warm
- Azuero-rooted without folklore
- technical without becoming cryptic
- startup-polished without feeling like a generic SaaS kit

Avoid:

- fake maps
- decorative satellites
- generic green agriculture styling
- overloaded dashboards
- AI slop
- fake real-time indicators
- visual claims stronger than the evidence

## Palette

Use a warm Azuero palette:

- deep institutional blue for structure, titles, and confidence
- cream / sand paper backgrounds
- terracotta for **NO INFERIR** and risk of bad inference
- mineral green for **USABLE**
- amber / ochre for **REVISAR**, context, and caution
- muted river blue / turquoise for hydrological evidence
- stone gray for borders, dividers, and technical surfaces

Rules:

- Terracotta is for insufficient evidence or bad-inference risk.
- Green is only for usable confidence.
- Amber is for review, context, or priority.
- Avoid neon colors.
- Avoid one-note green agriculture visuals.

## Main Screens

### Decision Mode

Purpose: explain the decision in less than 10 seconds.

Show:

- confidence state
- valid evidence percentage
- date
- AOI
- short explanation
- next action
- official-run identity
- minimal context badges only when they explain priority

Do not lead with:

- raw JSON paths
- CSV paths
- MNDWI / NDTI
- sample counts
- SAR metrics
- rainfall matrices
- exposure placeholders

Decision mode is an executive report, not a table.

### Technical Data Mode

Purpose: show evidence and traceability.

Show:

- AOI
- sensor
- resolution
- API status
- ledger status
- validPercent
- sampleCount
- noDataCount
- MNDWI
- NDTI
- raw JSON path
- processed CSV
- brief path
- auxiliary context layers
- scientific limits

Technical mode may be dense, but it must stay ordered and auditable.

### Kairós Watch

Purpose: show subcorridor/date confidence patterns.

Watch is not an alert board. It shows when Copernicus evidence is usable, reviewable, or not inferable across dates and nodes.

Auxiliary layers may appear here only as context:

- SAR physical context
- HydroClimate rainfall context
- Exposure readiness / pending status

They must not override the main Sentinel-2 confidence classification.

## Component Principles

### Decision Card

The main state should dominate:

- **USABLE**
- **REVISAR**
- **NO INFERIR**

The card should be sparse and decisive. It should answer what to do next.

### Context Badges

Context badges are small. They may explain why a technician should review, verify, or wait, but they must not create a new risk class.

Allowed examples:

- "Lluvia antecedente: revisar contexto territorial."
- "SAR context available."
- "Exposure layer pending official land-cover pull."

### Evidence Identity

Evidence identity must remain visible:

- source
- AOI
- date
- sensor
- API status
- ledger status

### Limits Cards

Scientific limits should be calm but visible. They protect the product from overclaiming.

## Language

Use:

- "La observación Sentinel no tiene suficiente evidencia válida para una inferencia responsable."
- "Usar para interpretación exploratoria con límites explícitos."
- "Revisar contexto territorial."
- "Solicitar verificación territorial."
- "Capa auxiliar de contexto."
- "Evidencia pendiente."
- "Cadena auditable de evidencia."

Avoid:

- "detecta contaminación"
- "agua segura"
- "crisis validada"
- "alerta de contaminación"
- "pesticidas detectados"
- "metales pesados detectados"
- "patógenos detectados"
- "IA detectó"
- "confirmado por satélite"
- "sensor fusion validated model"

## Scientific Limits

Azuero Kairós does not detect contamination, water safety, pesticides, pathogens, heavy metals, dissolved chemical conditions, or crisis validation. Chemical or sanitary claims require laboratory analysis or authorized verification.

## Non-Negotiables

- No chemical claims.
- No water-safety claims.
- No fake maps.
- No AI slop.
- No generic SaaS dashboard.
- No data layer without a decision reason.
- Do not let auxiliary context override Sentinel-2 confidence.
- Preserve traceability.
- Preserve uncertainty.
- Make "do not infer" a strength, not a failure.
