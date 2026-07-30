#!/usr/bin/env python3
"""Capsa capsule validator — read-only, stdlib-only, optional.

Usage:  python3 validator/validate.py path/to/capsule

Checks conformance rules SPEC.md §5 (manifest, per-type frontmatter,
naming/numbering, verification-evidence rules). It only reads; it never
writes or "fixes". Exit 0 = conforming, 1 = findings, 2 = not a capsule.

The spec is the source of truth; this checker mirrors schema/ for the
subset of YAML that capsule frontmatter actually uses (flat scalar keys,
inline lists, one-level nested blocks like `verification:`). PyYAML is
used when available; otherwise a built-in mini-parser covers that subset.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# frontmatter parsing
# --------------------------------------------------------------------------

def parse_scalar(s: str):
    s = s.strip()
    if s in ("null", "~", ""):
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [parse_scalar(x) for x in _split_inline(inner)]
    return s


def _split_inline(inner: str) -> list[str]:
    parts, depth, cur, quote = [], 0, "", None
    for ch in inner:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            cur += ch
        elif ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def mini_yaml(text: str) -> dict:
    """Parse the flat-plus-one-nested-block YAML subset used by capsules."""
    out: dict = {}
    stack: list[tuple[int, dict]] = [(0, out)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()
        target = stack[-1][1]
        if line.startswith("- "):
            # block list item — attach to the most recent list key
            key = target.get("__lastkey__")
            if key is not None and isinstance(target.get(key), list):
                target[key].append(parse_scalar(line[2:]))
            continue
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.split(" #")[0] if not rest.strip().startswith(('"', "'")) else rest
        if rest.strip() == "":
            child: dict = {}
            target[key] = child
            target["__lastkey__"] = key
            stack.append((indent + 2, child))
            # could also be a block list; convert lazily on first "- "
            target[key] = child
        else:
            target[key] = parse_scalar(rest)
            target["__lastkey__"] = key
    def scrub(d):
        if isinstance(d, dict):
            d.pop("__lastkey__", None)
            for v in d.values():
                scrub(v)
    scrub(out)
    return out


try:  # pragma: no cover - environment dependent
    import yaml  # type: ignore

    def load_yaml(text: str) -> dict:
        return yaml.safe_load(text) or {}
except Exception:  # PyYAML absent — use the subset parser
    load_yaml = mini_yaml


FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)


def frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return None
    try:
        data = load_yaml(m.group(1))
    except Exception as exc:
        return f"YAML error: {exc}"
    return data if isinstance(data, dict) else {}


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
findings: list[str] = []


def err(path, msg):
    findings.append(f"{path}: {msg}")


def is_date(v) -> bool:
    return isinstance(v, str) and bool(DATE.match(v)) or hasattr(v, "isoformat")


def need(fm, path, field, kinds=None, enum=None):
    if field not in fm or fm[field] is None:
        err(path, f"missing required field `{field}`")
        return None
    v = fm[field]
    if kinds and not isinstance(v, kinds):
        err(path, f"`{field}` has wrong type ({type(v).__name__})")
    if enum and v not in enum:
        err(path, f"`{field}`={v!r} not in {sorted(enum)}")
    return v


def check_verification(fm, path, required):
    v = fm.get("verification")
    if v is None:
        if required:
            err(path, "missing required `verification` block")
        return
    if not isinstance(v, dict):
        err(path, "`verification` must be a mapping")
        return
    status = need(v, path, "status", str, {"verified", "unverified", "failed"})
    if status == "verified" and not v.get("evidence_ref"):
        err(path, "verification.status=verified without evidence_ref (SPEC §2.3)")


NUMBERED = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9-]*\.md$")
# Releases name their slug after the version (SPEC §2.2), so dots are legal.
NUMBERED_RELEASE = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9.-]*\.md$")


def numbered(dirpath: Path, pattern=NUMBERED):
    seen = {}
    for f in sorted(dirpath.glob("*.md")):
        m = pattern.match(f.name)
        if not m:
            err(f, "filename must be NNNN-slug.md (SPEC §2.2)")
            continue
        fm = frontmatter(f)
        if fm is None or isinstance(fm, str):
            err(f, fm or "missing frontmatter (--- fences)")
            continue
        nnnn = int(m.group(1))
        if fm.get("id") != nnnn:
            err(f, f"frontmatter id={fm.get('id')} != filename number {nnnn}")
        if nnnn in seen:
            err(f, f"duplicate number {nnnn} (also {seen[nnnn].name})")
        seen[nnnn] = f
        yield f, fm


def validate(root: Path) -> int:
    man_path = root / "capsule.yaml"
    if not man_path.exists():
        print(f"not a capsule: {man_path} missing")
        return 2
    man = frontmatter_free_yaml(man_path)
    if isinstance(man, str):
        err(man_path, man)
        man = {}
    ver = need(man, man_path, "capsa_version", str)
    if ver and not re.fullmatch(r"\d+\.\d+\.\d+", ver):
        err(man_path, f"capsa_version {ver!r} is not MAJOR.MINOR.PATCH")
    proj = man.get("project")
    if not isinstance(proj, dict):
        err(man_path, "missing `project` mapping")
    else:
        need(proj, man_path, "name", str)
        slug = need(proj, man_path, "slug", str)
        if slug and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            err(man_path, f"slug {slug!r} is not kebab-case")
    need(man, man_path, "status", str,
         {"planning", "active", "maintained", "paused", "archived"})

    for f, fm in numbered(root / "requirements") if (root / "requirements").is_dir() else []:
        need(fm, f, "title", str)
        need(fm, f, "level", str, {"must", "should", "may"})
        status = need(fm, f, "status", str,
                      {"proposed", "accepted", "met", "unmet", "dropped"})
        if not is_date(fm.get("opened")):
            err(f, "`opened` must be a date")
        check_verification(fm, f, required=True)
        v = fm.get("verification") or {}
        if status == "met" and (not isinstance(v, dict) or v.get("status") != "verified"):
            err(f, "status=met but verification.status != verified (SPEC §4.1)")

    for f, fm in numbered(root / "plans") if (root / "plans").is_dir() else []:
        need(fm, f, "title", str)
        need(fm, f, "kind", str, {"charter", "initiative", "maintenance"})
        need(fm, f, "status", str, {"draft", "in_progress", "completed", "abandoned"})
        if not is_date(fm.get("opened")):
            err(f, "`opened` must be a date")
        if fm.get("priority") not in (None, "P1", "P2", "P3"):
            err(f, f"priority {fm.get('priority')!r} invalid")

    for f, fm in numbered(root / "decisions") if (root / "decisions").is_dir() else []:
        need(fm, f, "title", str)
        need(fm, f, "status", str, {"proposed", "accepted", "superseded", "deprecated"})
        if not is_date(fm.get("date")):
            err(f, "`date` must be a date")

    for f, fm in numbered(root / "discussions") if (root / "discussions").is_dir() else []:
        need(fm, f, "title", str)
        need(fm, f, "status", str, {"open", "resolved", "archived"})
        if not is_date(fm.get("opened")):
            err(f, "`opened` must be a date")

    for f, fm in numbered(root / "issues") if (root / "issues").is_dir() else []:
        need(fm, f, "title", str)
        kind = need(fm, f, "kind", str, {"bug", "risk", "task"})
        status = need(fm, f, "status", str,
                      {"new", "triaged", "in_progress", "awaiting_verification",
                       "closed", "rejected"})
        need(fm, f, "source", str, {"ceo", "system", "agent"})
        if fm.get("severity") not in (None, "S1", "S2", "S3", "S4"):
            err(f, f"severity {fm.get('severity')!r} invalid")
        if not is_date(fm.get("opened")):
            err(f, "`opened` must be a date")
        if status == "closed" and kind == "bug":
            if not fm.get("fix_commit"):
                err(f, "closed bug without fix_commit (SPEC §4.5)")
            if not fm.get("regression_ref"):
                err(f, "closed bug without regression_ref (SPEC §4.5)")
        check_verification(fm, f, required=False)

    dep_dir = root / "dependencies"
    if dep_dir.is_dir():
        for f in sorted(dep_dir.glob("*.md")):
            fm = frontmatter(f)
            if fm is None or isinstance(fm, str):
                err(f, fm or "missing frontmatter")
                continue
            name = need(fm, f, "name", str)
            need(fm, f, "version", str)
            eco = need(fm, f, "ecosystem", str, {"pypi", "npm", "vendored-js", "other"})
            tier = need(fm, f, "tier", str, {"allow", "review", "deny", "unknown"})
            need(fm, f, "direct", bool)
            if eco and name and f.name != f"{eco}-{name}.md":
                err(f, f"filename should be {eco}-{name}.md (SPEC §2.2)")
            if tier == "deny" and fm.get("decision_ref") is None:
                err(f, "deny-tier dependency without admitting decision_ref (SPEC §4.6)")

    for f, fm in numbered(root / "releases", NUMBERED_RELEASE) if (root / "releases").is_dir() else []:
        need(fm, f, "version", str)
        commit = need(fm, f, "commit", str)
        if commit and len(str(commit)) < 7:
            err(f, "`commit` must be a sha (>=7 chars)")
        if not is_date(fm.get("date")):
            err(f, "`date` must be a date")

    ins = root / "insights"
    if ins.is_dir():
        for sub in ("dev", "design", "code"):
            for f in sorted((ins / sub).glob("*.md")) if (ins / sub).is_dir() else []:
                fm = frontmatter(f)
                if fm is None or isinstance(fm, str):
                    err(f, fm or "missing frontmatter")
                    continue
                kind = need(fm, f, "kind", str, {"dev", "design", "code"})
                need(fm, f, "title", str)
                if not is_date(fm.get("created")):
                    err(f, "`created` must be a date")
                if kind and kind != sub:
                    err(f, f"kind={kind} but file is under insights/{sub}/ (SPEC §4.9)")
                if kind == "code" and not fm.get("code_globs"):
                    err(f, "kind=code requires non-empty code_globs (SPEC §4.9)")

    if findings:
        print(f"NON-CONFORMING — {len(findings)} finding(s):")
        for line in findings:
            print("  -", line)
        return 1
    print("conforming capsule ✔")
    return 0


def frontmatter_free_yaml(path: Path):
    """capsule.yaml is bare YAML (no --- fences)."""
    try:
        data = load_yaml(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"YAML error: {exc}"
    return data if isinstance(data, dict) else {}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(validate(Path(sys.argv[1])))
