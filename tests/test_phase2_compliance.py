from backend.api.services.audit_v2 import build_audit_event
from backend.api.services.jorc_v2 import generate_kenya_el_report, generate_ni43101_report


def test_ni43101_generation_contains_urls():
    out = generate_ni43101_report('Matuu Compliance', {'drilling': 'phase2-sample'})
    assert out['pdf_url'].startswith('minio://')
    assert out['json_url'].startswith('minio://')


def test_kenya_el_generation_contains_docx_url():
    out = generate_kenya_el_report('Matuu Compliance', {'nema_checklist': {'dust': 'ok'}})
    assert out['docx_url'].startswith('minio://')


def test_audit_event_has_hash_and_id():
    evt = build_audit_event({'action': 'test', 'resource_type': 'report'})
    assert 'input_hash' in evt and len(evt['input_hash']) == 64
    assert 'event_id' in evt
