from __future__ import annotations

from typing import Any


def _table_columns(rows: list[dict[str, Any]], limit: int = 8) -> list[str]:
    priority = [
        "sample_id", "point_id", "profile_id", "lon", "lat", "ta_ppm", "nb_ppm",
        "susceptibility_si", "apparent_resistivity_ohm_m", "fix_quality",
        "document_type", "page_count",
    ]
    keys: list[str] = []
    for key in priority:
        if any(key in row for row in rows):
            keys.append(key)
    for row in rows[:20]:
        for key in row:
            if key not in keys and key not in {"flagged", "flag_reasons"}:
                keys.append(key)
            if len(keys) >= limit:
                return keys
    return keys[:limit]


def _chart_series(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numeric_keys = []
    for row in rows[:30]:
        for key, value in row.items():
            if key in {"lon", "lat", "flagged"}:
                continue
            if isinstance(value, (int, float)):
                numeric_keys.append(key)
    if not numeric_keys:
        return []
    key = numeric_keys[0]
    label_key = "sample_id" if any("sample_id" in r for r in rows) else None
    series = []
    for row in rows[:24]:
        if key not in row:
            continue
        series.append({
            "label": str(row.get(label_key, len(series) + 1)) if label_key else str(len(series) + 1),
            "value": float(row[key]),
        })
    return series


def _map_bounds(features: list[dict[str, Any]]) -> list[float] | None:
    lons, lats = [], []
    for feature in features:
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2:
            lons.append(float(coords[0]))
            lats.append(float(coords[1]))
    if not lons:
        return None
    pad = 0.01
    return [min(lons) - pad, min(lats) - pad, max(lons) + pad, max(lats) + pad]


def build_display_view(
    *,
    rows: list[dict[str, Any]],
    geojson: dict[str, Any] | None,
    file_format: str,
    instrument_type: str,
    transport: str,
    filename: str | None = None,
) -> dict[str, Any]:
    features = (geojson or {}).get("features", [])
    has_points = any(f.get("geometry", {}).get("type") == "Point" for f in features) or any(
        "lon" in r and "lat" in r for r in rows
    )

    if file_format == "pdf" or instrument_type == "pdf_report":
        doc = rows[0] if rows else {}
        return {
            "display_type": "document",
            "summary": {
                "title": doc.get("filename", filename or "PDF report"),
                "pages": doc.get("page_count", 1),
                "size_bytes": doc.get("size_bytes"),
                "keywords": doc.get("keywords", []),
            },
            "document": {"excerpt": doc.get("text_excerpt", ""), "keywords": doc.get("keywords", [])},
            "table": None,
            "map": None,
            "chart": None,
        }

    table_rows = [{key: row.get(key) for key in _table_columns(rows)} for row in rows[:100]]
    chart = _chart_series(rows)
    if has_points and chart:
        display_type = "mixed"
    elif has_points:
        display_type = "map"
    elif chart:
        display_type = "chart"
    else:
        display_type = "table"

    return {
        "display_type": display_type,
        "summary": {
            "rows": len(rows),
            "flagged": sum(1 for row in rows if row.get("flagged")),
            "instrument_type": instrument_type,
            "file_format": file_format,
            "transport": transport,
            "filename": filename,
        },
        "table": {"columns": _table_columns(rows), "rows": table_rows},
        "map": {
            "type": "FeatureCollection",
            "features": features[:200],
            "bounds": _map_bounds(features),
        } if has_points else None,
        "chart": {"series": chart, "value_label": chart[0]["label"] if chart else None} if chart else None,
        "document": None,
    }


def build_raster_display(
    raster_result: dict[str, Any],
    *,
    instrument_type: str,
    transport: str,
    filename: str | None = None,
) -> dict[str, Any]:
    layers = []
    for key in ("dtm", "dsm", "chm", "slope", "ortho"):
        layer = raster_result.get(key)
        if isinstance(layer, dict):
            layers.append({
                "name": key.upper(),
                "preview_url": layer.get("preview_url"),
                "tile_url_template": layer.get("tile_url_template"),
                "storage_key": layer.get("storage_key"),
            })
    return {
        "display_type": "raster",
        "summary": {
            "instrument_type": instrument_type,
            "transport": transport,
            "filename": filename,
            "point_count": raster_result.get("point_count"),
            "layers": len(layers),
        },
        "raster": {"layers": layers, "bounds": raster_result.get("bounds")},
        "table": {
            "columns": ["field", "value"],
            "rows": [
                {"field": key, "value": value}
                for key, value in raster_result.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            ][:20],
        },
        "map": None,
        "chart": None,
        "document": None,
    }