from fastapi import FastAPI

from backend.api.routers.geodata import router as geodata_router
from backend.api.routers.instruments import router as instruments_router
from backend.api.routers.jobs import router as jobs_router
from backend.api.routers.modeling import router as modeling_router
from backend.api.routers.reports import router as reports_router
from backend.api.routers.spectral import router as spectral_router
from backend.api.routers.seismic import router as seismic_router
from backend.api.routers.historical import router as historical_router
from backend.api.routers.petrography import router as petrography_router
from backend.api.routers.marketplace import router as marketplace_router
from backend.api.routers.compliance import router as compliance_router

app = FastAPI(title="Terraforge Labs API", version="0.2.0")
app.include_router(geodata_router)
app.include_router(instruments_router)
app.include_router(modeling_router)
app.include_router(reports_router)
app.include_router(jobs_router)
app.include_router(spectral_router)
app.include_router(seismic_router)
app.include_router(historical_router)
app.include_router(petrography_router)
app.include_router(marketplace_router)
app.include_router(compliance_router)

app = FastAPI(title="Terraforge Labs API", version="0.1.0")
app.include_router(geodata_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.get("/version")
async def version() -> dict:
    return {"version": app.version}
