import json
from pathlib import Path

import pytest

from backend.api.services.jorc_report import GEOBOTANY_DISCLAIMER, build_jorc_report
from backend.processing.geobotany_active_learning import (
    normalise_observation,
    should_trigger_retrain,
)
from backend.processing.geobotany_anomaly import (
    composite_anomaly_score,
    pearson_calibration,
)
from backend.processing.vegetation_stress import (
    compute_composite_stress,
    compute_hyperspectral_indices,
    compute_sentinel_indices,
    zscore_anomaly,
)
from models.geobotany_classifier.dataset import (
    GEOBOTANY_CONFIDENCE_THRESHOLD,
    get_affinity,
)
from models.geobotany_classifier.infer import classify_plant_stub
from models.geobotany_classifier.train import train_geobotany_classifier_stub
from shared.instruments.biogeochemical import (
    calculate_bcf,
    parse_icp_ms_csv,
    summarise_biogeochem,
)


def test_geobotany_classifier_contract_and_affinity():
    result = classify_plant_stub("placeholder")
    assert result["species"] == "ocimum_centraliafricanum"
    assert result["confidence"] >= GEOBOTANY_CONFIDENCE_THRESHOLD
    assert result["mineral_affinity"]["Cu"] == "VERY_HIGH"
    assert get_affinity("silene_cobalticola") == {"Co": "VERY_HIGH"}


def test_geobotany_training_stub_targets_are_met():
    metrics = train_geobotany_classifier_stub(epochs=3)
    assert metrics["architecture"] == "EfficientNet-B0"
    assert metrics["top1_accuracy"] >= metrics["target_top1_accuracy"]
    assert metrics["top3_accuracy"] >= metrics["target_top3_accuracy"]
    assert metrics["model_size_mb"] < metrics["target_tflite_size_mb"]


def test_vegetation_stress_indices_and_anomaly_flag():
    indices = compute_sentinel_indices(
        {
            "B02": 0.08,
            "B03": 0.12,
            "B04": 0.11,
            "B05": 0.15,
            "B06": 0.25,
            "B07": 0.32,
            "B08": 0.45,
        }
    )
    assert indices["ndvi"] > 0.5
    hyper = compute_hyperspectral_indices(
        {
            430: 0.08,
            445: 0.09,
            550: 0.25,
            615: 0.16,
            680: 0.28,
            700: 0.34,
            710: 0.35,
            740: 0.36,
            760: 0.33,
            800: 0.50,
        }
    )
    stress = compute_composite_stress({**indices, **hyper})
    assert "composite_stress_score" in stress
    assert zscore_anomaly(88, 50, 10)["flagged"] is True


def test_biogeochemical_csv_and_bcf(tmp_path):
    csv_path = tmp_path / "plant_icpms.csv"
    csv_path.write_text(
        "sample_id,species_name,plant_part,lon,lat,plant_cu_ppm,soil_cu_ppm\n"
        "B1,ocimum_centraliafricanum,leaf,37.48,-1.15,250,25\n",
        encoding="utf-8",
    )
    rows = parse_icp_ms_csv(csv_path)
    assert rows[0]["plant_cu_ppm"] == 250
    assert calculate_bcf(250, 25) == 10
    summary = summarise_biogeochem(rows, "Cu")
    assert summary["hyperaccumulator_count"] == 1
    assert summary["join_radius_m"] == 50


def test_biogeochemical_csv_requires_species_and_part(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("sample_id,plant_cu_ppm\nB1,250\n", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_icp_ms_csv(csv_path)


def test_composite_anomaly_score_and_calibration():
    score = composite_anomaly_score(
        {
            "vegetation_stress": 75,
            "indicator_species": 95,
            "biogeochemistry": 88,
            "species_richness": 40,
            "historical_records": 65,
        }
    )
    assert score["classification"] == "strong"
    calibration = pearson_calibration([20, 50, 90], [30, 80, 140])
    assert calibration["r_squared"] > 0.9


def test_active_learning_observation_and_trigger():
    observation = normalise_observation(
        {
            "species": "ocimum_centraliafricanum",
            "lon": 37.48,
            "lat": -1.15,
            "vigour": 2,
            "leaf_colour": "chlorotic",
            "density": "moderate",
            "label_confidence": "geologist_confirmed",
            "local_name": "maua ya shaba",
            "local_significance": "community copper plant",
        }
    )
    assert observation["local_name"] == "maua ya shaba"
    assert should_trigger_retrain([observation] * 10)["trigger_retrain"] is True


def test_jorc_geobotany_sections_and_disclaimer():
    result = build_jorc_report(
        {
            "project_name": "Track Q JORC",
            "geobotany": {
                "species_name": "ocimum_centraliafricanum",
                "n_samples": 12,
                "species_list": ["ocimum_centraliafricanum"],
                "mineral_list": ["Cu", "Ni"],
                "n_strong": 2,
                "r_value": 0.72,
            },
        }
    )
    assert result["json_url"].startswith("minio://")
    data = json.loads(
        Path("artifacts/track_q_jorc_jorc.json").read_text(encoding="utf-8")
    )
    assert "geobotanical_sampling" in data["sections"]["1_sampling_techniques"]
    assert (
        GEOBOTANY_DISCLAIMER
        in data["sections"]["2_reporting_of_exploration_results"][
            "geobotany_disclaimer"
        ]["text"]
    )
