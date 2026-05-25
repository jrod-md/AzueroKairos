# First Delivery: Azuero Kairós

## Short Description

Azuero Kairós is a Copernicus-based satellite confidence decision layer for agricultural decision support in Azuero, Panama. It classifies whether a Sentinel observation is usable for cautious exploratory hydro-sedimentary interpretation and generates a Markdown Confidence Brief.

## Problem

Agricultural users can see satellite-derived water and sediment indicators, but not every satellite observation is reliable enough to interpret. Clouds, no-data pixels, sparse valid samples, and uncertain acquisition quality can make a scene unsuitable for decision support. Without a confidence layer, users may overread weak satellite evidence.

## Solution

The MVP separates observation quality from interpretation. It takes reproducible Copernicus-derived evidence, classifies the observation into a decision state, and produces a brief that explains what can and cannot be responsibly inferred.

## Why It Uses Copernicus

Copernicus provides open Sentinel observations suitable for transparent, repeatable Earth Observation workflows. The MVP is designed around official Sentinel metadata and statistical outputs so the confidence decision can be traced from source evidence to final brief.

## Decision States

- `usable`: use for exploratory hydro-sedimentary interpretation with stated limits.
- `low_confidence`: review cautiously and consider field verification.
- `do_not_infer`: do not make a satellite-based inference; wait for a new acquisition or request field verification.

## Milestone 1 Demonstration

Milestone 1 will demonstrate the first reproducible official pipeline pieces:

- A clean repository with documented scientific and originality limits.
- AOI and date configuration files for repeatable runs.
- A pure Python confidence engine using valid-pixel percentage thresholds.
- A Markdown Confidence Brief generated from a structured observation record.
- Output traceability from raw JSON path to confidence decision and recommended action.

## Scientific Limits

Azuero Kairós does not detect pesticides, atrazine, pathogens, heavy metals, dissolved chemical contamination, or safe water. It does not make chemical, sanitary, medical, legal, or regulatory claims. Laboratory or authorized field verification is required for those claims.

## Clean-Build Statement

This is the official hackathon build. Pre-hackathon work was limited to planning and discarded feasibility spikes. Official code, official outputs, dashboard views, and briefs are generated during the hackathon window from this clean repository.

## Next 6-Day Plan

Day 1: finalize official scaffold, confidence engine, and brief generator.

Day 2: connect Copernicus CDSE catalog queries and save raw JSON evidence.

Day 3: add statistical extraction and processed CSV generation.

Day 4: connect processed CSV records to the confidence engine and evidence ledger.

Day 5: build the minimal dashboard around decision states, traceability, and briefs.

Day 6: test the full reproducible run, prepare demo materials, and review every claim against the scientific limits.
