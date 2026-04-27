from apps.field_agent.terraforge_agent import run_agent_cycle


def test_agent_replans_on_high_anomaly():
    out = run_agent_cycle(0.9, 20)
    assert out['replan_triggered'] is True
