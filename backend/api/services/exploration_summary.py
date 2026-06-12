from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _artifacts_dir() -> Path:
    return _repo_root() / "artifacts"


def _block_model_csv_path(*, job_id: str | None = None) -> Path | None:
    artifacts = _artifacts_dir()
    if job_id:
        path = artifacts / f"{job_id}_block_model.csv"
        return path if path.exists() else None

    candidates = sorted(
        artifacts.glob("*_block_model.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _latest_block_model_csv() -> Path | None:
    return _block_model_csv_path()


def _deposit_artifact_urls(csv_path: Path | None) -> dict[str, str]:
    if csv_path is None:
        base = "deposit_model"
    else:
        base = csv_path.name.removesuffix("_block_model.csv")
    return {
        "mesh_url": f"minio://models/{base}.obj",
        "block_model_url": f"minio://models/{base}_block_model.csv",
        "probability_map_url": f"minio://models/{base}_probability.tif",
        "tileset_url": f"minio://deposit-models/{base}/tileset.json",
    }


def load_blocks_preview(
    limit: int = 24,
    *,
    job_id: str | None = None,
) -> list[dict[str, Any]]:
    csv_path = _block_model_csv_path(job_id=job_id)
    if csv_path is None:
        return [
            {
                "x": i,
                "y": i % 4,
                "z": i % 5,
                "ta_ppm_mean": 110 + i * 2,
                "ta_ppm_p10": 95 + i,
                "ta_ppm_p90": 130 + i * 2,
                "unit": "pegmatite" if i % 2 == 0 else "saprolite",
            }
            for i in range(min(limit, 20))
        ]

    rows: list[dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "x": float(row.get("x", 0) or 0),
                    "y": float(row.get("y", 0) or 0),
                    "z": float(row.get("z", 0) or 0),
                    "ta_ppm_mean": float(row.get("ta_ppm_mean", row.get("ta_ppm", 0)) or 0),
                    "ta_ppm_p10": float(row.get("ta_ppm_p10", 0) or 0),
                    "ta_ppm_p90": float(row.get("ta_ppm_p90", 0) or 0),
                    "unit": row.get("unit", "unknown"),
                }
            )
            if len(rows) >= limit:
                break
    return rows


def build_deposit_summary_response(*, project_id: str | None = None) -> dict[str, Any]:
    csv_path = _latest_block_model_csv()
    deposit = load_deposit_summary()
    blocks = load_blocks_preview()
    artifact_urls = _deposit_artifact_urls(csv_path)
    return {
        **deposit,
        "project_id": project_id,
        "blocks_preview": blocks,
        **artifact_urls,
        "centre": {"lon": 37.5, "lat": -1.15, "elevation_m": 1180},
    }


def load_deposit_summary() -> dict[str, Any]:
    csv_path = _latest_block_model_csv()
    if csv_path is None:
        return {
            "source": "default",
            "estimated_deposit_volume_m3": 25_000,
            "mean_grade_ta_ppm": 132,
            "block_count": 0,
            "ore_tonnes_estimate": 3_000_000,
        }

    rows: list[dict[str, str]] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)

    grades = [
        float(row.get("ta_ppm_mean", row.get("ta_ppm", 0)) or 0) for row in rows
    ]
    mean_grade = sum(grades) / len(grades) if grades else 132.0
    block_volume_m3 = len(rows) * 125.0
    ore_tonnes = block_volume_m3 * 2.7

    return {
        "source": str(csv_path.name),
        "estimated_deposit_volume_m3": round(block_volume_m3, 1),
        "mean_grade_ta_ppm": round(mean_grade, 2),
        "block_count": len(rows),
        "ore_tonnes_estimate": round(ore_tonnes, 0),
        "resource_category": "inferred",
    }


def build_exploration_summary(
    *,
    project_id: str | None = None,
    commodity: str = "ta",
) -> dict[str, Any]:
    from backend.processing.ore_financials import (
        analyze_ore_economics,
        resolve_grade_from_observations,
    )

    payload: dict[str, Any] = {
        "commodity": commodity,
        "project_id": project_id,
        "element": "ta_ppm",
        "dataset": "matuu_synthetic" if not project_id else None,
        "run_monte_carlo": False,
    }
    deposit = load_deposit_summary()
    payload.setdefault("ore_tonnes", deposit["ore_tonnes_estimate"])

    grade_hint = resolve_grade_from_observations(payload)
    if grade_hint:
        payload["grade"] = grade_hint["grade"]
        payload.setdefault("grade_unit", grade_hint["grade_unit"])

    economics = analyze_ore_economics(payload)

    return {
        "project_id": project_id,
        "commodity": commodity,
        "deposit": deposit,
        "grade_from_geodata": grade_hint,
        "economics_preview": {
            "npv_usd": economics["metrics"]["npv_usd"],
            "irr": economics["metrics"]["irr"],
            "payback_years": economics["metrics"]["payback_years"],
            "annual_revenue_usd": economics["annual"]["annual_revenue_usd"],
        },
        "workflow_links": {
            "kriging": "/kriging",
            "financial": "/financial",
            "reports": "/reports",
            "deposit": "/deposit",
            "map": "/map",
        },
        "recommended_financial_payload": {
            "commodity": commodity,
            "ore_tonnes": deposit["ore_tonnes_estimate"],
            "grade": economics["inputs"]["grade"],
            "grade_unit": economics["inputs"]["grade_unit"],
            "project_id": project_id,
            "element": "ta_ppm",
        },
    }


def exploration_document(project_id: str | None, summary: dict[str, Any]) -> dict[str, str]:
    deposit = summary.get("deposit", {})
    econ = summary.get("economics_preview", {})
    grade = summary.get("grade_from_geodata") or {}
    text = (
        f"Project {project_id or 'global'} exploration summary. "
        f"Deposit blocks {deposit.get('block_count', 0)} mean grade "
        f"{deposit.get('mean_grade_ta_ppm', 'n/a')} ppm Ta. "
        f"Ore tonnes estimate {deposit.get('ore_tonnes_estimate', 'n/a')}. "
        f"NPV preview {econ.get('npv_usd', 'n/a')} USD IRR {econ.get('irr', 'n/a')}."
    )
    if grade:
        text += f" Field grade mean {grade.get('grade')} from {grade.get('observation_count')} samples."
    return {
        "id": f"exploration-{project_id or 'global'}",
        "title": f"Exploration summary ({project_id or 'global'})",
        "text": text,
        "source": "backend/api/services/exploration_summary.py",
    }