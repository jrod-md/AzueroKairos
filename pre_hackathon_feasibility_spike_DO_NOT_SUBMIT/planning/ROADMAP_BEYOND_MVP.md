# Roadmap Beyond MVP

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

This roadmap is vision, not MVP scope. Do not overpromise during the hackathon.

## Near-Term

### Regional Replication Pack

Create a config pattern for another agricultural river corridor:
- AOI file.
- Catalog date range.
- Index set.
- confidence thresholds.
- limitations.
- local verification contact.

Output: replication checklist, not deployed region.

### Prediction Ledger

Track expected next state versus later observation:
- pending.
- consistent.
- contradicted.
- insufficient evidence.

This is not guaranteed prediction.

### Evidence Packet Export

Export a compact evidence packet:
- date.
- AOI.
- source mode.
- confidence state.
- risk state.
- limitations.

Avoid compliance PDF in MVP.

## Post-Hackathon

### Sentinel-1 Cloud Resilience

Add Sentinel-1 only after the Sentinel-2 confidence product is stable. Purpose: cloud-resilience layer, not replacement for optical hydro-sedimentary signal.

### Crop Corridor Overlay

Add crop context if reliable crop/corridor data are available. Do not claim farm-level truth from rough overlays.

### Water Productivity / Irrigation Stress Roadmap

Explore ET, irrigation stress, and water productivity after core evidence workflow is trusted. Do not insert ERA5/CHIRPS into MVP unless core is done.

## Institutional Pilot

### Controlled Verification

Create a local feedback protocol:
- date.
- observed field condition.
- photo or field note.
- confidence state at time of observation.
- later comparison.

This is controlled community verification, not scientific validation by itself.

### Institutional Policy Brief Mode

Translate evidence into institutional language:
- what satellite suggests.
- what cannot be inferred.
- what local verification is recommended.

No legal advice. No operational closure advice.

## Regional Scale

### Regional Replication Pack

Package a node setup method for ALC:
- basin/corridor AOI.
- Sentinel-2 catalog range.
- confidence thresholds.
- local crop/irrigation context.
- limitations.

### Resilience Scorecard

Only after multiple observations and verification loops. The scorecard must remain evidence-weighted and caveated.

## Production Architecture Roadmap

Production architecture comes after MVP:
- secure secret handling.
- scheduled cache refresh.
- CDSE rate-limit aware queue.
- database for observations.
- audit log.
- static front-end or app server.
- optional cloud deployment.

AWS is post-hackathon unless explicitly required later. Do not build it during MVP.

## Anticipatory Action Trigger Design

A future trigger must be governed:
- satellite confidence gate.
- risk state threshold.
- field verification requirement.
- human decision owner.
- no automatic closure.
- no mandatory irrigation suspension.

## Do Not Overpromise

Do not promise operational readiness, chemical detection, crisis validation, or guaranteed prediction. The roadmap is a path to maturity, not proof that maturity already exists.
