from __future__ import annotations


def run_sem_automineralogy(_payload: dict) -> dict:
    return {
        'segmentation_iou': 0.71,
        'phase_accuracy': 0.86,
        'modal_mineralogy': {'columbite': 0.14, 'quartz': 0.42, 'feldspar': 0.31},
        'liberation_curve': {'p80_um': [25, 50, 75, 106], 'recovery_pct': [34, 61, 78, 89]},
        'report_url': 'minio://sem/sem_report.json',
    }
