from __future__ import annotations

import os
from pathlib import Path


def load_environment() -> None:
    """Load repo-root .env when present (never commit secrets)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)

    for key in ("LLM_API_KEY", "GEMINI_API_KEY"):
        value = os.getenv(key, "").strip()
        if value and not os.getenv("LLM_API_KEY"):
            os.environ.setdefault("LLM_API_KEY", value)
