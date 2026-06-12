from __future__ import annotations

from typing import Any

from backend.api.services.capture_display import build_display_view


def build_job_display(job: dict[str, Any]) -> dict[str, Any]:
    """Build a UI-friendly display envelope from a job store record."""

    status = job.get("status", "unknown")
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    job_type = job.get("job_type", "job")

    summary: dict[str, Any] = {
        "job_type": job_type,
        "status": status,
    }
    if job.get("error"):
        summary["error"] = job["error"]

    timeline = [
        {"step": "queued", "done": status != "queued"},
        {"step": "running", "done": status in {"complete", "failed"}},
        {
            "step": "complete" if status != "failed" else "failed",
            "done": status in {"complete", "failed"},
        },
    ]

    raster_layers: list[dict[str, Any]] = []
    for key in ("dtm", "dsm", "chm", "slope", "ortho", "dsm_uav"):
        layer = result.get(key)
        if isinstance(layer, dict) and layer.get("preview_url"):
            raster_layers.append(
                {
                    "name": key.upper(),
                    "preview_url": layer["preview_url"],
                    "tile_url_template": layer.get("tile_url_template"),
                    "storage_key": layer.get("storage_key"),
                }
            )

    if raster_layers:
        return {
            "display_type": "raster",
            "summary": {**summary, "layers": len(raster_layers)},
            "raster": {"layers": raster_layers, "bounds": result.get("bounds")},
            "table": _scalar_table(result),
            "timeline": timeline,
        }

    if result.get("observations") or result.get("points"):
        rows = result.get("observations") or result.get("points") or []
        if isinstance(rows, list) and rows:
            return build_display_view(
                rows=rows,
                geojson=None,
                file_format="job",
                instrument_type=job_type,
                transport="pipeline",
            )

    table_rows = _scalar_table(result)
    if table_rows:
        return {
            "display_type": "table",
            "summary": summary,
            "table": {"columns": ["field", "value"], "rows": table_rows},
            "timeline": timeline,
        }

    return {
        "display_type": "status",
        "summary": summary,
        "timeline": timeline,
        "message": f"Job {job_type} is {status}.",
    }


def _scalar_table(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in result.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append({"field": key, "value": value})
        elif isinstance(value, dict) and len(value) <= 4:
            for sub_key, sub_val in value.items():
                if isinstance(sub_val, (str, int, float, bool)) or sub_val is None:
                    rows.append({"field": f"{key}.{sub_key}", "value": sub_val})
    return rows[:40]


def attach_display(payload: dict[str, Any]) -> dict[str, Any]:
    if "display" in payload:
        return payload
    if payload.get("status") in {"complete", "failed", "running", "queued"}:
        payload = {**payload, "display": build_job_display(payload)}
    return payload