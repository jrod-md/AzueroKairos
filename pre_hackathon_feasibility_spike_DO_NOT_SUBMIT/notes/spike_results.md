# Internal Spike Results

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.

Current recommendation: GO TECHNICAL, ADJUST SCIENTIFIC.

Technical viability is demonstrated by existing CDSE authentication, EPSG:32617 reprojection, and returned MNDWI/NDTI statistics. Scientific signal remains inconclusive until catalog-confirmed acquisition dates are compared across broad_aoi, corridor_wide, and river_corridor_aoi.

Quality rule: validPercent < 10% is not interpreted; 10-30% is low confidence; >30% is usable for exploratory comparison.

## Technical ceiling assessment

Usable-date counts by AOI: broad_aoi=4, corridor_wide=2, river_corridor_aoi=2.

AOI with most usable dates: broad_aoi (4 usable dates).

Most scientifically defensible AOI: corridor_wide, because it balances river adjacency with enough surrounding riparian/agricultural pixels to reduce pure narrow-channel noise.

Product ceiling: Satellite confidence semaforo, with a possible upgrade to hydro-sedimentary exploratory semaforo only after a clear corridor_wide comparison.

## Usable Dates

| aoi | date | index | mean | stDev | sampleCount | noDataCount | valid % | quality |
|---|---|---|---:|---:|---:|---:|---:|---|
| broad_aoi | 2025-05-01 | mndwi | -0.4623 | 0.1477 | 99189 | 36157 | 63.5500 | usable_gt_30pct |
| broad_aoi | 2025-05-01 | ndti | 0.0886 | 0.1207 | 99189 | 36157 | 63.5500 | usable_gt_30pct |
| broad_aoi | 2025-05-06 | mndwi | -0.4555 | 0.1428 | 99189 | 8246 | 91.6900 | usable_gt_30pct |
| broad_aoi | 2025-05-06 | ndti | 0.0489 | 0.1150 | 99189 | 8246 | 91.6900 | usable_gt_30pct |
| broad_aoi | 2025-06-01 | mndwi | -0.4053 | 0.1364 | 99189 | 36247 | 63.4600 | usable_gt_30pct |
| broad_aoi | 2025-06-01 | ndti | 0.0230 | 0.0855 | 99189 | 36247 | 63.4600 | usable_gt_30pct |
| broad_aoi | 2025-06-21 | mndwi | -0.3138 | 0.1789 | 99189 | 50408 | 49.1800 | usable_gt_30pct |
| broad_aoi | 2025-06-21 | ndti | -0.0871 | 0.1101 | 99189 | 50408 | 49.1800 | usable_gt_30pct |
| corridor_wide | 2025-05-01 | mndwi | -0.4527 | 0.1373 | 108832 | 67982 | 37.5300 | usable_gt_30pct |
| corridor_wide | 2025-05-01 | ndti | 0.0918 | 0.1126 | 108832 | 67982 | 37.5300 | usable_gt_30pct |
| corridor_wide | 2025-05-06 | mndwi | -0.4789 | 0.1366 | 108832 | 46909 | 56.9000 | usable_gt_30pct |
| corridor_wide | 2025-05-06 | ndti | 0.0547 | 0.1173 | 108832 | 46909 | 56.9000 | usable_gt_30pct |
| river_corridor_aoi | 2025-05-06 | mndwi | -0.5090 | 0.0942 | 33550 | 18117 | 46.0000 | usable_gt_30pct |
| river_corridor_aoi | 2025-05-06 | ndti | 0.0885 | 0.1020 | 33550 | 18117 | 46.0000 | usable_gt_30pct |

## Low Confidence Dates

| aoi | date | index | mean | stDev | sampleCount | noDataCount | valid % | quality |
|---|---|---|---:|---:|---:|---:|---:|---|
| broad_aoi | 2025-06-11 | mndwi | -0.3644 | 0.1320 | 99189 | 72030 | 27.3800 | low_confidence_10_30pct |
| broad_aoi | 2025-06-11 | ndti | -0.0601 | 0.1265 | 99189 | 72030 | 27.3800 | low_confidence_10_30pct |
| river_corridor_aoi | 2025-05-01 | mndwi | -0.4671 | 0.1226 | 33550 | 23958 | 28.5900 | low_confidence_10_30pct |
| river_corridor_aoi | 2025-05-01 | ndti | 0.1194 | 0.0877 | 33550 | 23958 | 28.5900 | low_confidence_10_30pct |

## Invalid / Low-Validity Dates

| aoi | date | index | mean | stDev | sampleCount | noDataCount | valid % | quality |
|---|---|---|---:|---:|---:|---:|---:|---|
| broad_aoi | 2025-05-11 | mndwi | NaN | NaN | 99189 | 99189 | 0.0000 | invalid_lt_10pct |
| broad_aoi | 2025-05-11 | ndti | NaN | NaN | 99189 | 99189 | 0.0000 | invalid_lt_10pct |
| broad_aoi | 2025-05-13 | mndwi | NaN | NaN | 99189 | 99189 | 0.0000 | invalid_lt_10pct |
| broad_aoi | 2025-05-22 | mndwi | NaN | NaN | 99189 | 99189 | 0.0000 | invalid_lt_10pct |
| broad_aoi | 2025-05-22 | ndti | NaN | NaN | 99189 | 99189 | 0.0000 | invalid_lt_10pct |
| broad_aoi | 2025-07-01 | mndwi | 0.0697 | 0.0960 | 99189 | 99183 | 0.0100 | invalid_lt_10pct |
| broad_aoi | 2025-07-01 | ndti | 0.0056 | 0.0209 | 99189 | 99183 | 0.0100 | invalid_lt_10pct |
| corridor_wide | 2025-05-11 | mndwi | NaN | NaN | 108832 | 108832 | 0.0000 | invalid_lt_10pct |
| corridor_wide | 2025-05-11 | ndti | NaN | NaN | 108832 | 108832 | 0.0000 | invalid_lt_10pct |
| corridor_wide | 2025-05-13 | mndwi | NaN | NaN | 108832 | 108832 | 0.0000 | invalid_lt_10pct |
| corridor_wide | 2025-05-13 | ndti | NaN | NaN | 108832 | 108832 | 0.0000 | invalid_lt_10pct |
| corridor_wide | 2025-05-16 | mndwi | NaN | NaN | 108832 | 108832 | 0.0000 | invalid_lt_10pct |
| corridor_wide | 2025-05-16 | ndti | NaN | NaN | 108832 | 108832 | 0.0000 | invalid_lt_10pct |
| river_corridor_aoi | 2025-05-11 | mndwi | NaN | NaN | 33550 | 33550 | 0.0000 | invalid_lt_10pct |

Interpretation limit: MNDWI supports observable water/wetness signal. NDTI is only a proxy for señal satelital exploratoria asociada a riesgo hidro-sedimentario observable. This does not detect pesticides, atrazine, dissolved chemicals, metals, pathogens, or complete water quality.
