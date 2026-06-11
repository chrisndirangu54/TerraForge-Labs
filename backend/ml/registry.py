from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Literal

Stage = Literal["staging", "production"]

_REGISTRY: "ModelRegistry | None" = None
VALID_STAGES = frozenset({"staging", "production"})
SUPPORTED_TASKS = frozenset(
    {
        "mineral",
        "geobotany",
        "thin_section",
        "spectral",
        "grain_segmentation",
    }
)


class ModelRegistry(ABC):
    @abstractmethod
    def register_version(
        self,
        task: str,
        *,
        version: str | None = None,
        params: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        artifact_path: str | None = None,
        stage: Stage = "staging",
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_versions(self, task: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_version(self, task: str, version: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def get_production(self, task: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def promote(self, task: str, version: str, stage: Stage) -> dict[str, Any]:
        raise NotImplementedError


class MemoryModelRegistry(ModelRegistry):
    def __init__(self) -> None:
        self._versions: dict[str, dict[str, dict[str, Any]]] = {}
        self._production: dict[str, str] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for task in SUPPORTED_TASKS:
            version = "v0.1.0-baseline"
            self._versions.setdefault(task, {})[version] = {
                "task": task,
                "version": version,
                "stage": "production",
                "params": {"backbone": "torchvision-resnet18", "feature_dim": 512},
                "metrics": {"accuracy": 0.72},
                "artifact_path": f"registry://{task}/{version}",
                "created_at": now,
            }
            self._production[task] = version

    def register_version(
        self,
        task: str,
        *,
        version: str | None = None,
        params: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        artifact_path: str | None = None,
        stage: Stage = "staging",
    ) -> dict[str, Any]:
        if task not in SUPPORTED_TASKS:
            raise ValueError(f"Unsupported task: {task}")
        if stage not in VALID_STAGES:
            raise ValueError(f"Invalid stage: {stage}")

        resolved_version = version or f"v{uuid.uuid4().hex[:8]}"
        record = {
            "task": task,
            "version": resolved_version,
            "stage": stage,
            "params": params or {},
            "metrics": metrics or {},
            "artifact_path": artifact_path
            or f"registry://{task}/{resolved_version}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._versions.setdefault(task, {})[resolved_version] = record
        if stage == "production":
            self._demote_other_production(task, resolved_version)
            self._production[task] = resolved_version
        return record

    def list_versions(self, task: str) -> list[dict[str, Any]]:
        versions = list(self._versions.get(task, {}).values())
        versions.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return versions

    def get_version(self, task: str, version: str) -> dict[str, Any] | None:
        return self._versions.get(task, {}).get(version)

    def get_production(self, task: str) -> dict[str, Any] | None:
        version = self._production.get(task)
        if not version:
            return None
        return self.get_version(task, version)

    def promote(self, task: str, version: str, stage: Stage) -> dict[str, Any]:
        record = self.get_version(task, version)
        if record is None:
            raise ValueError(f"Version not found: {task}/{version}")
        if stage not in VALID_STAGES:
            raise ValueError(f"Invalid stage: {stage}")

        record = {**record, "stage": stage}
        self._versions[task][version] = record
        if stage == "production":
            self._demote_other_production(task, version)
            self._production[task] = version
        return record

    def _demote_other_production(self, task: str, keep_version: str) -> None:
        for version, record in self._versions.get(task, {}).items():
            if version != keep_version and record.get("stage") == "production":
                self._versions[task][version] = {**record, "stage": "staging"}


class MlflowModelRegistry(ModelRegistry):
    """Optional MLflow-backed registry when the ml group is installed."""

    def __init__(self) -> None:
        import mlflow

        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
        mlflow.set_tracking_uri(tracking_uri)
        self._mlflow = mlflow
        self._memory = MemoryModelRegistry()

    def register_version(
        self,
        task: str,
        *,
        version: str | None = None,
        params: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        artifact_path: str | None = None,
        stage: Stage = "staging",
    ) -> dict[str, Any]:
        record = self._memory.register_version(
            task,
            version=version,
            params=params,
            metrics=metrics,
            artifact_path=artifact_path,
            stage=stage,
        )
        with self._mlflow.start_run(run_name=f"{task}-{record['version']}"):
            if params:
                self._mlflow.log_params({f"param_{k}": str(v) for k, v in params.items()})
            if metrics:
                self._mlflow.log_metrics(
                    {k: float(v) for k, v in metrics.items() if _is_numeric(v)}
                )
        return record

    def list_versions(self, task: str) -> list[dict[str, Any]]:
        return self._memory.list_versions(task)

    def get_version(self, task: str, version: str) -> dict[str, Any] | None:
        return self._memory.get_version(task, version)

    def get_production(self, task: str) -> dict[str, Any] | None:
        return self._memory.get_production(task)

    def promote(self, task: str, version: str, stage: Stage) -> dict[str, Any]:
        return self._memory.promote(task, version, stage)


def _is_numeric(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _backend_name() -> str:
    configured = os.getenv("MODEL_REGISTRY_BACKEND", "").lower()
    if configured:
        return configured
    try:
        import mlflow  # noqa: F401

        return "mlflow" if os.getenv("MLFLOW_TRACKING_URI") else "memory"
    except ImportError:
        return "memory"


def get_model_registry() -> ModelRegistry:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY

    backend = _backend_name()
    if backend == "mlflow":
        try:
            _REGISTRY = MlflowModelRegistry()
        except ImportError:
            _REGISTRY = MemoryModelRegistry()
    else:
        _REGISTRY = MemoryModelRegistry()
    return _REGISTRY


def reset_model_registry() -> None:
    global _REGISTRY
    _REGISTRY = None