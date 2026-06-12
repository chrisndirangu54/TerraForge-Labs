from __future__ import annotations

import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pull_field_datasets() -> dict[str, str]:
    root = repo_root()
    fixtures = root / "tests" / "fixtures"
    target = root / "data" / "field"
    target.mkdir(parents=True, exist_ok=True)

    copied: dict[str, str] = {}
    for name in (
        "matuu_synthetic.geojson",
        "sample_bruker_export.csv",
        "sample_terrameter.xml",
        "sample_gnss.nmea",
    ):
        source = fixtures / name
        if not source.exists():
            continue
        destination = target / name
        shutil.copy2(source, destination)
        copied[name] = str(destination)

    return {"status": "ok", "files": copied, "target_dir": str(target)}


if __name__ == "__main__":
    import json

    print(json.dumps(pull_field_datasets(), indent=2))