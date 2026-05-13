from __future__ import annotations

MIN_NEW_LABELS_FOR_RETRAIN = 10
RESEARCH_GRADE_CONFIDENCE = "geologist_confirmed"


def normalise_observation(payload: dict) -> dict:
    return {
        "species": payload.get("species", "unknown_vegetation"),
        "lon": float(payload.get("lon", 0.0)),
        "lat": float(payload.get("lat", 0.0)),
        "vigour": int(payload.get("vigour", 3)),
        "leaf_colour": payload.get("leaf_colour", "normal"),
        "density": payload.get("density", "unknown"),
        "label_confidence": payload.get("label_confidence", "unconfirmed"),
        "image_upload_id": payload.get("image_upload_id"),
        "local_name": payload.get("local_name"),
        "local_significance": payload.get("local_significance"),
        "gbif_taxon_linked": bool(payload.get("gbif_taxon_key")),
    }


def should_trigger_retrain(
    labelled_observations: list[dict],
) -> dict[str, int | bool | str | None]:
    accepted = [
        obs
        for obs in labelled_observations
        if obs.get("label_confidence") == RESEARCH_GRADE_CONFIDENCE
    ]
    return {
        "new_confirmed_labels": len(accepted),
        "trigger_retrain": len(accepted) >= MIN_NEW_LABELS_FOR_RETRAIN,
        "next_model_version": (
            "geobotany-b0-v0.2" if len(accepted) >= MIN_NEW_LABELS_FOR_RETRAIN else None
        ),
    }
