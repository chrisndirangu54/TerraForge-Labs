# TERRAFORGE LABS — Phase 4 Agent Brief Expanded

Version **4.0-EX** expands TerraForge into a Pan-African sovereign geoscience intelligence platform for Year 2, covering **Weeks 53–104**. The build adds hydrogeology, urban planning and settlements, infrastructure, a complete 2D/3D/satellite mapping stack, React web app, Flutter mobile app, and public API.

## Phase 4 prerequisites

- All Phase 3 Definition of Done checks pass in CI.
- At least 10 paying customers across all tiers.
- At least one signed institutional partner: geological survey, DFI, or university.
- MRR at or above $15,000.
- Kenya legal entity and IP protection established.
- Team hired: backend engineer, geoscientist, and business development lead.
- Country expansion legal review completed for first three target countries.

Scope note: Track M must be prioritised first because hydrogeology, urban planning, infrastructure, satellite feeds, geobotany, and sovereign intelligence all render through the mapping layer.

## Full Phase 4 track map

| Track | Feature | Weeks | Priority |
| --- | --- | --- | --- |
| A | Real-time satellite feeds: Sentinel-2, SAR, GRACE, thermal | 53–60 | CRITICAL |
| B | Isotope geochemistry | 53–62 | CRITICAL |
| C | Carbon Capture & Storage site assessment | 55–65 | CRITICAL |
| D | Pan-African federated nodes across 10 countries | 57–72 | CRITICAL |
| E | EPMA and microprobe integration | 57–65 | HIGH |
| F | Full 3D seismic reflection processing | 60–72 | HIGH |
| G | Quantum sensing integration | 65–78 | HIGH |
| H | Digital twin geological environment + TimescaleDB | 68–82 | HIGH |
| I | Public API and developer platform | 53–62 | MEDIUM |
| J | Automated resource estimation + NPV/IRR | 70–85 | MEDIUM |
| K | AR/VR field geology interface | 75–90 | MEDIUM |
| L | Sovereign geological intelligence + illegal mining detection | 80–104 | LONG |
| M | Complete mapping stack: 2D/3D/satellite, web + mobile | 53–65 | CRITICAL |
| N | Hydrogeology groundwater modelling platform | 57–70 | CRITICAL |
| O | Urban planning, settlements, and land use | 62–78 | HIGH |
| P | Infrastructure: roads, utilities, pipelines, grid | 68–85 | HIGH |
| Q | Geobotany and biogeochemistry | 62–80 | HIGH |

## Track M — Complete mapping stack

Open source remains the default map strategy:

- **2D vector maps:** MapLibre GL JS with OpenFreeMap and Martin MVT from PostGIS.
- **Satellite:** Sentinel-2 for weekly project imagery and ESRI/Google only where premium imagery is explicitly enabled.
- **3D:** CesiumJS with GemPy OBJ → glTF → 3D Tiles conversion.
- **Mobile:** MapLibre Native with PMTiles offline packs.
- **Geocoding/routing:** Nominatim/Photon and OSRM/Valhalla by default.
- **Google Maps:** optional paid tier for high-resolution urban satellite and photorealistic 3D.

The scaffold exposes tile, offline pack, Sentinel-2 basemap, layer catalogue, map-provider plan, and Cesium tileset endpoints. It also documents all geological, hydrogeological, urban, infrastructure, environmental, and satellite layer groups.

## Track N — Hydrogeology

Hydrogeology adds groundwater modelling, borehole siting, water quality compliance, MODFLOW/FloPy model construction, and WRMA/NEMA-ready reporting. The data pipeline supports YSI, Solinst Levelogger, Hach, pumping-test, flow-meter, rain-gauge, soil-moisture, EC, and Terrameter aquifer-imaging workflows.

Implemented scaffold capabilities:

- Slug-test hydraulic conductivity and transmissivity estimate.
- Pumping-test Theis/Cooper-Jacob contract with minimum datapoint validation.
- WHO and Kenya NEMA water-quality compliance flags, including Rift Valley fluoride.
- MODFLOW 6 model-run contract with recharge, GHB, pumping wells, and ET boundary conditions.
- Borehole siting report stub with expected yield and success probability.

## Track O — Urban planning, settlements, and land use

Urban planning uses OSM, Microsoft footprints, GHSL, WorldPop, Kenya census boundaries, ESA WorldCover, Sentinel-2 NDVI, and geology/hydrogeology constraints. The scaffold includes settlement classification, population estimation, service access, development suitability, and mining-settlement conflict checks.

County planner dashboard requirements include ward-level population, settlement risk, service gaps, land-use alerts, mining licence overlays, infrastructure condition, and water quality status.

## Track P — Infrastructure

Infrastructure modules cover road access, grid proximity, least-cost pipeline routing, telecoms/Starlink availability, logistics cost, and mining infrastructure assessment. Layers include roads, power grid, water pipelines, telecom towers, grid coverage, infrastructure gap zones, optimal routes, haulage routes, and InSAR deformation alerts.

## Complete app architecture

### Web app

A React 18 + TypeScript + Vite shell is scaffolded under `apps/web/`, with route metadata for Dashboard, Map, Projects, Upload, Kriging, Deposit, Hydrogeology, Urban, Infrastructure, Satellite, Reports, Marketplace, Digital Twin, AR, Settings, and Admin. Map dependencies are documented in `package.json`: MapLibre, Cesium, deck.gl, Turf, TanStack Query, Zustand, PMTiles, Recharts, Tailwind, and shadcn-related utilities.

### Flutter mobile app

The mobile shell now includes Phase 4 routes and dependencies for MapLibre, PMTiles, GoRouter, WebView Cesium, background sync, secure storage, and Google sign-in. New screen scaffolds cover main map, 3D map, hydrogeology, urban, infrastructure, satellite, digital twin, and offline manager workflows while preserving the existing field capture, classifier, kriging, geobotany, and reporting screens.

## Shared Phase 4 API surface

- Mapping: `/tiles/{z}/{x}/{y}`, `/tiles/offline/{region}`, `/basemap/sentinel2`, `/mapping/layers`, `/mapping/provider-plan`, `/mapping/cesium-tileset`.
- Hydrogeology: `/hydro/slug-test`, `/hydro/pump-test`, `/hydro/water-quality`, `/hydro/modflow`, `/hydro/borehole-siting`, `/hydro/groundwater-table`, `/hydro/boreholes`.
- Urban: `/urban/classify-settlement`, `/urban/service-access`, `/urban/suitability`, `/urban/conflict-check`, `/urban/settlements`, `/urban/land-use`, `/urban/population`.
- Infrastructure: `/infra/route`, `/infra/pipeline-route`, `/infra/mining-assessment`, `/infra/roads`, `/infra/power-grid`, `/infra/telecoms`.
- Satellite: `/satellite/scenes`, `/satellite/latest`, `/satellite/change-detect`, `/satellite/insar`.

## Phase 4 budget and target

The Phase 4 scaffold tracks a Year 2 budget target near **$400,085**: roughly $74,900 instruments, $120,000 infrastructure/operations, $68,000 team, $30,000 legal/IP, $55,000 marketing/GTM, and 15% contingency. Revenue target remains **$1M ARR by Month 24**, driven by enterprise, corporate, professional, API, marketplace, and county-planning contracts.

## Definition of Done summary

- Track M: MapLibre 2D, CesiumJS 3D, PMTiles offline, Google paid-tier toggles, Martin MVT target, and all map layers.
- Track N: MODFLOW model, pump/slug tests, WRMA/NEMA reports, water-table layers.
- Track O: settlement classifier, county dashboard, conflict detection, 47-county filtering.
- Track P: OSRM route, pipeline least-cost routing, mining infrastructure assessment, infrastructure layers.
- Platform: ≥10 active country nodes, ≥70% Phase 4 coverage, Flutter/web checks, no committed credentials, and MRR on track for $1M ARR.
