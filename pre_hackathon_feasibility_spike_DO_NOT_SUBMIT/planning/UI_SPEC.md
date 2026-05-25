# UI Spec

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

This is a design specification only. Do not build the UI before the official hackathon window.

## UI Principle

Evidence confidence comes before risk. If evidence is weak, the product must say **do not infer**.

## Screens

### 1. Landing / Demo Intro

Purpose: explain the single-node demo in 15 seconds.

Content:
- Project name: Azuero AgroShield.
- One-line: Satellite Confidence Semaforo for agricultural water-risk screening.
- Mode indicator: cached Copernicus-derived evidence.
- Limitation line: not chemical detection; decision support, not laboratory replacement.

### 2. AOI + Date Selection

Purpose: choose `corridor_wide AOI`, optional `river` zoom, and catalog-confirmed date.

Components:
- AOI badge.
- Date selector.
- Cached/live mode indicator.
- Valid acquisition note from Catalog API.

Default:
- AOI: `corridor_wide`.
- Mode: cache.

### 3. Satellite Confidence Semaforo

Purpose: show whether satellite evidence can be interpreted.

Components:
- Confidence badge: usable / low confidence / invalid.
- Valid pixels bar.
- sampleCount, noDataCount, validPercent.
- Claim limitation box.

Rules:
- validPercent < 10%: invalid.
- 10% <= validPercent < 30%: low confidence.
- validPercent >= 30%: usable.

### 4. Hydro-Sedimentary Risk Panel

Purpose: show exploratory risk state only when confidence allows.

Components:
- Risk badge: normal / watch / review / do not infer.
- MNDWI chart.
- NDTI chart.
- Evidence table.

Rules:
- If confidence=invalid, risk state must be "do not infer".
- If validPercent < 10%, do not show risk recommendation.
- Never describe NDTI as chemical detection.

### 5. Why This State? Explainability

Purpose: defend the system in technical Q&A.

Components:
- Explanation box.
- Rules list.
- Evidence table.
- AOI and date metadata.
- Cloud/no-data note.

Must answer:
- What was measured?
- Was there enough valid data?
- Which rule fired?
- What should not be inferred?

### 6. AgroShield Confidence Brief

Purpose: operator-facing decision support.

Components:
- Recommendation card.
- Confidence sentence.
- Risk sentence.
- Field verification recommended line.
- Not chemical detection limitation.

### 7. AI-Generated Audience View

Purpose: show controlled translation for audiences.

Audiences:
- producer.
- technical_operator.
- jury.
- institutional_policy.

Rules:
- If AI unavailable, show template.
- AI must not calculate risk.
- AI output passes Claim Firewall.

### 8. Prediction Ledger

Purpose: trust differentiator.

Components:
- Date.
- Expected next observation state.
- Actual later state when available.
- Status: pending / consistent / contradicted / insufficient evidence.

Rule:
- No guaranteed prediction language.

### 9. Replication Pack / Roadmap

Purpose: show ALC scalability without claiming deployment.

Components:
- AOI config example.
- Data pipeline checklist.
- Limitations.
- Future roadmap.

## Components

- Map panel.
- AOI badge.
- Date selector.
- Confidence badge: usable / low confidence / invalid.
- Risk badge: normal / watch / review / do not infer.
- Valid pixels bar.
- MNDWI chart.
- NDTI chart.
- Evidence table.
- Explanation box.
- Recommendation card.
- Claim limitation box.
- AI brief card.
- Export button placeholder.
- Cached/live mode indicator.

## UX Rules

- If confidence=invalid, risk state is "do not infer".
- If validPercent < 10%, no risk recommendation is shown.
- If AI is unavailable, local template is shown.
- Always show "not chemical detection".
- Never use certainty language.
- Demo must work without internet using cache.
- Do not hide noDataCount.
- The primary AOI is `corridor_wide`; `river` is zoom/secondary.

## Visual Tone

Sober, technical, decision-oriented. No decorative hero. No generic dashboard grid. The first screen should feel like an evidence workbench, not a landing page.
