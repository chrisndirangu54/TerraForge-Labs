# TERRAFORGE LABS — Track Q: Geobotany & Biogeochemistry

Track Q is a Phase 4 addendum for **Plant Indicator Mapping**, **Biogeochemical Sampling**, **Hyperspectral Vegetation Stress**, **Species AI Classification**, and **Active Learning Field Survey**. It inserts between Track P (Infrastructure) and the existing Tracks A–L, running during **Weeks 62–80** in parallel with Tracks O and P.

## Strategic context

East Africa has globally important copper indicator plant flora. Species such as `Ocimum centraliafricanum` (copper flower) and `Haumaniastrum` are treated as high-value metallophyte indicators. TerraForge can integrate geobotany with geophysics, geochemistry, hyperspectral imagery, and compliance reporting in one offline-first model.

## Dependencies and data sources

- **Dependencies:** Track A Sentinel-2, Track M mapping stack, Phase 2 Track A hyperspectral Pika L + drone.
- **New instruments:** external plant tissue ICP-MS service and field portable chlorophyll meter.
- **Open data:** GBIF, iNaturalist, East African Plants Database, and USGS Spectral Library.
- **Budget target:** approximately **$25,530**, mostly Year 1 ICP-MS lab work, with satellite/software data sources free and hyperspectral drone hardware already covered by Phase 2.

## Why geobotany belongs in TerraForge

Geobotany uses plant distribution and plant chemistry to infer subsurface mineralisation. The current exploration workflow is mostly paper maps, botanical keys, and local knowledge that rarely reaches exploration software. TerraForge already has the enabling pieces: Sentinel-2 red-edge bands, Resonon Pika L hyperspectral data, XRF geochemistry, mobile field capture, and GBIF/iNaturalist-style occurrence infrastructure.

Commercially, Track Q gives junior explorers a low-cost way to map vegetation stress, indicator species, and plant-tissue chemistry. It also supports environmental baseline surveys required for Kenyan EIAs and allows indigenous plant-mineral knowledge to be recorded with attribution.

## Three scientific methods

| Method | TerraForge implementation | Notes |
| --- | --- | --- |
| Indicator plant mapping | Mobile photo classifier returns species, confidence, mineral affinity, and recommended action. | Strong for obligate indicators such as copper flower. |
| Plant appearance and physiology | Sentinel-2/Pika L vegetation indices identify chlorosis, stunting, pigment shifts, and red-edge movement. | Medium certainty; drought, disease, shade, and disturbance can confound results. |
| Biogeochemical sampling | Plant tissue ICP-MS is ingested, BCF is calculated, and anomaly surfaces can be kriged. | Quantitative and cross-calibrated to XRF soil data. |

## Key indicator species scaffolded

The classifier and affinity table include copper, cobalt, nickel/serpentine, geothermal/lithological, Pb/Zn, gold-pathfinder, salinity, and negative-indicator classes, including:

- `ocimum_centraliafricanum` — Cu VERY_HIGH, Ni HIGH.
- `haumaniastrum_katangense` — Cu HIGH, Co MEDIUM.
- `silene_cobalticola` — Co VERY_HIGH.
- `senecio_coronatus` — Ni HIGH, Cr MEDIUM.
- `gypsophila_patrinii` — B MEDIUM, Li MEDIUM.
- `panicum_maximum` — negative low-fertility/disturbance indicator.

The Kendege/Kehancha-style field observation workflow is represented as georeferenced plant observations collected alongside XRF and structural measurements.

## Architecture

### Q1 — Plant species classifier

- EfficientNet-B0 training scaffold using iNaturalist, GBIF, East African Plants Database, and consented TerraForge field photos.
- INT8 TFLite mobile asset placeholder for `assets/models/geobotany_classifier_int8.tflite`.
- Target metrics: top-1 ≥ 75%, top-3 ≥ 90%, model < 8 MB, Android inference < 400 ms.
- Mineral affinity lookup and confidence threshold of 0.65.

### Q2 — Vegetation stress mapping

- Sentinel-2 indices: NDVI, EVI, NDRE, CRE, and MCARI.
- Hyperspectral indices: Cu-SRI, NPCI, SIPI, red-edge position, red-edge blueshift, and VII.
- Thresholds: stress z-score ≥ 2.0, NDVI vegetation mask ≥ 0.20, minimum stress zone area 300 m², VII metal stress threshold 0.85.

### Q3 — Biogeochemical sampling

- ICP-MS CSV ingestion requires `species_name` and `plant_part`.
- Calculates BCF and transfer coefficient.
- BCF ≥ 5 is treated as a strong geobotanical signal; BCF ≥ 10 as hyperaccumulator behaviour.
- Plant-to-soil join radius defaults to 50 m.

### Q4 — Geobotanical anomaly engine

Composite score inputs are vegetation stress, indicator species presence, biogeochemical anomaly, species richness anomaly, and historical GBIF/iNaturalist records. Default weights are 0.25, 0.30, 0.30, 0.05, and 0.10 respectively. Strong anomalies are scores ≥ 80, moderate anomalies are scores ≥ 60.

### Q5 — Active learning field survey

- Mobile survey logs species, GPS, vigour, leaf colour, density, local names, and local significance.
- A nightly retrain trigger activates when at least 10 geologist-confirmed labels are available.
- Model versions remain auditable so observations can be traced to the classifier version that produced them.
- Local names/significance fields support indigenous knowledge capture and attribution.

## API endpoints

- `POST /geobotany/classify-plant`
- `POST /geobotany/log-observation`
- `POST /geobotany/stress-map`
- `POST /geobotany/biogeochem-upload`
- `GET /geobotany/anomaly-map`
- `GET /geobotany/indicator-species`
- `POST /geobotany/survey-plan`

## JORC integration

When geobotany payload data is present, TerraForge generates supplementary JORC Section 1 sampling-techniques language and Section 2 geology language. Reports include a required disclaimer that geobotanical results supplement, rather than replace, primary geochemistry and geophysics and that all anomalies require conventional geochemical confirmation.

## Definition of Done summary

- Q1 classifier targets met and Flutter screen can identify copper flower test images.
- Q2 Sentinel-2 and hyperspectral stress indices render as map layers and flag z-score anomalies.
- Q3 ICP-MS parser, BCF calculation, plant-soil joins, and lab submission workflow work on synthetic data.
- Q4 composite anomaly score, calibration report, and geobotanical inference blocks are generated.
- Q5 observation logging, active-learning retraining, model deployment, and indigenous knowledge fields are auditable.
- JORC geobotany text and disclaimers are always present when geobotany-informed reporting is used.
