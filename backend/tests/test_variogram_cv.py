from fastapi.testclient import TestClient

from backend.api.main import app
from backend.processing.variogram_cv import analyze_variogram, leave_one_out_cross_validate

client = TestClient(app)


def test_leave_one_out_cross_validation_metrics():
    xs = [37.48, 37.50, 37.52, 37.49, 37.51]
    ys = [-1.18, -1.15, -1.12, -1.14, -1.16]
    values = [40.0, 120.0, 220.0, 90.0, 180.0]
    result = leave_one_out_cross_validate(xs, ys, values, variogram_model="spherical")
    assert result["n_folds"] == 5
    assert result["rmse"] >= 0
    assert result["mae"] >= 0
    assert len(result["folds"]) == 5


def test_variogram_analyze_endpoint_uses_matuu_fixture():
    response = client.post(
        "/geodata/variogram/cross-validate",
        json={"element": "ta_ppm", "dataset": "matuu_synthetic", "variogram_model": "spherical"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cross_validation"]["n_folds"] >= 4
    assert body["empirical"]["lags"]
    assert body["fitted"]["curve"]