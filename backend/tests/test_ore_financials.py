from fastapi.testclient import TestClient

from backend.api.main import app
from backend.processing.ore_financials import (
    analyze_ore_economics,
    build_cash_flows,
    irr,
    metal_tonnes_from_ore,
    npv,
    parse_ore_inputs,
    payback_years,
    sensitivity_analysis,
)

client = TestClient(app)


def test_metal_tonnes_from_ppm_grade():
    metal = metal_tonnes_from_ore(
        1_000_000,
        grade=100.0,
        grade_unit="ppm",
        recovery=0.8,
    )
    assert metal == 80.0


def test_metal_tonnes_from_percent_grade():
    metal = metal_tonnes_from_ore(
        1_000_000,
        grade=1.0,
        grade_unit="percent",
        recovery=0.9,
    )
    assert metal == 9_000.0


def test_npv_and_irr_simple_project():
    inputs = parse_ore_inputs(
        {
            "commodity": "ta",
            "ore_tonnes": 2_000_000,
            "grade": 150,
            "recovery": 0.75,
            "metal_price_usd": 400,
            "price_unit": "per_kg",
            "opex_usd_per_tonne_ore": 40,
            "capex_usd": 50_000_000,
            "mine_life_years": 8,
            "discount_rate": 0.10,
            "tax_rate_pct": 0,
        }
    )
    flows = build_cash_flows(inputs)
    assert flows[0] < 0
    assert all(flow > 0 for flow in flows[1:])
    assert npv(flows, 0.10) > 0
    assert irr(flows) is not None
    assert irr(flows) > 0.10
    assert payback_years(flows) is not None


def test_analyze_endpoint_returns_metrics():
    response = client.post(
        "/financial/ore/analyze",
        json={
            "commodity": "ta",
            "ore_tonnes": 3_000_000,
            "grade": 120,
            "capex_usd": 60_000_000,
            "mine_life_years": 10,
            "run_monte_carlo": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["npv_usd"] != 0
    assert body["annual"]["annual_revenue_usd"] > 0
    assert len(body["cash_flows"]) == 11


def test_analyze_uses_matuu_grade_when_project_missing_explicit_grade():
    result = analyze_ore_economics(
        {
            "commodity": "ta",
            "dataset": "matuu_synthetic",
            "element": "ta_ppm",
            "capex_usd": 40_000_000,
            "mine_life_years": 5,
            "run_monte_carlo": False,
        }
    )
    assert "grade_from_geodata" in result
    assert result["inputs"]["grade"] > 0


def test_sensitivity_endpoint_orders_tornado():
    response = client.post(
        "/financial/ore/sensitivity",
        json={
            "commodity": "cu",
            "ore_tonnes": 10_000_000,
            "grade": 0.9,
            "capex_usd": 200_000_000,
            "mine_life_years": 12,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["base_npv_usd"] != 0
    assert len(body["tornado"]) == 10
    assert body["tornado"][0]["delta_npv_usd"] != 0


def test_presets_endpoint_lists_commodities():
    response = client.get("/financial/ore/presets")
    assert response.status_code == 200
    body = response.json()
    assert "ta" in body["commodities"]
    assert body["defaults"]["discount_rate"] == 0.12