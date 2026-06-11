# Service Level Objectives (SLOs)

TerraForge Labs API availability and latency targets for critical geoscience workflows.
Error budgets are measured monthly unless noted otherwise.

## Global API

| Metric | Target | Measurement window |
|--------|--------|--------------------|
| Availability | 99.5% | Rolling 30 days |
| p95 latency (all routes) | < 500 ms | Rolling 7 days |
| p99 latency (all routes) | < 2 s | Rolling 7 days |
| 5xx error rate | < 0.5% | Rolling 7 days |

Prometheus metrics exposed at `GET /metrics`:

- `http_requests_total{method,path,status}`
- `http_request_duration_seconds_{count,sum}{method,path}`

## Classification (`POST /classification/gpu`, cloud classify routes)

| Metric | Target | Notes |
|--------|--------|-------|
| Availability | 99.0% | Includes GPU worker queue saturation |
| p95 sync latency | < 3 s | Stub/small batch inference |
| p95 async job completion | < 120 s | Full scene / large tile batch |
| Job success rate | > 98% | Excludes client validation errors (4xx) |

**Alerting:** page on-call when classify p95 > 5 s for 15 minutes or success rate < 95% over 1 hour.

## Kriging (`POST /geodata/fuse-geodata`, kriging pipeline)

| Metric | Target | Notes |
|--------|--------|-------|
| Availability | 99.5% | Core geostatistics path |
| p95 latency | < 8 s | Up to 10k sample points |
| p99 latency | < 30 s | Large fused rasters |
| Job success rate | > 99% | Numerical failures are rare |

**Alerting:** warn when kriging p95 > 15 s for 30 minutes; page when availability < 99% over 24 hours.

## Reports (`POST /reports/jorc`, Celery `reports` queue)

| Metric | Target | Notes |
|--------|--------|-------|
| Availability | 99.0% | Async PDF/DOCX generation |
| p95 enqueue latency | < 500 ms | API accepts job and returns job id |
| p95 end-to-end completion | < 180 s | Standard JORC report package |
| Job success rate | > 97% | Retries allowed for transient worker faults |

**Alerting:** page when report queue depth > 50 for 10 minutes or completion p95 > 300 s for 1 hour.

## Error budget policy

1. Burn > 50% of monthly error budget in 7 days → freeze non-critical releases; focus on reliability.
2. Burn > 100% → incident review required before new feature deploys.
3. SLO regressions tracked in Grafana dashboard `TerraForge API Overview` (`infra/dashboards/terraforge.json`).

## Observability stack (optional)

Enable the `monitoring` Docker Compose profile:

```bash
docker compose -f infra/docker-compose.yml --profile monitoring up -d
```

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (default admin password set at deploy time)