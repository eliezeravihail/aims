# The aims record format — knowledge co-located with code

Design knowledge lives **in the code tree, next to the code it describes** — never in a separate
mirror directory. The one directory structure is *both* the code graph and the knowledge tree, so
understanding and navigation come from the structure itself. Move a directory and its knowledge moves
with it; there is no parallel tree to keep in sync.

## Where a record lives — location is scope

- A **component** is a directory of code. Its record is a `component.md` **inside that directory**,
  next to the code (`src/render/component.md` beside `src/render/render.py`).
- Records scoped to a component live under it: `src/render/decisions/…`, `src/render/insights/{dev,design,code}/…`.
- **Cross-cutting** records live at the **repo root**: `charter.md`, a root `decisions/…`.

A record's **location is what it governs.** `src/render/component.md` and everything under
`src/render/` binds render; a root record binds the whole project. A reader loads what is in force by
**walking from where it works up to the root** — reading the records at each level, not the whole tree.
Local knowledge stays local (a render decision is invisible to someone working in `accounts/`);
cross-cutting knowledge sits at the root.

## A record is lean

`title` + `date` + a prose body carrying the decision and its rationale. The **kind comes from the
location** — `component.md`, a file under `decisions/`, a file under `insights/`, or `charter.md` at the
root. There is **no `code:` field**: the record's own directory *is* its subject.

```yaml
---
title: "render owns SVG output"
date: 2026-08-12
---
render turns a maze into SVG. It must not know how the maze was generated. Chose SVG over canvas
because the pages are static.
```

## The anchor — derived from location, machine-stamped

To detect drift, a record carries one anchor hash, and **the target is derived from where the record
sits** — you never name a path:

- a **`component.md`** → a `shape:` fingerprint of *its own directory* (the parts), so adding/removing/
  renaming a file in the component trips it, an ordinary edit inside does not;
- a **decision/insight under a component** → a `hash:` of that component's code, so a code change flags
  the record for re-verification;
- a **root / cross-cutting** record (`charter.md`, a project-wide norm) → **no anchor**; a standing rule
  does not drift from a file.

The design records themselves (the `.md` files, the `decisions/` and `insights/` subdirs) are **excluded**
from the hash, so editing knowledge never trips its own anchor. Stamp it by running, from the repo root:

```
python3 knowledge/anchor.py src/render/component.md
```

The tool finds the record's owning directory, computes the right anchor (shape for a `component.md`,
content otherwise), and writes the single `hash:`/`shape:` line — you never compute a hash or name a
path. A read-time hook later re-derives and, on drift, advises *"re-verify"* — it never blocks.

## A component is a directory — and that keeps concerns cohesive

Because a record lives *in* a directory, a design component **is** a directory of code. If a concern
cannot be given its own directory — if it is scattered across an arbitrary subset of files — that is an
architecture smell (shotgun surgery / an over-generic directory), and the fix is a **refactoring
objective** that gives the concern its own directory, after which it has a natural home for its record.
The one exception is a **project-wide norm** ("all types are PascalCase"): it legitimately applies
everywhere, so it is a root record with no anchor.

## `decisions/` are append-only

To change a decision, add a new one that supersedes it (name the superseded one in the body, and mark
the old one superseded); never rewrite a decided record.

## What ships, and what doesn't

The records are ordinary Markdown files committed **with the product** — they travel and are browsed
with the code. Loop run-state lives outside them in `.aims/state.md` (git-ignored). Enforcing a norm
(a linter over the code) is an opt-in fitness-function, never part of these passive records.

---

*Lineage: the record grammar (one record per fact, structure carries scope, anchored to code) grew out
of an earlier standalone format; it is developed here now, under aims. MIT.*
