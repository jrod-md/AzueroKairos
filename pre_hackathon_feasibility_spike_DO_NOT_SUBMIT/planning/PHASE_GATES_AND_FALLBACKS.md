# Phase Gates And Fallbacks

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

| Phase | Gate to enter | Gate to exit | Fallback if failed | What remains shippable | Decision owner | Must stop if |
|---|---|---|---|---|---|---|
| 0 Evidence Kernel | Fresh official repo exists; no copied spike code; `.env` ignored | Cached official CSV loads and one safe CDSE path is reproducible | Use static sample CSV generated during official window | Data access demo | Technical lead | Secrets appear in logs or repo |
| 1 Satellite Confidence Semaforo | Evidence Kernel outputs validPercent | Every row gets usable/low/invalid | Show evidence table with no semaforo styling | Copernicus evidence viewer | Remote sensing engineer | Invalid rows produce risk |
| 2 Hydro-Sedimentary Screening | Confidence state exists | Risk state only appears for valid evidence | Fallback to Satellite Confidence Semaforo | Confidence-only MVP | Remote sensing engineer | NDTI is treated as chemistry |
| 3 Agricultural Decision Brief | Risk/confidence state exists | Brief gives cautious action support | Confidence Brief without risk state | Operator-facing brief | Product lead | Recommendation implies obligation |
| 4 Risk Explainability Panel | Rules are defined | Panel explains state with metrics | Static explanation box | Auditable confidence app | UX lead | Jury cannot trace state |
| 5 Multi-AOI Decision Mode | Single-AOI flow stable | broad/corridor_wide/river comparison works | Use corridor_wide only | Single-node AgroShield | Product lead | AOI comparison confuses primary decision |
| 6 Evidence Packet Export | Brief and evidence table work | Export preview/copy block works | On-screen evidence only | Demo app with manual citation | Technical lead | Export looks like final compliance report |
| 7 Optional Live Refresh | Cache demo works | One date/index refresh succeeds | Cache-only mode | Fully demoable cached MVP | Technical lead | CDSE rate limit or auth issue |
| 8 AI BriefWriter | Deterministic brief exists | AI text matches structured input | Local templates | Non-AI Confidence Brief | AI lead | AI invents risk or evidence |
| 9 AI Claim Firewall | Text outputs exist | Unsafe claims blocked and replaced | Disable AI; templates only | Safe non-AI app | Auditor | Blocked claims not caught |
| 10 Prediction Ledger | Risk states and dates exist | Ledger records expected next check | Static "next observation" note | Trust-aware brief | Product lead | It becomes guaranteed prediction |
| 11 Food Security Impact Layer | MVP core stable | Impact note is sober and tied to decision support | Positioning text only | Core MVP | Product lead | It implies food safety certification |
| 12 Regional Replication Pack | Azuero flow works | Config checklist works | Single-node story | Azuero MVP | Technical lead | It claims regional deployment complete |
| 13 Controlled Community Verification | Partner concept is defined | Verification protocol is shown | "Field verification recommended" note | Evidence-only app | Product lead | Fake field validation is suggested |
| 14 Sentinel-1 Cloud-Resilience Layer | Core app complete | S1 roadmap or tiny prototype is isolated | S2-only app | Core MVP | Remote sensing engineer | S1 delays core delivery |
| 15 Institutional Policy Brief Mode | Claim Firewall stable | Policy brief remains limited | Jury/technical brief only | Operator MVP | Auditor | It becomes legal advice |
| 16 Crop Corridor Overlay | AOI mode stable | Crop layer is clearly contextual | AOI-only mode | Semaforo MVP | Remote sensing engineer | Crop data is unverified |
| 17 Water Productivity / Irrigation Stress Roadmap | Core scientific limits accepted | Roadmap is separated from MVP | Remove section | MVP remains intact | Product lead | ERA5/CHIRPS enters core too early |
| 18 Anticipatory Action Trigger Design | Ledger and verification loop exist | Trigger design requires human review | Ledger only | Trust MVP | Auditor | It implies automatic closure |
| 19 Resilience Scorecard | Multiple observations exist | Scorecard is clearly exploratory | Date-level brief | Core MVP | Product lead | Score hides uncertainty |
| 20 Production Architecture Roadmap | MVP demo works | Architecture is future plan only | Local-only MVP | Hackathon demo | Technical lead | Team starts building production AWS |

## Critical Fallback Rules

- If Phase 2 does not show interpretable hydro-sedimentary signal, fallback to Satellite Confidence Semaforo.
- If Phase 3 only produces "do not infer", convert it into a Confidence Brief without aggressive risk state.
- If AI fails, use local templates.
- If CDSE live refresh fails, use cache.
- If river AOI fails, use `corridor_wide AOI` as operational primary.
- If rate limit occurs, stop and use cache.
- If eligibility becomes uncertain, cut the feature.
