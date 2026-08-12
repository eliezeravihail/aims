#!/usr/bin/env python3
"""aims anchor — write-time staleness-anchor stamper (lean format).

A record declares the code it concerns *once*, in a `code:` frontmatter field (a file, a directory,
or a `dir/**` glob). This tool reads that `code:` and stamps a single anchor hash:

  - `hash:`  — content anchor: sha256 over the concerned file(s)' bytes. For a record about what the
               code *says*. Chosen by default.
  - `shape:` — structure anchor: sha256 over the child-name set of the subtree (content-blind). For a
               record about *arrangement* (a component's parts). Chosen for `components/**/component.md`
               or with --shape.

The `code:` is a SINGLE cohesive target on purpose. If a record cannot name its code as one unit —
if the concern is scattered across an arbitrary subset of files — that is an architecture smell (poor
cohesion / an over-generic directory); the fix is to make the concern cohesive in the code, not to
list scattered paths here (see references/design-record.md).

Called explicitly by the method the moment it files a record — never as a hook. Stdlib only;
idempotent; touches exactly one record file, preserving every other key and the body.

Usage:
  aims_anchor.py <record>              # stamp hash: (or shape: for a component)
  aims_anchor.py <record> --shape      # force a structure anchor
  aims_anchor.py <record> --content    # force a content anchor
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

FENCE = "---"
_CODE_RE = re.compile(r'^\s*code:\s*(.+?)\s*$', re.M)


# ─────────────────────────────── hashing ────────────────────────────────

def _resolve_code(code: str, base: Path) -> tuple[Path, list[Path]]:
    """Return (root_dir, files) for a `code:` value: a file, a directory, or a `dir/**` glob.

    root_dir is the directory the target lives under (used for shape). files is every concerned
    file (one, for a file target; all files under the dir/glob otherwise), sorted.
    """
    raw = code.strip().strip('"').strip("'")
    stripped = raw.rstrip("/").removesuffix("/**").removesuffix("/*")
    p = base / stripped
    if p.is_file():
        return p.parent, [p]
    if p.is_dir():
        return p, sorted(f for f in p.rglob("*") if f.is_file())
    # a glob pattern that is not a plain dir
    matches = sorted(f for f in base.glob(raw) if f.is_file())
    return (p if p.is_dir() else p.parent), matches


def content_hash(files: list[Path], base: Path) -> str:
    """'sha256:<hex>' over the concerned files' bytes, keyed by relative path (sorted)."""
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(base).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def shape_hash(root: Path, base: Path) -> str:
    """'sha256:<hex>' over the sorted child-name set under root (names only, content-blind)."""
    names = sorted(
        e.relative_to(root).as_posix() + ("/" if e.is_dir() else "")
        for e in root.rglob("*")
        if not e.name.startswith(".") and ".capsa" not in e.parts
    )
    h = hashlib.sha256()
    h.update("\n".join(names).encode("utf-8"))
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
    if not s or s[0].isspace():
        return False
    if s.lstrip().startswith(("#", "-")):
        return False
    return ":" in s


def _drop_keys(fm: list[str], keys: set[str]) -> list[str]:
    return [l for l in fm if not (_is_top_level_key(l) and l.split(":", 1)[0] in keys)]


def _read_code(fm_text: str) -> str | None:
    m = _CODE_RE.search(fm_text)
    return m.group(1).strip() if m else None


def stamp(record: Path, base: Path, kind: str | None) -> str:
    """Read the record's `code:`, compute the anchor, write a single `hash:`/`shape:` line.

    kind: 'content' | 'shape' | None (auto: shape for a component record, else content).
    Returns a short status string. Idempotent; preserves all other frontmatter and the body.
    """
    text = record.read_text(encoding="utf-8")
    fm, rest = _split_frontmatter(text)
    fm_text = "".join(fm)
    code = _read_code(fm_text)
    if not code:
        return f"no `code:` field in {record} — nothing to anchor (pure-intent record)."

    if kind is None:
        kind = "shape" if record.name == "component.md" else "content"

    root, files = _resolve_code(code, base)
    if kind == "shape":
        if not root.is_dir():
            raise SystemExit(f"error: shape anchor needs a directory; `code: {code}` is not one.")
        field, value = "shape", shape_hash(root, base)
    else:
        if not files:
            raise SystemExit(f"error: `code: {code}` matched no files to content-anchor.")
        field, value = "hash", content_hash(files, base)

    fm = _drop_keys(fm, {"hash", "shape"})
    while fm and fm[-1].strip() == "":
        fm.pop()
    new_fm = "".join(fm) + f'{field}: "{value}"\n'
    record.write_text(FENCE + "\n" + new_fm + rest, encoding="utf-8")
    return f"anchored ({field}): {record}  <-  code: {code}  ({len(files)} file(s))"


def main(argv: list[str]) -> int:
    args = list(argv)
    kind: str | None = None
    rest: list[str] = []
    for a in args:
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
        print("usage: aims_anchor.py <record> [--shape|--content]", file=sys.stderr)
        return 2
    record = _resolve_record(rest[0])
    print(stamp(record, Path.cwd(), kind))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
