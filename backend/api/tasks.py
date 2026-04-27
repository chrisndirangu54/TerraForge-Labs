from __future__ import annotations

from backend.processing.deposit_model import generate_deposit_model_files

JOB_STORE: dict[str, dict] = {}


def run_kriging(job_id: str, payload: dict) -> dict:
    from backend.api.kriging import run_kriging_pipeline

    JOB_STORE[job_id] = {"status": "running"}
    result = run_kriging_pipeline(payload)
    JOB_STORE[job_id] = {"status": "complete", "result": result}
    return result


def run_deposit_model(job_id: str, payload: dict) -> dict:
    JOB_STORE[job_id] = {"status": "running"}
    result = generate_deposit_model_files(payload)
    JOB_STORE[job_id] = {"status": "complete", "result": result}
    return result


def generate_jorc_report(job_id: str, payload: dict) -> dict:
    from backend.api.services.jorc_report import build_jorc_report

    JOB_STORE[job_id] = {"status": "running"}
    result = build_jorc_report(payload)
    JOB_STORE[job_id] = {"status": "complete", "result": result}
    return result
