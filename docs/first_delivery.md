# First Delivery: Azuero Kairós

## Short Description

Azuero Kairós is a Copernicus-based satellite confidence decision layer for agricultural decision support in Azuero, Panama. It turns Sentinel-2 observation quality into a clear decision state and a traceable Confidence Brief.

## Problem

Agricultural decision support often treats satellite scenes as if every observation is equally usable. In practice, clouds, no-data pixels, sparse valid samples, and acquisition limits can make a Sentinel scene inappropriate for inference. Without a confidence layer, weak evidence can be overread.

## Solution

The MVP separates observation confidence from interpretation. It runs official Sentinel-2 statistics for configured dates and AOIs, stores raw JSON evidence, converts it into a processed CSV, classifies each row with a deterministic confidence engine, and presents the result in a Spanish decision console and Confidence Brief.

## Copernicus Use

The MVP uses the Copernicus Data Space Ecosystem Statistical API with Sentinel-2 observations. The official run computes MNDWI and NDTI summary indicators, plus evidence quality metrics such as `sampleCount`, `noDataCount`, and `validPercent`.

Copernicus is used because it provides open, reproducible Earth Observation evidence that can be traced from API response to dashboard decision.

## Decision States

- `usable`: use for exploratory hydro-sedimentary interpretation with explicit limits.
- `low_confidence`: review cautiously and consider territorial or field verification.
- `do_not_infer`: do not make a satellite-based inference from this observation.

## Official MVP Status

The first delivery now includes:

- Official Sentinel-2 batch runner with API OK rows for five dates.
- Raw JSON responses saved under `outputs/raw_json/`.
- Processed CSV saved under `outputs/processed_csv/`.
- Deterministic confidence engine.
- Spanish Streamlit decision console connected to the official CSV.
- Spanish Markdown Confidence Brief generator.
- Evidence Ledger CLI for auditability.

## Current Official Results

These are confidence-of-observation results. They are not chemical or sanitary measurements.

| Date | AOI | validPercent | confidence_class |
| --- | --- | ---: | --- |
| 2025-06-02 | corridor_wide | 49.15 | `usable` |
| 2025-06-10 | corridor_wide | 2.26 | `do_not_infer` |
| 2025-06-15 | corridor_wide | 44.22 | `usable` |
| 2025-06-30 | corridor_wide | 71.06 | `usable` |
| 2025-07-15 | corridor_wide | 52.22 | `usable` |

The 2025-06-10 scene is important because it demonstrates restraint: the product tells the user not to infer when valid satellite evidence is too limited.

## What the Demo Shows

The demo shows the chain from Copernicus evidence to responsible action:

```text
Copernicus evidence -> confidence state -> decision -> Confidence Brief -> Evidence Ledger
```

In under 30 seconds, judges should see:

- A default `do_not_infer` case for 2025-06-10.
- A comparison with a usable case on 2025-06-30.
- Decision-critical metrics instead of generic charts.
- A generated Confidence Brief with scientific limits.
- An auditable ledger linking raw JSON, processed CSV, classification, and brief path.

## Remaining Work Before Final Submission

- Generate final briefs for all official rows that need them.
- Re-run the Evidence Ledger after final brief generation.
- Perform final dashboard visual QA on the demo machine.
- Confirm every public-facing claim stays within the scientific limits.
- Prepare final submission narrative and screenshots from the official build only.

## Scientific Limits

Azuero Kairós does not detect pesticides, atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe water. It does not validate a crisis, prove contamination, declare sanitary status, automate closures, or make operational readiness claims.

The MVP only classifies whether a Sentinel-2 observation has enough usable evidence for cautious exploratory hydro-sedimentary interpretation. Chemical or sanitary claims require laboratory analysis or authorized field verification.

## Clean-Build Statement

This is the official hackathon build. Pre-hackathon work was limited to planning and discarded feasibility spikes. Official code, official outputs, dashboard views, briefs, and ledgers are generated during the hackathon window from this clean repository.
