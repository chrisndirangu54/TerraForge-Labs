from __future__ import annotations

import json
from pathlib import Path

NI43101_QP_DECLARATION = 'Qualified Person declaration: This technical report has not yet been signed by a Qualified Person.'
KENYA_EL_TEMPLATE_NOTICE = 'Kenya EL progress report scaffold (Mining Act 2016 / Regulations 2017).'


ARTIFACT_DIR = Path('artifacts')
ARTIFACT_DIR.mkdir(exist_ok=True)


def generate_ni43101_report(project_name: str, data: dict) -> dict:
    base = project_name.lower().replace(' ', '_')
    payload = {
        'standard': 'NI_43_101',
        'project_name': project_name,
        'qp_declaration': NI43101_QP_DECLARATION,
        'sections': {
            'property_description': data.get('property_description', 'INCOMPLETE'),
            'drilling': data.get('drilling', 'INCOMPLETE'),
            'data_verification': data.get('data_verification', 'INCOMPLETE'),
        },
    }
    json_path = ARTIFACT_DIR / f'{base}_ni43101.json'
    pdf_path = ARTIFACT_DIR / f'{base}_ni43101.pdf'
    json_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    pdf_path.write_bytes((NI43101_QP_DECLARATION + '\n' + json.dumps(payload)).encode('utf-8'))
    return {
        'json_url': f'minio://reports/{json_path.name}',
        'pdf_url': f'minio://reports/{pdf_path.name}',
    }


def generate_kenya_el_report(project_name: str, data: dict) -> dict:
    base = project_name.lower().replace(' ', '_')
    report = {
        'standard': 'KENYA_EL',
        'project_name': project_name,
        'notice': KENYA_EL_TEMPLATE_NOTICE,
        'nema_checklist': data.get('nema_checklist', {}),
    }
    json_path = ARTIFACT_DIR / f'{base}_kenya_el.json'
    docx_path = ARTIFACT_DIR / f'{base}_kenya_el.docx'
    json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    docx_path.write_bytes((KENYA_EL_TEMPLATE_NOTICE + '\n' + json.dumps(report)).encode('utf-8'))
    return {
        'json_url': f'minio://reports/{json_path.name}',
        'docx_url': f'minio://reports/{docx_path.name}',
    }
