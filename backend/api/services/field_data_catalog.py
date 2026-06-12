from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def catalog_field_datasets() -> dict[str, Any]:
    root = _repo_root()
    catalogs: list[dict[str, Any]] = []

    manifests = [
        ("thin_section", root / "data" / "thin_section" / "manifest.json"),
        ("spectral", root / "data" / "spectral" / "manifest.json"),
        ("field_geochem", root / "data" / "field" / "matuu_synthetic.geojson"),
        ("gbif", root / "data" / "geobotany" / "gbif_kenya_metallophytes.json"),
        ("inaturalist", root / "data" / "geobotany" / "inaturalist_kenya_plants.json"),
    ]

    for name, path in manifests:
        if not path.exists():
            catalogs.append({"name": name, "path": str(path), "status": "missing"})
            continue
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            catalogs.append(
                {
                    "name": name,
                    "path": str(path),
                    "status": "ready",
                    "samples": payload.get("sample_count", payload.get("records")),
                    "classes": payload.get("classes"),
                }
            )
        else:
            catalogs.append(
                {
                    "name": name,
                    "path": str(path),
                    "status": "ready",
                    "size_bytes": path.stat().st_size,
                }
            )

    return {
        "catalogs": catalogs,
        "ingest_instructions": {
            "thin_section": "Place PPL/XPL pairs under data/thin_section/corpus/ and rebuild manifest",
            "spectral": "Export ENVI reflectance as .npy under data/spectral/corpus/",
            "field_geochem": "Upload geojson/csv via /ingest/observations with assay fields",
        },
    }


def register_field_upload(
    *,
    dataset: str,
    files: list[str],
    project_id: str | None = None,
) -> dict[str, Any]:
    root = _repo_root() / "data" / "uploads" / (project_id or "global")
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / f"{dataset}_upload_manifest.json"
    payload = {
        "dataset": dataset,
        "project_id": project_id,
        "files": files,
        "status": "registered",
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"manifest": str(manifest_path), **payload}