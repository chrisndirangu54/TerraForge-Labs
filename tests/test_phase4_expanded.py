from pathlib import Path

import pytest

from backend.processing.groundwater_model import (
    build_modflow_model,
    pumping_test_theis,
    slug_test_conductivity,
    water_quality_compliance,
)
from backend.processing.infrastructure import (
    mining_infrastructure_assessment,
    pipeline_route,
    power_grid_proximity,
    telecoms_coverage,
)
from backend.processing.mapping_stack import (
    cesium_tileset_job,
    layer_catalogue,
    map_provider_plan,
    offline_pack_manifest,
)
from backend.processing.satellite_feeds import (
    change_detect,
    latest_index,
    scene_catalogue,
)
from backend.processing.urban_analysis import (
    classify_settlement,
    mining_settlement_conflict,
    service_access,
    suitability_score,
)
from shared.instruments.hydrogeology import (
    lab_water_quality_schema,
    parse_levelogger_csv,
    parse_pump_test_csv,
)


def test_mapping_stack_open_source_default_and_offline_manifest():
    plan = map_provider_plan(use_google=False)
    assert plan["provider"] == "open_source"
    assert plan["estimated_monthly_cost_usd"] == 0
    google = map_provider_plan(use_google=True)
    assert google["free_events"]["essentials"] == 10_000
    manifest = offline_pack_manifest("Kenya")
    assert manifest["offline_ready"] is True
    assert manifest["packs"][0]["name"] == "kenya_osm.pmtiles"
    layers = layer_catalogue()
    assert "hydrogeology" in layers["layer_groups"]
    assert cesium_tileset_job("matuu", "minio://models/matuu.obj")[
        "tileset_url"
    ].endswith("tileset.json")


def test_hydrogeology_slug_pump_quality_and_modflow():
    slug = slug_test_conductivity([1.0, 0.7, 0.4, 0.2])
    assert slug["hydraulic_conductivity_m_day"] > 0
    pump = pumping_test_theis([1 + i * 0.05 for i in range(20)], 250)
    assert pump["transmissivity_m2_day"] > 0
    with pytest.raises(ValueError):
        pumping_test_theis([1, 2, 3], 250)
    quality = water_quality_compliance(
        {"fluoride_mg_l": 2.0, "nitrate_mg_l": 20, "tds_mg_l": 1200}
    )
    assert "WHO_FLUORIDE_EXCEEDANCE" in quality["flags"]
    assert "KENYA_NEMA_TDS_EXCEEDANCE" in quality["flags"]
    model = build_modflow_model([37.45, -1.2, 37.55, -1.1], 180, 3)
    assert model["engine"] == "MODFLOW 6 via FloPy"
    assert model["converged"] is True


def test_hydrogeology_csv_parsers(tmp_path):
    levelogger = tmp_path / "levelogger.csv"
    levelogger.write_text(
        "timestamp,water_level_m,temperature_c\n2026-01-01T00:00:00Z,42.5,24.1\n",
        encoding="utf-8",
    )
    assert parse_levelogger_csv(levelogger)[0]["water_level_m"] == 42.5
    pump = tmp_path / "pump.csv"
    pump.write_text("elapsed_min,drawdown_m,well_id\n1,0.2,PW-1\n", encoding="utf-8")
    assert parse_pump_test_csv(pump)[0]["well_id"] == "PW-1"
    assert "fluoride_mg_l" in lab_water_quality_schema()


def test_urban_planning_analysis_contracts():
    informal = classify_settlement(
        {"buildings_per_ha": 150, "road_km_per_km2": 4, "building_regularity": 0.2}
    )
    assert informal["settlement_type"] == "informal_settlement"
    access = service_access(2.5, "water_point")
    assert access["underserved"] is True
    suitability = suitability_score(
        {
            "distance_to_road_km": 1,
            "flood_risk": 0.1,
            "slope_deg": 4,
            "groundwater_depth_m": 30,
        }
    )
    assert suitability["score"] >= 70
    conflict = mining_settlement_conflict(400)
    assert conflict["conflict"] is True


def test_infrastructure_assessment_contracts():
    grid = power_grid_proximity(34.2)
    assert grid["recommendation"] == "solar_preferred"
    route = pipeline_route([37.48, -1.15], [37.55, -1.1], 1.1)
    assert route["estimated_cost_usd"] > 0
    telecoms = telecoms_coverage(-1.15, 22.1)
    assert telecoms["starlink_available"] is True
    assessment = mining_infrastructure_assessment(
        {"production_tpd": 500, "nearest_paved_road_km": 12.4, "nearest_grid_km": 34.2}
    )
    assert assessment["road_access"]["road_upgrade_required"] is True
    assert assessment["total_infrastructure_capex_usd"] > 0


def test_satellite_feed_contracts():
    scenes = scene_catalogue([37.45, -1.2, 37.55, -1.1], "2026-01-01", "2026-06-30")
    assert scenes["scenes"][0]["source"] == "sentinel2"
    ndvi = latest_index([37.45, -1.2, 37.55, -1.1], "ndvi")
    assert ndvi["statistics"]["mean"] > 0
    change = change_detect("before.tif", "after.tif")
    assert change["changed_area_km2"] > 0


def test_expanded_docs_and_web_mobile_scaffolds_present():
    doc = Path("docs/phase4-expanded-brief.md").read_text(encoding="utf-8")
    assert (
        "Track M" in doc and "Track N" in doc and "Track O" in doc and "Track P" in doc
    )
    routes = Path("apps/web/src/routes.ts").read_text(encoding="utf-8")
    assert "/hydrogeology" in routes and "/infrastructure" in routes
    mobile = Path("apps/mobile/lib/main.dart").read_text(encoding="utf-8")
    assert "MainMapScreen" in mobile and "OfflineManagerScreen" in mobile
