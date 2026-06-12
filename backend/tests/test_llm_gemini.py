import os
from unittest.mock import patch

from backend.api.services.gemini_client import is_gemini_configured
from backend.api.services.llm import llm_status, rag_query


def test_llm_status_reports_configuration():
    status = llm_status()
    assert "provider" in status
    assert "gemini_configured" in status
    assert status["active"] is False or status["gemini_configured"]


def test_rag_query_stub_mode_has_citations():
    os.environ["LLM_FORCE_STUB"] = "true"
    result = rag_query("Explain kriging uncertainty for drill spacing", {"project_id": "p1"})
    assert result["citation_count"] >= 1
    assert result["citations"][0]["id"]
    assert result["answer"]


@patch("backend.api.services.llm._use_gemini", return_value=True)
@patch("backend.api.services.llm._build_gemini_answer")
def test_rag_query_uses_gemini_when_available(mock_gemini, _mock_use):
    mock_gemini.return_value = {
        "answer": "Kriging variance informs drill spacing. Sources:\n- [kriging-uncertainty]",
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "prompt_tokens": 10,
        "output_tokens": 20,
    }
    os.environ.pop("LLM_FORCE_STUB", None)
    result = rag_query("How does kriging uncertainty affect drilling?", {})
    assert result["provider"] == "gemini"
    assert "Kriging" in result["answer"] or "kriging" in result["answer"].lower()


def test_is_gemini_configured_without_key():
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "LLM_API_KEY": ""}, clear=False):
        assert is_gemini_configured() is False