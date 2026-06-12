from __future__ import annotations

import json
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def import_minpet_catalog(source_dir: Path, *, project_id: str | None = None) -> dict:
    """Scaffold MINPET thin-section import into data/thin_section/corpus/."""
    root = repo_root()
    target = root / "data" / "thin_section" / "corpus"
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    if source_dir.exists():
        for path in source_dir.glob("*.jpg"):
            destination = target / path.name
            shutil.copy2(path, destination)
            copied.append(str(destination))
    manifest = {
        "source": "minpet",
        "project_id": project_id,
        "files": copied,
        "status": "imported" if copied else "empty_source",
    }
    manifest_path = root / "data" / "thin_section" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"manifest": str(manifest_path), **manifest}


def import_envi_spectral(source_hdr: Path, *, project_id: str | None = None) -> dict:
    """Scaffold ENVI reflectance import into data/spectral/corpus/."""
    root = repo_root()
    target = root / "data" / "spectral" / "corpus"
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    if source_hdr.exists():
        for suffix in (".hdr", ".dat", ".img"):
            candidate = source_hdr.with_suffix(suffix)
            if candidate.exists():
                destination = target / candidate.name
                shutil.copy2(candidate, destination)
                copied.append(str(destination))
    manifest = {
        "source": "envi",
        "project_id": project_id,
        "files": copied,
        "status": "imported" if copied else "missing_hdr",
    }
    manifest_path = root / "data" / "spectral" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"manifest": str(manifest_path), **manifest}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import MINPET/ENVI field formats")
    parser.add_argument("--format", choices=["minpet", "envi"], required=True)
    parser.add_argument("--source", required=True, help="Source directory or ENVI .hdr path")
    parser.add_argument("--project-id", default=None)
    args = parser.parse_args()
    source = Path(args.source)
    if args.format == "minpet":
        result = import_minpet_catalog(source, project_id=args.project_id)
    else:
        result = import_envi_spectral(source, project_id=args.project_id)
    print(json.dumps(result, indent=2))