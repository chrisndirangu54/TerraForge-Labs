from backend.api.services.stac_catalog import get_stac_catalog, reset_stac_catalog
from backend.api.services.storage import get_storage_service, reset_storage_service
from backend.processing.raster_pipeline import get_stac_item, ingest_raster, list_stac_items


def setup_function() -> None:
    reset_storage_service()
    reset_stac_catalog()


def test_stac_catalog_persists_ingested_raster():
    result = ingest_raster(
        {
            "bbox": [37.45, -1.20, 37.55, -1.10],
            "source": "sentinel-2",
            "collection": "matuu-rasters",
            "project_id": "11111111-1111-1111-1111-111111111111",
        }
    )
    item = get_stac_item(result["stac_item_id"])
    assert item is not None
    assert item["collection"] == "matuu-rasters"
    assert item.get("stac_signed_url")

    listed = list_stac_items(collection="matuu-rasters")
    assert any(row["item_id"] == result["stac_item_id"] for row in listed)


def test_mapping_stac_endpoints(client=None):
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    ingest = client.post(
        "/mapping/rasters/ingest",
        json={"source": "api-test", "collection": "test-rasters"},
    )
    assert ingest.status_code == 200
    item_id = ingest.json()["stac_item_id"]

    listed = client.get("/mapping/stac/items", params={"collection": "test-rasters"})
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    fetched = client.get(f"/mapping/stac/items/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json()["item_id"] == item_id


def test_storage_registers_artifact_metadata():
    storage = get_storage_service()
    record = storage.put("demo/key.tif", b"raster-bytes", content_type="image/tiff")
    catalog = get_stac_catalog()
    saved = catalog.register_artifact(
        {
            "id": record["id"],
            "artifact_type": "raster",
            "storage_key": "demo/key.tif",
            "content_type": "image/tiff",
            "size_bytes": record["size_bytes"],
            "checksum": record["checksum"],
            "metadata": {},
        }
    )
    assert saved["id"] == record["id"]
    assert storage.get("demo/key.tif") == b"raster-bytes"