from __future__ import annotations

from backend.api.services.llm import generate_section


def infer_criterion_text(criterion: str, *, context: dict | None = None) -> str:
    return generate_section(
        f"Draft JORC-compliant text for criterion: {criterion}",
        context or {"criterion": criterion},
    )