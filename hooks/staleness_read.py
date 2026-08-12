#!/usr/bin/env python3
"""aims staleness read hook (lean format).

Fires as a PostToolUse hook on Read. When the read touched a capsa record carrying an anchor
(`hash:` for content, `shape:` for structure) over the code it declares in `code:`, it recomputes
that anchor against the CURRENT source and, on drift, emits an advisory ("re-verify") as
additionalContext. Advisory only: never blocks, never edits, never auto-invalidates. Fail-open.

Reuses the hashing in ../tools/aims_anchor.py so read-time and write-time hashes always agree.
See hooks/staleness-read.md and docs/format-profile.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Share the exact hashing used at write time. Search likely layouts; fail-open if none import.
_HASH_OK = True
_here = Path(__file__).resolve().parent
for _cand in (_here, _here.parent / "tools", Path(os.environ.get("AIMS_HOME", ""))):
    if _cand and (_cand / "aims_anchor.py").is_file():
        sys.path.insert(0, str(_cand))
        break
try:
    from aims_anchor import _resolve_code, content_hash, shape_hash  # type: ignore
except Exception:  # pragma: no cover - degrade silently, never break a read
    _HASH_OK = False

FENCE = "---"
_CODE_RE = re.compile(r'^\s*code:\s*(.+?)\s*$', re.M)
_HASH_RE = re.compile(r'^\s*hash:\s*"([^"]+)"', re.M)
_SHAPE_RE = re.compile(r'^\s*shape:\s*"([^"]+)"', re.M)


def _frontmatter(text: str) -> str | None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != FENCE:
        return None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == FENCE:
            return "".join(lines[1:i])
    return None


def check_record(record: Path, repo_root: Path) -> list[str]:
    """Return drift messages for one record. Empty = in-sync or nothing to check. Never raises."""
    if not _HASH_OK:
        return []
    try:
        fm = _frontmatter(record.read_text(encoding="utf-8"))
    except Exception:
        return []
    if fm is None:
        return []
    cm = _CODE_RE.search(fm)
    if not cm:
        return []
    code = cm.group(1).strip().strip('"').strip("'")
    try:
        root, files = _resolve_code(code, repo_root)
    except Exception:
        return []

    hm, sm = _HASH_RE.search(fm), _SHAPE_RE.search(fm)
    try:
        if sm:
            if not root.is_dir():
                return [f"`{code}` is missing (possibly moved or renamed)"]
            if shape_hash(root, repo_root) != sm.group(1):
                return [f"the structure under `{code}` changed (moved/renamed/merged)"]
        elif hm:
            if not files:
                return [f"`{code}` matched no files (possibly moved or renamed)"]
            if content_hash(files, repo_root) != hm.group(1):
                return [f"the code under `{code}` changed since this record was written"]
    except Exception:
        return []
    return []


def advisory(record: Path, msgs: list[str]) -> str:
    return (f"[aims] The record `{record}` may be stale: {'; '.join(msgs)}. "
            f"Re-verify it against the current code before relying on it "
            f"(this flags *possible* staleness, not proven falsehood).")


def on_read(read_path: Path, repo_root: Path) -> str | None:
    if ".capsa" not in read_path.parts or read_path.suffix != ".md":
        return None
    msgs = check_record(read_path, repo_root)
    return advisory(read_path, msgs) if msgs else None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = event.get("tool_input") or {}
    fp = tool_input.get("file_path") or tool_input.get("path")
    if not fp:
        return 0
    repo_root = Path(event.get("cwd") or ".").resolve()
    read_path = Path(fp)
    if not read_path.is_absolute():
        read_path = (repo_root / read_path).resolve()
    try:
        note = on_read(read_path, repo_root)
    except Exception:
        return 0
    if note:
        print(json.dumps({
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
