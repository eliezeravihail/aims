#!/usr/bin/env python3
"""aims staleness read hook (companion records).

PostToolUse hook on Read. When the read touched a companion record carrying a `hash:` anchor, it
recomputes the content hash of the same-named source file (the record's name with `.md` removed) and,
on drift, emits an advisory ("re-verify") as additionalContext. Advisory only: never blocks, never
edits. Fail-open. Reuses anchor.py (sibling file) so read-time and write-time hashes always agree.
See knowledge/format.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_OK = True
_here = Path(__file__).resolve().parent
for _cand in (_here, Path(os.environ.get("AIMS_HOME", ""))):
    if _cand and (_cand / "anchor.py").is_file():
        sys.path.insert(0, str(_cand))
        break
try:
    from anchor import target, content_hash  # type: ignore
except Exception:  # pragma: no cover
    _OK = False

FENCE = "---"
_HASH_RE = re.compile(r'^\s*hash:\s*"([^"]+)"', re.M)


def _frontmatter(text: str) -> str | None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != FENCE:
        return None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == FENCE:
            return "".join(lines[1:i])
    return None


def check_record(record: Path) -> list[str]:
    """Drift messages for one companion; empty = in-sync or not an anchored record. Never raises."""
    if not _OK or record.suffix != ".md":
        return []
    try:
        fm = _frontmatter(record.read_text(encoding="utf-8"))
    except Exception:
        return []
    if fm is None:
        return []
    m = _HASH_RE.search(fm)
    if not m:
        return []                       # not an anchored companion
    try:
        t = target(record)
        if t is None:
            return [f"`{record.with_suffix('').name}` is missing (possibly moved or renamed)"]
        if content_hash(t) != m.group(1):
            return [f"`{t.name}` changed since this record was written"]
    except Exception:
        return []
    return []


def advisory(record: Path, msgs: list[str]) -> str:
    return (f"[aims] The record `{record}` may be stale: {'; '.join(msgs)}. "
            f"Re-verify it against the current code before relying on it "
            f"(this flags *possible* staleness, not proven falsehood).")


def on_read(read_path: Path) -> str | None:
    msgs = check_record(read_path)
    return advisory(read_path, msgs) if msgs else None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    ti = event.get("tool_input") or {}
    fp = ti.get("file_path") or ti.get("path")
    if not fp:
        return 0
    root = Path(event.get("cwd") or ".").resolve()
    rp = Path(fp)
    if not rp.is_absolute():
        rp = (root / rp).resolve()
    try:
        note = on_read(rp)
    except Exception:
        return 0
    if note:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
