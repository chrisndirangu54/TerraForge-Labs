from __future__ import annotations

from typing import Any

DEFAULT_WEIGHTS = {
    "geochemistry": 0.35,
    "geophysics": 0.30,
    "geobotany": 0.20,
    "structural": 0.15,
}


def _normalise_score(value: float) -> float:
    return max(0.0, min(1.0, float(value) / 100.0))


def compute_fusion_score(payload: dict[str, Any]) -> dict[str, Any]:
    """Fuse multi-source exploration evidence into a ranked targeting score."""

    weights = {**DEFAULT_WEIGHTS, **(payload.get("weights") or {})}
    sources = payload.get("sources", payload)

    contributions: dict[str, float] = {}
    for source, weight in weights.items():
        raw = sources.get(source, sources.get(f"{source}_score", 0.0))
        if isinstance(raw, dict):
            raw = raw.get("score", raw.get("value", 0.0))
        contributions[source] = round(_normalise_score(float(raw)) * float(weight), 4)

    fusion_score = round(sum(contributions.values()), 4)
    classification = (
        "high_priority"
        if fusion_score >= 0.75
        else "moderate" if fusion_score >= 0.50 else "low_priority"
    )

    targets = payload.get("targets", [])
    ranked_targets = []
    for target in targets:
        target_score = float(target.get("base_score", fusion_score * 100.0))
        ranked_targets.append(
            {
                **target,
                "fusion_score": round(
                    fusion_score + _normalise_score(target_score) * 0.15,
                    4,
                ),
            }
        )
    ranked_targets.sort(key=lambda item: item["fusion_score"], reverse=True)

    return {
        "fusion_score": fusion_score,
        "classification": classification,
        "contributions": contributions,
        "weights": weights,
        "ranked_targets": ranked_targets,
        "recommended_action": (
            "Prioritise infill geochem and scout drilling"
            if classification == "high_priority"
            else "Collect additional lines before drill commitment"
        ),
    }
