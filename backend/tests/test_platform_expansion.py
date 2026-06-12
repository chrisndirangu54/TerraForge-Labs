from fastapi.testclient import TestClient

from backend.api.auth.repository import reset_auth_repository
from backend.api.main import app
from backend.processing.platform_expansion import (
    drone_cv_analyze,
    evidence_bundle,
    exploration_stop_criterion,
    fusion_score_v2,
    gpr_interpret,
    lidar_process,
)

client = TestClient(app)


def setup_function() -> None:
    reset_auth_repository()


def _headers() -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": "platform@example.com", "password": "securepass1", "role": "geologist"},
    )
    token = client.post(
        "/auth/login",
        json={"email": "platform@example.com", "password": "securepass1"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_fusion_v2_returns_attributions():
    result = fusion_score_v2(
        {
            "sources": {
                "kriging_grade": 82,
                "kriging_uncertainty": 0.25,
                "geobotany": 70,
                "aeromag_structure": 65,
            }
        }
    )
    assert "fusion_score" in result
    assert len(result["attributions"]) >= 4
    assert result["attributions"][0]["shap_style_rank"] == 1


def test_platform_router_fusion_and_lineage():
    headers = _headers()
    fusion = client.post(
        "/platform/fusion/v2",
        headers=headers,
        json={"sources": {"kriging_grade": 90, "geobotany": 75}},
    )
    assert fusion.status_code == 200
    assert "evidence_bundle_id" in fusion.json()

    lineage = client.post(
        "/platform/lineage/record",
        headers=headers,
        json={
            "artifact_type": "kriging_cog",
            "storage_key": "kriging/demo_mean.tif",
            "project_id": "matuu",
        },
    )
    assert lineage.status_code == 200
    record_id = lineage.json()["id"]
    listed = client.get("/platform/lineage/list", headers=headers)
    assert listed.status_code == 200
    assert any(row["id"] == record_id for row in listed.json()["records"])


def test_platform_modality_endpoints():
    headers = _headers()
    endpoints = [
        ("/platform/uav/survey", {"project_id": "matuu", "flight_id": "f1"}),
        ("/platform/aeromag/fusion", {"mag_amplitude_nt": 150}),
        ("/platform/lidar/process", {"storage_key": "lidar/demo.laz"}),
        ("/platform/drone/cv/analyze", {"frame_count": 90}),
        ("/platform/gpr/interpret", {"max_depth_m": 6}),
        ("/platform/geomagnetism/analyze", {"gradient_nt_m": 4.2}),
        ("/platform/tectonics/context", {"lon": 37.5, "lat": -1.15}),
        ("/platform/seismic/summary", {"events": [{"magnitude": 3.1}]}),
        ("/platform/exploration/stop-criterion", {"marginal_npv_next_hole_usd": 100000}),
        ("/platform/conformal/grade", {"grades": [100, 120, 90]}),
        ("/platform/climate-risk/npv", {"commodity": "ta", "ore_tonnes": 1_000_000}),
    ]
    for path, body in endpoints:
        response = client.post(path, headers=headers, json=body)
        assert response.status_code == 200, path


def test_processing_stubs_smoke():
    assert drone_cv_analyze({"frame_count": 60})["geobotany_keyframes"] >= 2
    assert gpr_interpret({"max_depth_m": 5})["shallow_structure_detected"] is True
    assert exploration_stop_criterion({"marginal_npv_next_hole_usd": 200000})["continue_campaign"]
    bundle = evidence_bundle({"project_id": "demo"})
    assert bundle["bundle_id"]
    assert lidar_process({"project_id": "demo"})["lineage_id"]