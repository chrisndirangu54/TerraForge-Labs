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


## Phase 3 scaffold highlights
- Added 3D MT inversion and geothermal resource estimate scaffolds.
- Added SEM automated mineralogy, tectonic context, and paleontology processing scaffolds.
- Added autonomous field agent loop scaffold and mission planning endpoint.
- Added TerraForge-Geo LLM training/evaluation placeholders and gRPC instrument streaming proto.
AGPL-3.0 offline-first geological platform scaffold for Phase 0.

## Phase 0 scope
- FastAPI skeleton (`backend/api`) with `/health`, `/version`, and `/fuse-geodata` stub.
- Django marketplace/admin scaffold (`backend/marketplace`) with `Dataset` model placeholders.
- Shared constants + instrument parser protocol and stubs (`shared/`).
- Local infra (`infra/docker-compose.yml`) for API, marketplace, PostGIS, Redis, MinIO.
- Flutter app skeleton (`apps/mobile`) and docs baseline (`docs/`).

## Quick start
```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```
