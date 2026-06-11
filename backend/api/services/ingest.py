from __future__ import annotations

from shared.schemas.observation import ObservationRecord

PARSER_VERSIONS: dict[str, str] = {
    "xrf_bruker": "xrf_bruker@1.0.0",
    "terrameter": "terrameter@1.0.0",
    "kappameter": "kappameter@1.0.0",
    "gnss_trimble": "gnss_trimble@1.0.0",
}


def parser_version_for(instrument_type: str) -> str:
    return PARSER_VERSIONS.get(instrument_type, f"{instrument_type}@1.0.0")


def rows_to_observations(
    rows: list[dict],
    *,
    project_id: str,
    source: str,
    parser_version: str,
    instrument_type: str | None = None,
    upload_id: str | None = None,
    crs: str = "EPSG:4326",
) -> list[ObservationRecord]:
    observations: list[ObservationRecord] = []
    for row in rows:
        lon = row.get("lon")
        lat = row.get("lat")
        sample_id = row.get("sample_id") or row.get("profile_id")
        payload = {
            key: value
            for key, value in row.items()
            if key
            not in {"lon", "lat", "sample_id", "profile_id", "flagged", "flag_reasons"}
        }
        observations.append(
            ObservationRecord(
                project_id=project_id,
                source=source,
                parser_version=parser_version,
                crs=crs,
                instrument_type=instrument_type,
                sample_id=str(sample_id) if sample_id is not None else None,
                lon=float(lon) if lon is not None else None,
                lat=float(lat) if lat is not None else None,
                data=payload,
                flagged=bool(row.get("flagged", False)),
                flag_reasons=list(row.get("flag_reasons") or []),
                upload_id=upload_id,
            )
        )
    return observations


def ingest_observations(observations: list[ObservationRecord]) -> dict:
    from backend.api.ingest.store import get_ingest_store

    if not observations:
        return {"inserted": 0, "project_id": None}
    store = get_ingest_store()
    inserted = store.insert_observations(observations)
    return {
        "inserted": inserted,
        "project_id": observations[0].project_id,
        "source": observations[0].source,
        "parser_version": observations[0].parser_version,
        "crs": observations[0].crs,
    }


def list_project_observations(
    *,
    project_id: str | None = None,
    project_ids: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    from backend.api.ingest.store import get_ingest_store

    store = get_ingest_store()
    items = store.list_observations(
        project_id=project_id,
        project_ids=project_ids,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "limit": limit, "offset": offset, "count": len(items)}
