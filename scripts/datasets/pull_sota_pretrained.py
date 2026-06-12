from __future__ import annotations

import json
import shutil
from pathlib import Path

from shared.sota_catalog import SOTA_DATASETS, SOTA_PRETRAINED_MODELS


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pull_sota_assets(*, prefetch_torch_weights: bool = False) -> dict:
    root = repo_root()
    sota_dir = root / "data" / "sota"
    sota_dir.mkdir(parents=True, exist_ok=True)

    usgs_src = root / "tests" / "fixtures" / "usgs_mineral_signatures.json"
    usgs_dst = sota_dir / "usgs_mineral_signatures.json"
    if usgs_src.exists():
        shutil.copy2(usgs_src, usgs_dst)

    manifest = {
        "datasets": SOTA_DATASETS,
        "pretrained_models": SOTA_PRETRAINED_MODELS,
        "files": {
            "usgs_mineral_signatures": str(usgs_dst) if usgs_dst.exists() else None,
        },
    }

    torch_status = "skipped"
    if prefetch_torch_weights:
        try:
            from backend.ml.pretrained_backbone import build_backbone

            build_backbone("torchvision-resnet18")
            build_backbone("torchvision-efficientnet-b0")
            torch_status = "cached"
        except Exception as exc:
            torch_status = f"error:{exc}"

    manifest["torchvision_weights"] = torch_status
    manifest_path = sota_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"status": "ok", "manifest": str(manifest_path), **manifest}


if __name__ == "__main__":
    print(json.dumps(pull_sota_assets(), indent=2))