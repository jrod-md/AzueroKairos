# PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT

This folder is a private, disposable technical spike for Azuero AgroShield.

DO NOT submit this folder, its code, evalscripts, outputs, notes, screenshots, or derived artifacts to TAIKAI or to any official hackathon repository.

All official hackathon code, notebooks, evalscripts, dashboards, reports, processed results, and delivery documentation must be regenerated from zero inside the official competition window.

## Narrow Question

Can the Copernicus Data Space Ecosystem / Sentinel Hub Statistical API return useful Sentinel-2 L2A statistics over an approximate Chitre / La Arena AOI for exploratory MNDWI and NDTI comparisons during May-July 2025?

This spike may only support a private eligibility decision. It must not be presented as operational validation, water quality validation, pesticide detection, chemical detection, pathogen detection, or irrigation shutdown evidence.

Correct scope wording:

> señal satelital exploratoria asociada a riesgo hidro-sedimentario observable

## Setup

Create local environment variables. Do not commit a real `.env` file.

```powershell
$env:CDSE_CLIENT_ID="your-client-id"
$env:CDSE_CLIENT_SECRET="your-client-secret"
```

Install minimal dependencies if needed:

```powershell
pip install -r requirements.txt
```

## Minimal Commands

Authentication check:

```powershell
python src/auth_cdse.py
```

Single date, exploratory MNDWI:

```powershell
python src/run_single_date.py --date 2025-06-11 --index mndwi
```

Short batch:

```powershell
python src/run_date_batch.py --limit 6
python src/summarize_results.py
```

Outputs are internal scratch artifacts under `outputs/` and `notes/`.
