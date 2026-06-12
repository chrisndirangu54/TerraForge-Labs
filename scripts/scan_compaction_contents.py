"""Find longest Python-like content blobs in compaction JSON files."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from iter_strings(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_strings(item)


def main() -> None:
    needle = sys.argv[1]
    root = Path(sys.argv[2])
    best = ""
    for path in root.glob("**/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for text in iter_strings(data):
            if needle in text and text.strip().startswith(("from ", "import ", "def ", "class ")):
                if len(text) > len(best):
                    best = text
    if not best:
        print("NOT_FOUND")
        raise SystemExit(2)
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    if out:
        out.write_text(best, encoding="utf-8")
        print(f"wrote {len(best)} chars to {out}")
    else:
        print(best)


if __name__ == "__main__":
    main()