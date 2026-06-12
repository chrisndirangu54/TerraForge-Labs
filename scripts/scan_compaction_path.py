"""Find longest content blob for a specific file path suffix."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_LINE_PREFIX = re.compile(r"^\s*\d+\|")


def clean(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        lines.append(_LINE_PREFIX.sub("", line))
    return "\n".join(lines).strip() + "\n"


def iter_args(obj):
    if isinstance(obj, dict):
        raw = obj.get("arguments")
        if isinstance(raw, str):
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                pass
        for value in obj.values():
            yield from iter_args(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_args(item)


def main() -> None:
    suffix = sys.argv[1].replace("\\", "/")
    root = Path(sys.argv[2])
    out = Path(sys.argv[3])
    best = ""
    for path in root.glob("**/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for args in iter_args(data):
            file_path = str(args.get("path", "")).replace("\\", "/")
            if not file_path.endswith(suffix):
                continue
            for key in ("contents", "new_string"):
                content = args.get(key)
                if content and len(content) > len(best):
                    best = content
    if not best:
        print("NOT_FOUND")
        raise SystemExit(2)
    out.write_text(clean(best), encoding="utf-8")
    print(f"wrote {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()