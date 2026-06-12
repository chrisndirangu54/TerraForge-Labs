from __future__ import annotations

from backend.api.celery_app import celery_app
from backend.api.jobs.store import JobStore, get_job_store
from backend.processing.deposit_model import generate_deposit_model_files
from backend.processing.gpu_classifier import classify_gpu, classify_gpu_batch


def _store() -> JobStore:
    return get_job_store()


def _set(job_id: str, job_type: str, **data: object) -> None:
    store = _store()
    store.set(job_id, {"job_type": job_type, **data})


def _mark_dead_letter(
    job_id: str,
    job_type: str,
    exc: Exception,
    *,
    retries: int,
    task_name: str,
) -> None:
    _set(
        job_id,
        job_type,
        status="failed",
        error=str(exc),
        dead_letter={
            "reason": str(exc),
            "job_type": job_type,
            "task": task_name,
            "retries": retries,
            "final": True,
        },
    )


def run_kriging(job_id: str, payload: dict) -> dict:
    from backend.api.kriging import run_kriging_pipeline

    _set(job_id, "kriging", status="running")
    result = run_kriging_pipeline(payload)
    _set(job_id, "kriging", status="complete", result=result)
    return result


def run_deposit_model(job_id: str, payload: dict) -> dict:
    from backend.api.services.exploration_summary import load_blocks_preview

    _set(job_id, "deposit_model", status="running")
    run_payload = {**payload, "job_id": job_id}
    result = generate_deposit_model_files(run_payload)
    result["job_id"] = job_id
    result["blocks_preview"] = load_blocks_preview(job_id=job_id)
    _set(job_id, "deposit_model", status="complete", result=result)
    return result


def generate_jorc_report(job_id: str, payload: dict) -> dict:
    from backend.api.services.jorc_report import build_jorc_report

    _set(job_id, "jorc_report", status="running")
    result = build_jorc_report(payload)
    _set(job_id, "jorc_report", status="complete", result=result)
    return result


def run_gpu_classification(job_id: str, payload: dict) -> dict:
    task = payload.get("task", "mineral")
    _set(job_id, "gpu_classification", status="running", task=task, accelerator="gpu")

    if payload.get("batch"):
        result = classify_gpu_batch(task, payload.get("items", []))
    else:
        result = classify_gpu(task, payload)

    _set(
        job_id,
        "gpu_classification",
        status="complete",
        task=task,
        accelerator=result.get("accelerator", "gpu"),
        result=result,
    )
    return result


def _wrap_celery_task(name: str, runner):
    if celery_app is None:
        return None

    @celery_app.task(bind=True, name=name, max_retries=1)
    def _task(self, job_id: str, payload: dict) -> dict:
        job_type = payload.get("_job_type") or name.split(".")[-1]
        if job_type == "run_gpu_classification":
            job_type = "gpu_classification"
        elif job_type == "run_kriging":
            job_type = "kriging"
        elif job_type == "run_deposit_model":
            job_type = "deposit_model"
        elif job_type == "generate_jorc_report":
            job_type = "jorc_report"

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return runner(job_id, payload)
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    continue
                _mark_dead_letter(
                    job_id,
                    job_type,
                    exc,
                    retries=attempt,
                    task_name=name,
                )
                raise
        assert last_exc is not None
        raise last_exc

    return _task


celery_run_kriging = _wrap_celery_task("terraforge.run_kriging", run_kriging)
celery_run_deposit_model = _wrap_celery_task(
    "terraforge.run_deposit_model", run_deposit_model
)
celery_generate_jorc_report = _wrap_celery_task(
    "terraforge.generate_jorc_report", generate_jorc_report
)
celery_gpu_classification = _wrap_celery_task(
    "terraforge.run_gpu_classification", run_gpu_classification
)


def pull_datasets(job_id: str, payload: dict) -> dict:
    from backend.api.services.dataset_pull import pull_all_datasets

    _set(job_id, "dataset_pull", status="running")
    result = pull_all_datasets(
        include_gbif=bool(payload.get("include_gbif", True)),
        include_domain=bool(payload.get("include_domain", True)),
    )
    _set(job_id, "dataset_pull", status="complete", result=result)
    return result


def train_mineral(job_id: str, payload: dict) -> dict:
    from models.mineral_classifier.evaluate import evaluate_mineral_classifier
    from models.mineral_classifier.train import train_mineral_classifier

    _set(job_id, "mineral_train", status="running")
    checkpoint = payload.get("checkpoint_path")
    train_result = train_mineral_classifier(
        epochs=int(payload.get("epochs", 5)),
        samples_per_class=int(payload.get("samples_per_class", 20)),
        checkpoint_path=checkpoint,
        data_source=str(payload.get("data_source", "synthetic")),
    )
    eval_result = evaluate_mineral_classifier(
        checkpoint_path=train_result["checkpoint_path"],
        seed=int(payload.get("seed", 77)),
    )
    result = {"train": train_result, "evaluation": eval_result}
    _set(job_id, "mineral_train", status="complete", result=result)
    return result


def train_geobotany(job_id: str, payload: dict) -> dict:
    from models.geobotany_classifier.evaluate import evaluate_geobotany_classifier
    from models.geobotany_classifier.train import train_geobotany_classifier

    _set(job_id, "geobotany_train", status="running")
    train_result = train_geobotany_classifier(
        epochs=int(payload.get("epochs", 5)),
        data_source=str(payload.get("data_source", "synthetic")),
    )
    eval_result = evaluate_geobotany_classifier(
        checkpoint_path=train_result["checkpoint_path"]
    )
    result = {"train": train_result, "evaluation": eval_result}
    _set(job_id, "geobotany_train", status="complete", result=result)
    return result


def train_thin_section(job_id: str, payload: dict) -> dict:
    from models.thin_section_classifier.evaluate import evaluate_thin_section_classifier
    from models.thin_section_classifier.train import train_thin_section_classifier

    _set(job_id, "thin_section_train", status="running")
    train_result = train_thin_section_classifier(
        epochs=int(payload.get("epochs", 6)),
        data_source=str(payload.get("data_source", "corpus")),
        samples_per_class=int(payload.get("samples_per_class", 200)),
    )
    eval_result = evaluate_thin_section_classifier(
        data_source=str(payload.get("data_source", "corpus")),
        n_splits=int(payload.get("cv_folds", 5)),
        epochs=int(payload.get("cv_epochs", payload.get("epochs", 6))),
        samples_per_class=int(payload.get("samples_per_class", 80)),
    )
    result = {"train": train_result, "evaluation": eval_result}
    _set(job_id, "thin_section_train", status="complete", result=result)
    return result


def train_spectral(job_id: str, payload: dict) -> dict:
    from models.spectral_classifier.evaluate import evaluate_spectral_classifier
    from models.spectral_classifier.train import train_spectral_classifier

    _set(job_id, "spectral_train", status="running")
    train_result = train_spectral_classifier(
        epochs=int(payload.get("epochs", 8)),
        data_source=str(payload.get("data_source", "corpus")),
        samples_per_class=int(payload.get("samples_per_class", 400)),
    )
    eval_result = evaluate_spectral_classifier(
        data_source=str(payload.get("data_source", "corpus")),
        n_splits=int(payload.get("cv_folds", 5)),
        epochs=int(payload.get("cv_epochs", payload.get("epochs", 8))),
        samples_per_class=int(payload.get("samples_per_class", 120)),
    )
    result = {"train": train_result, "evaluation": eval_result}
    _set(job_id, "spectral_train", status="complete", result=result)
    return result


celery_pull_datasets = _wrap_celery_task("terraforge.pull_datasets", pull_datasets)
celery_train_mineral = _wrap_celery_task("terraforge.train_mineral", train_mineral)
celery_train_geobotany = _wrap_celery_task("terraforge.train_geobotany", train_geobotany)
celery_train_thin_section = _wrap_celery_task(
    "terraforge.train_thin_section", train_thin_section
)
celery_train_spectral = _wrap_celery_task("terraforge.train_spectral", train_spectral)