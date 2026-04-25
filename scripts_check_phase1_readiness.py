from __future__ import annotations

from pathlib import Path

CHECKS = {
    'phase1_tests_exist': Path('tests/test_kriging.py').exists() and Path('tests/test_jorc.py').exists(),
    'instrument_upload_route_exists': Path('backend/api/routers/instruments.py').exists(),
    'fuse_geodata_route_exists': Path('backend/api/routers/geodata.py').exists(),
    'deposit_model_exists': Path('backend/processing/deposit_model.py').exists(),
    'mobile_classifier_asset_exists': Path('apps/mobile/assets/models/mineral_classifier_int8.tflite').exists(),
    'readme_has_problem_statement': '## Problem statement' in Path('README.md').read_text(encoding='utf-8'),
    'readme_has_demo_link_placeholder': 'Demo video link' in Path('README.md').read_text(encoding='utf-8'),
}

if __name__ == '__main__':
    all_ok = all(CHECKS.values())
    for name, ok in CHECKS.items():
        print(f'{name}: {"PASS" if ok else "FAIL"}')
    raise SystemExit(0 if all_ok else 1)
