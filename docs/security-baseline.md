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

## OWASP Top 10 checklist

Implementation status for the FastAPI backend (`backend/api`). Status values: **Done**, **Partial**, **Planned**.

| # | Risk | Status | Implementation |
|---|------|--------|----------------|
| A01 | Broken Access Control | **Partial** | JWT + RBAC (`require_mutating_access`), project membership checks on jobs/ingest. Regulator role read-only. |
| A02 | Cryptographic Failures | **Partial** | bcrypt password hashing; JWT signed with `JWT_SECRET`. TLS termination expected at reverse proxy in production. |
| A03 | Injection | **Partial** | Pydantic request validation; parameterized SQL via psycopg. No raw SQL from user input in routers. |
| A04 | Insecure Design | **Partial** | Async job queue for heavy work; project isolation by design. Threat modeling documented here. |
| A05 | Security Misconfiguration | **Done** | `SecurityHeadersMiddleware` sets CSP, frame denial, nosniff, referrer policy, COOP/CORP. CORS allow-list in `main.py`. |
| A06 | Vulnerable Components | **Done** | CI runs `pip-audit` on Poetry environment (`.github/workflows/ci.yml`). |
| A07 | Identification & Auth Failures | **Partial** | Bearer JWT auth; `AUTH_REQUIRED` toggle. Password minimum length enforced at register. MFA not yet implemented. |
| A08 | Software & Data Integrity | **Partial** | GitHub Actions CI for lint/test; signed container images planned. No unsigned webhook callbacks in core API. |
| A09 | Security Logging & Monitoring | **Done** | `TelemetryMiddleware` + `GET /metrics` Prometheus exposition; optional Prometheus/Grafana via `monitoring` compose profile. |
| A10 | SSRF | **Planned** | Outbound fetches (satellite, external geodata) should use allow-listed hosts; audit before production egress. |

### Response headers (PR-21)

`SecurityHeadersMiddleware` attaches on every response:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `0` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; frame-ancestors 'none'` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |

Enable HSTS at the TLS-terminating proxy or set `enable_hsts=True` when serving HTTPS directly.

### Dependency scanning

```bash
poetry run pip install pip-audit
poetry run pip-audit
```

Failures in CI block merges until vulnerabilities are patched or explicitly waived with documented risk acceptance.