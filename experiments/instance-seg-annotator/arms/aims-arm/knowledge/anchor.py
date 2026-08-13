#!/usr/bin/env python3
"""aims anchor — write-time staleness-anchor stamper (companion records).

Design knowledge is co-located with the code (knowledge/format.md):

  - **File-level** — a source file `foo.py` that has something worth recording gets a companion `foo.py.md` beside it, holding what is
    known about *that file* under the sections Insights / Decisions / Discussions. Its anchor is a
    content `hash:` of the same-named sibling source file.
  - **System-level** — cross-cutting records at the repo root (`goals.md`, `architecture.md`,
    `base-dependencies.md`, `dependencies.md`, ADRs under `decisions/`). These have no same-named source
    file, so they carry no anchor (they are intent, not tied to one file).

The rule is a single derivation: a record `X.md` anchors to a sibling file named `X` (its name with the
`.md` removed) when that file exists; otherwise it is a system record and gets no anchor. Called
explicitly by the method when it files a record — never as a hook. Stdlib only; idempotent.

Usage:  python3 knowledge/anchor.py <record.md>
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

FENCE = "---"


def target(record: Path) -> Path | None:
    """The source file a companion describes — its name with `.md` stripped — if it exists."""
    sib = record.with_suffix("")          # foo.py.md -> foo.py ; goals.md -> goals
    return sib if sib.is_file() else None


def content_hash(file: Path) -> str:
    """'sha256:<hex>' over the file's bytes."""
    return "sha256:" + hashlib.sha256(file.read_bytes()).hexdigest()


# ────────────────────────── frontmatter surgery ──────────────────────────

def _resolve_record(record: str) -> Path:
    p = Path(record)
    if p.suffix != ".md":
        p = Path(record + ".md")
    if not p.is_file():
        raise FileNotFoundError(f"record not found: {p}")
    return p


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != FENCE:
        raise ValueError("record does not start with a '---' frontmatter fence")
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == FENCE:
            return lines[1:i], "".join(lines[i:])
    raise ValueError("unterminated frontmatter (no closing '---')")


def _is_top_level_key(line: str) -> bool:
    s = line.rstrip("\n")
    return bool(s) and not s[0].isspace() and not s.lstrip().startswith(("#", "-")) and ":" in s


def stamp(record: Path) -> str:
    """Write a `hash:` of the companion's same-named source file, or report a system record."""
    t = target(record)
    if t is None:
        return f"system record (no same-named source file): {record} — no anchor."
    value = content_hash(t)
    fm, rest = _split_frontmatter(record.read_text(encoding="utf-8"))
    fm = [l for l in fm if not (_is_top_level_key(l) and l.split(":", 1)[0] == "hash")]
    while fm and fm[-1].strip() == "":
        fm.pop()
    record.write_text(FENCE + "\n" + "".join(fm) + f'hash: "{value}"\n' + rest, encoding="utf-8")
    return f"anchored: {record}  <-  {t}"


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    print(stamp(_resolve_record(argv[0])))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
