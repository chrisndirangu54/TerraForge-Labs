from backend.api.kriging import run_kriging_pipeline
from backend.api.services.storage import get_storage_service, reset_storage_service
from shared.constants import NUGGET_RANGE


def setup_function() -> None:
    reset_storage_service()


def test_kriging_persists_artifacts_via_storage_service():
    result = run_kriging_pipeline(
        {
            "element": "ta_ppm",
            "observations": [
                {"ta_ppm": 100 + i * 3, "assay_error_pct": 8 + (i % 4)}
                for i in range(20)
            ],
        }
    )
    storage = get_storage_service()
    assert result["grid_geotiff_url"].startswith("minio://")
    assert result["storage_backend"] == "memory"
    assert storage.list_keys("kriging/")
    assert NUGGET_RANGE[0] <= result["variogram_params"]["nugget"] <= NUGGET_RANGE[1]
