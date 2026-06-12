from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Any

import numpy as np
from scipy.optimize import brentq

from shared.constants import (
    DISCOUNT_RATE_BASE,
    HEDGING_SIMULATIONS,
    METAL_PRICE_VOLATILITY,
)

TROY_OZ_PER_TONNE = 32_150.7465686

COMMODITY_PRESETS: dict[str, dict[str, Any]] = {
    "ta": {
        "name": "Tantalum (Ta)",
        "grade_unit": "ppm",
        "default_grade": 120.0,
        "recovery": 0.75,
        "metal_price_usd": 350.0,
        "price_unit": "per_kg",
        "opex_usd_per_tonne_ore": 45.0,
        "typical_capex_usd_per_tonne_annual_capacity": 120.0,
    },
    "nb": {
        "name": "Niobium (Nb)",
        "grade_unit": "ppm",
        "default_grade": 500.0,
        "recovery": 0.70,
        "metal_price_usd": 45.0,
        "price_unit": "per_kg",
        "opex_usd_per_tonne_ore": 40.0,
        "typical_capex_usd_per_tonne_annual_capacity": 100.0,
    },
    "cu": {
        "name": "Copper (Cu)",
        "grade_unit": "percent",
        "default_grade": 0.8,
        "recovery": 0.88,
        "metal_price_usd": 9_500.0,
        "price_unit": "per_tonne",
        "opex_usd_per_tonne_ore": 25.0,
        "typical_capex_usd_per_tonne_annual_capacity": 80.0,
    },
    "au": {
        "name": "Gold (Au)",
        "grade_unit": "ppm",
        "default_grade": 2.5,
        "recovery": 0.92,
        "metal_price_usd": 2_350.0,
        "price_unit": "per_oz",
        "opex_usd_per_tonne_ore": 35.0,
        "typical_capex_usd_per_tonne_annual_capacity": 150.0,
    },
    "sn": {
        "name": "Tin (Sn)",
        "grade_unit": "percent",
        "default_grade": 0.5,
        "recovery": 0.80,
        "metal_price_usd": 28_000.0,
        "price_unit": "per_tonne",
        "opex_usd_per_tonne_ore": 30.0,
        "typical_capex_usd_per_tonne_annual_capacity": 90.0,
    },
    "li": {
        "name": "Lithium (Li)",
        "grade_unit": "percent",
        "default_grade": 1.2,
        "recovery": 0.75,
        "metal_price_usd": 18_000.0,
        "price_unit": "per_tonne",
        "opex_usd_per_tonne_ore": 55.0,
        "typical_capex_usd_per_tonne_annual_capacity": 200.0,
    },
}

SENSITIVITY_FACTORS = (0.8, 0.9, 1.0, 1.1, 1.2)


@dataclass(frozen=True)
class OreFinancialInputs:
    commodity: str
    ore_tonnes: float
    grade: float
    grade_unit: str
    recovery: float
    metal_price_usd: float
    price_unit: str
    opex_usd_per_tonne_ore: float
    capex_usd: float
    mine_life_years: int
    discount_rate: float
    annual_throughput_tonnes: float | None = None
    sustaining_capex_usd: float = 0.0
    royalty_pct: float = 0.0
    tax_rate_pct: float = 0.0


def metal_price_per_tonne(price: float, unit: str) -> float:
    if unit == "per_tonne":
        return price
    if unit == "per_kg":
        return price * 1_000.0
    if unit == "per_oz":
        return price * TROY_OZ_PER_TONNE
    raise ValueError(f"unsupported price_unit: {unit}")


def metal_tonnes_from_ore(
    ore_tonnes: float,
    *,
    grade: float,
    grade_unit: str,
    recovery: float,
) -> float:
    if grade_unit == "ppm":
        contained = ore_tonnes * (grade / 1_000_000.0)
    elif grade_unit == "percent":
        contained = ore_tonnes * (grade / 100.0)
    else:
        raise ValueError(f"unsupported grade_unit: {grade_unit}")
    return contained * recovery


def build_cash_flows(inputs: OreFinancialInputs) -> list[float]:
    annual_ore = inputs.annual_throughput_tonnes
    if annual_ore is None:
        annual_ore = inputs.ore_tonnes / max(inputs.mine_life_years, 1)

    metal_per_year = metal_tonnes_from_ore(
        annual_ore,
        grade=inputs.grade,
        grade_unit=inputs.grade_unit,
        recovery=inputs.recovery,
    )
    price_per_tonne = metal_price_per_tonne(
        inputs.metal_price_usd,
        inputs.price_unit,
    )
    annual_revenue = metal_per_year * price_per_tonne
    annual_opex = annual_ore * inputs.opex_usd_per_tonne_ore
    royalty_rate = inputs.royalty_pct / 100.0
    tax_rate = inputs.tax_rate_pct / 100.0

    flows = [-inputs.capex_usd]
    for _ in range(inputs.mine_life_years):
        royalty = annual_revenue * royalty_rate
        ebit = (
            annual_revenue
            - annual_opex
            - royalty
            - inputs.sustaining_capex_usd
        )
        tax = max(ebit, 0.0) * tax_rate
        flows.append(ebit - tax)
    return flows


def npv(cash_flows: list[float], discount_rate: float) -> float:
    total = 0.0
    for period, amount in enumerate(cash_flows):
        total += amount / (1.0 + discount_rate) ** period
    return total


def _npv_at_rate(cash_flows: list[float], rate: float) -> float:
    return npv(cash_flows, rate)


def irr(cash_flows: list[float]) -> float | None:
    if not cash_flows or cash_flows[0] >= 0:
        return None
    if sum(cash_flows[1:]) <= 0:
        return None

    def objective(rate: float) -> float:
        return _npv_at_rate(cash_flows, rate)

    try:
        if objective(0.0) <= 0:
            return None
        return float(brentq(objective, -0.5, 5.0, maxiter=200))
    except ValueError:
        return None


def payback_years(cash_flows: list[float]) -> float | None:
    cumulative = 0.0
    for year, amount in enumerate(cash_flows):
        prev = cumulative
        cumulative += amount
        if cumulative >= 0 and year > 0:
            if amount == 0:
                return float(year)
            fraction = -prev / amount
            return year - 1 + fraction
    return None


def annual_summary(inputs: OreFinancialInputs) -> dict[str, float]:
    annual_ore = inputs.annual_throughput_tonnes
    if annual_ore is None:
        annual_ore = inputs.ore_tonnes / max(inputs.mine_life_years, 1)

    metal_per_year = metal_tonnes_from_ore(
        annual_ore,
        grade=inputs.grade,
        grade_unit=inputs.grade_unit,
        recovery=inputs.recovery,
    )
    price_per_tonne = metal_price_per_tonne(
        inputs.metal_price_usd,
        inputs.price_unit,
    )
    revenue = metal_per_year * price_per_tonne
    opex = annual_ore * inputs.opex_usd_per_tonne_ore
    return {
        "annual_ore_tonnes": annual_ore,
        "annual_metal_tonnes": metal_per_year,
        "annual_revenue_usd": revenue,
        "annual_opex_usd": opex,
        "annual_ebitda_usd": revenue - opex,
    }


def parse_ore_inputs(payload: dict[str, Any]) -> OreFinancialInputs:
    commodity = str(payload.get("commodity", "ta")).lower()
    preset = COMMODITY_PRESETS.get(commodity, COMMODITY_PRESETS["ta"])

    mine_life = int(payload.get("mine_life_years", 10))
    annual_throughput = payload.get("annual_throughput_tonnes")
    ore_tonnes = float(payload.get("ore_tonnes", 5_000_000))
    if annual_throughput is not None:
        annual_throughput = float(annual_throughput)
        if payload.get("ore_tonnes") is None:
            ore_tonnes = annual_throughput * mine_life

    capex = payload.get("capex_usd")
    if capex is None:
        throughput = annual_throughput or (ore_tonnes / max(mine_life, 1))
        capex = throughput * float(
            preset.get("typical_capex_usd_per_tonne_annual_capacity", 100.0)
        )

    return OreFinancialInputs(
        commodity=commodity,
        ore_tonnes=ore_tonnes,
        grade=float(payload.get("grade", preset["default_grade"])),
        grade_unit=str(payload.get("grade_unit", preset["grade_unit"])),
        recovery=float(payload.get("recovery", preset["recovery"])),
        metal_price_usd=float(
            payload.get("metal_price_usd", preset["metal_price_usd"])
        ),
        price_unit=str(payload.get("price_unit", preset["price_unit"])),
        opex_usd_per_tonne_ore=float(
            payload.get("opex_usd_per_tonne_ore", preset["opex_usd_per_tonne_ore"])
        ),
        capex_usd=float(capex),
        mine_life_years=mine_life,
        discount_rate=float(payload.get("discount_rate", DISCOUNT_RATE_BASE)),
        annual_throughput_tonnes=annual_throughput,
        sustaining_capex_usd=float(payload.get("sustaining_capex_usd", 0.0)),
        royalty_pct=float(payload.get("royalty_pct", 0.0)),
        tax_rate_pct=float(payload.get("tax_rate_pct", 30.0)),
    )


def resolve_grade_from_observations(payload: dict[str, Any]) -> dict[str, Any] | None:
    element = payload.get("element", "ta_ppm")
    if not payload.get("project_id") and not payload.get("dataset"):
        return None

    from backend.api.services.kriging_observations import (
        extract_kriging_points,
        resolve_kriging_observations,
    )

    observations = resolve_kriging_observations({**payload, "element": element})
    if len(observations) < 1:
        return None

    _, _, values = extract_kriging_points(observations, element=element)
    grade_unit = "ppm" if element.endswith("_ppm") else "percent"
    return {
        "grade": mean(values),
        "grade_unit": grade_unit,
        "element": element,
        "observation_count": len(values),
        "grade_min": min(values),
        "grade_max": max(values),
    }


def analyze_ore_economics(payload: dict[str, Any]) -> dict[str, Any]:
    grade_hint = resolve_grade_from_observations(payload)
    merged = dict(payload)
    if grade_hint and merged.get("grade") is None:
        merged["grade"] = grade_hint["grade"]
        merged.setdefault("grade_unit", grade_hint["grade_unit"])

    inputs = parse_ore_inputs(merged)
    cash_flows = build_cash_flows(inputs)
    discount = inputs.discount_rate
    annual = annual_summary(inputs)
    total_metal = metal_tonnes_from_ore(
        inputs.ore_tonnes,
        grade=inputs.grade,
        grade_unit=inputs.grade_unit,
        recovery=inputs.recovery,
    )

    result: dict[str, Any] = {
        "commodity": inputs.commodity,
        "inputs": {
            "ore_tonnes": inputs.ore_tonnes,
            "grade": inputs.grade,
            "grade_unit": inputs.grade_unit,
            "recovery": inputs.recovery,
            "metal_price_usd": inputs.metal_price_usd,
            "price_unit": inputs.price_unit,
            "opex_usd_per_tonne_ore": inputs.opex_usd_per_tonne_ore,
            "capex_usd": inputs.capex_usd,
            "mine_life_years": inputs.mine_life_years,
            "discount_rate": discount,
            "royalty_pct": inputs.royalty_pct,
            "tax_rate_pct": inputs.tax_rate_pct,
        },
        "resource": {
            "contained_metal_tonnes": total_metal,
            "recovered_metal_tonnes": total_metal,
            "metal_price_usd_per_tonne": metal_price_per_tonne(
                inputs.metal_price_usd,
                inputs.price_unit,
            ),
        },
        "annual": annual,
        "metrics": {
            "npv_usd": npv(cash_flows, discount),
            "irr": irr(cash_flows),
            "payback_years": payback_years(cash_flows),
            "undiscounted_cash_flow_usd": sum(cash_flows),
        },
        "cash_flows": [
            {"year": year, "amount_usd": round(amount, 2)}
            for year, amount in enumerate(cash_flows)
        ],
    }
    if grade_hint:
        result["grade_from_geodata"] = grade_hint

    if payload.get("run_monte_carlo", True):
        result["monte_carlo"] = run_price_monte_carlo(inputs, payload)

    return result


def run_price_monte_carlo(
    inputs: OreFinancialInputs,
    payload: dict[str, Any],
) -> dict[str, Any]:
    iterations = int(payload.get("monte_carlo_iterations", min(HEDGING_SIMULATIONS, 2000)))
    volatility = float(payload.get("price_volatility", METAL_PRICE_VOLATILITY))
    rng = np.random.default_rng(int(payload.get("seed", 42)))

    npv_samples: list[float] = []
    irr_samples: list[float] = []
    for _ in range(iterations):
        shock = rng.normal(1.0, volatility)
        shocked_price = max(inputs.metal_price_usd * shock, 0.01)
        scenario = OreFinancialInputs(
            commodity=inputs.commodity,
            ore_tonnes=inputs.ore_tonnes,
            grade=inputs.grade,
            grade_unit=inputs.grade_unit,
            recovery=inputs.recovery,
            metal_price_usd=shocked_price,
            price_unit=inputs.price_unit,
            opex_usd_per_tonne_ore=inputs.opex_usd_per_tonne_ore,
            capex_usd=inputs.capex_usd,
            mine_life_years=inputs.mine_life_years,
            discount_rate=inputs.discount_rate,
            annual_throughput_tonnes=inputs.annual_throughput_tonnes,
            sustaining_capex_usd=inputs.sustaining_capex_usd,
            royalty_pct=inputs.royalty_pct,
            tax_rate_pct=inputs.tax_rate_pct,
        )
        flows = build_cash_flows(scenario)
        npv_samples.append(npv(flows, inputs.discount_rate))
        scenario_irr = irr(flows)
        if scenario_irr is not None:
            irr_samples.append(scenario_irr)

    npv_arr = np.array(npv_samples)
    irr_arr = np.array(irr_samples) if irr_samples else np.array([0.0])
    return {
        "iterations": iterations,
        "price_volatility": volatility,
        "npv": {
            "p10_usd": float(np.percentile(npv_arr, 10)),
            "p50_usd": float(np.percentile(npv_arr, 50)),
            "p90_usd": float(np.percentile(npv_arr, 90)),
            "mean_usd": float(np.mean(npv_arr)),
            "positive_probability": float(np.mean(npv_arr > 0)),
        },
        "irr": {
            "p10": float(np.percentile(irr_arr, 10)) if len(irr_samples) else None,
            "p50": float(np.percentile(irr_arr, 50)) if len(irr_samples) else None,
            "p90": float(np.percentile(irr_arr, 90)) if len(irr_samples) else None,
        },
    }


def sensitivity_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    base_inputs = parse_ore_inputs(payload)
    base_npv = npv(build_cash_flows(base_inputs), base_inputs.discount_rate)

    def scenario_npv(**overrides: float) -> float:
        merged = {
            "commodity": base_inputs.commodity,
            "ore_tonnes": base_inputs.ore_tonnes,
            "grade": base_inputs.grade,
            "grade_unit": base_inputs.grade_unit,
            "recovery": base_inputs.recovery,
            "metal_price_usd": base_inputs.metal_price_usd,
            "price_unit": base_inputs.price_unit,
            "opex_usd_per_tonne_ore": base_inputs.opex_usd_per_tonne_ore,
            "capex_usd": base_inputs.capex_usd,
            "mine_life_years": base_inputs.mine_life_years,
            "discount_rate": base_inputs.discount_rate,
            "annual_throughput_tonnes": base_inputs.annual_throughput_tonnes,
            "sustaining_capex_usd": base_inputs.sustaining_capex_usd,
            "royalty_pct": base_inputs.royalty_pct,
            "tax_rate_pct": base_inputs.tax_rate_pct,
        }
        merged.update(overrides)
        inputs = parse_ore_inputs(merged)
        return npv(build_cash_flows(inputs), inputs.discount_rate)

    variables = {
        "metal_price_usd": base_inputs.metal_price_usd,
        "grade": base_inputs.grade,
        "recovery": base_inputs.recovery,
        "capex_usd": base_inputs.capex_usd,
        "opex_usd_per_tonne_ore": base_inputs.opex_usd_per_tonne_ore,
    }

    table: list[dict[str, Any]] = []
    for name, base_value in variables.items():
        for factor in SENSITIVITY_FACTORS:
            adjusted = base_value * factor
            value = scenario_npv(**{name: adjusted})
            table.append(
                {
                    "variable": name,
                    "factor": factor,
                    "value": adjusted,
                    "npv_usd": value,
                    "delta_npv_usd": value - base_npv,
                }
            )

    ranked = sorted(table, key=lambda row: abs(row["delta_npv_usd"]), reverse=True)
    return {
        "base_npv_usd": base_npv,
        "tornado": ranked[:10],
        "table": table,
    }


def list_commodity_presets() -> dict[str, Any]:
    return {
        "commodities": {
            key: {
                "name": preset["name"],
                "grade_unit": preset["grade_unit"],
                "default_grade": preset["default_grade"],
                "recovery": preset["recovery"],
                "metal_price_usd": preset["metal_price_usd"],
                "price_unit": preset["price_unit"],
                "opex_usd_per_tonne_ore": preset["opex_usd_per_tonne_ore"],
            }
            for key, preset in COMMODITY_PRESETS.items()
        },
        "defaults": {
            "discount_rate": DISCOUNT_RATE_BASE,
            "price_volatility": METAL_PRICE_VOLATILITY,
        },
    }