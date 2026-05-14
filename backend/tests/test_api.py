from pathlib import Path


def test_api_main_defines_core_routes():
    source = Path("backend/api/main.py").read_text()
    assert '@app.get("/health")' in source
    assert '@app.get("/version")' in source
    assert "app.include_router(instruments_router)" in source
    assert 'app.include_router(instruments_router)' in source


def test_geodata_router_contains_kriging_pipeline():
    source = Path("backend/api/routers/geodata.py").read_text()
    assert '@router.post("/fuse-geodata")' in source
    assert "run_kriging_pipeline" in source


def test_api_main_includes_geobotany_router():
    source = Path("backend/api/main.py").read_text()
    assert "geobotany_router" in source
    assert "app.include_router(geobotany_router)" in source


def test_geobotany_router_defines_track_q_endpoints():
    source = Path("backend/api/routers/geobotany.py").read_text()
    assert '@router.post("/geobotany/classify-plant")' in source
    assert '@router.post("/geobotany/stress-map")' in source
    assert '@router.post("/geobotany/biogeochem-upload")' in source
    assert '@router.post("/geobotany/survey-plan")' in source
    assert 'run_kriging_pipeline' in source
def test_api_main_defines_health_and_version_routes():
    source = Path("backend/api/main.py").read_text()
    assert '@app.get("/health")' in source
    assert '@app.get("/version")' in source


def test_geodata_router_contains_fuse_geodata_stub():
    source = Path("backend/api/routers/geodata.py").read_text()
    assert '@router.post("/fuse-geodata")' in source
    assert '"mode": "phase0-stub"' in source
