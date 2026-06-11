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

## Protected endpoints

When `AUTH_REQUIRED=true`, mutating routes require a valid token:

- `POST /classification/gpu*`
- `POST /reports/jorc`
- `POST /projects`

## Storage

- Passwords hashed with bcrypt.
- Job status persisted in Postgres (`jobs`, `job_events`); optional Redis cache layer.

## Client guidance

- Mobile and web clients store tokens in memory/session and attach Bearer headers on API calls.
- Use HTTPS in production; restrict CORS origins to known front-end hosts.