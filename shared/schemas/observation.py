from __future__ import annotations

from pydantic import BaseModel, Field


class ObservationRecord(BaseModel):
    project_id: str
    source: str
    parser_version: str
    crs: str = "EPSG:4326"
    instrument_type: str | None = None
    sample_id: str | None = None
    lon: float | None = None
    lat: float | None = None
    data: dict = Field(default_factory=dict)
    flagged: bool = False
    flag_reasons: list[str] = Field(default_factory=list)
    upload_id: str | None = None
