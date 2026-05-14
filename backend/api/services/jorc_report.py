from __future__ import annotations

import json
from pathlib import Path

from backend.api.services.llm import generate_section

DISCLAIMER = "⚠ This report was generated with AI assistance and has NOT been reviewed by a Competent Person as defined under JORC 2012. It must not be used for investment decisions, regulatory filings, or public disclosure without independent review and sign-off by a suitably qualified and experienced Competent Person."
GEOBOTANY_DISCLAIMER = "Geobotanical results are supplementary to primary geochemical and geophysical data. Indicator species responses can be confounded by soil pH, moisture, competition, and disturbance. All anomalies require confirmation by conventional geochemical sampling."

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


def build_geobotany_jorc_sections(data: dict) -> dict:
    species_list = ", ".join(data.get("species_list", ["indicator species"]))
    minerals = ", ".join(data.get("mineral_list", ["target"]))
    section_1 = (
        f"Biogeochemical sampling was conducted using {data.get('species_name', 'target species')} "
        f"{data.get('plant_part', 'leaf')} tissue collected at {data.get('n_samples', 0)} stations "
        f"along {data.get('transect_description', 'planned geobotanical transects')}. Samples were "
        f"dried, ground, and digested by aqua regia prior to ICP-MS analysis at "
        f"{data.get('lab_name', 'external laboratory')} for {data.get('element_list', 'Cu, Co, Ni, Zn')}. "
        "Bioconcentration factors were calculated relative to co-located soil XRF data where "
        f"available (n={data.get('n_pairs', 0)})."
    )
    section_2 = (
        "Geobotanical anomalies were mapped using satellite vegetation stress mapping, "
        f"field indicator species observations of {species_list} with affinity for {minerals} "
        "mineralisation, and plant-tissue biogeochemical sampling. "
        f"The composite score exceeded 80 at {data.get('n_strong', 0)} locations and "
        f"covered {data.get('total_area_km2', 0)} km² across {data.get('n_zones', 0)} zones. "
        f"Spatial calibration against soil geochemistry returned Pearson r = {data.get('r_value', 'pending')}."
    )
    return {
        "sampling_techniques": section_1,
        "geology": section_2,
        "disclaimer": GEOBOTANY_DISCLAIMER,
    }


def build_jorc_report(payload: dict) -> dict:
    project = payload.get("project_name", "Matuu Pilot")
    report = {
        "project": project,
        "disclaimer_acknowledged": False,
        "disclaimer": DISCLAIMER,
        "sections": {},
    }

    for sec, criteria in JORC_SECTIONS.items():
        if isinstance(criteria, list):
            report["sections"][sec] = {}
            for criterion in criteria:
                text = generate_section(f"JORC criterion: {criterion}", payload)
                report["sections"][sec][criterion] = {"text": text, "status": "auto"}
        else:
            report["sections"][sec] = {"status": "INCOMPLETE", "reason": criteria}

    if payload.get("geobotany"):
        geobotany_sections = build_geobotany_jorc_sections(payload["geobotany"])
        report["sections"]["1_sampling_techniques"]["geobotanical_sampling"] = {
            "text": geobotany_sections["sampling_techniques"],
            "status": "auto",
        }
        report["sections"]["2_reporting_of_exploration_results"][
            "geobotany_geology"
        ] = {
            "text": geobotany_sections["geology"],
            "status": "auto",
        }
        report["sections"]["2_reporting_of_exploration_results"][
            "geobotany_disclaimer"
        ] = {
            "text": geobotany_sections["disclaimer"],
            "status": "required",
        }

    base = project.lower().replace(" ", "_")
    json_path = ARTIFACT_DIR / f"{base}_jorc.json"
    html_path = ARTIFACT_DIR / f"{base}_jorc.html"
    pdf_path = ARTIFACT_DIR / f"{base}_jorc.pdf"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path.write_text(
        f"<html><body><h1>{project}</h1><p>{DISCLAIMER}</p><pre>{json.dumps(report, indent=2)}</pre></body></html>",
        encoding="utf-8",
    )
    pdf_path.write_bytes(
        ("PDF-PLACEHOLDER\n" + DISCLAIMER + "\n" + json.dumps(report)).encode("utf-8")
    )

    return {
        "json_url": f"minio://reports/{json_path.name}",
        "html_url": f"minio://reports/{html_path.name}",
        "pdf_url": f"minio://reports/{pdf_path.name}",
    }
