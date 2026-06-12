from backend.api.services.job_display import attach_display, build_job_display


def test_build_job_display_raster_layers():
    display = build_job_display(
        {
            "job_type": "lidar_process",
            "status": "complete",
            "result": {
                "point_count": 2500,
                "bounds": [37.45, -1.2, 37.55, -1.1],
                "dtm": {
                    "preview_url": "/mapping/cog/demo/preview.png",
                    "tile_url_template": "/mapping/cog/demo/tiles/{z}/{x}/{y}.png",
                    "storage_key": "lidar/demo_dtm.tif",
                },
            },
        }
    )
    assert display["display_type"] == "raster"
    assert len(display["raster"]["layers"]) == 1


def test_attach_display_adds_envelope():
    payload = attach_display({"job_id": "abc", "status": "complete", "job_type": "test", "result": {"value": 1}})
    assert "display" in payload