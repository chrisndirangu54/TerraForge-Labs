from backend.api.bootstrap import load_environment

load_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware.security_headers import SecurityHeadersMiddleware
from backend.api.middleware.telemetry import TelemetryMiddleware
from backend.api.routers.auth import router as auth_router
from backend.api.routers.cloud_classification import (
    router as cloud_classification_router,
)
from backend.api.routers.copilot import router as copilot_router
from backend.api.routers.projects import router as projects_router
from backend.api.routers.compliance import router as compliance_router
from backend.api.routers.ethnolinguistics import router as ethnolinguistics_router
from backend.api.routers.gap_closure import router as gap_closure_router
from backend.api.routers.geobotany import router as geobotany_router
from backend.api.routers.geodata import router as geodata_router
from backend.api.routers.historical import router as historical_router
from backend.api.routers.hydrogeology import router as hydrogeology_router
from backend.api.routers.infrastructure import router as infrastructure_router
from backend.api.routers.ingest import router as ingest_router
from backend.api.routers.labeling import router as labeling_router
from backend.api.routers.instruments import router as instruments_router
from backend.api.routers.jobs import router as jobs_router
from backend.api.routers.mapping import router as mapping_router
from backend.api.routers.marketplace import router as marketplace_router
from backend.api.routers.metrics import router as metrics_router
from backend.api.routers.marketplace_payments import (
    router as marketplace_payments_router,
)
from backend.api.routers.mission import router as mission_router
from backend.api.routers.modeling import router as modeling_router
from backend.api.routers.models import router as models_router
from backend.api.routers.mt3d import router as mt3d_router
from backend.api.routers.paleontology import router as paleontology_router
from backend.api.routers.petrography import router as petrography_router
from backend.api.routers.reports import router as reports_router
from backend.api.routers.satellite_phase4 import router as satellite_phase4_router
from backend.api.routers.seismic import router as seismic_router
from backend.api.routers.spectral import router as spectral_router
from backend.api.routers.tectonics import router as tectonics_router
from backend.api.routers.urban import router as urban_router

app = FastAPI(title="Terraforge Labs API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://10.0.2.2:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TelemetryMiddleware)

app.include_router(metrics_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(cloud_classification_router)
app.include_router(geodata_router)
app.include_router(ingest_router)
app.include_router(instruments_router)
app.include_router(modeling_router)
app.include_router(models_router)
app.include_router(reports_router)
app.include_router(jobs_router)
app.include_router(spectral_router)
app.include_router(seismic_router)
app.include_router(historical_router)
app.include_router(petrography_router)
app.include_router(marketplace_router)
app.include_router(compliance_router)
app.include_router(mt3d_router)
app.include_router(tectonics_router)
app.include_router(paleontology_router)
app.include_router(mission_router)
app.include_router(marketplace_payments_router)
app.include_router(geobotany_router)
app.include_router(mapping_router)
app.include_router(hydrogeology_router)
app.include_router(urban_router)
app.include_router(infrastructure_router)
app.include_router(satellite_phase4_router)
app.include_router(gap_closure_router)
app.include_router(ethnolinguistics_router)
app.include_router(labeling_router)
app.include_router(copilot_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.get("/version")
async def version() -> dict:
    return {"version": app.version}
