# Day 1 Build Plan

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

Official build rule: create fresh code during the hackathon. Do not copy spike code.

## Hour 0-1: Fresh Official Repo

- Create fresh official repo.
- Add README with official scope.
- Add `.gitignore`.
- Add `.env.example`.
- Confirm `.env` ignored.
- No secrets in logs.

Output: clean repo skeleton.

## Hour 1-2: Data Schema

- Define official processed observation schema.
- Define AOI metadata.
- Define confidence and risk state enums.
- Copy no prebuilt code; reimplement from understanding.

Output: schema file and sample rows.

## Hour 2-3: Recreate CDSE Auth And Cache Loader

- Rebuild auth from scratch.
- Rebuild cache loader.
- Confirm cached data path works.
- Optional auth smoke test only if safe.

Output: cache can load official generated rows.

## Hour 3-4: Rebuild Processed CSV Generator

- Recreate Statistical API payload builder.
- Recreate EPSG:32617 reprojection.
- Generate or load official cached CSV.
- Keep cache-first behavior.

Output: processed CSV with confidence fields.

## Hour 4-6: Build Streamlit Skeleton

- Create simple app shell.
- Add AOI/date selector.
- Add cached/live mode indicator.
- No styling rabbit holes.

Output: first visible UI reading cached/generated data.

## Hour 6-8: Confidence Semaforo

- Add confidence badge.
- Add valid pixels bar.
- Add sample/noData metrics.
- Enforce invalid => do not infer.

Output: Phase 1 shippable.

## Hour 8-10: Risk Screening

- Add MNDWI/NDTI table/chart.
- Add exploratory risk state.
- Add limitations.
- No chemical claims.

Output: Phase 2 shippable.

## Hour 10-12: Explainability Panel + Basic Demo

- Add Why This State panel.
- Add AgroShield Confidence Brief.
- Add local template.
- Add claim limitation box.

Output: first complete demo path.

## Deliverable By End Of Day

First visible UI reading cached/generated data, showing confidence state, risk state, explanation, and safe brief.

## Day 1 Non-Negotiables

- No copied spike code.
- No final claims.
- No AWS.
- No Twilio.
- No Sentinel-1.
- No chemical detection.
- No live dependency for the demo.
