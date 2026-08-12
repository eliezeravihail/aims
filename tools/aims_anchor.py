#!/usr/bin/env python3
"""aims anchor — write-time staleness-anchor stamper.

Stamps a staleness anchor into a capsa record's YAML frontmatter. The anchor kind follows the
record's claim (docs/format-profile.md §2):

  - a record about FILE CONTENT      -> `anchors:` (one sha256 per file)
  - a record about STRUCTURE          -> `shape:`   (sha256 of a subtree's child-name set)

Called explicitly by the method the moment it files a record — never as a hook. Stdlib only;
idempotent; touches exactly one record file, preserving every other key, the body, and formatting.

Usage:
  aims_anchor.py <record> <path>...          stamp anchors: (content hashes)
  aims_anchor.py --shape [--depth N] <record> <root>

<record> is a capsa record file (path with or without .md). <path>/<root> are repo-relative to the
product root (the current working directory). Hashes are read/written symmetrically with the read
hook (hooks/staleness_read.py), so the two always agree.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

FENCE = "---"


# ─────────────────────────────── hashing ────────────────────────────────

def content_hash(file: Path) -> str:
    """'sha256:<hex>' over the file's bytes. Raises FileNotFoundError if absent."""
    h = hashlib.sha256()
    h.update(file.read_bytes())
    return "sha256:" + h.hexdigest()


def _child_names(root: Path, depth: int) -> list[str]:
    """Sorted set of child names under `root` down to `depth` levels, as posix-relative paths.

    Names only — never file contents. Hidden entries and the capsule itself are skipped so a
    capsule edit never trips a product-structure anchor.
    """
    names: set[str] = set()

    def walk(d: Path, level: int) -> None:
        if level > depth:
            return
        try:
            entries = sorted(d.iterdir(), key=lambda p: p.name)
        except (FileNotFoundError, NotADirectoryError):
            return
        for e in entries:
            if e.name.startswith(".") or e.name == ".capsa":
                continue
            names.add(e.relative_to(root).as_posix() + ("/" if e.is_dir() else ""))
            if e.is_dir():
                walk(e, level + 1)

    walk(root, 1)
    return sorted(names)


def shape_hash(root: Path, depth: int = 1) -> str:
    """'sha256:<hex>' over the sorted child-name set under `root` to `depth`. Content-blind."""
    if not root.is_dir():
        raise NotADirectoryError(f"shape root is not a directory: {root}")
    h = hashlib.sha256()
    h.update("\n".join(_child_names(root, depth)).encode("utf-8"))
    return "sha256:" + h.hexdigest()


# ────────────────────────── frontmatter surgery ──────────────────────────
# Text-surgical: we never round-trip the whole YAML (which would reorder/reformat other keys).
# We locate the `--- ... ---` frontmatter, drop any existing top-level `anchors:`/`shape:` block,
# and append the freshly-computed one. Everything else stays byte-identical.

def _resolve_record(record: str) -> Path:
    p = Path(record)
    if p.suffix != ".md":
        p = p.with_suffix(".md")
    if not p.is_file():
        raise FileNotFoundError(f"record not found: {p}")
    return p


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    """Return (frontmatter_lines, rest) where rest is the closing fence + body, unchanged.

    Requires the file to open with a `---` fence. Raises ValueError otherwise.
    """
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


def _drop_block(fm: list[str], key: str) -> list[str]:
    """Remove a top-level `key:` line and its indented/list continuation from frontmatter lines."""
    out: list[str] = []
    i = 0
    while i < len(fm):
        if _is_top_level_key(fm[i]) and fm[i].split(":", 1)[0] == key:
            i += 1
            while i < len(fm):
                if _is_top_level_key(fm[i]):
                    break
                if fm[i].strip() != "" and not (fm[i][0].isspace() or fm[i].lstrip().startswith("-")):
                    break
                i += 1
            continue
        out.append(fm[i])
        i += 1
    return out


def _other_anchor_present(fm: list[str], other: str) -> bool:
    return any(_is_top_level_key(l) and l.split(":", 1)[0] == other for l in fm)


def _render_anchors(anchors: list[tuple[str, str]]) -> str:
    lines = ["anchors:\n"]
    for path, h in sorted(anchors):
        lines.append(f'- {{path: "{path}", hash: "{h}"}}\n')
    return "".join(lines)


def _render_shape(root: str, children_hash: str, depth: int) -> str:
    return (f"shape:\n"
            f'  root: "{root}"\n'
            f'  children_hash: "{children_hash}"\n'
            f"  depth: {depth}\n")


def _write_block(record: Path, key: str, other: str, block: str) -> None:
    text = record.read_text(encoding="utf-8")
    fm, rest = _split_frontmatter(text)
    if _other_anchor_present(fm, other):
        raise SystemExit(
            f"error: {record} already carries `{other}:` — a record is content-anchored OR "
            f"structure-anchored, not both (its claim is one kind). Remove the `{other}:` block first.")
    fm = _drop_block(fm, key)
    while fm and fm[-1].strip() == "":
        fm.pop()
    new = FENCE + "\n" + "".join(fm) + block + rest
    record.write_text(new, encoding="utf-8")


def stamp_anchors(record: Path, paths: list[Path]) -> None:
    """Compute one content hash per path and write the `anchors:` block. Idempotent."""
    anchors = [(p.as_posix(), content_hash(p)) for p in paths]
    _write_block(record, "anchors", "shape", _render_anchors(anchors))


def stamp_shape(record: Path, root: Path, depth: int = 1) -> None:
    """Compute the shape fingerprint for `root` and write the `shape:` block. Idempotent."""
    _write_block(record, "shape", "anchors",
                 _render_shape(root.as_posix(), shape_hash(root, depth), depth))


# ──────────────────────────────── cli ────────────────────────────────

def main(argv: list[str]) -> int:
    args = list(argv)
    shape = False
    depth = 1
    rest: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--shape":
            shape = True
        elif a == "--depth":
            i += 1
            depth = int(args[i])
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            rest.append(a)
        i += 1

    if len(rest) < 2:
        print("usage: aims_anchor.py <record> <path>...  |  --shape [--depth N] <record> <root>",
              file=sys.stderr)
        return 2

    record = _resolve_record(rest[0])
    if shape:
        stamp_shape(record, Path(rest[1]), depth)
        print(f"anchored (shape): {record} <- {rest[1]} (depth {depth})")
    else:
        stamp_anchors(record, [Path(p) for p in rest[1:]])
        print(f"anchored (content): {record} <- {', '.join(rest[1:])}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
