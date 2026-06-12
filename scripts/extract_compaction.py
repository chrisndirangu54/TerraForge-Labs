"""Search compaction JSON blobs for file contents containing a needle."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def walk(obj, needle: str, path_suffix: str) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        raw = obj.get("arguments")
        if isinstance(raw, str):
            try:
                args = json.loads(raw)
            except json.JSONDecodeError:
                args = {}
            for key in ("contents", "new_string"):
                content = args.get(key)
                file_path = str(args.get("path", "")).replace("\\", "/")
                if (
                    content
                    and needle in content
                    and file_path.endswith(path_suffix.replace("\\", "/"))
                ):
                    found.append(content)
        for value in obj.values():
            found.extend(walk(value, needle, path_suffix))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(walk(item, needle, path_suffix))
    return found


def main() -> None:
    if len(sys.argv) < 4:
        print("usage: extract_compaction.py <json> <needle> <path_suffix>")
        raise SystemExit(1)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    matches = walk(data, sys.argv[2], sys.argv[3])
    if not matches:
        print("NOT_FOUND")
        raise SystemExit(2)
    best = max(matches, key=len)
    print(best)


if __name__ == "__main__":
    main()