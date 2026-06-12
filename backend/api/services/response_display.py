from __future__ import annotations

from typing import Any

from backend.api.services.capture_display import build_display_view

LIST_KEYS = (
    "items",
    "records",
    "boreholes",
    "scenes",
    "catalogs",
    "devices",
    "results",
    "layers",
    "settlements",
    "features",
    "packs",
)

CLASSIFICATION_KEYS = ("label", "species", "confidence", "top3", "top_k", "classes")


def _table_columns(rows: list[dict[str, Any]], limit: int = 8) -> list[str]:
    if not rows:
        return []
    keys: list[str] = []
    for row in rows[:20]:
        for key in row:
            if key not in keys:
                keys.append(key)
            if len(keys) >= limit:
                return keys
    return keys


def _scalar_table(record: dict[str, Any]) -> dict[str, Any] | None:
    rows = [
        {"field": key, "value": value}
        for key, value in record.items()
        if isinstance(value, (str, int, float, bool)) and key != "display"
    ]
    if len(rows) < 2:
        return None
    return {
        "display_type": "table",
        "summary": {"fields": len(rows)},
        "table": {"columns": ["field", "value"], "rows": rows},
    }


def _list_table(rows: list[dict[str, Any]], source: str) -> dict[str, Any]:
    columns = _table_columns(rows)
    table_rows = [{col: row.get(col) for col in columns} for row in rows[:100]]
    display: dict[str, Any] = {
        "display_type": "table",
        "summary": {"rows": len(rows), "source": source},
        "table": {"columns": columns, "rows": table_rows},
    }
    if any("lon" in row and "lat" in row for row in rows):
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row.get("lon", 37.5), row.get("lat", -1.15)]},
                "properties": row,
            }
            for row in rows[:200]
            if row.get("lon") is not None and row.get("lat") is not None
        ]
        if features:
            display["display_type"] = "mixed"
            display["map"] = {"type": "FeatureCollection", "features": features}
    return display


def _classification_display(record: dict[str, Any]) -> dict[str, Any] | None:
    label = record.get("label") or record.get("species")
    confidence = record.get("confidence") or record.get("model_confidence")
    if label is None and confidence is None:
        return None

    top = record.get("top3") or record.get("top_k") or record.get("classes")
    rows: list[dict[str, Any]] = []
    if isinstance(top, list):
        for entry in top[:5]:
            if isinstance(entry, dict):
                rows.append(entry)
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                rows.append({"label": entry[0], "confidence": entry[1]})
            else:
                rows.append({"label": str(entry)})
    if not rows:
        rows = [{"label": label, "confidence": confidence}]

    summary = {
        "label": label,
        "confidence": confidence,
        "accelerator": record.get("accelerator") or record.get("model"),
        "task": record.get("task"),
    }
    return {
        "display_type": "chart",
        "summary": {k: v for k, v in summary.items() if v is not None},
        "chart": {
            "series": [
                {
                    "label": str(row.get("label") or row.get("species") or f"#{index + 1}"),
                    "value": float(row.get("confidence") or row.get("score") or 0),
                }
                for index, row in enumerate(rows)
                if row.get("confidence") is not None or row.get("score") is not None
            ]
            or [{"label": str(label), "value": float(confidence or 0)}],
        },
        "table": {
            "columns": list(rows[0].keys()) if rows else ["label", "confidence"],
            "rows": rows,
        },
    }


def infer_display(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        if isinstance(value.get("display"), dict):
            return value["display"]
        if any(key in value for key in CLASSIFICATION_KEYS):
            return _classification_display(value)
        for key in LIST_KEYS:
            items = value.get(key)
            if isinstance(items, list) and items and isinstance(items[0], dict):
                return _list_table(items, key)
        if isinstance(value.get("layer_groups"), dict):
            rows = [
                {"group": group, "layers": ", ".join(layers)}
                for group, layers in value["layer_groups"].items()
            ]
            return _list_table(rows, "layer_groups")
        return _scalar_table(value)
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return _list_table(value, "items")
    return None


def enrich_response(value: Any) -> Any:
    """Attach a structured display view to API/stub payloads for UI rendering."""
    if not isinstance(value, dict):
        return value
    if isinstance(value.get("display"), dict):
        return value

    display = infer_display(value)
    if display is None and isinstance(value.get("result"), dict):
        display = infer_display(value["result"])

    if display is None:
        return value

    enriched = dict(value)
    enriched["display"] = display
    return enriched


def enrich_capture_like(
    *,
    rows: list[dict[str, Any]],
    instrument_type: str = "generic",
    transport: str = "api",
    filename: str | None = None,
    file_format: str = "json",
) -> dict[str, Any]:
    preview = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r.get("lon", 37.5), r.get("lat", -1.15)]},
                "properties": r,
            }
            for r in rows
            if r.get("lon") is not None
        ],
    }
    return build_display_view(
        rows=rows,
        geojson=preview,
        file_format=file_format,
        instrument_type=instrument_type,
        transport=transport,
        filename=filename,
    )