from __future__ import annotations

from pydantic import BaseModel, Field


class DrillholeRecord(BaseModel):
    project_id: str
    source: str
    parser_version: str
    crs: str = "EPSG:4326"
    hole_id: str
    collar_lon: float
    collar_lat: float
    depth_m: float | None = None
    azimuth_deg: float | None = None
    dip_deg: float | None = None
    metadata: dict = Field(default_factory=dict)
