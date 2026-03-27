from fastapi import FastAPI

from backend.api.routers.geodata import router as geodata_router

app = FastAPI(title="Terraforge Labs API", version="0.1.0")
app.include_router(geodata_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.get("/version")
async def version() -> dict:
    return {"version": app.version}
