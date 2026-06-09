# TERRAFORGE LABS — Phase 4 Gap Closure Addendum

This addendum captures the genuine commercial gaps identified after the four-phase scaffold review. It adds commercially immediate workflows that make TerraForge more defensible for junior exploration, JORC reporting, county-government flood risk, and investor diligence.

## Priority order

1. **Drill planning optimiser** — answers the next commercial question after modelling: where should the next metre be drilled to reduce uncertainty per dollar.
2. **Sample management / lightweight LIMS** — tracks field samples through preparation, dispatch, lab receipt, assay, validation, and chain-of-custody audit.
3. **QA/QC geochemistry** — analyses standards, blanks, and duplicates for JORC defensibility and AmCham/investor credibility.
4. **Flood inundation modelling** — opens county-government, infrastructure, mining EIA, and humanitarian planning markets.
5. **Pathfinder and soil-gas geochemistry** — improves target generation from subtle halos and surface gas flux anomalies.

## New Track R — Exploration Targeting & Resource Risk

Track R fills the gaps between mapping a deposit and deciding what to do next.

- **Geochemical pathfinder analysis:** ranks pathfinder elements such as As, Sb, Bi, Te, Hg, and Se by anomaly/halo strength and calculates a dispersion-vector proxy toward the likely source.
- **Geostatistical simulation:** adds Sequential Gaussian Simulation contracts that generate P10/P90 uncertainty envelopes and risk-cube artifact URLs, distinct from a single kriging estimate.
- **Drill planning optimiser:** ranks candidate drill holes by expected uncertainty reduction, target probability, depth, and budget to choose the next highest-information holes.
- **Downhole geophysics:** adds LAS parsing and lithology-correlation scaffolds for gamma, density, sonic, resistivity, caliper, and deviation logs.
- **Fluid inclusion analysis:** summarises microthermometry and salinity data to classify ore-fluid systems.

## New Track S — Geochemistry QA/QC, Soil Gas & LIMS

Track S makes TerraForge stickier in daily exploration operations.

- **QA/QC module:** checks standards for lab drift, blanks for contamination, and duplicates for precision failure.
- **Soil gas geochemistry:** supports RAD7 radon, CO₂, helium, H₂S, and CH₄ readings for fault, geothermal, and buried-mineralisation signals.
- **LIMS:** records sample state changes and provides chain-of-custody artifact URLs.
- **Tenement management:** tracks licence expiry, annual report due dates, expenditure commitments, and alert levels.
- **Investor data room:** creates a redacted, permissioned, time-limited project view with audit logging.

## New Track T — Earth Observation Corrections & SAR Intelligence

Track T improves cross-date and cross-sensor reliability.

- **GNSS/GACOS InSAR tropospheric correction:** addresses atmospheric noise, a key Sentinel-1 InSAR error source over East Africa.
- **Hyperspectral atmospheric correction:** defines 6S/ATCOR-style reflectance retrieval outputs so Pika L surveys from different dates can be compared rigorously.
- **SAR polarimetry:** adds VV/VH decomposition outputs to separate surface, volume, and double-bounce scattering for outcrop and infrastructure discrimination.

## New Track U — Hydrogeology & Environmental Risk Extensions

Track U extends the Phase 4 hydro/urban/infrastructure brief with predictive risk models.

- **MODPATH particle tracking:** returns particle tracks and capture-zone artifacts for wellhead protection and contamination-plume prediction.
- **3D ERT aquifer mapping:** combines multiple Terrameter profiles into 3D aquifer geometry inversion contracts.
- **Groundwater age dating:** ingests tritium/helium-3, CFC, and SF6-style tracer data to estimate residence time and sustainable abstraction risk.
- **Flood inundation modelling:** HEC-RAS/LISFLOOD-FP-style design storm contracts return flood-depth grids and inundated area.
- **Noise and air-quality dispersion:** AERMOD/blast-noise stubs support Kenyan NEMA EIA prediction rather than only monitoring.
- **Traffic and haulage simulation:** estimates trips, daily truck-km, and road-wear index for mining infrastructure assessments.
- **Building structural assessment:** combines InSAR displacement and optical change into settlement/mine-subsidence inspection priorities.

## API endpoints added

- `/targeting/pathfinder-analysis`
- `/targeting/drill-plan-optimise`
- `/targeting/geostat-simulate`
- `/geochemistry/soil-gas`
- `/geochemistry/qaqc`
- `/geochemistry/fluid-inclusions`
- `/earth-observation/insar-correction`
- `/earth-observation/hyperspectral-correction`
- `/earth-observation/sar-polarimetry`
- `/hydro/modpath`
- `/hydro/ert-3d`
- `/hydro/groundwater-age`
- `/environment/flood-inundation`
- `/environment/air-quality`
- `/environment/noise`
- `/environment/traffic-haulage`
- `/environment/structural-assessment`
- `/platform/lims/sample-event`
- `/platform/tenements/obligations`
- `/platform/data-room`

## Definition of Done

- Drill optimiser selects holes within budget and reports planned metres, spend, and information gain.
- LIMS sample events enforce valid lifecycle states and generate chain-of-custody URLs.
- QA/QC flags standards, blanks, and duplicates with clear JORC-ready status.
- Flood inundation model returns a depth grid and inundated area for a design storm.
- Pathfinder analysis ranks deposit-style elements and outputs a source-vector proxy.
- Soil-gas module flags fault/geothermal anomaly signals from CO₂, helium, and radon readings.
- InSAR, hyperspectral, and SAR polarimetry correction endpoints return explicit corrected artifact URLs.
- MODPATH, 3D ERT, groundwater-age, traffic, dispersion, and structural-assessment stubs are covered by tests.
