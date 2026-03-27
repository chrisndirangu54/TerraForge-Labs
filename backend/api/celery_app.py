from __future__ import annotations

import os

try:
    from celery import Celery
except Exception:  # pragma: no cover
    Celery = None


if Celery:
    celery_app = Celery("terraforge", broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"), backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    celery_app.conf.task_time_limit = 600
    celery_app.conf.task_soft_time_limit = 540
else:
    celery_app = None
