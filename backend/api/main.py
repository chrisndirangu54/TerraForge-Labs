from fastapi import FastAPI

from backend.api.routers.geodata import router as geodata_router
from backend.api.routers.instruments import router as instruments_router
from backend.api.routers.jobs import router as jobs_router
from backend.api.routers.modeling import router as modeling_router
from backend.api.routers.reports import router as reports_router

app = FastAPI(title="Terraforge Labs API", version="0.2.0")
app.include_router(geodata_router)
app.include_router(instruments_router)
app.include_router(modeling_router)
app.include_router(reports_router)
app.include_router(jobs_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.get("/version")
async def version() -> dict:
    return {"version": app.version}
