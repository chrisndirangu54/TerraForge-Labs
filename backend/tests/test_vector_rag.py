from shared.schemas.observation import ObservationRecord

from backend.api.services.ingest import ingest_observations
from backend.api.services.jorc_report import build_jorc_report, get_report_store, reset_report_store
from backend.api.services.llm import rag_query
from backend.api.services.vector_rag import rebuild_vector_index, reset_vector_index, vector_search


def setup_function() -> None:
    reset_vector_index()
    reset_report_store()


def test_vector_search_prefers_ingest_documents():
    ingest_observations(
        [
            ObservationRecord(
                project_id="matuu",
                source="xrf_field",
                parser_version="xrf_bruker@1.0.0",
                crs="EPSG:4326",
                sample_id="MTU-900",
                lon=37.51,
                lat=-1.14,
                data={"ta_ppm": 410.5, "nb_ppm": 1200.0},
            )
        ]
    )
    stats = rebuild_vector_index(project_id="matuu")
    assert stats["ingest_documents"] >= 1

    hits = vector_search("ta_ppm anomaly matuu sample", project_id="matuu", limit=3)
    assert any(hit["id"].startswith("ingest-") for hit in hits)


def test_vector_search_includes_jorc_report_sections():
    build_jorc_report(
        {
            "project_name": "matuu",
            "report_id": "report-vector-1",
            "geobotany": {
                "species_name": "Haumaniastrum",
                "n_samples": 12,
                "element_list": "Cu, Co",
            },
        }
    )
    rebuild_vector_index(project_id="matuu")

    hits = vector_search("geobotanical sampling biogeochemical", project_id="matuu", limit=5)
    assert any(hit["source"].startswith("reports/") for hit in hits)


def test_rag_query_reports_vector_retrieval_meta():
    result = rag_query("JORC sampling QA/QC controls", {"project_id": "matuu"})
    assert result["citation_count"] >= 1
    assert result["meta"]["retrieval"] == "vector_tfidf"
    assert result["meta"]["retrieved_ids"]