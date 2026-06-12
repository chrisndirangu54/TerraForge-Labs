from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

RESEARCH_TAXA = [
    "Haumaniastrum",
    "Ocimum",
    "Commelina",
    "Crotalaria",
    "Silene",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fetch_inaturalist_observations(
    *,
    taxon_name: str,
    place_id: int = 8173,
    per_page: int = 80,
) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "taxon_name": taxon_name,
            "place_id": str(place_id),
            "quality_grade": "research",
            "photos": "true",
            "geo": "true",
            "per_page": str(per_page),
        }
    )
    url = f"https://api.inaturalist.org/v1/observations?{params}"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows: list[dict] = []
    for item in payload.get("results", []):
        photo_url = None
        photos = item.get("photos") or []
        if photos:
            photo_url = photos[0].get("url")
            if photo_url and "square" in photo_url:
                photo_url = photo_url.replace("square", "medium")
        rows.append(
            {
                "species_guess": item.get("species_guess") or item.get("taxon", {}).get("name"),
                "latitude": item.get("location", "").split(",")[0] if item.get("location") else None,
                "longitude": item.get("location", "").split(",")[1] if item.get("location") else None,
                "observed_on_year": int(str(item.get("observed_on", "2020"))[:4]),
                "quality_grade_score": 0.95 if item.get("quality_grade") == "research" else 0.7,
                "photo_url": photo_url,
            }
        )
    return rows


def download_observation_images(records: list[dict]) -> dict[str, int]:
    from models.geobotany_classifier.dataset_images import (
        _image_path_for_record,
        corpus_dir,
    )
    from models.geobotany_classifier.dataset_sota import _species_to_class

    corpus_dir().mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    for record in records:
        photo_url = record.get("photo_url")
        if not photo_url:
            skipped += 1
            continue
        class_idx = _species_to_class(record.get("species_guess"))
        target = _image_path_for_record(record, class_idx)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            skipped += 1
            continue
        try:
            with urllib.request.urlopen(photo_url, timeout=30) as response:
                target.write_bytes(response.read())
            downloaded += 1
        except Exception:
            skipped += 1
    return {"downloaded": downloaded, "skipped": skipped}


def pull_inaturalist_geobotany(*, download_images: bool = False) -> dict:
    target_dir = repo_root() / "data" / "geobotany"
    target_dir.mkdir(parents=True, exist_ok=True)
    combined: list[dict] = []
    by_taxon: dict[str, int] = {}
    for taxon in RESEARCH_TAXA:
        rows = fetch_inaturalist_observations(taxon_name=taxon)
        by_taxon[taxon] = len(rows)
        combined.extend(rows)

    output = target_dir / "inaturalist_kenya_plants.json"
    output.write_text(json.dumps({"results": combined, "taxa": by_taxon}, indent=2))
    result = {
        "status": "ok",
        "records": len(combined),
        "output": str(output),
        "taxa": by_taxon,
    }
    if download_images:
        result["images"] = download_observation_images(combined)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--download-images", action="store_true")
    args = parser.parse_args()
    print(json.dumps(pull_inaturalist_geobotany(download_images=args.download_images), indent=2))