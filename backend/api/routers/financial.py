from __future__ import annotations

from fastapi import APIRouter

from backend.processing.ore_financials import (
    analyze_ore_economics,
    list_commodity_presets,
    resolve_grade_from_observations,
    sensitivity_analysis,
)

router = APIRouter()


@router.get("/financial/ore/presets")
async def ore_financial_presets() -> dict:
    return list_commodity_presets()


@router.post("/financial/ore/grade-hint")
async def ore_grade_hint(payload: dict) -> dict:
    hint = resolve_grade_from_observations(payload)
    if hint is None:
        return {"error": "no_observations", "element": payload.get("element", "ta_ppm")}
    return hint


@router.post("/financial/ore/analyze")
async def ore_financial_analyze(payload: dict) -> dict:
    return analyze_ore_economics(payload)


@router.post("/financial/ore/sensitivity")
async def ore_financial_sensitivity(payload: dict) -> dict:
    return sensitivity_analysis(payload)