from __future__ import annotations

import os

try:
    from celery import Celery
    from kombu import Queue
except Exception:  # pragma: no cover
    Celery = None  # type: ignore[misc, assignment]
    Queue = None  # type: ignore[misc, assignment]

QUEUE_DEFAULT = "default"
QUEUE_GPU = "gpu"
QUEUE_REPORTS = "reports"

TASK_ROUTES = {
    "terraforge.run_gpu_classification": {"queue": QUEUE_GPU},
    "terraforge.run_kriging": {"queue": QUEUE_DEFAULT},
    "terraforge.run_deposit_model": {"queue": QUEUE_DEFAULT},
    "terraforge.generate_jorc_report": {"queue": QUEUE_REPORTS},
}

if Celery:
    celery_app = Celery(
        "terraforge",
        broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
    celery_app.conf.update(
        task_time_limit=600,
        task_soft_time_limit=540,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_default_queue=QUEUE_DEFAULT,
        task_queues=(
            Queue(QUEUE_DEFAULT),
            Queue(QUEUE_GPU),
            Queue(QUEUE_REPORTS),
        ),
        task_routes=TASK_ROUTES,
        imports=("backend.api.tasks",),
        task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower()
        in {"1", "true", "yes"},
        task_eager_propagates=os.getenv("CELERY_TASK_EAGER_PROPAGATES", "").lower()
        in {"1", "true", "yes"},
    )
else:
    celery_app = None
