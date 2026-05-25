# Technical Errors

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.

Append API, authentication, AOI, rate-limit, and processing-unit failures here. Do not hide failed dates.

## 2026-05-13 Local Setup Check

Auth: FAIL/SKIPPED - CDSE_CLIENT_ID and CDSE_CLIENT_SECRET were not present in the environment. No Statistical API request was attempted, and no scientific result was inferred.

## 2026-05-13 Resolution Patch

Previous failure reason: Statistical API payload used numeric `resx`/`resy` with an EPSG:4326 AOI, producing an invalid meters-per-pixel request such as `6451.12 meters per pixel`, above the S2L2A limit of `1500.00 meters per pixel`.

Superseded patch attempt: `resx: "20m"` and `resy: "20m"` were rejected by CDSE with `COMMON_BAD_PAYLOAD`, parameter `aggregation->resx`, invalid value `"20m"`.

Current patch: `src/stats_request.py` keeps the CLI value as user-facing meters but sends numeric payload values, defaulting to `resx: 20` and `resy: 20`. `src/run_single_date.py` and `src/run_date_batch.py` accept `--resolution-meters`, default `20`, and print `user_resolution_meters`, `payload_resx`, and `payload_resy`.

Payload handling: sanitized request payloads are now saved before every Statistical API request as `outputs/raw/request_payload_<index>_<date>_<resolution>m.json`.

Current patched request status in this Codex run: not confirmed against CDSE because `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET` were not present in this process environment. `python src/auth_cdse.py` returned `Auth: FAIL` for missing local environment variables.

Existing raw files from the previous attempt show `data: []` for `mndwi_2025-06-11_raw.json` and `ndti_2025-06-11_raw.json`, but those files came from the old numeric-resolution payload and must not be used for a pivot decision.

Next recommended action: run the requested 20m single-date MNDWI/NDTI commands with CDSE credentials available. If 20m returns usable JSON, test 10m. If patched 20m still returns `data: []`, run the same command with `data/aoi_chitre_la_arena_wide_test.geojson`, then test multiple dates before deciding GO, ADJUST AOI, or PIVOT.

## 2026-05-13 UTM Reprojection Patch

Root cause refinement: numeric `resx`/`resy` are valid for the Statistical API only when the AOI geometry CRS is metric. The previous payload sent lon/lat degree coordinates with `resx: 20` and `resy: 20`, so CDSE interpreted the request as an excessively coarse meters-per-pixel request and rejected it with the S2L2A `1500.00 meters per pixel` limit.

Patch: `src/reproject_aoi.py` now validates source AOI coordinates as `[longitude, latitude]`, reprojects Polygon/MultiPolygon AOI geometry from CRS84/lonlat to EPSG:32617, and returns projected GeoJSON coordinates in meters. `src/stats_request.py` now sets `input.bounds.properties.crs` to `http://www.opengis.net/def/crs/EPSG/0/32617` and keeps numeric `aggregation.resx` / `aggregation.resy`.

Local validation: projected AOI bounds for `data/aoi_chitre_la_arena_approx.geojson` were `[558625.925, 878586.819, 564806.408, 885007.47]`; payload CRS was EPSG:32617; payload `resx` and `resy` were integer `20`.

CDSE execution status in this Codex process: not confirmed against CDSE because `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET` were not visible in this process environment. The requested `auth_cdse.py`, MNDWI single-date, and NDTI single-date commands failed locally before making Statistical API requests.

Next recommended action: rerun the requested 2025-06-11 MNDWI/NDTI commands in the credentialed environment. If patched EPSG:32617 requests succeed but return `data: []`, do not mark failure yet; test `--window-days 10` and then the wider AOI file.

## 2026-05-13 Catalog Validation Patch

Scientific-validation patch: added `src/catalog_search_s2.py` to query Sentinel Hub Catalog API for Sentinel-2 L2A acquisitions between 2025-05-01 and 2025-07-15, added `src/run_catalog_dates.py` to run MNDWI/NDTI on catalog-confirmed dates, and added `data/aoi_chitre_river_corridor_test.geojson` as an approximate narrow river-corridor AOI.

Local execution status in this Codex process: `python src/catalog_search_s2.py` failed before network/API because `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET` were not visible. `python src/run_catalog_dates.py --limit-dates 3` failed because `data/candidate_dates_from_catalog.csv` remains header-only until catalog search succeeds.

Existing broad-AOI raw outputs still demonstrate technical viability, but they are not enough for crisis validation. Next action in a credentialed environment: run catalog search, then run catalog-confirmed dates for both `broad_aoi` and `river_corridor_aoi`.

## 2026-05-13 Rate Limit Management Patch

Observed issue: `run_catalog_dates.py` can trigger CDSE Statistical API HTTP 429 `RATE_LIMIT_EXCEEDED` when it sends many requests across catalog dates, two indices, and multiple AOIs.

Interpretation: HTTP 429 is a request-management/rate-limit issue, not a Sentinel-2 availability failure and not a scientific failure.

Patch: `run_catalog_dates.py` now uses cache-first behavior for raw JSON outputs, defaults to at most 5 catalog dates per run, supports `--date-filter`, supports `--indices mndwi,ndti` or a single index, sleeps between live API requests, and stops gracefully after one 30-second retry if CDSE returns 429 again.

Next recommended action: run small batches, prefer cache hits, and split MNDWI/NDTI or AOIs into separate runs if CDSE throttles again.

## 2026-05-13 Corridor Wide AOI Patch

Technical-ceiling patch: added `data/aoi_chitre_corridor_wide_test.geojson` as an approximate agricultural-riparian corridor AOI. It is narrower than the broad Chitre/La Arena rectangle and wider than the narrow river-only AOI. It is not final geometry.

Runner patch: `run_catalog_dates.py` now accepts `--aoi label=path`, so corridor-wide batches can be run independently, for example `--aoi corridor_wide=data/aoi_chitre_corridor_wide_test.geojson`.

Local execution status in this Codex process: both requested corridor-wide MNDWI and NDTI commands stopped before CDSE because `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET` were not visible in this process environment. No corridor-wide scientific conclusion was inferred.
