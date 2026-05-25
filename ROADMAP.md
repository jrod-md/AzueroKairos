# Roadmap

## Phase 0: Clean Repository Scaffold

- Establish the official hackathon repository structure.
- Document scientific limits and originality boundaries.
- Add AOI and date configuration placeholders.
- Keep output folders empty except for `.gitkeep` files.

## Phase 1: Reproducible Data Inputs

- Validate official AOI geometry files.
- Confirm official analysis dates from hackathon requirements.
- Add deterministic Sentinel data acquisition scripts.
- Store raw API responses in `outputs/raw_json/`.

## Phase 2: Confidence Classification

- Convert Sentinel observations into processed tabular evidence.
- Classify each observation as `usable`, `low_confidence`, or `do_not_infer`.
- Preserve evidence thresholds and reasons in the ledger.

## Phase 3: Confidence Briefs

- Generate one Confidence Brief per official observation batch.
- Include decision state, evidence summary, limits, and recommended next action.
- Save generated briefs in `outputs/briefs/`.

## Phase 4: Minimal Dashboard

- Display AOI, date batch, decision states, and brief summaries.
- Avoid contamination, pesticide, pathogen, heavy-metal, or safe-water claims.
- Keep dashboard behavior reproducible from official outputs.

## Explicitly Deferred

- Cloud infrastructure.
- AWS deployment.
- Twilio or SMS notifications.
- Production authentication.
- Automated operational alerts.
