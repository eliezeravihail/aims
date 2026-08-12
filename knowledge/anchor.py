#!/usr/bin/env python3
"""aims anchor — write-time staleness-anchor stamper (co-located records).

Design records live IN the code tree, next to the code they describe (knowledge/format.md). The
record's LOCATION is its subject, so this tool derives the anchor target from where the record sits —
there is no `code:` field and you never name a path:

  - a `component.md`                    -> `shape:` of its own directory (the parts)
  - a decision/insight under a component -> `hash:` of that component's code
  - a root / cross-cutting record        -> no anchor (a norm does not drift)

The design records themselves (the .md files, the decisions/ and insights/ subdirs) and any nested
subcomponent are excluded, so editing knowledge never trips its own anchor and each component owns
only its own code. Called explicitly by the method when it files a record — never as a hook. Stdlib
only; idempotent; touches exactly one record file.

Usage:
  python3 knowledge/anchor.py <record>            # shape for a component.md, else content
  python3 knowledge/anchor.py <record> --shape    # force shape
  python3 knowledge/anchor.py <record> --content  # force content
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

FENCE = "---"
_DESIGN_DIRS = {"decisions", "insights"}


# ─────────────────────── locate the owning component ───────────────────────

def owning_dir(record: Path) -> Path | None:
    """The component directory a record belongs to, or None for a cross-cutting/root record."""
    if record.name == "component.md":
        return record.parent
    for anc in record.parents:
        if (anc / "component.md").is_file():
            return anc
    return None


def owned(component: Path) -> tuple[list[str], list[Path]]:
    """(names, files) that the component owns — excluding design records and nested subcomponents.

    names feed the shape fingerprint (child names, content-blind); files feed the content hash.
    A subdirectory that has its own component.md is a boundary: its name is included (it is a
    structural child) but its contents are not (it owns itself).
    """
    names: list[str] = []
    files: list[Path] = []

    def rec(d: Path) -> None:
        for e in sorted(d.iterdir(), key=lambda p: p.name):
            if e.name.startswith(".") or e.name in _DESIGN_DIRS:
                continue
            rel = e.relative_to(component).as_posix()
            if e.is_dir():
                names.append(rel + "/")
                if not (e / "component.md").is_file():
                    rec(e)                     # descend unless it's a subcomponent boundary
            elif e.name != "component.md":
                names.append(rel)
                files.append(e)

    rec(component)
    return sorted(names), files


# ─────────────────────────────── hashing ────────────────────────────────

def shape_hash(names: list[str]) -> str:
    h = hashlib.sha256()
    h.update("\n".join(names).encode("utf-8"))
    return "sha256:" + h.hexdigest()


def content_hash(files: list[Path], base: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(files):
        h.update(f.relative_to(base).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


# ────────────────────────── frontmatter surgery ──────────────────────────

def _resolve_record(record: str) -> Path:
    p = Path(record)
    if p.suffix != ".md":
        p = p.with_suffix(".md")
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
    if not s or s[0].isspace() or s.lstrip().startswith(("#", "-")):
        return False
    return ":" in s


def _drop_keys(fm: list[str], keys: set[str]) -> list[str]:
    return [l for l in fm if not (_is_top_level_key(l) and l.split(":", 1)[0] in keys)]


def stamp(record: Path, kind: str | None) -> str:
    """Derive the anchor target from the record's location and write one hash:/shape: line."""
    comp = owning_dir(record)
    if comp is None:
        return f"cross-cutting record (no owning component): {record} — no anchor."

    if kind is None:
        kind = "shape" if record.name == "component.md" else "content"
    names, files = owned(comp)

    if kind == "shape":
        field, value = "shape", shape_hash(names)
    else:
        if not files:
            return f"{comp} owns no code files to content-anchor: {record} — no anchor."
        field, value = "hash", content_hash(files, comp)

    text = record.read_text(encoding="utf-8")
    fm, rest = _split_frontmatter(text)
    fm = _drop_keys(fm, {"hash", "shape"})
    while fm and fm[-1].strip() == "":
        fm.pop()
    record.write_text(FENCE + "\n" + "".join(fm) + f'{field}: "{value}"\n' + rest, encoding="utf-8")
    return f"anchored ({field}): {record}  <-  {comp}/  ({len(files)} code file(s))"


def main(argv: list[str]) -> int:
    kind: str | None = None
    rest: list[str] = []
    for a in argv:
        if a == "--shape":
            kind = "shape"
        elif a == "--content":
            kind = "content"
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            rest.append(a)
    if not rest:
        print("usage: python3 knowledge/anchor.py <record> [--shape|--content]", file=sys.stderr)
        return 2
    print(stamp(_resolve_record(rest[0]), kind))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
