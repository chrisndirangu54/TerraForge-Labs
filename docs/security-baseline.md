# Security Baseline

## Authentication

- JWT bearer tokens (`Authorization: Bearer <token>`) issued by `POST /auth/login`.
- `AUTH_REQUIRED=false` by default for local dev and CI; set `AUTH_REQUIRED=true` in production.
- Rotate `JWT_SECRET` per environment; never commit real secrets.

## Roles (RBAC)

| Role | Capabilities |
|------|--------------|
| `admin` | Full access, project membership management |
| `geologist` | Create projects, run mutating analysis endpoints |
| `contractor` | Run field workflows, limited project write |
| `regulator_readonly` | Read-only; mutating routes return 403 |

## Project isolation

- Users only see projects they belong to (via `project_memberships`), except `admin` and anonymous dev mode.
- `GET /projects` lists membership-scoped projects.
- `GET /jobs`, `GET /jobs/{id}`, and `GET /ingest/observations` filter by accessible `project_id`(s).
- Cross-project access returns **403** (`Not a member of this project`).
- Job enqueue attaches `project_id` and `created_by` from the authenticated user and payload.

## Protected endpoints

When `AUTH_REQUIRED=true`, mutating routes require a valid token:

- All `POST` analysis/workflow routes (via `require_mutating_access`)
- `POST /classification/gpu*`
- `POST /reports/jorc`
- `POST /projects`
- `POST /ingest/observations`
- `POST /instruments/upload`
- `POST /models/{task}/versions/{version}/promote`

Read routes (`GET`) remain available to authenticated users with project scope; `regulator_readonly` may read but not mutate.

## Storage

- Passwords hashed with bcrypt.
- Job status persisted in Postgres (`jobs`, `job_events`); optional Redis cache layer.
- Model versions tracked in memory registry (or MLflow when `MODEL_REGISTRY_BACKEND=mlflow`).

## Client guidance

- Mobile and web clients store tokens in memory/session and attach Bearer headers on API calls.
- Include `project_id` on job submissions and instrument uploads when auth is enabled.
- Use HTTPS in production; restrict CORS origins to known front-end hosts.