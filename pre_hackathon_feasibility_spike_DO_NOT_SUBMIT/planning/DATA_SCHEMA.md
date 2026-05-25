# Data Schema

PRE-HACKATHON PLANNING / DO NOT SUBMIT.

## Raw CDSE Response Reference

```json
{
  "raw_response_id": "string",
  "source_mode": "cache|live",
  "raw_path": "string",
  "payload_path": "string",
  "cdse_endpoint": "statistics|catalog",
  "aoi_label": "corridor_wide",
  "date": "YYYY-MM-DD",
  "index": "mndwi|ndti",
  "resolution_meters": 20,
  "generated_at": "ISO-8601",
  "algorithm_version": "agroshield-mvp-v1",
  "limitations": ["not chemical detection", "not field validated"]
}
```

## Processed Observation Row

```json
{
  "date": "YYYY-MM-DD",
  "datetime": "ISO-8601",
  "aoi_label": "corridor_wide",
  "aoi_type": "agricultural_riparian_corridor",
  "index": "combined",
  "mndwi_mean": -0.45,
  "mndwi_stdev": 0.13,
  "ndti_mean": 0.05,
  "ndti_stdev": 0.11,
  "sampleCount": 108832,
  "noDataCount": 46909,
  "validPercent": 56.9,
  "confidence_state": "usable",
  "risk_state": "watch",
  "recommendation_code": "LOCAL_REVIEW_RECOMMENDED",
  "explanation_rules": ["validPercent >= 30", "NDTI shift reviewed against baseline"],
  "source_mode": "cache",
  "cdse_item_id": "S2x_MSIL2A_...",
  "generated_at": "ISO-8601",
  "algorithm_version": "agroshield-mvp-v1",
  "limitations": ["No chemical detection", "No crisis validation"]
}
```

## AOI Metadata

```json
{
  "aoi_label": "corridor_wide",
  "aoi_type": "agricultural_riparian_corridor",
  "display_name": "Rio La Villa agricultural-riparian corridor",
  "source_crs": "CRS84/lonlat",
  "processing_crs": "EPSG:32617",
  "geometry_path": "data/aoi_chitre_corridor_wide.geojson",
  "is_primary": true,
  "is_validated": false,
  "limitations": ["Approximate AOI", "Not final hydrologic boundary"]
}
```

## Confidence State

```json
{
  "confidence_state": "usable|low_confidence|invalid",
  "validPercent": 56.9,
  "sampleCount": 108832,
  "noDataCount": 46909,
  "rules": [
    "validPercent < 10 => invalid",
    "10 <= validPercent < 30 => low_confidence",
    "validPercent >= 30 => usable"
  ],
  "do_not_infer": false
}
```

## Risk State

```json
{
  "risk_state": "normal|watch|review|do_not_infer",
  "recommendation_code": "NO_ACTION|WATCH_NEXT_ACQUISITION|LOCAL_REVIEW_RECOMMENDED|DO_NOT_INFER",
  "basis": ["mndwi_mean", "ndti_mean", "baseline_comparison", "confidence_state"],
  "limitations": ["Exploratory hydro-sedimentary screening only"]
}
```

## AI Brief Input JSON

```json
{
  "audience": "producer|technical_operator|jury|institutional_policy",
  "date": "YYYY-MM-DD",
  "aoi_label": "corridor_wide",
  "confidence_state": "usable",
  "risk_state": "watch",
  "recommendation_code": "LOCAL_REVIEW_RECOMMENDED",
  "mndwi_mean": -0.45,
  "ndti_mean": 0.05,
  "validPercent": 56.9,
  "explanation_rules": ["validPercent >= 30"],
  "limitations": ["not chemical detection", "not laboratory replacement"]
}
```

## AI Brief Output JSON

```json
{
  "audience": "producer",
  "brief_text": "string",
  "claim_firewall_status": "passed|blocked_replaced",
  "blocked_claims": [],
  "generated_by": "template|gemini|openrouter",
  "generated_at": "ISO-8601"
}
```

## Prediction Ledger Row

```json
{
  "ledger_id": "string",
  "date": "YYYY-MM-DD",
  "aoi_label": "corridor_wide",
  "risk_state": "watch",
  "expected_next_state": "watch_or_review_if_signal_persists",
  "next_observation_date": "YYYY-MM-DD",
  "actual_next_state": "pending|normal|watch|review|do_not_infer",
  "ledger_status": "pending|consistent|contradicted|insufficient_evidence",
  "limitations": ["not guaranteed prediction"]
}
```

## Export Brief Metadata

```json
{
  "brief_id": "string",
  "date": "YYYY-MM-DD",
  "aoi_label": "corridor_wide",
  "source_mode": "cache|live",
  "cdse_item_id": "string",
  "algorithm_version": "agroshield-mvp-v1",
  "generated_at": "ISO-8601",
  "limitations": [
    "Decision support, not laboratory replacement",
    "Not chemical detection",
    "Field verification recommended when risk_state=review"
  ]
}
```
