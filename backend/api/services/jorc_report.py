from __future__ import annotations



import json

from datetime import datetime, timezone

from typing import Any

from uuid import uuid4



from backend.api.services.audit_v2 import get_audit_store

from backend.api.services.jorc_pdf import build_jorc_pdf

from backend.api.services.llm import generate_section

from backend.api.services.storage import get_storage_service

from backend.ml.registry import get_model_registry



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



VALID_STATES = frozenset({"draft", "review", "approved"})

VALID_TRANSITIONS = {

    "draft": {"review"},

    "review": {"approved", "draft"},

    "approved": set(),

}





class MemoryReportStore:

    def __init__(self) -> None:

        self._reports: dict[str, dict[str, Any]] = {}



    def save(self, report: dict[str, Any]) -> dict[str, Any]:

        self._reports[report["report_id"]] = report

        return report



    def get(self, report_id: str) -> dict[str, Any] | None:

        return self._reports.get(report_id)



    def list_reports(self) -> list[dict[str, Any]]:

        return sorted(

            self._reports.values(),

            key=lambda item: item.get("updated_at", ""),

            reverse=True,

        )



    def reset(self) -> None:

        self._reports.clear()





_REPORT_STORE: MemoryReportStore | None = None





def get_report_store() -> MemoryReportStore:

    global _REPORT_STORE

    if _REPORT_STORE is None:

        _REPORT_STORE = MemoryReportStore()

    return _REPORT_STORE





def reset_report_store() -> None:

    global _REPORT_STORE

    _REPORT_STORE = None





def _model_provenance() -> dict[str, Any]:

    registry = get_model_registry()

    provenance: dict[str, Any] = {}

    for task in ("mineral", "geobotany", "grain_segmentation"):

        production = registry.get_production(task)

        if production:

            provenance[task] = {

                "version": production.get("version"),

                "artifact_path": production.get("artifact_path"),

                "metrics": production.get("metrics", {}),

            }

    return provenance





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

    report_id = payload.get("report_id") or str(uuid4())

    now = datetime.now(timezone.utc).isoformat()

    report = {

        "report_id": report_id,

        "project": project,

        "state": "draft",

        "disclaimer_acknowledged": False,

        "disclaimer": DISCLAIMER,

        "sections": {},

        "provenance": _model_provenance(),

        "created_at": now,

        "updated_at": now,

        "approved_by": None,

        "approved_at": None,

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



    storage = get_storage_service()

    base = project.lower().replace(" ", "_")

    json_key = f"reports/{base}_jorc.json"

    html_key = f"reports/{base}_jorc.html"

    pdf_key = f"reports/{base}_jorc.pdf"



    storage.put(json_key, json.dumps(report, indent=2), content_type="application/json")

    storage.put(

        html_key,

        f"<html><body><h1>{project}</h1><p>{DISCLAIMER}</p><pre>{json.dumps(report, indent=2)}</pre></body></html>",

        content_type="text/html",

    )

    storage.put(

        pdf_key,

        build_jorc_pdf(report, disclaimer=DISCLAIMER),

        content_type="application/pdf",

    )



    get_report_store().save(report)

    get_audit_store().record(

        {

            "action": "jorc_report_created",

            "resource_type": "jorc_report",

            "resource_id": report_id,

            "actor": payload.get("actor", "system"),

            "metadata": {"project": project, "state": "draft"},

        }

    )



    return {

        "report_id": report_id,

        "state": report["state"],

        "json_url": storage.get_public_url(json_key),

        "html_url": storage.get_public_url(html_key),

        "pdf_url": storage.get_public_url(pdf_key),

        "provenance": report["provenance"],

    }





def transition_report_state(

    report_id: str,

    *,

    target_state: str,

    actor: str = "system",

) -> dict[str, Any]:

    if target_state not in VALID_STATES:

        raise ValueError(f"Invalid report state: {target_state}")



    store = get_report_store()

    report = store.get(report_id)

    if report is None:

        raise KeyError(f"Report not found: {report_id}")



    current_state = report["state"]

    if target_state not in VALID_TRANSITIONS.get(current_state, set()):

        raise ValueError(f"Invalid transition from {current_state} to {target_state}")



    if target_state == "approved" and not report.get("disclaimer_acknowledged"):

        raise ValueError("Disclaimer must be acknowledged before approval")



    now = datetime.now(timezone.utc).isoformat()

    report = {

        **report,

        "state": target_state,

        "updated_at": now,

        "approved_by": (

            actor if target_state == "approved" else report.get("approved_by")

        ),

        "approved_at": now if target_state == "approved" else report.get("approved_at"),

    }

    store.save(report)

    get_audit_store().record(

        {

            "action": "jorc_report_transition",

            "resource_type": "jorc_report",

            "resource_id": report_id,

            "actor": actor,

            "metadata": {

                "from_state": current_state,

                "to_state": target_state,

            },

        }

    )

    return report





def acknowledge_disclaimer(report_id: str) -> dict[str, Any]:

    store = get_report_store()

    report = store.get(report_id)

    if report is None:

        raise KeyError(f"Report not found: {report_id}")

    report = {

        **report,

        "disclaimer_acknowledged": True,

        "updated_at": datetime.now(timezone.utc).isoformat(),

    }

    store.save(report)

    return report
