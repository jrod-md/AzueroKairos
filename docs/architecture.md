# MVP Architecture

Azuero Kairós is a small, reproducible pipeline that turns Copernicus Sentinel observation evidence into confidence decisions and human-readable briefs.

## Core Pipeline

```text
Copernicus CDSE Catalog/Statistical API
  -> raw JSON
  -> processed CSV
  -> confidence engine
  -> Confidence Brief
  -> dashboard
```

## Components

- `configs/`: AOI and official date configuration.
- `outputs/raw_json/`: source evidence from Copernicus CDSE responses.
- `outputs/processed_csv/`: normalized observation metrics for the MVP.
- `src/azuero_kairos/confidence_engine.py`: deterministic classification into `usable`, `low_confidence`, or `do_not_infer`.
- `src/azuero_kairos/brief_generator.py`: Markdown Confidence Brief generation from one structured record.
- `src/azuero_kairos/evidence_ledger.py`: traceable decision records.
- `dashboard/app.py`: minimal viewer for decision states, evidence quality, brief summaries, and source traceability.

## Data Flow

1. Load the official AOI and date configuration.
2. Query the Copernicus CDSE Catalog API for matching Sentinel acquisitions.
3. Request statistical evidence for the selected AOI/date observations.
4. Save source responses as raw JSON.
5. Convert raw responses into processed CSV records with valid percentage, sample count, no-data count, and selected satellite indicators.
6. Classify each record with the confidence engine.
7. Generate a Confidence Brief for each official record.
8. Display the resulting decision, evidence quality, brief, and traceability in the dashboard.

## MVP Decision Layer

The MVP confidence engine is deterministic and threshold-based:

- `validPercent < 10`: `do_not_infer`
- `10 <= validPercent < 30`: `low_confidence`
- `validPercent >= 30`: `usable`

These states describe whether the satellite observation is usable for cautious exploratory hydro-sedimentary interpretation. They are not declarations about contamination or safety.

## Optional Enhanced Demo: Field Evidence Workflow

A future optional Field Evidence workflow may allow a demo user to attach notes, photos, or authorized field observations to a confidence brief. This would be an enhanced demo layer for context and traceability, not part of the core MVP decision engine.

## Scope Boundary

The MVP does not detect pesticides, atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe water. It does not automate operational interventions. Its core output is a confidence classification, a responsible interpretation boundary, and a traceable Confidence Brief.
