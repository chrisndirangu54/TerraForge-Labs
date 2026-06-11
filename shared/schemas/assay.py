from __future__ import annotations

from pydantic import BaseModel, Field


class AssayRecord(BaseModel):
    project_id: str
    source: str
    parser_version: str
    crs: str = "EPSG:4326"
    sample_id: str
    hole_id: str | None = None
    from_m: float | None = None
    to_m: float | None = None
    element: str
    value: float
    unit: str = "ppm"
    metadata: dict = Field(default_factory=dict)
