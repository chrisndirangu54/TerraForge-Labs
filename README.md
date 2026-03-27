# Terraforge Labs

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
