from __future__ import annotations

import json

import numpy as np
import pytest

from backend.api.services import training_data_upload as upload_mod


@pytest.fixture()
def repo_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(upload_mod, "_repo_root", lambda: tmp_path)
    return tmp_path


def test_ingest_thin_section_npy_pair(repo_tmp):
    pair = np.stack(
        [
            np.full((64, 64), 0.8, dtype=np.float32),
            np.full((64, 64), 0.4, dtype=np.float32),
        ]
    )
    buffer = __import__("io").BytesIO()
    np.save(buffer, pair)
    result = upload_mod.ingest_thin_section_upload(
        class_name="quartz",
        pair_bytes=buffer.getvalue(),
        pair_filename="pair.npy",
        project_id="matuu",
    )
    assert result["status"] == "ingested"
    assert result["class_name"] == "quartz"
    manifest = json.loads((repo_tmp / "data/thin_section/manifest.json").read_text())
    assert manifest["sample_count"] == 1


def test_ingest_spectral_json_reflectance(repo_tmp):
    payload = json.dumps({"reflectance": [0.2 + i * 0.001 for i in range(224)]})
    result = upload_mod.ingest_spectral_upload(
        class_name="coltan",
        file_bytes=payload.encode("utf-8"),
        filename="usgs_coltan.json",
        project_id="matuu",
    )
    assert result["status"] == "ingested"
    assert result["n_bands"] == 224
    manifest = json.loads((repo_tmp / "data/spectral/manifest.json").read_text())
    assert manifest["sample_count"] == 1


def test_unknown_class_rejected(repo_tmp):
    pair = np.zeros((2, 32, 32), dtype=np.float32)
    buffer = __import__("io").BytesIO()
    np.save(buffer, pair)
    with pytest.raises(ValueError):
        upload_mod.ingest_thin_section_upload(
            class_name="not_a_mineral",
            pair_bytes=buffer.getvalue(),
            pair_filename="pair.npy",
        )