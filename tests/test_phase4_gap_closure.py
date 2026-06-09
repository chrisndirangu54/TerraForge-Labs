from pathlib import Path

import pytest

from backend.processing.gap_closure import (
    dispersion_model,
    earth_observation_correction,
    ert_3d_inversion,
    flood_inundation_model,
    fluid_inclusion_summary,
    geochemistry_qaqc,
    groundwater_age,
    investor_data_room,
    lims_sample_event,
    modpath_capture_zone,
    optimise_drill_plan,
    pathfinder_analysis,
    sequential_gaussian_simulation,
    soil_gas_interpretation,
    structural_assessment,
    tenement_obligations,
    traffic_haulage_simulation,
)
from shared.instruments.downhole_geophysics import (
    correlate_logs_to_lithology,
    parse_las,
)
from shared.instruments.soil_gas import parse_soil_gas_csv


def test_pathfinder_analysis_and_sgs_support_drill_targeting():
    samples = [
        {
            "sample_id": "S1",
            "lon": 37.45,
            "lat": -1.20,
            "As": 10,
            "Sb": 1,
            "Bi": 0.5,
            "grade": 80,
        },
        {
            "sample_id": "S2",
            "lon": 37.50,
            "lat": -1.15,
            "As": 120,
            "Sb": 8,
            "Bi": 2.0,
            "grade": 160,
        },
        {
            "sample_id": "S3",
            "lon": 37.55,
            "lat": -1.10,
            "As": 80,
            "Sb": 4,
            "Bi": 5.0,
            "grade": 220,
        },
    ]
    pathfinder = pathfinder_analysis(samples, "orogenic_au")
    assert pathfinder["ranked_pathfinders"][0]["halo_score"] > 0
    assert pathfinder["dispersion_vector"]["toward_lon"] > 0
    simulation = sequential_gaussian_simulation(samples, realisations=250)
    assert simulation["realisations"] == 250
    assert simulation["p90_grade"] > simulation["p10_grade"]


def test_drill_planning_optimiser_selects_holes_within_budget():
    plan = optimise_drill_plan(
        [
            {
                "hole_id": "DH-1",
                "depth_m": 200,
                "target_probability": 0.8,
                "uncertainty_reduction": 0.7,
            },
            {
                "hole_id": "DH-2",
                "depth_m": 150,
                "target_probability": 0.5,
                "uncertainty_reduction": 0.3,
            },
            {
                "hole_id": "DH-3",
                "depth_m": 300,
                "target_probability": 0.9,
                "uncertainty_reduction": 0.8,
            },
        ],
        budget_usd=70_000,
        max_depth_m=250,
    )
    assert plan["selected_holes"]
    assert plan["estimated_spend_usd"] <= 70_000
    assert plan["selected_holes"][0]["information_gain"] > 0


def test_qaqc_lims_tenements_and_data_room():
    qaqc = geochemistry_qaqc(
        [
            {
                "sample_id": "STD-1",
                "sample_type": "standard",
                "expected_ppm": 100,
                "measured_ppm": 116,
            },
            {
                "sample_id": "BLK-1",
                "sample_type": "blank",
                "detection_limit_ppm": 0.01,
                "measured_ppm": 0.2,
            },
            {
                "sample_id": "DUP-1",
                "sample_type": "duplicate",
                "original_ppm": 100,
                "duplicate_ppm": 140,
            },
        ]
    )
    assert qaqc["failure_count"] == 3
    assert qaqc["jorc_ready"] is False
    event = lims_sample_event("S-001", "collected", "geologist")
    assert event["next_status"] == "prepared"
    with pytest.raises(ValueError):
        lims_sample_event("S-001", "lost", "geologist")
    obligations = tenement_obligations(
        [
            {
                "licence_id": "EL-1",
                "days_to_expiry": 45,
                "expenditure_commitment_usd": 50000,
            }
        ]
    )
    assert obligations["obligations"][0]["alert_level"] == "high"
    data_room = investor_data_room("matuu", ["kriging"], 24)
    assert data_room["raw_data_hidden"] is True


def test_soil_gas_and_downhole_parsers(tmp_path):
    gas_csv = tmp_path / "soil_gas.csv"
    gas_csv.write_text(
        "sample_id,lon,lat,co2_ppm,helium_ppm,radon_bq_m3,h2s_ppm,ch4_ppm\n"
        "G1,37.45,-1.20,400,5.20,100,0,1\n"
        "G2,37.50,-1.15,1200,5.80,900,0,1\n"
        "G3,37.55,-1.10,410,5.21,105,0,1\n",
        encoding="utf-8",
    )
    readings = parse_soil_gas_csv(gas_csv)
    assert readings[0]["co2_ppm"] == 400
    interpretation = soil_gas_interpretation(readings)
    assert interpretation["sample_count"] == 3

    las = tmp_path / "downhole.las"
    las.write_text(
        "~A DEPTH GAMMA DENSITY RESISTIVITY\n0 45 2.65 80\n1 110 2.95 25\n",
        encoding="utf-8",
    )
    logs = parse_las(las)
    correlation = correlate_logs_to_lithology(logs)
    assert correlation["shale_indicator_intervals"] == 1
    assert correlation["massive_sulphide_or_mafic_intervals"] == 1


def test_fluid_inclusion_and_earth_observation_corrections():
    fluid = fluid_inclusion_summary(
        [
            {"homogenisation_c": 320, "salinity_wt_pct_nacl": 12},
            {"homogenisation_c": 340, "salinity_wt_pct_nacl": 14},
        ]
    )
    assert fluid["inferred_fluid_system"] == "magmatic_hydrothermal"
    insar = earth_observation_correction("insar_tropospheric", {"input_url": "s1.tif"})
    assert "GACOS" in insar["method"]
    hyperspectral = earth_observation_correction(
        "hyperspectral_atmospheric", {"input_url": "pika.bsq"}
    )
    assert "6s_atcor" in hyperspectral["output_url"]


def test_hydro_environment_and_structural_extensions():
    modpath = modpath_capture_zone([{"well_id": "BH-1"}], porosity=0.22)
    assert modpath["well_count"] == 1
    ert = ert_3d_inversion(profile_count=5, electrode_count=64)
    assert ert["inversion_cells"] == 1280
    age = groundwater_age([{"tritium_tu": 1.2, "cfc12_pptv": 300}])
    assert age["mean_residence_time_years"] > 0
    flood = flood_inundation_model("dem.tif", rainfall_mm=150, return_period_years=100)
    assert flood["inundated_area_km2"] > 0
    air = dispersion_model("air", emission_rate=100, distance_m=500)
    assert air["model"] == "AERMOD_stub"
    haulage = traffic_haulage_simulation(500, 25, 120)
    assert haulage["trips_per_day"] == 20
    structural = structural_assessment(insar_mm=25, optical_change_score=0.5)
    assert structural["structurally_compromised"] is True


def test_gap_closure_docs_and_web_metadata():
    doc = Path("docs/phase4-gap-closure-addendum.md").read_text(encoding="utf-8")
    assert "Drill planning optimiser" in doc
    assert "Sample management / lightweight LIMS" in doc
    api = Path("apps/web/src/api/phase4.ts").read_text(encoding="utf-8")
    assert "/targeting/drill-plan-optimise" in api
    layers = Path("apps/web/src/components/map/layers.ts").read_text(encoding="utf-8")
    assert "flood_inundation_depth" in layers
