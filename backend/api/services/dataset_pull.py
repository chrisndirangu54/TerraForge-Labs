from __future__ import annotations

from typing import Any


def pull_all_datasets(*, include_gbif: bool = True) -> dict[str, Any]:
    from scripts.datasets.pull_field_data import pull_field_datasets

    result: dict[str, Any] = {"field": pull_field_datasets()}
    if include_gbif:
        try:
            from scripts.datasets.pull_gbif import pull_gbif_geobotany

            result["gbif"] = pull_gbif_geobotany()
        except Exception as exc:
            result["gbif"] = {"status": "error", "error": str(exc)}
    return result