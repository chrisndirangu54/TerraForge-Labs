import numpy as np
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.services.storage import get_storage_service, reset_storage_service
from backend.processing.cog_io import array_to_cog_bytes

client = TestClient(app)


def setup_function() -> None:
    reset_storage_service()


def test_cog_tile_and_preview_endpoints():
    storage = get_storage_service()
    grid = np.linspace(0, 100, 64 * 64, dtype=np.float32).reshape(64, 64)
    key = "rasters/demo_cog.tif"
    storage.put(
        key,
        array_to_cog_bytes(grid, (37.45, -1.20, 37.55, -1.10)),
        content_type="image/tiff",
    )

    metadata = client.get(f"/mapping/cog/{key}/metadata")
    assert metadata.status_code == 200
    body = metadata.json()
    assert body["storage_key"] == key
    assert body["tile_url_template"]

    preview = client.get(f"/mapping/cog/{key}/preview.png")
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.content[:8] == b"\x89PNG\r\n\x1a\n"

    tile = client.get(f"/mapping/cog/{key}/tiles/10/580/395.png")
    assert tile.status_code == 200
    assert tile.headers["content-type"] == "image/png"