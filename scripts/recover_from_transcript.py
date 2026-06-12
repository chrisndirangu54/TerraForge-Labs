"""Recover TerraForge files from session transcript Write operations only."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRANSCRIPT = Path(
    r"C:\Users\Admin\.grok\sessions\C%3A%5CWINDOWS%5Csystem32"
    r"\019eb4fb-7013-70a3-a839-ce26517ca045\updates.jsonl"
)

SKIP_PATTERNS = (
    "error TS",
    "SyntaxError",
    "Exit code:",
    "npm run build",
    "pytest",
    "vite v",
    "transforming...",
    "built in",
    "FAILED",
    "AssertionError",
    "Traceback",
    "At line:",
    "IndentationError",
)

# Never overwrite committed core files with short stub fragments.
MIN_BYTES = {
    "backend/api/main.py": 2000,
    "backend/api/tasks.py": 1500,
    "apps/web/src/main.tsx": 100,
    "apps/web/package.json": 200,
    "backend/tests/conftest.py": 200,
}


def norm_rel(path: str) -> str | None:
    marker = "TerraForge-Labs"
    idx = path.find(marker)
    if idx < 0:
        return None
    tail = path[idx + len(marker) :].lstrip("\\/")
    return tail.replace("\\", "/")


def is_corrupt(content: str) -> bool:
    if not content or len(content) < 20:
        return True
    if any(pat in content for pat in SKIP_PATTERNS):
        return True
    stripped = content.lstrip()
    if stripped.startswith("assert ") and content.count("\n") < 3:
        return True
    if stripped.startswith("@router.") or stripped.startswith("app.include_router("):
        return True
    return False


def collect_files() -> dict[str, str]:
    files: dict[str, str] = {}
    with TRANSCRIPT.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            upd = obj.get("params", {}).get("update", {})
            if upd.get("sessionUpdate") != "tool_call":
                continue
            if upd.get("title") != "Write":
                continue
            raw = upd.get("rawInput", {})
            rel = norm_rel(raw.get("path", ""))
            contents = raw.get("contents", "")
            if not rel or is_corrupt(contents):
                continue
            min_len = MIN_BYTES.get(rel, 0)
            if len(contents) < min_len:
                continue
            if len(contents) >= len(files.get(rel, "")):
                files[rel] = contents
    return files


def main() -> None:
    files = collect_files()
    print(f"Collected {len(files)} files from transcript")
    written = 0
    for rel, content in sorted(files.items()):
        dest = REPO / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        current = dest.read_text(encoding="utf-8", errors="replace") if dest.exists() else ""
        if current == content:
            continue
        dest.write_text(content, encoding="utf-8", newline="\n")
        written += 1
    print(f"Updated {written} files")


if __name__ == "__main__":
    main()