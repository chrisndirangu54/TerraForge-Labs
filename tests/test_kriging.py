import json

from backend.api.kriging import run_kriging_pipeline
from shared.constants import NUGGET_RANGE


def test_kriging_outputs_and_nugget_range():
    payload = {
        "element": "ta_ppm",
        "observations": [f["properties"] for f in json.loads(open("tests/fixtures/matuu_synthetic.geojson").read())["features"]],
    }
    res = run_kriging_pipeline(payload)
    assert res["grid_geotiff_url"].startswith("minio://")
    assert res["variance_geotiff_url"].startswith("minio://")
    assert NUGGET_RANGE[0] <= res["variogram_params"]["nugget"] <= NUGGET_RANGE[1]
