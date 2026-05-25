# Master Roadmap v3

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

## Executive Framing

Azuero AgroShield should be built as a decision-support product, not a generic dashboard and not a chemical detector. The defensible product is a **Satellite Confidence Semaforo** plus **Hydro-sedimentary exploratory screening** for the agricultural-riparian corridor around Rio La Villa.

The project should continue: **GO TECHNICAL / ADJUST SCIENTIFIC**. The technical kernel works; the scientific claim must remain cautious.

## Why This Matters For Food Security

Agricultural decisions around irrigation and food safety often happen with incomplete evidence. Copernicus cannot replace field sampling or laboratory analysis, but it can reduce blind decisions by identifying whether satellite evidence is usable, low-confidence, or invalid for a given acquisition. The value is not "automatic truth"; the value is disciplined evidence triage.

## What The Spike Proved

- CDSE authentication works.
- Sentinel Hub / CDSE Statistical API works.
- Catalog API works.
- CRS84/lonlat to EPSG:32617 reprojection works.
- Sentinel-2 L2A MNDWI and NDTI return statistics.
- Broad AOI returns data but likely dilutes river signal.
- River AOI returns data but has fewer usable dates.
- `corridor_wide AOI` is currently the most defensible primary AOI hypothesis.
- Cache-first operation is necessary for rate limits.

## What The Spike Did Not Prove

- It did not validate the June 2025 crisis.
- It did not detect atrazine, pesticides, chemicals, metals, pathogens, or complete water quality.
- It did not prove an operational irrigation decision system.
- It did not prove real-time operation.

## Product Thesis

AgroShield wins if it is a trust product: it tells the operator when to trust, when to review, and when to **do not infer** from Copernicus evidence. The MVP should show a compact, serious workflow that a producer association or institution could understand and pilot.

## Phase Ladder

| Phase | Objective | What gets built | Input | Visible output | Success criterion | Fallback | Do NOT | Risk | Pitch demo | Size | Dependencies | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 Evidence Kernel | Rebuild official data kernel from zero | Fresh auth, catalog loader, cache loader, schema | Official env vars, AOIs, dates | Processed CSV | Cached rows load and one safe live refresh can run | Cache-only demo | Copy spike code | Eligibility/secrets | Show reproducible Copernicus-derived table | M | None | MVP core |
| 1 Satellite Confidence Semaforo | Classify evidence trust | Confidence rules and badge | validPercent, noDataCount, sampleCount | usable/low/invalid state | Invalid data never produces risk claim | Data access demo | Risk before confidence | Weak UX | Toggle dates and show confidence | S | 0 | MVP core |
| 2 Hydro-Sedimentary Screening | Add cautious risk interpretation | MNDWI/NDTI comparison rules | MNDWI/NDTI stats | risk state | Risk only shown when confidence allows | Confidence-only product | Claim chemicals/crisis | Weak NDTI | Show normal/watch/review/do not infer | M | 0,1 | MVP core |
| 3 Agricultural Decision Brief | Translate state into action support | Brief card with recommendation code | confidence + risk | AgroShield Confidence Brief | Recommendations are cautious and local-verification oriented | Confidence Brief only | Mandatory action | Overclaiming | Read one brief | S | 1,2 | MVP core |
| 4 Risk Explainability Panel | Explain why the state happened | Rules panel, evidence table | metrics + thresholds | "Why this state?" | Jury can audit every decision | Static explanation text | Hide uncertainty | Q&A failure | Expand explanation | M | 1,2,3 | MVP core |
| 5 Multi-AOI Decision Mode | Compare broad/corridor/river | AOI tabs and comparison table | AOI rows | AOI comparison | corridor_wide primary remains clear | Single AOI mode | Confuse user | UI clutter | Switch AOIs | M | 0-4 | Strong demo |
| 6 Evidence Packet Export | Package one date decision | Simple export metadata / copy block | selected row | Evidence packet preview | User can cite inputs/limits | On-screen brief only | Compliance PDF | Time sink | Export placeholder | S | 0-4 | Strong demo |
| 7 Optional Live Refresh | Demonstrate live Copernicus connection | One date/index refresh | CDSE quota | cache/live indicator | Works once without rate-limit | Cache-only mode | Repeated live calls | 429 | Press refresh once | M | 0 | Stretch |
| 8 AI BriefWriter | Translate structured row by audience | Provider-agnostic text module | structured JSON | audience brief | AI output passes firewall | Local templates | AI decides risk | Hallucination | Compare producer/jury text | M | 3,9 | AI maturity |
| 9 AI Claim Firewall | Block unsafe language | Deterministic validator | AI/template text | safe text or fallback | Forbidden claims blocked | Use safe templates | Trust AI alone | Unsafe output | Show blocked example | M | 3,8 | AI maturity |
| 10 Prediction Ledger | Track expectations vs later evidence | Simple ledger table | date/risk/next check | ledger row | Later observations can update status | Static caveat | Guaranteed prediction | Overclaiming | Show ledger entry | M | 1-4 | Trust differentiator |
| 11 Food Security Impact Layer | Tie output to food-security relevance | Impact copy + categories | user type + state | impact note | No operational overclaim | Product positioning only | Claim safety | Policy pushback | Show impact card | S | 3,4 | Roadmap |
| 12 Regional Replication Pack | Show ALC scalability | AOI/config template | node metadata | replication checklist | Another basin can be configured conceptually | Azuero-only MVP | Claim 52 nodes done | Scope creep | Show config schema | M | 0-6 | Regional scalability |
| 13 Controlled Community Verification | Define local validation loop | Verification protocol design | field partner concept | verification checklist | Local observation can be logged | Desk-only workflow | Fake field data | Partner gap | Show verification card | L | 10,12 | Roadmap |
| 14 Sentinel-1 Cloud-Resilience Layer | Add cloud-resilient EO path | S1 roadmap / optional prototype | S1 GRD | cloud fallback concept | Only after core stable | S2-only | Force S1 | Complexity | Roadmap slide | L | 0-4 | Roadmap |
| 15 Institutional Policy Brief Mode | Translate outputs for institutions | Policy audience template | selected evidence | policy brief view | Limits remain visible | Jury brief only | Legal claims | Misuse | Show policy text | M | 8,9 | Roadmap |
| 16 Crop Corridor Overlay | Add crop/ag corridor context | Crop/corridor layer spec | external crop data | corridor overlay | Does not imply farm-level truth | AOI-only | Farm claims | Data gap | Show mock layer plan | L | 12 | Roadmap |
| 17 Water Productivity / Irrigation Stress Roadmap | Connect to future irrigation analytics | roadmap only | future ET/water data | roadmap section | No MVP dependency | Postpone | Add ERA5/CHIRPS now | Overbuild | Explain future | L | 11,16 | Roadmap |
| 18 Anticipatory Action Trigger Design | Design trigger governance | trigger spec | confidence/risk history | trigger design | Trigger requires human verification | Ledger only | Automatic closure | Liability | Explain governance | L | 10,13 | Roadmap |
| 19 Resilience Scorecard | Summarize node resilience over time | scorecard concept | multiple dates | scorecard mock | Score has caveats | Date-level brief | Simplistic score | Trust risk | Show roadmap | M | 10-13 | Roadmap |
| 20 Production Architecture Roadmap | Show path to real service | architecture plan | MVP learnings | roadmap diagram | No production claim | Local app only | Build AWS now | Time sink | Explain next steps | M | all core | Post-hackathon |

## Recommended Build Order

Build 0, 1, 2, 3, 4 first. Phase 4 must come before Multi-AOI because it protects the Q&A: the jury must see why the system gave a state. Then add 5 and 6 for a strong demo. Add 8 and 9 only after the deterministic product works. Add 10 if time allows as the trust differentiator.

## Winning Demo Shape

Others show maps; AgroShield shows whether the satellite evidence is trustworthy enough to support an agricultural decision.

The demo should move from one date to the confidence state, then to risk state, then to why the state happened, then to a confidence brief. It should work offline from cache. Optional live refresh is a bonus, not the core.

## What Not To Build

Do not build a generic dashboard, broad risk map, chemical detector, real-time monitor, operational alert tool, or automated agricultural decision system.

## How AI Is Used Safely

AI is communication-only. It does not calculate risk, choose states, change thresholds, or invent recommendations. It receives structured JSON, writes short audience-specific text, and must pass the Claim Firewall. If AI fails, local templates are used.

## How The Project Scales To ALC

The scalable unit is not a massive map. The scalable unit is a configured **Confidence Brief node**: AOI, catalog dates, indices, thresholds, evidence table, limitations, and local verification loop. That can later replicate to other agricultural river corridors in ALC.

## Final Recommended MVP Definition

A fresh official app that reads cached Copernicus-derived outputs for `corridor_wide AOI`, computes confidence and exploratory hydro-sedimentary risk states, explains every state, generates a safe AgroShield Confidence Brief, and refuses to infer when evidence is insufficient.
