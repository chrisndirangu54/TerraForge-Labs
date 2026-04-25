# Phase 2 Execution Plan (Scaffold)

This commit bootstraps the Track A–F module layout described in the Phase 2 brief:

- Track A: `/fuse-spectral`, LiDAR and hyperspectral parser scaffolds.
- Track B: thin section + XRD parser endpoints and instrument modules.
- Track C: `/fuse-seismic` plus inversion/gravity/MT processing scaffolds.
- Track D: `/ingest-historical` plus OCR borehole extraction scaffold.
- Track E: plugin base + auto-discovery and marketplace catalogue endpoint/fixtures.
- Track F: foundations remain in JORC services; NI 43-101/Kenya-specific templates are queued for follow-up.

> Note: This is a structural + API scaffold step to prepare the codebase for full Phase 2 implementation and validation.


## Compliance bootstrap added in this iteration
- Added `backend/api/services/jorc_v2.py` with NI 43-101 + Kenya EL report scaffolds.
- Added `backend/api/services/audit_v2.py` for hash-based audit event records.
- Added `backend/api/routers/compliance.py` exposing `/reports/ni43101` and `/reports/kenya-el`.
- Added `scripts_check_phase1_readiness.py` to enforce Phase 2 prerequisite gating checks before further work.


## Platform hardening docs/bootstrap
- Added licensing docs (`LICENSE.md`, `docs/commercial-license-template.md`, `docs/pricing.md`).
- Added marketplace data models/views scaffold and schema docs under `docs/schemas/`.
- Added grain-segmentation model scaffolds under `models/grain_segmentation/`.
