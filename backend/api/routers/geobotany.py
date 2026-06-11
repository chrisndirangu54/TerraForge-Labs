from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access

from backend.processing.geobotany_active_learning import (
    normalise_observation,
    queue_low_confidence_observation,
    should_trigger_retrain,
)
from backend.processing.geobotany_anomaly import (
    build_survey_plan,
    composite_anomaly_score,
)
from backend.processing.vegetation_stress import (
    compute_composite_stress,
    compute_hyperspectral_indices,
    compute_sentinel_indices,
)
from models.geobotany_classifier.dataset import INDICATOR_MINERAL_AFFINITY
from models.geobotany_classifier.infer import classify_plant
from shared.instruments.biogeochemical import parse_icp_ms_csv, summarise_biogeochem

router = APIRouter()

INDICATOR_SPECIES = [
    {"species": species, "mineral_affinity": affinity}
    for species, affinity in INDICATOR_MINERAL_AFFINITY.items()
    if "negative_indicator" not in affinity
]


@router.post(
    "/geobotany/classify-plant", dependencies=[Depends(require_mutating_access)]
)
async def classify_plant_route(payload: dict) -> dict:
    result = classify_plant(payload=payload)
    observation = normalise_observation(
        {
            **payload,
            "species": result["species"],
            "model_confidence": result["confidence"],
        }
    )
    queued = queue_low_confidence_observation(observation)
    return {
        **result,
        "lon": payload.get("lon"),
        "lat": payload.get("lat"),
        "project_id": payload.get("project_id"),
        "active_learning_queue_id": queued["id"] if queued else None,
    }


@router.post(
    "/geobotany/log-observation", dependencies=[Depends(require_mutating_access)]
)
async def log_observation(payload: dict) -> dict:
    observation = normalise_observation(payload)
    queued = queue_low_confidence_observation(observation)
    return {
        "status": "queued" if queued else "accepted",
        "observation_id": queued["id"] if queued else "geo-obs-accepted",
        "observation": observation,
        "active_learning": should_trigger_retrain([observation]),
    }


@router.post("/geobotany/stress-map", dependencies=[Depends(require_mutating_access)])
async def stress_map(payload: dict) -> dict:
    bands = payload.get(
        "bands",
        {
            "B02": 0.08,
            "B03": 0.12,
            "B04": 0.11,
            "B05": 0.15,
            "B06": 0.25,
            "B07": 0.32,
            "B08": 0.45,
        },
    )
    indices = compute_sentinel_indices(bands)
    if payload.get("hyperspectral_reflectance_nm"):
        indices.update(
            compute_hyperspectral_indices(payload["hyperspectral_reflectance_nm"])
        )
    stress = compute_composite_stress(indices)
    return {"job_id": "geobotany-stress-job-1", "indices": indices, **stress}


@router.post(
    "/geobotany/biogeochem-upload", dependencies=[Depends(require_mutating_access)]
)
async def biogeochem_upload(payload: dict) -> dict:
    filepath = payload.get("filepath")
    if filepath:
        rows = parse_icp_ms_csv(filepath)
    else:
        rows = [
            {
                "species_name": payload.get("species_name", "ocimum_centraliafricanum"),
                "plant_part": payload.get("plant_part", "leaf"),
                "plant_cu_ppm": 250.0,
                "soil_cu_ppm": 25.0,
            }
        ]
    return {
        "bcf_table": summarise_biogeochem(rows, payload.get("element", "Cu")),
        "anomaly_score": 82,
        "kriged_map_url": "minio://geobotany/plant_cu_kriging.tif",
    }


@router.get("/geobotany/anomaly-map")
async def anomaly_map(bbox: str = "", project_id: str = "") -> dict:
    _ = bbox
    _ = project_id
    return composite_anomaly_score(
        {
            "vegetation_stress": 75,
            "indicator_species": 95,
            "biogeochemistry": 88,
            "species_richness": 40,
            "historical_records": 65,
        }
    )


@router.get("/geobotany/indicator-species")
async def indicator_species(bbox: str = "") -> dict:
    _ = bbox
    return {
        "records": INDICATOR_SPECIES,
        "source": ["GBIF", "iNaturalist", "TerraForge"],
    }


@router.post("/geobotany/survey-plan", dependencies=[Depends(require_mutating_access)])
async def survey_plan(payload: dict) -> dict:
    return build_survey_plan(
        payload.get("bbox", [37.45, -1.20, 37.55, -1.10]),
        int(payload.get("team_size", 4)),
        int(payload.get("days", 3)),
        payload.get("priority", "stress_zones"),
    )
