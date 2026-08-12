#!/usr/bin/env python3
"""aims staleness read hook (co-located records).

PostToolUse hook on Read. When the read touched an aims design record that carries an anchor
(`hash:` or `shape:`), it recomputes that anchor from the record's own LOCATION (its owning component)
against the current code and, on drift, emits an advisory ("re-verify") as additionalContext. Advisory
only: never blocks, never edits, never auto-invalidates. Fail-open.

Reuses the derivation and hashing in anchor.py (sibling file) so read-time and write-time always agree.
See knowledge/format.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HASH_OK = True
_here = Path(__file__).resolve().parent
for _cand in (_here, Path(os.environ.get("AIMS_HOME", ""))):
    if _cand and (_cand / "anchor.py").is_file():
        sys.path.insert(0, str(_cand))
        break
try:
    from anchor import owning_dir, owned, shape_hash, content_hash  # type: ignore
except Exception:  # pragma: no cover - degrade silently, never break a read
    _HASH_OK = False

FENCE = "---"
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


def check_record(record: Path) -> list[str]:
    """Drift messages for one record; empty = in-sync or not an anchored record. Never raises."""
    if not _HASH_OK or record.suffix != ".md":
        return []
    try:
        fm = _frontmatter(record.read_text(encoding="utf-8"))
    except Exception:
        return []
    if fm is None:
        return []
    hm, sm = _HASH_RE.search(fm), _SHAPE_RE.search(fm)
    if not (hm or sm):
        return []                       # not an anchored record — nothing to check
    try:
        comp = owning_dir(record)
        if comp is None or not comp.is_dir():
            return [f"the code for `{record.name}` is missing (possibly moved or renamed)"]
        names, files = owned(comp)
        if sm and shape_hash(names) != sm.group(1):
            return [f"the structure of `{comp.as_posix()}/` changed (a file added/removed/renamed)"]
        if hm and files and content_hash(files, comp) != hm.group(1):
            return [f"the code in `{comp.as_posix()}/` changed since this record was written"]
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
    tool_input = event.get("tool_input") or {}
    fp = tool_input.get("file_path") or tool_input.get("path")
    if not fp:
        return 0
    repo_root = Path(event.get("cwd") or ".").resolve()
    read_path = Path(fp)
    if not read_path.is_absolute():
        read_path = (repo_root / read_path).resolve()
    try:
        note = on_read(read_path)
    except Exception:
        return 0
    if note:
        print(json.dumps({
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
