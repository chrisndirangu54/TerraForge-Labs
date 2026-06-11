from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.services.storage import get_storage_service, reset_storage_service
from backend.api.services.stac_catalog import reset_stac_catalog
from backend.processing.raster_pipeline import ingest_raster, reset_raster_pipeline

client = TestClient(app)


def setup_function() -> None:
    reset_storage_service()
    reset_stac_catalog()
    reset_raster_pipeline()


def test_raster_pipeline_registers_stac_item_and_artifact():
    result = ingest_raster(
        {
            "bbox": [37.45, -1.20, 37.55, -1.10],
            "source": "sentinel-2",
            "collection": "matuu-rasters",
        }
    )
    storage = get_storage_service()
    assert result["stac_item_id"]
    assert storage.exists(result["artifact_key"])
    assert result["artifact_url"].startswith("minio://")
    assert "{z}" in result["tile_redirect_template"]


def test_storage_signed_urls_and_tile_redirect():
    storage = get_storage_service()
    storage.put(
        "tiles/10/512/384.mvt",
        "vector-tile",
        content_type="application/vnd.mapbox-vector-tile",
    )
    signed = storage.get_signed_url("tiles/10/512/384.mvt")
    assert "sig=" in signed

    response = client.get("/tiles/10/512/384", follow_redirects=False)
    assert response.status_code == 302
    assert "tiles/10/512/384.mvt" in response.headers["location"]
    assert response.headers["location"].startswith("memory://")
