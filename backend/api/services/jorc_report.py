from __future__ import annotations

import json
from pathlib import Path

from backend.api.services.llm import generate_section

DISCLAIMER = "⚠ This report was generated with AI assistance and has NOT been reviewed by a Competent Person as defined under JORC 2012. It must not be used for investment decisions, regulatory filings, or public disclosure without independent review and sign-off by a suitably qualified and experienced Competent Person."

JORC_SECTIONS = {
    "1_sampling_techniques": [
        "sampling",
        "drilling",
        "sampling_recovery",
        "logging",
        "sub_sampling",
        "quality_of_assay_data",
        "verification",
        "location_of_data_points",
        "data_spacing",
        "orientation",
        "sample_security",
        "audits",
    ],
    "2_reporting_of_exploration_results": [
        "mineral_tenement",
        "exploration_done",
        "geology",
        "drill_hole_info",
        "data_aggregation",
        "relationship_width_grade",
        "diagrams",
        "balanced_reporting",
        "other_substantive_exploration_data",
        "further_work",
    ],
    "3_estimation_and_reporting_resources": "GEOLOGIST_REVIEW_REQUIRED",
    "4_estimation_and_reporting_reserves": "GEOLOGIST_REVIEW_REQUIRED",
}

ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)


def build_jorc_report(payload: dict) -> dict:
    project = payload.get("project_name", "Matuu Pilot")
    report = {"project": project, "disclaimer_acknowledged": False, "disclaimer": DISCLAIMER, "sections": {}}

    for sec, criteria in JORC_SECTIONS.items():
        if isinstance(criteria, list):
            report["sections"][sec] = {}
            for criterion in criteria:
                text = generate_section(f"JORC criterion: {criterion}", payload)
                report["sections"][sec][criterion] = {"text": text, "status": "auto"}
        else:
            report["sections"][sec] = {"status": "INCOMPLETE", "reason": criteria}

    base = project.lower().replace(" ", "_")
    json_path = ARTIFACT_DIR / f"{base}_jorc.json"
    html_path = ARTIFACT_DIR / f"{base}_jorc.html"
    pdf_path = ARTIFACT_DIR / f"{base}_jorc.pdf"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path.write_text(f"<html><body><h1>{project}</h1><p>{DISCLAIMER}</p><pre>{json.dumps(report, indent=2)}</pre></body></html>", encoding="utf-8")
    pdf_path.write_bytes(("PDF-PLACEHOLDER\n" + DISCLAIMER + "\n" + json.dumps(report)).encode("utf-8"))

    return {
        "json_url": f"minio://reports/{json_path.name}",
        "html_url": f"minio://reports/{html_path.name}",
        "pdf_url": f"minio://reports/{pdf_path.name}",
    }
