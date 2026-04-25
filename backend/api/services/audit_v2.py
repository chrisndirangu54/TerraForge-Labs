from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4


def build_audit_event(payload: dict) -> dict:
    serialized = json.dumps(payload, sort_keys=True)
    event_hash = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    return {
        'event_id': str(uuid4()),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'input_hash': event_hash,
        'action': payload.get('action', 'unknown'),
        'resource_type': payload.get('resource_type', 'unknown'),
    }
