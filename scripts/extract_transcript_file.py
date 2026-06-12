"""Extract longest Write payload for a file from session updates.jsonl."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: extract_transcript_file.py <updates.jsonl> <suffix>")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    suffix = sys.argv[2].replace("\\", "/")
    best = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        upd = row.get("params", {}).get("update", {})
        if upd.get("sessionUpdate") != "tool_call_update":
            continue
        raw = upd.get("rawInput") or {}
        file_path = str(raw.get("path", "")).replace("\\", "/")
        if not file_path.endswith(suffix):
            continue
        content = raw.get("contents")
        if content and len(content) > len(best):
            best = content
    if not best:
        print("NOT_FOUND")
        raise SystemExit(2)
    print(best)


if __name__ == "__main__":
    main()