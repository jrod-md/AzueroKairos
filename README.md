# Azuero Kairós

Azuero Kairós is a Copernicus-based satellite confidence decision layer for agricultural decision support in Azuero, Panama.

The project does not detect contamination and does not declare water safe. It classifies Sentinel-2 observations into confidence states so a user can decide whether a scene is usable for cautious exploratory hydro-sedimentary interpretation, should be reviewed, or should not be used for inference.

## Decision States

- `usable`: the observation has enough valid evidence to support a limited satellite-based interpretation.
- `low_confidence`: the observation may contain partial signal, but quality limits require caution.
- `do_not_infer`: the observation does not support a responsible satellite-based inference.

## Current Official Sentinel-2 Results

These are confidence-of-observation results from the official Sentinel-2 Statistical API run. They are not chemical or sanitary measurements.

| Date | AOI | validPercent | confidence_class |
| --- | --- | ---: | --- |
| 2025-06-02 | corridor_wide | 49.15 | `usable` |
| 2025-06-10 | corridor_wide | 2.26 | `do_not_infer` |
| 2025-06-15 | corridor_wide | 44.22 | `usable` |
| 2025-06-30 | corridor_wide | 71.06 | `usable` |
| 2025-07-15 | corridor_wide | 52.22 | `usable` |

The important product behavior is the contrast between scenes: Azuero Kairós does not force an alert when evidence is weak. It explicitly marks weak observations as `do_not_infer`.

## Setup

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Variables

The Sentinel-2 batch runner uses Copernicus Data Space Ecosystem OAuth credentials from environment variables only.

```powershell
$env:CDSE_CLIENT_ID = "your-client-id"
$env:CDSE_CLIENT_SECRET = "your-client-secret"
```

Do not commit `.env` files or secrets. The repository is configured to ignore local environment files.

## Run the Sentinel-2 Batch

From the repository root:

```powershell
python scripts/run_official_s2_batch.py
```

Optional flags:

```powershell
python scripts/run_official_s2_batch.py --force --aoi corridor_wide --resolution 20
```

The runner writes raw API responses to `outputs/raw_json/` and the processed official CSV to `outputs/processed_csv/sentinel2_stats_confidence.csv`.

## Run the Dashboard

```powershell
streamlit run dashboard/app.py
```

The dashboard loads the newest processed CSV when available. If no official CSV exists, it clearly labels fallback records as UI preview only.

## Generate the Evidence Ledger

```powershell
python scripts/build_evidence_ledger.py
```

The ledger is written to `outputs/ledger/evidence_ledger.csv` and links the decision chain:

```text
raw JSON -> processed CSV -> confidence classification -> generated brief
```

## Module Demos

```powershell
python -m src.azuero_kairos.confidence_engine
python -m src.azuero_kairos.brief_generator
```

The brief demo writes a Markdown Confidence Brief under `outputs/briefs/`.

## Scientific Limits

Azuero Kairós does not detect pesticides, atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe water. It does not make chemical, sanitary, medical, legal, or regulatory claims. Laboratory or authorized field verification is required for chemical or sanitary claims.

The output is a confidence assessment for satellite observation usability, not proof of contamination, safety, crisis conditions, or operational readiness.

## Official Clean-Build Policy

This repository is the official hackathon build for Azuero Kairós.

Pre-hackathon work consisted only of planning and discarded feasibility spikes. Official code, official outputs, dashboard views, briefs, and ledgers are generated during the hackathon window from this clean repository.
