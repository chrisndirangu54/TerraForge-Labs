from pathlib import Path


def test_api_main_defines_core_routes():
    source = Path("backend/api/main.py").read_text()
    assert '@app.get("/health")' in source
    assert '@app.get("/version")' in source
    assert "app.include_router(instruments_router)" in source


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


def test_phase4_expanded_routers_registered():
    source = Path("backend/api/main.py").read_text()
    for router_name in [
        "mapping_router",
        "hydrogeology_router",
        "urban_router",
        "infrastructure_router",
        "satellite_phase4_router",
    ]:
        assert router_name in source


def test_phase4_expanded_endpoint_sources_exist():
    checks = {
        "backend/api/routers/mapping.py": [
            "/tiles/offline/{region}",
            "/mapping/layers",
        ],
        "backend/api/routers/hydrogeology.py": ["/hydro/slug-test", "/hydro/modflow"],
        "backend/api/routers/urban.py": [
            "/urban/classify-settlement",
            "/urban/conflict-check",
        ],
        "backend/api/routers/infrastructure.py": [
            "/infra/mining-assessment",
            "/infra/pipeline-route",
        ],
        "backend/api/routers/satellite_phase4.py": [
            "/satellite/scenes",
            "/satellite/insar",
        ],
    }
    for path, endpoints in checks.items():
        source = Path(path).read_text()
        for endpoint in endpoints:
            assert endpoint in source
