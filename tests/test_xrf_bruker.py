import json
from pathlib import Path

from shared.instruments.xrf_bruker import XrfBrukerParser


def test_parse_validate_calibrate_geojson(tmp_path):
    parser = XrfBrukerParser()
    rows = parser.parse("tests/fixtures/sample_bruker_export.csv")
    assert len(rows) == 10
    assert {"sample_id", "ta_ppm", "rel_error_pct", "flagged"}.issubset(rows[0].keys())

    result = parser.validate(rows)
    assert "flagged_count" in result

    cal = tmp_path / "cal.json"
    cal.write_text(json.dumps({"ta_ppm": {"slope": 2.0, "intercept": 1.0}}))
    calibrated = parser.calibrate(rows, str(cal))
    assert calibrated[0]["ta_ppm"] == rows[0]["ta_ppm"] * 2.0 + 1.0

    geojson = parser.to_geojson(rows)
    assert geojson["type"] == "FeatureCollection"
    assert geojson["crs"]["properties"]["name"] == "EPSG:4326"
