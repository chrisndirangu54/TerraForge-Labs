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
