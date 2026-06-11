from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

_LAST_CALLS: list[float] = []


def _api_key() -> str | None:
    key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
    return key.strip() if key else None


def _rate_limit() -> None:
    max_rpm = int(os.getenv("GEMINI_MAX_RPM", "12"))
    if max_rpm <= 0:
        return
    now = time.time()
    window_start = now - 60.0
    while _LAST_CALLS and _LAST_CALLS[0] < window_start:
        _LAST_CALLS.pop(0)
    if len(_LAST_CALLS) >= max_rpm:
        sleep_for = 60.0 - (now - _LAST_CALLS[0]) + 0.05
        if sleep_for > 0:
            time.sleep(sleep_for)
    _LAST_CALLS.append(time.time())


def is_gemini_configured() -> bool:
    provider = os.getenv("LLM_PROVIDER", "stub").lower()
    return provider == "gemini" and bool(_api_key())


def generate_text(
    prompt: str,
    *,
    system_instruction: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int = 1024,
) -> dict[str, Any]:
    key = _api_key()
    if not key:
        raise RuntimeError("Gemini API key not configured (set LLM_API_KEY)")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )

    parts: list[dict[str, str]] = []
    if system_instruction:
        parts.append({"text": system_instruction})
    parts.append({"text": prompt})

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    _rate_limit()
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {exc.code}: {detail}") from exc

    candidates = body.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {body}")

    content = candidates[0].get("content") or {}
    text_parts = content.get("parts") or []
    text = "\n".join(
        part.get("text", "") for part in text_parts if isinstance(part, dict)
    ).strip()
    if not text:
        raise RuntimeError("Gemini returned empty text")

    usage = body.get("usageMetadata") or {}
    return {
        "text": text,
        "model": model,
        "provider": "gemini",
        "prompt_tokens": usage.get("promptTokenCount"),
        "output_tokens": usage.get("candidatesTokenCount"),
    }
