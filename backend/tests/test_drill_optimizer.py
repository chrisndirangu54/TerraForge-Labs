from backend.processing.gap_closure import drill_plan_optimise


def test_drill_plan_optimise_returns_ranked_holes_within_budget():
    plan = drill_plan_optimise(
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
    assert plan["ranked_holes"]
    assert plan["ranked_holes"][0]["rank"] == 1
    assert (
        plan["ranked_holes"][0]["priority_score"]
        >= plan["ranked_holes"][-1]["priority_score"]
    )
    assert plan["selected_holes"]
    assert plan["estimated_spend_usd"] <= 70_000
