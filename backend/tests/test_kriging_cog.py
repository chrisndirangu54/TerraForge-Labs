import numpy as np

from backend.api.kriging import run_kriging_pipeline
from backend.api.services.storage import get_storage_service, reset_storage_service
from backend.processing.cog_io import is_geotiff, read_cog_metadata
from shared.constants import NUGGET_RANGE


def setup_function() -> None:
    reset_storage_service()


def test_kriging_writes_geotiff_cogs():
    result = run_kriging_pipeline(
        {
            "element": "ta_ppm",
            "observations": [
                {
                    "lon": 37.50 + i * 0.01,
                    "lat": -1.15 + (i % 3) * 0.01,
                    "ta_ppm": 80 + i * 5,
                    "assay_error_pct": 6 + (i % 4),
                }
                for i in range(12)
            ],
        }
    )
    storage = get_storage_service()
    mean_key = result["grid_storage_key"]
    content = storage.get(mean_key)
    assert content is not None
    assert is_geotiff(content)
    meta = read_cog_metadata(content)
    assert meta["width"] >= 5
    assert meta["height"] >= 5
    assert result["engine"] == "pykrige_ordinary_kriging"
    assert result["cog_tile_url_template"].startswith("/mapping/cog/")
    assert NUGGET_RANGE[0] <= result["variogram_params"]["nugget"] <= NUGGET_RANGE[1]


def test_kriging_prediction_grid_is_not_flat():
    result = run_kriging_pipeline(
        {
            "element": "ta_ppm",
            "observations": [
                {"lon": 37.48, "lat": -1.18, "ta_ppm": 40.0},
                {"lon": 37.52, "lat": -1.12, "ta_ppm": 220.0},
                {"lon": 37.50, "lat": -1.15, "ta_ppm": 120.0},
                {"lon": 37.49, "lat": -1.14, "ta_ppm": 90.0},
                {"lon": 37.51, "lat": -1.16, "ta_ppm": 180.0},
            ],
        }
    )
    storage = get_storage_service()
    content = storage.get(result["grid_storage_key"])
    assert content is not None
    from backend.processing.cog_io import read_cog_array

    array, _meta = read_cog_array(content)
    assert float(np.std(array)) > 1.0