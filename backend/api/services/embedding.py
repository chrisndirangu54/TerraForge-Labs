from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.error
import urllib.request
from typing import Any


def embedding_dimension() -> int:
    return int(os.getenv("EMBEDDING_DIM", "768"))


def _hash_embedding(text: str, *, dim: int) -> list[float]:
    tokens = [token for token in text.lower().split() if token]
    vector = [0.0] * dim
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for byte_idx, byte in enumerate(digest):
            index = (int.from_bytes(digest[byte_idx : byte_idx + 2], "big")) % dim
            vector[index] += (byte / 255.0) - 0.5
    norm = math.sqrt(sum(value * value for value in vector))
    if norm > 0:
        vector = [value / norm for value in vector]
    return vector


def _gemini_embedding(text: str) -> list[float]:
    key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Gemini API key not configured for embeddings")
    model = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:embedContent?key={key}"
    )
    payload = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": text[:8000]}]},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini embedding error {exc.code}: {detail}") from exc

    values = body.get("embedding", {}).get("values")
    if not values:
        raise RuntimeError(f"Gemini embedding returned no values: {body}")
    return [float(value) for value in values]


def embed_text(text: str) -> dict[str, Any]:
    provider = os.getenv("EMBEDDING_PROVIDER", "hash").lower()
    dim = embedding_dimension()
    if provider == "gemini" and (os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")):
        try:
            vector = _gemini_embedding(text)
            return {"vector": vector, "provider": "gemini", "dimension": len(vector)}
        except Exception:
            if os.getenv("EMBEDDING_FORCE_HASH", "").lower() not in {"0", "false", "no"}:
                pass
            else:
                raise
    vector = _hash_embedding(text, dim=dim)
    return {"vector": vector, "provider": "hash", "dimension": len(vector)}


def embed_batch(texts: list[str]) -> list[dict[str, Any]]:
    return [embed_text(text) for text in texts]