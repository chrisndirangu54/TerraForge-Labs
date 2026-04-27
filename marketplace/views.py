from __future__ import annotations

import json
from pathlib import Path


SEED_PATH = Path('marketplace/fixtures/seed_catalogue.json')


def get_catalogue() -> dict:
    items = json.loads(SEED_PATH.read_text(encoding='utf-8')) if SEED_PATH.exists() else []
    return {'items': items, 'count': len(items)}
