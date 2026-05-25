# Architecture

Azuero Kairós is organized as a small, reproducible pipeline.

## Components

- `configs/`: official AOI and date configuration files.
- `src/azuero_kairos/settings.py`: shared filesystem settings.
- `src/azuero_kairos/confidence_engine.py`: confidence state definitions and future observation classifier.
- `src/azuero_kairos/evidence_ledger.py`: JSON Lines ledger helpers for traceable decisions.
- `src/azuero_kairos/brief_generator.py`: Markdown Confidence Brief generator.
- `dashboard/app.py`: minimal dashboard scaffold.
- `outputs/`: generated raw responses, processed tables, briefs, and ledgers.

## Data Flow

1. Load AOI and official date configuration.
2. Acquire Sentinel observation metadata and measurements.
3. Save raw source responses to `outputs/raw_json/`.
4. Transform official observations into processed CSV evidence.
5. Classify each observation as `usable`, `low_confidence`, or `do_not_infer`.
6. Write decision records to `outputs/ledger/`.
7. Generate Confidence Briefs in `outputs/briefs/`.
8. Display official outputs in the dashboard.

## Scope Boundary

The system is a confidence decision layer, not a contamination detector. It does not identify pesticides, atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe water.

No cloud infrastructure, AWS code, Twilio integration, or external notification service is included in this initial scaffold.
