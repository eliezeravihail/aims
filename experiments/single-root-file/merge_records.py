"""Convert a tree of aims records into one root file, changing no word of any record.

The single-root-file experiment compares two layouts of the *same* knowledge. The layout is the only
variable, so the conversion must be mechanical: every record's text is carried over unchanged, under a
heading naming what it is about; the record's own headings move one level down so they nest under it. Frontmatter is dropped — its title is the heading, and the anchor hash has
no meaning once a record no longer sits beside its source file.

Usage: python3 merge_records.py <project-root> <output-file>
Prints each record merged, then a check that every body line survived.
"""
import pathlib
import sys

ROOT_RECORDS = ("goals.md", "architecture.md", "base-dependencies.md", "dependencies.md")


def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[4:end], text[end + 5:]
    return "", text


def is_record(path, root):
    rel = path.relative_to(root)
    if rel.parts[0] in (".git", ".aims", "node_modules"):
        return False
    if len(rel.parts) == 1 and rel.name in ROOT_RECORDS:
        return True
    if rel.parts[0] == "decisions" and len(rel.parts) == 2:
        return True
    # a companion or folder record: X.md beside a file or a folder named X
    sibling = path.with_name(path.name[:-3])
    return sibling.exists()


def demote(body):
    """Push a record's own headings one level down, so they nest under its subject heading."""
    return "\n".join("#" + ln if ln.startswith("#") else ln for ln in body.splitlines())


def text_of(line):
    return line.lstrip("#").strip()


def subject(path, root):
    rel = path.relative_to(root)
    if len(rel.parts) == 1 and rel.name in ROOT_RECORDS:
        return f"the project — {rel.name[:-3]}"
    if rel.parts[0] == "decisions":
        return f"the project — decision {rel.name[:-3]}"
    about = str(rel)[:-3]
    return f"`{about}/`" if (root / about).is_dir() else f"`{about}`"


def main(root, out):
    root = pathlib.Path(root).resolve()
    records = sorted(p for p in root.rglob("*.md") if is_record(p, root))
    parts, bodies = [], []
    for p in records:
        _, body = split_frontmatter(p.read_text())
        parts.append(f"## {subject(p, root)}\n\n{demote(body.strip())}\n")
        bodies.append(body)
        print("merged", p.relative_to(root))
    merged = "# Design notes\n\nEverything recorded about this project that the code does not say.\n\n" + "\n".join(parts)
    pathlib.Path(out).write_text(merged)
    kept = {text_of(ln) for ln in merged.splitlines()}
    lost = [ln for b in bodies for ln in b.splitlines() if text_of(ln) and text_of(ln) not in kept]
    print(f"{len(records)} records -> {out}; body lines lost: {len(lost)}")
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
