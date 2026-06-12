from __future__ import annotations

import os
from urllib.parse import quote


def titiler_base_url() -> str:
    return os.getenv("TITILER_BASE_URL", "http://localhost:8080").rstrip("/")


def titiler_enabled() -> bool:
    return os.getenv("TITILER_ENABLED", "true").lower() in {"1", "true", "yes"}


def cog_s3_url(storage_key: str) -> str:
    bucket = os.getenv("MINIO_BUCKET", "terraforge")
    return f"s3://{bucket}/{storage_key}"


def titiler_tile_url_template(storage_key: str) -> str:
    cog_url = quote(cog_s3_url(storage_key), safe="")
    return f"{titiler_base_url()}/cog/tiles/{{z}}/{{x}}/{{y}}.png?url={cog_url}"


def titiler_preview_url(storage_key: str) -> str:
    cog_url = quote(cog_s3_url(storage_key), safe="")
    return f"{titiler_base_url()}/cog/preview.png?url={cog_url}"


def titiler_metadata_url(storage_key: str) -> str:
    cog_url = quote(cog_s3_url(storage_key), safe="")
    return f"{titiler_base_url()}/cog/info?url={cog_url}"


def resolve_tile_urls(storage_key: str) -> dict[str, str]:
    if titiler_enabled():
        return {
            "tile_url_template": titiler_tile_url_template(storage_key),
            "preview_url": titiler_preview_url(storage_key),
            "metadata_url": titiler_metadata_url(storage_key),
            "tile_provider": "titiler",
        }
    return {
        "tile_url_template": f"/mapping/cog/{storage_key}/tiles/{{z}}/{{x}}/{{y}}.png",
        "preview_url": f"/mapping/cog/{storage_key}/preview.png",
        "metadata_url": f"/mapping/cog/{storage_key}/metadata",
        "tile_provider": "fastapi",
    }