"""Recover specific UI files from transcript Write operations only."""
from __future__ import annotations

import json
from pathlib import Path

TRANSCRIPT = Path(
    r"C:\Users\Admin\.grok\sessions\C%3A%5CWINDOWS%5Csystem32"
    r"\019eb4fb-7013-70a3-a839-ce26517ca045\updates.jsonl"
)
REPO = Path(__file__).resolve().parents[1]

TARGETS = {
    "apps/web/src/index.css",
    "apps/web/src/layout/AppLayout.tsx",
    "apps/web/src/pages/DashboardPage.tsx",
    "apps/web/src/pages/LoginPage.tsx",
    "apps/web/tailwind.config.js",
}


def norm_rel(path: str) -> str | None:
    marker = "TerraForge-Labs"
    idx = path.find(marker)
    if idx < 0:
        return None
    tail = path[idx + len(marker) :].lstrip("\\/")
    return tail.replace("\\", "/")


def main() -> None:
    best: dict[str, str] = {}
    with TRANSCRIPT.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            upd = obj.get("params", {}).get("update", {})
            if upd.get("sessionUpdate") != "tool_call":
                continue
            raw = upd.get("rawInput", {})
            if raw.get("title") != "Write":
                continue
            rel = norm_rel(raw.get("path", ""))
            if rel not in TARGETS:
                continue
            contents = raw.get("contents", "")
            if len(contents) > len(best.get(rel, "")):
                best[rel] = contents

    for rel in TARGETS:
        content = best.get(rel)
        if not content:
            print(f"MISSING {rel}")
            continue
        dest = REPO / rel
        dest.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {rel} ({len(content)} bytes)")


if __name__ == "__main__":
    main()