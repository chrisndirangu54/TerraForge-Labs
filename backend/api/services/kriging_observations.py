from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def observations_from_geojson(path: Path, *, element: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for feature in payload.get("features", []):
        props = dict(feature.get("properties") or {})
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        if len(coords) >= 2:
            props["lon"] = float(coords[0])
            props["lat"] = float(coords[1])
        if element not in props:
            continue
        rows.append(props)
    return rows


def observations_from_ingest(
    *,
    project_id: str | None,
    element: str,
    limit: int = 200,
) -> list[dict[str, Any]]:
    from backend.api.services.ingest import list_project_observations

    result = list_project_observations(project_id=project_id, limit=limit)
    rows: list[dict[str, Any]] = []
    for item in result["items"]:
        data = item.get("data") or {}
        if element not in data and element.replace("_ppm", "") not in str(data):
            if element not in data:
                continue
        row = {
            "sample_id": item.get("sample_id"),
            "lon": item.get("lon"),
            "lat": item.get("lat"),
            element: data.get(element),
            **{
                key: value
                for key, value in data.items()
                if key not in {element, "lon", "lat"}
            },
        }
        if row.get(element) is None:
            continue
        rows.append(row)
    return rows


def resolve_kriging_observations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("observations"):
        return list(payload["observations"])

    element = payload.get("element", "ta_ppm")
    project_id = payload.get("project_id")
    if project_id:
        ingest_rows = observations_from_ingest(
            project_id=str(project_id),
            element=element,
            limit=int(payload.get("max_points", 200)),
        )
        if ingest_rows:
            return ingest_rows

    dataset = payload.get("dataset", "matuu_synthetic")
    fixture = _repo_root() / "tests" / "fixtures" / f"{dataset}.geojson"
    if fixture.exists():
        return observations_from_geojson(fixture, element=element)

    data_path = payload.get("dataset_path")
    if data_path:
        path = Path(data_path)
        if not path.is_absolute():
            path = _repo_root() / path
        if path.exists() and path.suffix == ".geojson":
            return observations_from_geojson(path, element=element)

    return []


def extract_kriging_points(
    observations: list[dict[str, Any]],
    *,
    element: str = "ta_ppm",
) -> tuple[list[float], list[float], list[float]]:
    from shared.constants import KRIGING_GRID_RESOLUTION

    xs: list[float] = []
    ys: list[float] = []
    values: list[float] = []
    spacing = KRIGING_GRID_RESOLUTION

    for index, row in enumerate(observations):
        if element not in row or row[element] is None:
            continue
        value = float(row[element])
        if "lon" in row and "lat" in row:
            xs.append(float(row["lon"]))
            ys.append(float(row["lat"]))
        elif "x" in row and "y" in row:
            xs.append(float(row["x"]))
            ys.append(float(row["y"]))
        else:
            cols = max(3, index + 3)
            xs.append(float((index % cols) * spacing))
            ys.append(float((index // cols) * spacing))
        values.append(value)

    return xs, ys, values