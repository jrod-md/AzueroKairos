# Jury QA Advanced

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

## ¿Detectan atrazina?

No. AgroShield does not detect atrazine, pesticides, chemicals, pathogens, metals, or complete water quality. It uses Copernicus-derived MNDWI/NDTI statistics for satellite confidence and exploratory hydro-sedimentary screening.

## ¿Por qué no usar sensores de campo?

Field sensors and laboratory sampling are still necessary. AgroShield is the screening layer before or between field checks: it helps decide when satellite evidence is usable and when local verification is recommended.

## ¿Por qué Sentinel-2 si hay nubes?

Because Sentinel-2 gives open, repeatable optical observations with useful bands for water/wetness and red/green sediment proxies. When clouds dominate, AgroShield says low confidence or do not infer.

## ¿Qué pasa si validPercent es bajo?

If validPercent < 10%, risk state becomes do not infer. If 10-30%, the result is low confidence. The UI must show that limitation clearly.

## ¿Por qué corridor_wide y no solo el río?

The river-only AOI is hydrologically focused but can be too sparse and sensitive to mixed pixels. `corridor_wide` captures the agricultural-riparian corridor with enough pixels to support a more stable confidence screen.

## ¿No están diluyendo la señal?

That is exactly why broad AOI is not the primary product. Broad is useful as a technical ceiling; `corridor_wide` is the primary scientific compromise; river is secondary zoom.

## ¿Por qué NDTI?

NDTI is a simple exploratory red/green proxy for visible hydro-sedimentary signal. It is not chemistry and not a complete turbidity validation.

## ¿Qué validaron realmente?

We validated technical viability: authentication, Catalog API, Statistical API, reprojection, MNDWI/NDTI statistics, cache-first operation, and confidence labeling.

## ¿Qué no validaron?

We did not validate the June 2025 crisis, chemical contamination, operational agricultural decisions, or field/lab truth.

## ¿Qué hace la IA?

AI translates structured evidence into audience-specific language. It does not calculate risk, choose states, or change thresholds.

## ¿Puede la IA inventar recomendaciones?

It should not. The AI receives structured JSON and the Claim Firewall blocks unsafe claims. If AI fails, local templates are used.

## ¿Es esto seguridad alimentaria o agua potable?

Food security decision support for agricultural risk screening. It is not drinking-water certification.

## ¿Cómo escala a ALC?

By replicating the configured Confidence Brief node: AOI, catalog dates, indices, confidence rules, limitations, and local verification loop.

## ¿Qué parte fue hecha durante hackathon?

The official repo, code, UI, official cached outputs, and final documentation must be created during the competition. Pre-hackathon material is planning and feasibility only.

## ¿Qué pasa si CDSE rate-limits?

The demo uses cache. Live refresh is optional and limited to one safe request. If rate-limited, the app does not hammer the API.

## ¿Qué entrega si live refresh falla?

The cached Copernicus-derived demo still works: confidence state, risk screen, explanation, and brief.

## ¿Cómo evitan falsos positivos?

Confidence gates, do-not-infer states, claim firewall, and explicit field verification recommendations.

## ¿Qué diferencia tienen frente a dashboards?

Others show maps; AgroShield shows whether the satellite evidence is trustworthy enough to support an agricultural decision.

## ¿Cómo sabrán si se equivocaron?

Prediction Ledger and controlled community verification can track later observations and field feedback. The MVP itself remains exploratory.

## ¿Por qué no es overengineering?

Core phases are small: evidence table, confidence state, risk screen, explanation, brief. AI and roadmap features are optional and fallback-safe.
