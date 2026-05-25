# Codex Official Build Prompt

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

Use this only after the official competition window begins.

```text
Act as technical lead, remote sensing engineer, UX lead, and eligibility auditor for Azuero AgroShield.

Create a fresh official hackathon repository from zero. Do not copy pre-hackathon spike code. Use the planning specs only as guidance.

Build a Streamlit app or equivalent simple app for a Satellite Confidence Semaforo and hydro-sedimentary exploratory screening over the corridor_wide AOI near Rio La Villa, Azuero.

Rules:
- Create fresh code during the official window.
- Do not expose secrets.
- Read CDSE_CLIENT_ID and CDSE_CLIENT_SECRET only from environment or local .env.
- Ensure .env is ignored.
- Use cached Copernicus-derived outputs for demo reproducibility.
- Optional: implement one live CDSE refresh for one date/index only if quota allows.
- Implement phases 0-4 first: Evidence Kernel, Satellite Confidence Semaforo, Hydro-Sedimentary Screening, Agricultural Decision Brief, Risk Explainability Panel.
- Stop after the first working demo path before adding stretch features.
- No AWS.
- No Twilio.
- No Sentinel-1 yet.
- No CHIRPS/ERA5 yet.
- No chemical detection claims.
- No June 2025 crisis validation claim.
- No final claims beyond the evidence.

MVP must include:
- corridor_wide primary AOI.
- river secondary/zoom AOI if time allows.
- MNDWI and NDTI.
- confidence state: usable, low confidence, invalid.
- risk state: normal, watch, review, do not infer.
- valid pixels bar.
- explanation panel.
- AgroShield Confidence Brief.
- Claim Firewall.
- local template fallback for AI.

Build with a sober, technical UI. The demo must work offline from cache.
```
