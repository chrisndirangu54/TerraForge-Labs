from pathlib import Path


def test_api_main_defines_core_routes():
    source = Path("backend/api/main.py").read_text()
    assert '@app.get("/health")' in source
    assert '@app.get("/version")' in source
    assert 'app.include_router(instruments_router)' in source


def test_geodata_router_contains_kriging_pipeline():
    source = Path("backend/api/routers/geodata.py").read_text()
    assert '@router.post("/fuse-geodata")' in source
    assert 'run_kriging_pipeline' in source
def test_api_main_defines_health_and_version_routes():
    source = Path("backend/api/main.py").read_text()
    assert '@app.get("/health")' in source
    assert '@app.get("/version")' in source


def test_geodata_router_contains_fuse_geodata_stub():
    source = Path("backend/api/routers/geodata.py").read_text()
    assert '@router.post("/fuse-geodata")' in source
    assert '"mode": "phase0-stub"' in source
