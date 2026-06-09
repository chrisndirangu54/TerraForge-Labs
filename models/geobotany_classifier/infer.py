from __future__ import annotations

from models.geobotany_classifier.dataset import (
    GEOBOTANY_CONFIDENCE_THRESHOLD,
    GEOBOTANY_MODEL_VERSION,
    get_affinity,
)


def classify_plant_stub(_image_base64: str) -> dict:
    species = "ocimum_centraliafricanum"
    confidence = 0.82
    accepted_species = (
        species
        if confidence >= GEOBOTANY_CONFIDENCE_THRESHOLD
        else "unknown_vegetation"
    )
    return {
        "species": accepted_species,
        "confidence": confidence,
        "mineral_affinity": get_affinity(accepted_species),
        "recommended_action": "Collect leaf tissue sample and run XRF transect",
        "top3": [
            {"species": species, "score": confidence},
            {"species": "haumaniastrum_katangense", "score": 0.11},
            {"species": "commelina_zigzag", "score": 0.04},
        ],
        "model_version": GEOBOTANY_MODEL_VERSION,
    }
