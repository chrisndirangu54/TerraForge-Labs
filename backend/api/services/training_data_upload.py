from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from models.spectral_classifier.dataset import N_BANDS
from models.thin_section_classifier.dataset import IMAGE_SIZE, THIN_SECTION_CLASSES
from shared.constants import MINERAL_CLASSES


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _thin_manifest_path() -> Path:
    return _repo_root() / "data" / "thin_section" / "manifest.json"


def _spectral_manifest_path() -> Path:
    return _repo_root() / "data" / "spectral" / "manifest.json"


def _normalize_class_name(name: str, classes: list[str]) -> str:
    normalized = name.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "k-feldspar": "k_feldspar",
        "kfeldspar": "k_feldspar",
        "plag": "plagioclase",
        "ta": "coltan",
        "cassiterite": "cassiterite",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in classes:
        raise ValueError(f"Unknown class '{name}'. Expected one of: {', '.join(classes)}")
    return normalized


def _load_manifest(path: Path, *, default_classes: list[str]) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "source": "user_uploads",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classes": default_classes,
        "samples": [],
        "sample_count": 0,
    }


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    payload["sample_count"] = len(payload.get("samples", []))
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _decode_image_grayscale(data: bytes) -> np.ndarray:
    try:
        import cv2  # type: ignore

        array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Could not decode image bytes")
        resized = cv2.resize(image, (IMAGE_SIZE, IMAGE_SIZE))
        return (resized.astype(np.float32) / 255.0).clip(0.0, 1.0)
    except ImportError as exc:
        raise ValueError(
            "Image decode requires opencv-python; upload a .npy PPL/XPL pair instead."
        ) from exc


def _load_thin_section_pair(
    *,
    pair_bytes: bytes | None,
    pair_filename: str | None,
    ppl_bytes: bytes | None,
    xpl_bytes: bytes | None,
) -> np.ndarray:
    if pair_bytes:
        suffix = (pair_filename or "").lower()
        if suffix.endswith(".npy"):
            pair = np.load(io.BytesIO(pair_bytes))
            pair = np.asarray(pair, dtype=np.float32)
            if pair.ndim != 3 or pair.shape[0] != 2:
                raise ValueError("Thin-section .npy must have shape (2, H, W) for PPL/XPL")
            return pair
        raise ValueError("Thin-section pair file must be .npy with shape (2, H, W)")

    if ppl_bytes and xpl_bytes:
        ppl = _decode_image_grayscale(ppl_bytes)
        xpl = _decode_image_grayscale(xpl_bytes)
        return np.stack([ppl, xpl], axis=0).astype(np.float32)

    raise ValueError("Provide either pair_file (.npy) or both ppl_file and xpl_file")


def _resample_spectrum(values: np.ndarray, target_bands: int = N_BANDS) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32).reshape(-1)
    if values.size == target_bands:
        return np.clip(values, 0.01, 0.99)
    if values.size < 2:
        raise ValueError("Spectral vector must contain at least 2 reflectance values")
    source_x = np.linspace(0.0, 1.0, values.size)
    target_x = np.linspace(0.0, 1.0, target_bands)
    resampled = np.interp(target_x, source_x, values).astype(np.float32)
    return np.clip(resampled, 0.01, 0.99)


def _parse_spectral_bytes(data: bytes, filename: str) -> np.ndarray:
    lowered = filename.lower()
    if lowered.endswith(".npy"):
        curve = np.load(io.BytesIO(data))
        return _resample_spectrum(np.asarray(curve, dtype=np.float32))

    if lowered.endswith(".json"):
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, dict):
            for key in ("reflectance", "values", "spectrum", "curve"):
                if key in payload and isinstance(payload[key], list):
                    return _resample_spectrum(np.asarray(payload[key], dtype=np.float32))
            minerals = payload.get("minerals")
            if isinstance(minerals, dict) and minerals:
                first = next(iter(minerals.values()))
                if isinstance(first, dict):
                    for key in ("reflectance", "values", "spectrum"):
                        if key in first and isinstance(first[key], list):
                            return _resample_spectrum(np.asarray(first[key], dtype=np.float32))
        raise ValueError("JSON must include a reflectance array")

    if lowered.endswith(".csv") or lowered.endswith(".tsv"):
        text = data.decode("utf-8", errors="replace")
        delimiter = "\t" if lowered.endswith(".tsv") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            raise ValueError("CSV/TSV file is empty")
        preferred = (
            "reflectance",
            "value",
            "values",
            "refl",
            "usgs_reflectance",
        )
        for column in preferred:
            if column in rows[0]:
                values = [float(row[column]) for row in rows if row.get(column)]
                return _resample_spectrum(np.asarray(values, dtype=np.float32))
        numeric_rows = []
        for row in rows:
            nums = []
            for value in row.values():
                try:
                    nums.append(float(value))
                except (TypeError, ValueError):
                    continue
            if nums:
                numeric_rows.append(nums)
        if numeric_rows:
            longest = max(numeric_rows, key=len)
            return _resample_spectrum(np.asarray(longest, dtype=np.float32))
        raise ValueError("CSV/TSV must include a reflectance column or numeric values")

    raise ValueError("Spectral upload must be .npy, .csv, .tsv, or .json")


def ingest_thin_section_upload(
    *,
    class_name: str,
    pair_bytes: bytes | None = None,
    pair_filename: str | None = None,
    ppl_bytes: bytes | None = None,
    xpl_bytes: bytes | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    normalized = _normalize_class_name(class_name, THIN_SECTION_CLASSES)
    label = THIN_SECTION_CLASSES.index(normalized)
    pair = _load_thin_section_pair(
        pair_bytes=pair_bytes,
        pair_filename=pair_filename,
        ppl_bytes=ppl_bytes,
        xpl_bytes=xpl_bytes,
    )

    sample_id = uuid.uuid4().hex[:12]
    rel_path = Path("data") / "thin_section" / "corpus" / "uploads" / f"{normalized}_{sample_id}.npy"
    abs_path = _repo_root() / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(abs_path, pair)

    manifest_path = _thin_manifest_path()
    manifest = _load_manifest(manifest_path, default_classes=THIN_SECTION_CLASSES)
    record = {
        "id": f"upload-{sample_id}",
        "class_name": normalized,
        "label": label,
        "array_path": str(rel_path).replace("\\", "/"),
        "channels": ["ppl", "xpl"],
        "image_size": int(pair.shape[-1]),
        "source": "user_upload",
        "project_id": project_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest.setdefault("samples", []).append(record)
    manifest["source"] = manifest.get("source", "terraforge_thin_section_corpus")
    manifest["image_size"] = IMAGE_SIZE
    manifest["classes"] = THIN_SECTION_CLASSES
    _write_manifest(manifest_path, manifest)

    return {
        "status": "ingested",
        "dataset": "thin_section",
        "sample_id": record["id"],
        "class_name": normalized,
        "label": label,
        "array_path": record["array_path"],
        "manifest": str(manifest_path),
        "sample_count": manifest["sample_count"],
        "project_id": project_id,
    }


def ingest_spectral_upload(
    *,
    class_name: str,
    file_bytes: bytes,
    filename: str,
    project_id: str | None = None,
) -> dict[str, Any]:
    normalized = _normalize_class_name(class_name, MINERAL_CLASSES)
    label = MINERAL_CLASSES.index(normalized)
    curve = _parse_spectral_bytes(file_bytes, filename)

    sample_id = uuid.uuid4().hex[:12]
    rel_path = Path("data") / "spectral" / "corpus" / "uploads" / f"{normalized}_{sample_id}.npy"
    abs_path = _repo_root() / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(abs_path, curve)

    manifest_path = _spectral_manifest_path()
    manifest = _load_manifest(manifest_path, default_classes=MINERAL_CLASSES)
    record = {
        "id": f"upload-{sample_id}",
        "class_name": normalized,
        "label": label,
        "array_path": str(rel_path).replace("\\", "/"),
        "n_bands": int(curve.shape[0]),
        "source": "user_upload",
        "project_id": project_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
    }
    manifest.setdefault("samples", []).append(record)
    manifest["source"] = manifest.get("source", "usgs_spectral_corpus")
    manifest["n_bands"] = N_BANDS
    manifest["classes"] = MINERAL_CLASSES
    _write_manifest(manifest_path, manifest)

    return {
        "status": "ingested",
        "dataset": "spectral",
        "sample_id": record["id"],
        "class_name": normalized,
        "label": label,
        "array_path": record["array_path"],
        "n_bands": int(curve.shape[0]),
        "manifest": str(manifest_path),
        "sample_count": manifest["sample_count"],
        "project_id": project_id,
    }


def get_training_manifest(task: str) -> dict[str, Any]:
    normalized = task.lower()
    if normalized == "thin_section":
        from models.thin_section_classifier.dataset import get_dataset_manifest

        return get_dataset_manifest()
    if normalized == "spectral":
        from models.spectral_classifier.dataset import get_dataset_manifest

        return get_dataset_manifest()
    raise ValueError(f"Unknown training task: {task}")


def get_domain_eval_report() -> dict[str, Any]:
    path = _repo_root() / "artifacts" / "eval_domain_models_cv.json"
    if not path.exists():
        return {"error": "No domain CV report yet", "models": {}}
    return json.loads(path.read_text(encoding="utf-8"))