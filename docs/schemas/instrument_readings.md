# Schema: instrument_readings

Canonical georeferenced observation store (PostGIS).

## Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| id | UUID | yes | Primary key |
| upload_id | UUID | yes | Batch/upload identifier |
| project_id | UUID | yes (new writes) | Owning project |
| source | string | yes | Origin (`instrument_upload`, `api_ingest`, etc.) |
| parser_version | string | yes | Parser name + version (`xrf_bruker@1.0.0`) |
| crs | string | yes | Coordinate reference (`EPSG:4326`) |
| instrument_type | string | yes | Instrument/parser key |
| sample_id | string | no | Sample or profile identifier |
| geom | geometry(Point, 4326) | no | Point location when lon/lat known |
| data | JSONB | yes | Parsed instrument payload |
| flagged | boolean | no | QA/QC flag |
| flag_reasons | text[] | no | Flag explanations |
| uploaded_at | timestamptz | yes | Insert timestamp |

## API

- `POST /ingest/observations` — batch insert canonical `ObservationRecord` objects
- `GET /ingest/observations?project_id=` — list persisted rows
- `POST /instruments/upload` — parse file, persist preview + rows

## Shared schema

Pydantic model: `shared/schemas/observation.py` (`ObservationRecord`)