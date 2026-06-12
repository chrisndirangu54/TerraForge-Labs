from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

METALLOPHYTE_QUERIES = [
    "Haumaniastrum",
    "Cyanotis",
    "Aeolanthus",
    "Euphorbia",
    "Commelina",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fetch_gbif_occurrences(
    *,
    query: str,
    country: str = "KE",
    limit: int = 120,
) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "country": country,
            "hasCoordinate": "true",
            "limit": str(limit),
        }
    )
    url = f"https://api.gbif.org/v1/occurrence/search?{params}"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    results: list[dict] = []
    for row in payload.get("results", []):
        results.append(
            {
                "species": row.get("species") or row.get("scientificName"),
                "decimalLatitude": row.get("decimalLatitude"),
                "decimalLongitude": row.get("decimalLongitude"),
                "year": row.get("year"),
                "basisOfRecord": row.get("basisOfRecord"),
                "datasetKey": row.get("datasetKey"),
            }
        )
    return results


def pull_gbif_geobotany(*, country: str = "KE", limit_per_query: int = 80) -> dict:
    target_dir = repo_root() / "data" / "geobotany"
    target_dir.mkdir(parents=True, exist_ok=True)
    combined: list[dict] = []
    by_query: dict[str, int] = {}
    for query in METALLOPHYTE_QUERIES:
        rows = fetch_gbif_occurrences(query=query, country=country, limit=limit_per_query)
        by_query[query] = len(rows)
        combined.extend(rows)

    output = target_dir / "gbif_kenya_metallophytes.json"
    output.write_text(json.dumps({"records": combined, "queries": by_query}, indent=2))
    return {
        "status": "ok",
        "records": len(combined),
        "output": str(output),
        "queries": by_query,
    }


if __name__ == "__main__":
    print(json.dumps(pull_gbif_geobotany(), indent=2))