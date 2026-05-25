# MVP Scope Lock

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

## Product Frame

The official MVP should be a **Satellite Confidence Semaforo** with **Hydro-sedimentary exploratory screening** for the `corridor_wide AOI` near Rio La Villa, Azuero.

It is decision support, not laboratory replacement. It reduces blind decisions in irrigation and agricultural food-safety conversations by showing when Copernicus-derived evidence is usable, low-confidence, or invalid.

## MVP Includes

- Simple Streamlit app or equivalent simple web app, built from zero during the official window.
- Cached Copernicus-derived CSV generated during the official window.
- `corridor_wide AOI` as primary unit.
- `river AOI` as secondary/zoom unit if time allows.
- Sentinel-2 L2A MNDWI and NDTI.
- Confidence state: usable, low confidence, invalid.
- Exploratory risk state: normal, watch, review, do not infer.
- Risk Explainability Panel before extra map modes.
- AgroShield Confidence Brief.
- Agricultural recommendation as cautious guidance, not obligation.
- Optional AI BriefWriter with deterministic template fallback.
- Claim Firewall before any generated or templated text is displayed.
- Simple Prediction Ledger comparing projected expectation against later observations.
- Cached/live mode indicator.

## MVP Does Not Include

- AWS production architecture.
- Twilio or operational alerts.
- Chemical detection.
- Atrazine, pesticide, pathogen, metal, or complete water-quality claims.
- Sentinel-1 unless all core phases are done.
- CHIRPS/ERA5 unless all core phases are done.
- NitroSync.
- 52 nodes.
- Advanced compliance PDF.
- Real-time claims.
- Automatic closure or irrigation suspension recommendations.
- Validated June 2025 crisis detection.

## Scope Rule

If a feature does not improve trust, evidence clarity, or the demo story, cut it.

## Official Build Rule

No pre-hackathon spike code is copied into the official repository. Reimplement from understanding during the competition.
