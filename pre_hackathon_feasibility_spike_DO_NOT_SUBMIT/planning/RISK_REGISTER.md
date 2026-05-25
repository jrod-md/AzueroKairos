# Risk Register

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

| Risk | Probability | Impact | Mitigation | Fallback | Owner |
|---|---:|---:|---|---|---|
| Eligibility risk | Medium | Very high | Fresh official repo/code during competition; keep planning separate | Cut any questionable asset | Eligibility auditor |
| Rate limit | High | Medium | Cache-first; max one live refresh; sleep/backoff | Cache-only demo | Technical lead |
| Cloud cover | High | Medium | Catalog-confirmed dates; confidence labels | Show do not infer | Remote sensing engineer |
| AOI too narrow | Medium | Medium | Use `corridor_wide` primary; river as zoom | corridor_wide only | Remote sensing engineer |
| Weak NDTI signal | Medium | High | Treat NDTI as exploratory proxy; compare baseline carefully | Confidence Semaforo only | Remote sensing engineer |
| UI not ready | Medium | High | Build phases 0-4 first; avoid style rabbit holes | Evidence table + brief | UX lead |
| AI hallucination | Medium | High | AI communication-only; Claim Firewall; templates | Disable AI | AI lead |
| Overengineering | High | High | Stop after first working demo; postpone roadmap | Core phases only | Product lead |
| Competitors with polished demos | Medium | Medium | Differentiate with evidence confidence and claim discipline | Strong 3-minute story | Product strategist |
| Live demo failure | High | Medium | Cache-first demo; live refresh optional | Cached mode | Technical lead |
| Secret leakage | Low | Very high | `.env` ignored; no printing secrets; no logs | Rotate keys; remove file | Security owner |
| Scope creep | High | High | Scope lock; phase gates | Cut to phases 0-4 | Product lead |

## Highest-Risk Combination

Cloud cover + weak NDTI + overclaiming. The defense is simple: confidence first, risk second, do not infer when evidence is weak.
