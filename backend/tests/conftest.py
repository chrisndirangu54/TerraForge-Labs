import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("JOB_STORE_BACKEND", "memory")
os.environ.setdefault("AUTH_STORE_BACKEND", "memory")
os.environ.setdefault("INGEST_STORE_BACKEND", "memory")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "false")
os.environ.setdefault("MODEL_REGISTRY_BACKEND", "memory")
os.environ.setdefault("LLM_FORCE_STUB", "true")
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("STORAGE_BACKEND", "memory")
os.environ.setdefault("STAC_CATALOG_BACKEND", "memory")
