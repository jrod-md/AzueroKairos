# Satellite Capability Tests - 2026-05-18

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.

These tests were run only to understand the technical and scientific ceiling of AgroShield before the hackathon. They are not official hackathon outputs and must not be submitted as final deliverables.

## Commands run

- `python src/auth_cdse.py`
- `python src/run_catalog_dates.py --aoi corridor_wide=data\aoi_chitre_corridor_wide_test.geojson --resolution-meters 20 --date-filter 2025-06-02,2025-06-10,2025-06-15,2025-06-30,2025-07-07,2025-07-09,2025-07-15 --max-dates 10 --sleep-seconds 20 --indices mndwi,ndti --preferred-window-days 1 --fallback-window-days 1`
- `python src/run_catalog_dates.py --aoi corridor_wide=data\aoi_chitre_corridor_wide_test.geojson --resolution-meters 20 --date-filter 2025-06-10,2025-06-15,2025-07-07,2025-07-09 --max-dates 10 --sleep-seconds 20 --indices mndwi,ndti --preferred-window-days 2 --fallback-window-days 2`
- `python src/run_catalog_dates.py --aoi broad=data\aoi_chitre_la_arena_approx.geojson --aoi river=data\aoi_chitre_river_corridor_test.geojson --resolution-meters 20 --date-filter 2025-06-02,2025-06-15,2025-06-30,2025-07-15 --max-dates 10 --sleep-seconds 20 --indices mndwi,ndti --preferred-window-days 1 --fallback-window-days 1`
- `python src/run_catalog_dates.py --aoi corridor_wide=data\aoi_chitre_corridor_wide_test.geojson --resolution-meters 10 --date-filter 2025-06-02,2025-06-30 --max-dates 10 --sleep-seconds 20 --indices mndwi,ndti --preferred-window-days 1 --fallback-window-days 1`

No credentials were printed or written.

## Generated internal CSVs

- `outputs/processed/corridor_wide_targeted_1d_stats.csv`
- `outputs/processed/corridor_wide_problem_dates_2d_stats.csv`
- `outputs/processed/aoi_comparison_informative_dates_1d_stats.csv`
- `outputs/processed/corridor_wide_resolution_10m_check.csv`

## Key result: corridor_wide 20 m, 1-day windows

| date | cloudCover | confidence | validPercent | MNDWI mean | NDTI mean | interpretation |
|---|---:|---|---:|---:|---:|---|
| 2025-06-02 | 36.76 | usable | 47.72 | -0.4133 | 0.0242 | Usable baseline/candidate comparison date. |
| 2025-06-10 | 86.06 | invalid | 0.00 | NaN | NaN | Do not infer near June 11. Cloud/no-data blocks interpretation. |
| 2025-06-15 | 66.47 | low confidence | 13.24 | -0.3377 | -0.0595 | Possible weak reading, but not strong enough for risk claim. |
| 2025-06-30 | 51.81 | usable | 58.34 | -0.4798 | -0.1224 | Strong usable comparison date. |
| 2025-07-07 | 49.32 | invalid | 0.13 | -0.5887 | -0.1667 | Do not interpret despite numeric means. Valid pixels are too low. |
| 2025-07-09 | 36.06 | invalid | 0.01 | -0.5817 | -0.1652 | Do not interpret despite low cloudCover metadata. AOI pixels are invalid. |
| 2025-07-15 | 67.66 | usable | 34.94 | -0.3161 | -0.0565 | Usable late comparison date. |

## Two-day window test

Two-day windows did not rescue the important invalid dates:

- 2025-06-10 remained invalid at 0.00 validPercent.
- 2025-06-15 remained low confidence at 13.24 validPercent.
- 2025-07-07 remained invalid at 0.13 validPercent.
- 2025-07-09 remained invalid at 0.01 validPercent.

Conclusion: expanding from 1 day to 2 days does not solve the cloud/no-data problem for these dates. The product should explicitly show `do_not_infer` instead of trying to force a risk reading.

## AOI comparison on informative dates

| AOI | usable rows | low-confidence rows | invalid rows | interpretation |
|---|---:|---:|---:|---|
| broad | 6 | 2 | 0 | Strong data availability, but risk of diluted river/corridor signal. |
| river | 4 | 2 | 2 | Scientifically targeted, but fragile under clouds/no-data. |
| corridor_wide | 6 | 2 | 0 | Best current primary AOI: enough usable rows and more defensible than broad. |

Detailed comparison:

- 2025-06-02 is usable across broad, river, and corridor_wide.
- 2025-06-15 is low confidence for broad/corridor_wide and invalid for river.
- 2025-06-30 is usable across broad, river, and corridor_wide.
- 2025-07-15 is usable for broad/corridor_wide and low confidence for river.

Conclusion: `corridor_wide` remains the best operational primary AOI. `river` is valuable as secondary zoom, not as the only product unit.

## Resolution sensitivity

10 m results are very close to 20 m results for good dates:

| date | index | 20 m mean | 10 m mean | 20 m validPercent | 10 m validPercent |
|---|---|---:|---:|---:|---:|
| 2025-06-02 | MNDWI | -0.4133 | -0.4138 | 47.72 | 47.49 |
| 2025-06-02 | NDTI | 0.0242 | 0.0228 | 47.72 | 47.49 |
| 2025-06-30 | MNDWI | -0.4798 | -0.4809 | 58.34 | 58.04 |
| 2025-06-30 | NDTI | -0.1224 | -0.1267 | 58.34 | 58.04 |

Conclusion: 20 m is a safe default because B11 is a 20 m Sentinel-2 band and MNDWI depends on B11. 10 m can be shown only as a sensitivity check, not as the main claim.

## What AgroShield can now defensibly do

1. Build a Satellite Confidence Semaforo using actual Sentinel-2 catalog dates.
2. Show when a date is usable, low confidence, or invalid.
3. Use `corridor_wide` as primary AOI and `river` as secondary zoom.
4. Compare MNDWI/NDTI across usable dates.
5. Explain why some dates, including near June 11, must be `do_not_infer`.
6. Demonstrate cache-first reproducibility and avoid live-demo fragility.
7. Produce an AgroShield Confidence Brief with evidence, limitations, and recommended verification language.

## What AgroShield still cannot claim

1. It cannot claim June 2025 crisis validation.
2. It cannot claim chemical, pesticide, atrazine, pathogen, metal, or full water-quality detection.
3. It cannot claim operational authority for irrigation suspension or intake closure.
4. It cannot treat invalid dates as normal dates.
5. It cannot treat NDTI changes as calibrated sediment measurements without field validation.

## Decision

Recommendation remains: GO TECHNICAL / ADJUST SCIENTIFIC.

The product is more viable after these tests. The winning frame should be:

"AgroShield turns Copernicus into a satellite confidence semaforo and agricultural decision brief: it shows when evidence is strong enough to interpret, when it is weak, and when the responsible answer is do not infer."

## Next best technical action

During the official hackathon build, regenerate all code and outputs from zero. For the demo, use:

- `corridor_wide` as primary AOI.
- 20 m resolution as default.
- 2025-06-02, 2025-06-30, and 2025-07-15 as usable comparison examples.
- 2025-06-10 as a strong `do_not_infer` example near the June 11 question.
- `river` as secondary zoom to show why narrow AOIs can lose confidence.
