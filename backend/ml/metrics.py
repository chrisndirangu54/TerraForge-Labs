from __future__ import annotations

from typing import Any

from backend.ml.registry import Stage, get_model_registry


def log_training_run(
    task: str,
    *,
    params: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    artifact_path: str | None = None,
    version: str | None = None,
    stage: Stage = "staging",
) -> dict[str, Any]:
    registry = get_model_registry()
    return registry.register_version(
        task,
        version=version,
        params=params,
        metrics=metrics,
        artifact_path=artifact_path,
        stage=stage,
    )
