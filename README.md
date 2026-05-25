# Azuero Kairós

Azuero Kairós is a Copernicus-based satellite confidence decision layer for agricultural decision support in Azuero, Panama.

The system does not detect contamination and does not declare water safe. Its purpose is narrower: classify Sentinel observations into confidence states and generate a concise Confidence Brief that tells users whether an observation is usable for cautious decision support.

## Decision States

- `usable`: the observation has enough valid evidence to support a limited satellite-based interpretation.
- `low_confidence`: the observation may contain partial signal, but quality limits require caution.
- `do_not_infer`: the observation does not support an inference and should not be used for decision support.

## Official Clean-Build Policy

This repository is the official hackathon build for Azuero Kairós.

Pre-hackathon work consisted only of planning and discarded feasibility spikes. The official repository must not copy code, generated results, dashboards, briefs, or processed outputs from those spikes. Official code, official outputs, official dashboard views, and official briefs are produced during the hackathon window from this clean scaffold.

## Install

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For local imports without packaging the project yet:

```powershell
$env:PYTHONPATH = "src"
```

## Future Run Commands

The initial repository contains only the clean scaffold. Future scripts should be reproducible from configuration files in `configs/` and write generated artifacts into `outputs/`.

Expected future commands:

```powershell
python -m azuero_kairos.confidence_engine
python -m azuero_kairos.brief_generator
streamlit run dashboard/app.py
```

These commands are placeholders for future implementation work. Cloud infrastructure, AWS services, Twilio, and external notification integrations are intentionally not part of this initial scaffold.
