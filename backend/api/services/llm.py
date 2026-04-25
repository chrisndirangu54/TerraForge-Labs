from __future__ import annotations

import os


def generate_section(prompt: str, data_context: dict) -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return f"[{provider}:{model}] {prompt[:80]} | context_keys={sorted(data_context.keys())}"
