# Product Decision Memo

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.

## Decision

Continue AgroShield, but sharpen it into a **Satellite Confidence Semaforo plus exploratory hydro-sedimentary risk screening**. Do not pivot away yet. The technical base is real: CDSE auth works, Statistical API works, EPSG:32617 reprojection works, and MNDWI/NDTI statistics are returned with cache-first reproducibility.

This is not a validated June 2025 crisis detector and not a chemical contamination product.

## 1. What product can we defensibly build?

Build a small decision-support product for B2G/B2B agricultural water-risk screening:

**AgroShield Confidence Brief**: for each catalog-confirmed Sentinel-2 acquisition, show a traffic-light confidence state for an agricultural-riparian AOI around Rio La Villa near Chitre/La Arena. The output is not "water quality"; it is a confidence-screened satellite signal: MNDWI for water/wetness support, NDTI as an exploratory hydro-sedimentary proxy, valid-pixel confidence, cloud/no-data reasons, and a short action note.

Inspiration to borrow, not copy:
- Brazil's MapBiomas-style credibility: long-running, transparent EO products with clear classes and uncertainty.
- Europe's Copernicus early-warning style: confidence, status, and limits before operational action.
- China-scale remote-sensing monitoring style: systematic EO screening for agriculture/water, but adapted to a small Panama node.
- CopernicusLAC winner pattern: local territory, clear user, satellite evidence, and practical risk communication.

## 2. What product should we NOT build?

Do not build a generic dashboard, pretty risk map, or "AI water quality" website. Do not build a map-first product where the science is hidden behind colors. Do not build a crisis detector, chemical contamination detector, irrigation shutdown recommender, or broad "climate resilience platform."

The usual dashboard loses because it looks familiar and unsupported. The winning shape is a narrow, credible workflow: "Can this acquisition support a cautious hydro-sedimentary warning screen, or is the satellite confidence too low?"

## 3. Primary AOI

Use `corridor_wide` as the primary AOI.

Reason: it is the best scientific compromise. The broad AOI has more usable data but likely dilutes the river signal. The river AOI is hydrologically focused but often too sparse or low-confidence. `corridor_wide` captures the agricultural-riparian zone without averaging the whole urban/agricultural box.

Current technical ceiling rows: `corridor_wide` has 4 usable rows across 2 usable dates in the 5-date test.

## 4. Secondary AOI

Use `river` as a secondary/zoom AOI only.

Reason: it is useful for inspection and explanation, but not stable enough as the primary product unit. It should answer: "Does the narrower river strip agree with or challenge the corridor-wide signal?"

## 5. Core Value Proposition

AgroShield turns Copernicus observations into a **trustworthy yes/no/maybe confidence layer** for agricultural water-risk screening in Azuero:

- Is there enough valid satellite data to interpret this date?
- Is the water/wetness signal observable?
- Is there an exploratory red/green or turbidity-like proxy worth comparing against baseline?
- Should the user trust the satellite screen, wait for another acquisition, or seek ground confirmation?

## 6. Demo Story

Start with the problem: agricultural users cannot treat every cloudy or mixed-pixel satellite date as evidence.

Then show the pipeline:
1. Catalog-confirmed Sentinel-2 L2A dates.
2. Three AOI hypotheses: broad, corridor_wide, river.
3. Cache-first CDSE Statistical API outputs.
4. Confidence filtering: invalid, low confidence, usable.
5. A semaforo result with explicit uncertainty.

The honest ending: AgroShield is technically viable, but the scientific claim must remain exploratory until corridor-wide June comparisons are stronger.

## 7. Allowed Claims

- CDSE/Sentinel Hub Statistical API can return Sentinel-2 L2A MNDWI/NDTI statistics for the tested AOIs.
- EPSG:32617 reprojection and cache-first processing make the workflow reproducible.
- `corridor_wide` is the best current primary AOI hypothesis.
- The product can support a Satellite Confidence Semaforo with uncertainty.
- Correct language: "señal satelital exploratoria asociada a riesgo hidro-sedimentario observable."

## 8. Forbidden Claims

- Do not claim June 2025 crisis validation.
- Do not claim chemical contamination, pesticide, atrazine, metals, pathogens, or complete water-quality detection.
- Do not claim irrigation suspension, intake closure, or agricultural operational decision authority.
- Do not claim the AOIs are final or field-validated.
- Do not reuse these spike outputs as official hackathon deliverables.

## 9. Official Hackathon MVP To Win

Regenerate from zero during the official window. The MVP should be narrower and more memorable than a dashboard:

1. A single-node "confidence brief" for Chitre/La Arena, with `corridor_wide` primary and `river` zoom.
2. A reproducible Copernicus pipeline: Catalog API dates, Statistical API stats, cache-first outputs, one optional live refresh.
3. A semaforo that separates data confidence from hydro-sedimentary interpretation.
4. A small comparison table: baseline vs candidate date, MNDWI, NDTI, validPercent, confidence label.
5. A clear user: water-risk analyst, irrigation cooperative, municipal/environmental authority, or agro-export compliance team.
6. A sober UI that makes uncertainty visible, not a generic map dashboard.
7. A final narrative aligned with CopernicusLAC winner patterns: territorial relevance, actionable EO, transparent limits, and local/regional scalability.

## 10. What Should Be Postponed

- Sentinel-1 fusion.
- ERA5, CHIRPS, hydrologic modeling, and rainfall attribution.
- Chemical or microbiological claims.
- Production alerts, Twilio, AWS deployment, Streamlit dashboard, PDF reports.
- Multi-basin expansion.
- Automated agricultural decisions.
- Any polished pitch asset based on this spike.

## Evidence Used

Internal spike evidence:
- `technical_ceiling_summary.csv`: broad 4 usable rows, corridor_wide 4 usable rows, river 2 usable rows.
- `technical_ceiling_report.md`: GO TECHNICAL / ADJUST SCIENTIFIC; June 2025 crisis not validated.
- `go_no_go_decision.md`: CDSE Statistical API OK, CRS/reprojection OK, current scientific signal inconclusive.

External context:
- CopernicusLAC 2025 winner coverage: Comunidades Satelite emphasized territorial/community risk management. Source: https://www.copernicuslac-panama.eu/blog-es/la-experiencia-de-los-ganadores-del-hackathon-copernicuslac-2025-comunidades-satelite-y-su-apuesta-por-fortalecer-la-gestion-del-territorio-en-america-latina/
- CopernicusLAC 2025 conclusion note: the 2025 hackathon had 300+ participants from 30 countries and awarded Comunidades Satelites. Source: https://www.copernicuslac-panama.eu/news/the-2nd-hackathon-of-the-copernicuslac-panama-centre-and-sela-concludes/
- CopernicusLAC 2024 context: winners focused on informal urban growth monitoring, urban wetlands, and deforestation/water/agrochemicals. Source: https://www.copernicuslac-panama.eu/blog-en/a-year-of-growth-and-impact-key-achievements-of-the-copernicuslac-panama-centre-in-2024/
