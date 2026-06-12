from __future__ import annotations

import io
from typing import Any


def build_jorc_pdf(report: dict[str, Any], *, disclaimer: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story: list[Any] = []

    project = report.get("project", "TerraForge Report")
    story.append(Paragraph(f"<b>JORC Exploration Report — {project}</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(disclaimer.replace("\n", "<br/>"), styles["BodyText"]))
    story.append(Spacer(1, 12))

    provenance = report.get("provenance") or {}
    if provenance:
        story.append(Paragraph("<b>Model provenance</b>", styles["Heading2"]))
        for task, info in provenance.items():
            version = info.get("version", "unknown") if isinstance(info, dict) else info
            story.append(Paragraph(f"{task}: {version}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    sections = report.get("sections") or {}
    for section_name, section_body in sections.items():
        story.append(Paragraph(f"<b>{section_name}</b>", styles["Heading2"]))
        if isinstance(section_body, dict):
            for criterion, payload in section_body.items():
                if isinstance(payload, dict):
                    text = str(payload.get("text", ""))[:2000]
                    status = payload.get("status", "")
                    story.append(
                        Paragraph(
                            f"<b>{criterion}</b> ({status})<br/>{text}",
                            styles["BodyText"],
                        )
                    )
                else:
                    story.append(Paragraph(str(payload), styles["BodyText"]))
        else:
            story.append(Paragraph(str(section_body), styles["BodyText"]))
        story.append(Spacer(1, 6))

    doc.build(story)
    return buffer.getvalue()