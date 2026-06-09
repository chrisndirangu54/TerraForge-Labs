from __future__ import annotations

from fastapi import APIRouter

from backend.processing.satellite_feeds import (
    change_detect,
    insar_request,
    latest_index,
    scene_catalogue,
)

router = APIRouter()


def _parse_bbox(bbox: str) -> list[float]:
    if not bbox:
        return [37.45, -1.20, 37.55, -1.10]
    return [float(part) for part in bbox.split(",")]


@router.get("/satellite/scenes")
async def satellite_scenes(
    bbox: str = "", start: str = "2026-01-01", end: str = "2026-06-30"
) -> dict:
    return scene_catalogue(_parse_bbox(bbox), start, end)


@router.get("/satellite/latest")
async def satellite_latest(bbox: str = "", index: str = "ndvi") -> dict:
    return latest_index(_parse_bbox(bbox), index)


@router.post("/satellite/change-detect")
async def satellite_change_detect(payload: dict) -> dict:
    return change_detect(
        payload.get("before_url", "minio://satellite/before.tif"),
        payload.get("after_url", "minio://satellite/after.tif"),
    )


@router.post("/satellite/insar")
async def satellite_insar(payload: dict) -> dict:
    return insar_request(
        payload.get("bbox", [37.45, -1.20, 37.55, -1.10]),
        payload.get("date_range", ["2026-01-01", "2026-06-30"]),
    )
