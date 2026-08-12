#!/usr/bin/env python3
"""aims staleness read hook.

Fires as a PostToolUse hook on Read. When the read touched a capsa record carrying a staleness
anchor, it recomputes that anchor against the CURRENT source and, on drift, emits an advisory note
("re-verify") as additionalContext. Advisory only: it never blocks, never edits, never
auto-invalidates. Fail-open: a missing/unreadable source or any internal error yields no block and,
where it matters, a "possibly moved — re-verify" note instead of an exception.

Reuses the hashing in ../tools/aims_anchor.py so read-time and write-time hashes always agree. See
hooks/staleness-read.md and docs/format-profile.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Share the exact hashing used at write time. Search likely layouts (dogfood repo: hooks/ + ../tools/;
# installed: both files together under .aims/; or an explicit AIMS_HOME). If none import, stay
# fail-open (no advisory) — the hook must never break a read.
_HASH_OK = True
_here = Path(__file__).resolve().parent
for _cand in (_here, _here.parent / "tools", Path(os.environ.get("AIMS_HOME", ""))):
    if _cand and (_cand / "aims_anchor.py").is_file():
        sys.path.insert(0, str(_cand))
        break
try:
    from aims_anchor import content_hash, shape_hash  # type: ignore
except Exception:  # pragma: no cover - degrade silently, never break a read
    _HASH_OK = False

FENCE = "---"
_ANCHOR_RE = re.compile(r'path:\s*"([^"]+)"\s*,\s*hash:\s*"([^"]+)"')
_SHAPE_ROOT_RE = re.compile(r'^\s*root:\s*"([^"]+)"', re.M)
_SHAPE_HASH_RE = re.compile(r'^\s*children_hash:\s*"([^"]+)"', re.M)
_SHAPE_DEPTH_RE = re.compile(r'^\s*depth:\s*(\d+)', re.M)


def _frontmatter(text: str) -> str | None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != FENCE:
        return None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == FENCE:
            return "".join(lines[1:i])
    return None


def check_record(record: Path, repo_root: Path) -> list[str]:
    """Return human-readable drift messages for one record. Empty = in-sync or nothing to check.

    Never raises: an unreadable source becomes a 'possibly moved' message; parse issues yield [].
    """
    if not _HASH_OK:
        return []
    try:
        text = record.read_text(encoding="utf-8")
    except Exception:
        return []
    fm = _frontmatter(text)
    if fm is None:
        return []

    msgs: list[str] = []

    if "anchors:" in fm:
        for path, stored in _ANCHOR_RE.findall(fm):
            f = repo_root / path
            try:
                if content_hash(f) != stored:
                    msgs.append(f"`{path}` changed since this record was written")
            except FileNotFoundError:
                msgs.append(f"`{path}` is missing (possibly moved or renamed)")
            except Exception:
                pass

    if "shape:" in fm:
        rm, hm = _SHAPE_ROOT_RE.search(fm), _SHAPE_HASH_RE.search(fm)
        dm = _SHAPE_DEPTH_RE.search(fm)
        if rm and hm:
            root, stored = rm.group(1), hm.group(1)
            depth = int(dm.group(1)) if dm else 1
            try:
                if shape_hash(repo_root / root, depth) != stored:
                    msgs.append(f"the structure under `{root}/` changed (moved/renamed/merged)")
            except NotADirectoryError:
                msgs.append(f"`{root}/` is missing (possibly moved or renamed)")
            except Exception:
                pass

    return msgs


def advisory(record: Path, msgs: list[str]) -> str:
    body = "; ".join(msgs)
    return (f"[aims] The record `{record}` may be stale: {body}. "
            f"Re-verify it against the current code before relying on it "
            f"(this flags *possible* staleness, not proven falsehood).")


def on_read(read_path: Path, repo_root: Path) -> str | None:
    """If read_path is an anchored capsa record that drifted, return an advisory; else None."""
    parts = read_path.parts
    if ".capsa" not in parts or read_path.suffix != ".md":
        return None
    msgs = check_record(read_path, repo_root)
    return advisory(read_path, msgs) if msgs else None


def main() -> int:
    """PostToolUse entry: read the hook event on stdin, emit an advisory as additionalContext."""
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
        return 0  # fail-open: never let the hook break a read
    if note:
        print(json.dumps({
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
