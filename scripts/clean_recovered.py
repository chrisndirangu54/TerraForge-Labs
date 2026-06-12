"""Strip read-output line prefixes from recovered compaction blobs."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_LINE_PREFIX = re.compile(r"^\s*\d+\|")


def clean(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        lines.append(_LINE_PREFIX.sub("", line))
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    dst.write_text(clean(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"cleaned {src.name} -> {dst} ({dst.stat().st_size} bytes)")


if __name__ == "__main__":
    main()