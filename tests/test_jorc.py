import json
from pathlib import Path

from backend.api.services.jorc_report import DISCLAIMER, build_jorc_report


def test_jorc_report_generation_and_disclaimer_present():
    result = build_jorc_report({"project_name": "Matuu Test"})
    assert result["pdf_url"].startswith("minio://")
    html = Path("artifacts/matuu_test_jorc.html").read_text(encoding="utf-8")
    assert DISCLAIMER in html
    data = json.loads(Path("artifacts/matuu_test_jorc.json").read_text())
    assert "1_sampling_techniques" in data["sections"]
    assert data["disclaimer_acknowledged"] is False
