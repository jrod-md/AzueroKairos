# MVP Architecture

Azuero Kairós is a compact, reproducible pipeline that turns Copernicus Sentinel-2 observation evidence into confidence decisions, a dashboard view, a Confidence Brief, and an Evidence Ledger.

## Core Pipeline

```text
Copernicus CDSE Statistical API
  -> raw JSON
  -> processed CSV
  -> confidence engine
  -> dashboard
  -> Confidence Brief
  -> Evidence Ledger
```

## Components

- `configs/`: AOI and official date configuration.
- `src/azuero_kairos/cdse_auth.py`: CDSE OAuth helper using environment variables.
- `src/azuero_kairos/sentinel2_stats.py`: Sentinel-2 Statistical API request builder, cache-first raw JSON writer, and processed CSV generator.
- `outputs/raw_json/`: official source responses from Copernicus CDSE.
- `outputs/processed_csv/`: normalized official metrics, including MNDWI, NDTI, sample counts, no-data counts, valid percentage, API status, and confidence classification.
- `src/azuero_kairos/confidence_engine.py`: deterministic classification into `usable`, `low_confidence`, or `do_not_infer`.
- `dashboard/app.py`: Spanish decision console that loads the official CSV, shows the selected decision, compares key dates, and generates briefs on demand.
- `src/azuero_kairos/brief_generator.py`: Spanish Markdown Confidence Brief generator.
- `src/azuero_kairos/evidence_ledger.py` and `scripts/build_evidence_ledger.py`: audit layer linking raw JSON, processed CSV, confidence decision, and brief path.

## Data Flow

1. Load the official AOI and date configuration.
2. Authenticate to Copernicus CDSE with `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET`.
3. Request Sentinel-2 statistics for the configured AOI and dates.
4. Save each source response as raw JSON.
5. Convert raw responses into one processed CSV with `validPercent`, `sampleCount`, `noDataCount`, MNDWI, NDTI, `api_status`, and `api_error`.
6. Classify each processed row with the confidence engine.
7. Load the official CSV in the Streamlit dashboard.
8. Generate a Spanish Confidence Brief from a selected record.
9. Generate the Evidence Ledger to audit the full chain from source evidence to decision artifact.

## Current Official Results

These results describe observation usability only. They are not chemical or sanitary measurements.

| Date | validPercent | confidence_class |
| --- | ---: | --- |
| 2025-06-02 | 49.15 | `usable` |
| 2025-06-10 | 2.26 | `do_not_infer` |
| 2025-06-15 | 44.22 | `usable` |
| 2025-06-30 | 71.06 | `usable` |
| 2025-07-15 | 52.22 | `usable` |

## MVP Decision Layer

The confidence engine is deterministic and threshold-based:

- `validPercent < 10`: `do_not_infer`
- `10 <= validPercent < 30`: `low_confidence`
- `validPercent >= 30`: `usable`

These states describe whether a satellite observation is usable for cautious exploratory hydro-sedimentary interpretation. They are not declarations about contamination, safety, crisis validation, or operational action.

## Evidence Ledger

The Evidence Ledger is generated with:

```powershell
python scripts/build_evidence_ledger.py
```

It writes `outputs/ledger/evidence_ledger.csv` with row-level traceability:

- date, AOI, resolution, confidence class, and decision.
- evidence quality metrics and satellite indicators.
- API status and sanitized API error field.
- raw JSON path.
- processed CSV path.
- brief path.
- combined evidence status.

## Scope Boundary

The MVP does not detect pesticides, atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe water. It does not automate operational interventions or claim operational readiness.

Its core output is a confidence classification, a responsible interpretation boundary, a dashboard view, a Confidence Brief, and an Evidence Ledger.
