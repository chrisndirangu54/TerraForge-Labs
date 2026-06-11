from __future__ import annotations

from pydantic import BaseModel, Field


class ArtifactRecord(BaseModel):
    project_id: str
    source: str
    parser_version: str
    artifact_type: str
    uri: str
    checksum: str | None = None
    crs: str | None = None
    metadata: dict = Field(default_factory=dict)
