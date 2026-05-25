# Go/No-Go Decision for AgroShield Spike

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.

## 1. Executive decision: GO, ADJUST AOI, or PIVOT.

GO TECHNICAL, ADJUST SCIENTIFIC

## 2. Evidence summary.

Summarized rows: 55. Broad AOI rows: 17. Corridor-wide rows: 10. River corridor AOI rows: 28. Usable broad dates: 4. Usable corridor-wide dates: 2. Usable river dates: 2.

## 3. CDSE authentication result.

Auth: OK based on current spike status.

## 4. AOI validity.

Broad AOI returns data but likely dilutes river signal with urban/agricultural pixels. River corridor AOI is hydrologically targeted but can be too sparse. Corridor-wide is the intermediate technical-ceiling AOI and remains approximate.

## 5. Sentinel-2 data availability.

CDSE Statistical API: OK. Catalog-confirmed date discovery must drive the next comparison rather than arbitrary windows.

## 6. MNDWI interpretability.

MNDWI statistics are returned. Interpretation should be limited to observable water/wetness support and filtered by validPercent.

## 7. NDTI/Red-Green interpretability.

NDTI statistics are returned. Current scientific signal is inconclusive; no crisis validation is claimed.

## 8. Main technical risk.

The broad AOI may dilute signal, the river-only AOI may be too sparse, and corridor_wide must be tested in small cached batches. Cloud/SCL filtering may leave too few valid pixels on some dates.

## 9. Recommended next action.

Use Catalog API dates, cache-first Statistical API runs, 1-day windows with 2-day fallback if data are empty, and compare broad AOI, corridor_wide, and river corridor AOI before deciding whether scientific signal is strong enough. A final MVP should use cached precomputed outputs and optionally one live CDSE refresh, not repeated uncached request bursts.

## 10. What must NOT be reused in official hackathon repo.

Do not reuse this folder, code, evalscripts, raw outputs, processed CSVs, notes, AOI files, or wording as official hackathon deliverables.

CRS/reprojection: OK. Current scientific signal: inconclusive. Next decision depends on corridor_wide and river corridor AOIs plus catalog-confirmed dates.
