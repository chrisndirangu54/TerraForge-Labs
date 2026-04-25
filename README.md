# Terraforge Labs

AGPL-3.0 offline-first geological platform.

## Phase 1 implementation snapshot

Implemented modules:
- **Instrument parsing** for Bruker XRF, Terrameter LS2 XML, Kappameter, and Trimble GNSS NMEA.
- **Kriging pipeline** endpoint (`POST /fuse-geodata`) producing mean/variance/CI raster artifacts and MinIO-style URLs.
- **Deposit model** generation endpoint (`POST /deposit-model`) producing OBJ + block model CSV + probability map artifact.
- **JORC report** generation endpoint (`POST /reports/jorc`) with AI disclaimer in JSON/HTML/PDF artifacts.
- **Mobile Phase 1 screens/services** scaffold for field capture, kriging map, mineral classification, and JORC report workflows.

## Run tests
```bash
pytest --tb=short
```

## What this repo does (plain language)
- It ingests raw geological field files from common instruments.
- It converts those files into structured data and quick map/model artifacts.
- It can generate draft report outputs with explicit AI-assistance disclaimers.
- It includes a mobile app shell for field workflows and a backend API for automation.

For a non-technical walkthrough, see `docs/layman-overview.md`.


## Phase 2 scaffold highlights
- Added new backend endpoints for `/fuse-spectral`, `/fuse-seismic`, `/ingest-historical`, `/classify-thin-section`, `/parse-xrd`, and marketplace catalogue.
- Added instrument scaffolds for LiDAR, hyperspectral, thin section, XRD, Raman, MT, gravity, TDEM, SP, and hydrogeology.
- Added plugin auto-discovery scaffold and marketplace seed catalogue fixtures.


## Problem statement
Exploration teams in East Africa often work with fragmented, offline, and paper-heavy data pipelines. TerraForge aims to unify instrument ingestion, geospatial modeling, and compliance reporting in one offline-first stack.

## Demo assets
- Screenshots: pending live emulator capture in CI artifact pipeline.
- Demo video link: TODO (attach post-AmCham recording).
- Landing page: TODO (Carrd/GitHub Pages with early access form).
