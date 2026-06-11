# Deployment Guide

## Quick start (Docker Compose)

```bash
cd C:\Users\Admin\TerraForge-Labs
# 1. Copy and edit secrets locally (gitignored)
cp infra/env/production.env.example .env
# 2. Set LLM_API_KEY after rotating in Google AI Studio
# 3. Start stack
docker compose -f infra/docker-compose.yml up -d --build
```

Services:

| Service | URL | Notes |
|---------|-----|-------|
| API | http://localhost:8000 | `/health`, `/copilot/status` |
| MinIO API | http://localhost:9000 | Object storage |
| MinIO Console | http://localhost:9001 | `minioadmin` / `minioadmin` (change in prod) |
| Postgres | localhost:5432 | `terraforge` database |

## MinIO + STAC

With `STORAGE_BACKEND=minio` and `STAC_CATALOG_BACKEND=postgres`:

1. Upload raster: `POST /mapping/rasters/ingest`
2. List catalog: `GET /mapping/stac/items?collection=...`
3. Fetch item: `GET /mapping/stac/items/{item_id}`
4. Tiles redirect via signed URLs: `GET /tiles/raster/{z}/{x}/{y}`

Artifacts land in bucket `terraforge` under keys like `rasters/*.tif` and `stac/items/*.json`.
Postgres tables `artifacts` and `stac_items` hold metadata and lineage.

### Production MinIO checklist

- [ ] Replace default `minioadmin` credentials
- [ ] Enable TLS (`MINIO_SECURE=true`)
- [ ] Restrict bucket policy (no public read except signed URLs)
- [ ] Enable versioning + lifecycle rules for COG retention
- [ ] Backup `minio_data` volume or replicate to S3

## Gemini LLM setup

### 1. Rotate your API key (required if exposed)

If a key appeared in chat, logs, or git:

1. Open [Google AI Studio → API Keys](https://aistudio.google.com/apikey)
2. **Delete/revoke** the compromised key
3. Create a **new** key
4. Set `LLM_API_KEY=<new-key>` in `.env` (local) or your secrets manager (prod)

### 2. Local development

```env
LLM_PROVIDER=gemini
LLM_API_KEY=your-rotated-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_RPM=12
```

Verify:

```bash
curl http://localhost:8000/copilot/status
# gemini_configured: true, active: true
```

### 3. Docker Compose

`infra/docker-compose.yml` loads `../.env` via `env_file`. Set `LLM_API_KEY` there only — never in committed YAML.

### 4. GitHub Actions / CI

CI sets `LLM_FORCE_STUB=true` so tests never call Gemini. For staging deploys, add repository secrets:

| Secret | Purpose |
|--------|---------|
| `LLM_API_KEY` | Gemini production key |
| `JWT_SECRET` | Auth signing |
| `MINIO_ACCESS_KEY` | Object storage |
| `MINIO_SECRET_KEY` | Object storage |

Example deploy step (pseudo):

```yaml
- run: docker compose up -d
  env:
    LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
    JWT_SECRET: ${{ secrets.JWT_SECRET }}
```

### 5. Model selection

Default: `gemini-2.5-flash` (fast, cost-effective). For longer JORC sections use `gemini-2.5-pro`.

List available models:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=$LLM_API_KEY"
```

## Environment reference

See `infra/env/production.env.example` and root `.env.example`.

| Variable | Dev | Prod |
|----------|-----|------|
| `STORAGE_BACKEND` | `memory` | `minio` |
| `STAC_CATALOG_BACKEND` | `memory` | `postgres` |
| `AUTH_REQUIRED` | `false` | `true` |
| `LLM_FORCE_STUB` | unset | unset (live Gemini) |