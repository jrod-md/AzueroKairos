# Technical Ceiling Report

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.

Executive decision: GO TECHNICAL / ADJUST SCIENTIFIC

## What is technically proven

- CDSE authentication, Statistical API access, EPSG:32617 reprojection, caching, and resumable matrix execution are technically testable in this spike.
- Returned Sentinel-2 L2A MNDWI/NDTI statistics can be summarized with explicit valid-pixel confidence labels when API/cache rows exist.

## What is not proven

- June 2025 crisis validation is not proven.
- Chemical, pesticide, pathogen, metal, dissolved contaminant, or complete water-quality detection is not proven.
- Agricultural operational decisions are not proven.

## AOI assessment

Best AOI by usable date count: broad (4 usable rows, 2 usable dates).

Best AOI by scientific defensibility: corridor_wide: best balance between signal coverage and hydrologic/riparian defensibility.

June 2025 crisis validated: No.

## Rate limit implications

rate_limit_stop=false

CDSE rate limits require cache-first runs, small batches, sleeps between non-cached requests, and at most one live refresh pattern in any future MVP.

## Recommended product shape

Satellite confidence semaforo; hydro-sedimentary exploratory semaforo remains possible after stronger temporal contrast.

## Allowed claims

- Sentinel-2 L2A can return exploratory MNDWI/NDTI statistics over tested AOIs.
- Outputs can support a satellite confidence semaforo with explicit uncertainty if enough usable rows exist.
- Language should remain: señal satelital exploratoria asociada a riesgo hidro-sedimentario observable.

## Forbidden claims

- Do not claim validated crisis detection.
- Do not claim pesticide, atrazine, pathogen, metal, dissolved chemical, or complete water-quality detection.
- Do not claim irrigation shutdown, intake closure, or agricultural operational decision authority.

## Next 3 technical actions

1. Run corridor_wide in small cached batches around June dates and compare against broad/river.
2. Tighten catalog-date selection around low-cloud acquisitions and explicitly separate cloudy dates from signal dates.
3. If corridor_wide improves usable rows, regenerate all official work from zero during the competition window.
