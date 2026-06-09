from pathlib import Path

import pytest

from backend.processing.ethnolinguistics import (
    CommunityConsent,
    community_attribution_report,
    interpret_local_term,
    knowledge_layer,
    record_ethnolinguistic_term,
    toponym_analysis,
)


def test_record_ethnolinguistic_term_preserves_consent_and_interpretation():
    record = record_ethnolinguistic_term(
        {
            "term": "maua ya shaba",
            "language_code": "sw",
            "literal_translation": "copper flower",
            "community_id": "kendege-community",
            "consent_scope": "jorc_attribution_allowed",
            "attribution_text": "Kendege community field knowledge",
            "sensitivity": "community_restricted",
            "lon": 37.48,
            "lat": -1.15,
            "project_id": "matuu",
        }
    )
    assert record["language_name"] == "Swahili"
    assert record["consent"]["community_id"] == "kendege-community"
    assert record["inferred"]["top_domain"] in {"mineral", "geobotany"}
    assert record["location"] == {"lon": 37.48, "lat": -1.15}


def test_interpret_local_term_matches_mineral_and_hydro_terms():
    copper = interpret_local_term("shaba", "sw")
    assert copper["top_domain"] == "mineral"
    assert copper["matches"][0]["concept"] == "copper"
    water = interpret_local_term("maji chumvi", "sw")
    assert water["top_domain"] == "hydrogeology"
    assert water["confidence"] > 0


def test_toponym_analysis_and_knowledge_layer_redaction():
    result = toponym_analysis(
        [
            {
                "name": "Mlima Shaba",
                "language_code": "sw",
                "geometry": {"type": "Point", "coordinates": [37.5, -1.1]},
            },
            {
                "name": "Maji Chumvi",
                "language_code": "sw",
                "geometry": {"type": "Point", "coordinates": [37.6, -1.2]},
            },
        ]
    )
    assert result["feature_count"] == 2
    assert result["domain_counts"]["mineral"] >= 1
    layer = knowledge_layer(
        [
            {"term": "public rock", "sensitivity": "public"},
            {"term": "restricted spring", "sensitivity": "community_restricted"},
        ]
    )
    assert layer["visible_record_count"] == 1
    assert layer["redacted_record_count"] == 1


def test_community_attribution_and_sensitivity_validation():
    report = community_attribution_report(
        [
            {"community_id": "c1", "sensitivity": "public"},
            {"community_id": "c1", "sensitivity": "community_restricted"},
            {"community_id": "c2", "sensitivity": "sacred_or_sensitive"},
        ]
    )
    assert report["community_counts"] == {"c1": 2, "c2": 1}
    assert report["restricted_record_count"] == 2
    assert "verified by conventional geoscience" in report["jorc_notice"]
    with pytest.raises(ValueError):
        CommunityConsent("c1", "internal", "credit", "invalid").as_dict()


def test_ethnolinguistics_docs_and_web_metadata():
    doc = Path("docs/phase4-ethnolinguistics-addendum.md").read_text(encoding="utf-8")
    assert "Ethno-Linguistics" in doc
    assert "Consent first" in doc
    api = Path("apps/web/src/api/phase4.ts").read_text(encoding="utf-8")
    assert "/ethnolinguistics/record-term" in api
    layers = Path("apps/web/src/components/map/layers.ts").read_text(encoding="utf-8")
    assert "ethnolinguistic_knowledge" in layers
