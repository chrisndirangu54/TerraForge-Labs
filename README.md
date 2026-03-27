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
