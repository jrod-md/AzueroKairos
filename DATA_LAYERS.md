# Azuero Kairós - Data Layers

This document defines the allowed purpose of each data layer. A layer is useful only when it changes a decision, changes a priority, or explains uncertainty.

## Kairós Signal

**Source:** Sentinel-2 L2A / Copernicus Data Space Ecosystem Statistical API.

**Current status:** implemented.

**Supports:**

- primary confidence classification
- usable / low_confidence / do_not_infer states
- decision brief generation
- valid evidence percentage
- cautious hydro-sedimentary interpretation with limits

**Does not support:**

- contamination detection
- water safety
- pesticide claims
- pathogen claims
- heavy metal claims
- validated crisis claims

**Allowed UI language:**

- "Evidencia suficiente para interpretación exploratoria con límites."
- "La observación no tiene suficiente evidencia válida."
- "No inferir."
- "Esperar nueva adquisición o solicitar verificación territorial."

**Forbidden claims:**

- "Detecta contaminación."
- "El agua es segura."
- "Pesticidas detectados."
- "Crisis confirmada por satélite."

## Kairós Watch

**Source:** Kairós Signal node-level exports over subcorridors and dates.

**Current status:** implemented.

**Supports:**

- comparison by node and date
- regional confidence matrix
- identifying where confidence drops
- prioritizing review across time

**Does not support:**

- real-time alerts
- contamination maps
- farm-level conclusions
- automatic field dispatch

**Allowed UI language:**

- "Subcorredores por fecha."
- "Matriz de confianza."
- "Cada celda resume si la observación puede interpretarse, revisarse o no inferirse."

**Forbidden claims:**

- "Mapa de contaminación."
- "Alertas de agua insegura."
- "Riesgo confirmado por zona."

## Kairós Field

**Source:** human verification workflow, visible conditions, notes, roles, coordinates when implemented.

**Current status:** partial.

**Supports:**

- territorial verification requests
- documenting visible field conditions
- prioritizing human review when satellite confidence is low
- recommending possible laboratory escalation

**Does not support:**

- chemical validation
- pesticide confirmation
- pathogen confirmation
- safe-water declarations
- automatic lab conclusions

**Allowed UI language:**

- "Verificación territorial recomendada."
- "Condición visible registrada."
- "Requiere laboratorio."
- "Nota de campo."

**Forbidden claims:**

- "Campo confirmó contaminación química."
- "Visible condition proves pesticide presence."
- "Water is safe."

## Kairós Ledger

**Source:** evidence ledger exports, processed CSV paths, raw JSON paths, brief paths, run metadata.

**Current status:** implemented.

**Supports:**

- traceability
- auditability
- reproducibility
- official-run evidence chain

**Does not support:**

- scientific interpretation by itself
- contamination claims
- confidence overrides
- hidden corrections to weak evidence

**Allowed UI language:**

- "Cadena auditable de evidencia."
- "Official API OK."
- "Raw JSON path."
- "Processed CSV."

**Forbidden claims:**

- "Ledger validates contamination."
- "Ledger proves water safety."
- "Traceability replaces scientific limits."

## Kairós SAR Context

**Source:** Sentinel-1 GRD / Copernicus Data Space Ecosystem Statistical API, if available.

**Current status:** partial.

**Supports:**

- auxiliary physical context
- continuity under cloud conditions
- VV / VH / VV-VH context when observations exist
- explaining why optical evidence may need support

**Does not support:**

- contamination detection
- chemical validation
- water safety
- replacing Sentinel-2 confidence
- validated operational sensor fusion

**Allowed UI language:**

- "SAR context available."
- "Capa auxiliar Sentinel-1."
- "Contexto físico/SAR."
- "No reemplaza la confianza Sentinel-2."

**Forbidden claims:**

- "SAR detects contamination."
- "SAR validates water safety."
- "Sensor fusion confirms risk."
- "SAR overrides no inferir."

## Kairós HydroClimate

**Source:** CHIRPS daily rainfall via ClimateSERV; future optional ERA5-Land context.

**Current status:** partial.

**Supports:**

- antecedent rainfall context
- review priority when satellite evidence is low
- explaining possible runoff or sediment movement context
- field verification prioritization

**Does not support:**

- contamination detection
- crop loss detection
- water safety
- regulatory rainfall thresholds
- automatic risk claims

**Allowed UI language:**

- "Contexto de lluvia antecedente."
- "Revisar contexto territorial."
- "La lluvia antecedente puede elevar prioridad de verificación."
- "MVP contextual thresholds, not regulatory thresholds."

**Forbidden claims:**

- "Rainfall confirms contamination."
- "Rainfall proves unsafe water."
- "Flood/runoff risk confirmed."
- "Crop loss detected."

## Kairós Exposure

**Source:** pending Copernicus Land Monitoring Service land-cover/agricultural exposure layer.

**Current status:** pending.

**Supports:**

- future approximate land-cover composition around nodes
- exposure context once official CLMS data is pulled
- explaining evidence gaps while the layer is pending
- future prioritization only after official land-cover composition exists

**Does not support:**

- invented crop types
- exact farm boundaries
- private producer identification
- contamination claims
- water safety
- chemical exposure claims

**Allowed UI language:**

- "Exposure layer pending official CLMS pull."
- "Approximate land-cover context, when available."
- "Evidence gap."
- "No exposure values inferred."

**Forbidden claims:**

- "Farm boundary identified."
- "Producer identified."
- "Crop type confirmed."
- "Agricultural exposure proves contamination."
- "Exposure risk confirmed."
