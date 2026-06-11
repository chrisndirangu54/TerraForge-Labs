from backend.api.services.jorc_pdf import build_jorc_pdf


def test_build_jorc_pdf_returns_pdf_bytes():
    report = {
        "project": "Test Project",
        "provenance": {"mineral": {"version": "v0.1.0"}},
        "sections": {
            "1_sampling_techniques": {
                "sampling": {"text": "Chain of custody maintained.", "status": "auto"}
            }
        },
    }
    pdf = build_jorc_pdf(report, disclaimer="AI-assisted draft only.")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 200
