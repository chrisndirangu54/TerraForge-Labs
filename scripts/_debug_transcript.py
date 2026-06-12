import json
from pathlib import Path

TRANSCRIPT = Path(
    r"C:\Users\Admin\.grok\sessions\C%3A%5CWINDOWS%5Csystem32"
    r"\019eb4fb-7013-70a3-a839-ce26517ca045\updates.jsonl"
)
TARGETS = {
    "apps/web/src/index.css",
    "apps/web/src/layout/AppLayout.tsx",
    "apps/web/src/pages/DashboardPage.tsx",
}


def norm_rel(path: str) -> str | None:
    marker = "TerraForge-Labs"
    idx = path.find(marker)
    if idx < 0:
        return None
    tail = path[idx + len(marker) :].lstrip("\\/")
    return tail.replace("\\", "/")


writes = 0
matched = 0
with TRANSCRIPT.open(encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        upd = obj.get("params", {}).get("update", {})
        kind = upd.get("sessionUpdate")
        if kind != "tool_call":
            continue
        raw = upd.get("rawInput", {})
        if raw.get("title") != "Write":
            continue
        writes += 1
        rel = norm_rel(raw.get("path", ""))
        if rel in TARGETS:
            matched += 1
            print(rel, len(raw.get("contents", "")))

print("writes", writes, "matched", matched)