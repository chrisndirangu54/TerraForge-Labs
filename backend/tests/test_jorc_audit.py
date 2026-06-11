from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.services.audit_v2 import get_audit_store, reset_audit_store
from backend.api.services.jorc_report import (
    acknowledge_disclaimer,
    build_jorc_report,
    get_report_store,
    reset_report_store,
    transition_report_state,
)

client = TestClient(app)


def setup_function() -> None:
    reset_audit_store()
    reset_report_store()


def test_jorc_report_created_in_draft_with_provenance():
    result = build_jorc_report({"project_name": "Audit Pilot", "actor": "geologist"})
    report = get_report_store().get(result["report_id"])
    assert report is not None
    assert report["state"] == "draft"
    assert "mineral" in report["provenance"]
    events = get_audit_store().list_events(resource_type="jorc_report")
    assert events
    assert events[0]["action"] == "jorc_report_created"


def test_report_state_transitions_require_disclaimer_acknowledgement():
    created = build_jorc_report({"project_name": "Transition Pilot"})
    report_id = created["report_id"]

    with_transition_error = False
    try:
        transition_report_state(
            report_id, target_state="approved", actor="cp@example.com"
        )
    except ValueError:
        with_transition_error = True
    assert with_transition_error

    acknowledge_disclaimer(report_id)
    transition_report_state(
        report_id, target_state="review", actor="reviewer@example.com"
    )
    approved = transition_report_state(
        report_id,
        target_state="approved",
        actor="cp@example.com",
    )
    assert approved["state"] == "approved"
    assert approved["approved_by"] == "cp@example.com"


def test_report_transition_endpoint():
    created = build_jorc_report({"project_name": "API Transition"})
    report_id = created["report_id"]
    client.post(f"/reports/jorc/{report_id}/acknowledge-disclaimer")
    response = client.post(
        f"/reports/jorc/{report_id}/transition",
        json={"state": "review"},
    )
    assert response.status_code == 200
    assert response.json()["state"] == "review"
