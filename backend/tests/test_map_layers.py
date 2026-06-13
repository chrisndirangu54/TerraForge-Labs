from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_mapping_layers_endpoint_returns_feature_layers():
    response = client.get("/mapping/layers")
    assert response.status_code == 200
    body = response.json()

    assert "map_modes" in body
    assert "layer_groups" in body
    assert "feature_layers" in body
    assert "overlays" in body
    assert "center" in body
    assert "bounds" in body

    feature_layers = body["feature_layers"]
    assert "geological:sample_points" in feature_layers
    assert feature_layers["geological:sample_points"]["type"] == "FeatureCollection"
    assert len(feature_layers["geological:sample_points"]["features"]) > 0

    assert "geological:deposit_model_mesh" in feature_layers
    assert "hydrogeology:borehole_water_levels" in feature_layers


def test_mapping_layers_includes_overlays():
    response = client.get("/mapping/layers")
    body = response.json()
    overlays = body["overlays"]
    assert isinstance(overlays, list)
    assert len(overlays) >= 1
    kriging = overlays[0]
    assert kriging["id"] == "kriging_grade_heatmap"
    assert "available" in kriging
    assert "title" in kriging