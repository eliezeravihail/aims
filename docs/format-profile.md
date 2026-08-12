# The aims capsule format

This is the **whole** format aims uses — a lean profile of [capsa](../vendor/capsa/). You do not need
to read the full capsa spec to write records; this page is self-contained. (The vendored spec under
`vendor/capsa/` is the underlying grammar and lineage; aims relaxes its required-field sets to the
minimal core below. An aims capsule stays a readable capsa capsule.)

## A record

Design knowledge lives in a `.capsa/` capsule at the repo root, **one record per fact**, as a Markdown
file: a small YAML frontmatter + a prose body. A record is placed in the tree at the node it governs,
so **placement is scope** — a reader loads only the records in force where it is working.

**Required frontmatter is minimal — just two lines:**

```yaml
---
title: "core owns arithmetic"
date: 2026-08-12
---
core owns all arithmetic — a single owner. We chose X over Y because Z.
```

- `title` — one line naming the fact.
- `date` — `YYYY-MM-DD`.
- The **body** carries everything else in prose: the decision and its rationale, the road not taken.
- The record's **kind is its folder** — you never restate it. `decisions/`, `requirements/`,
  `insights/{dev,design,code}/`, `components/<slug>/component.md`, `charter.md`.
- Every other capsa field (`level`, `status`, `verification`, `tags`, `links`, …) is **optional** —
  add one only when it genuinely earns its place. Default to leaving them out.

## The anchor — two fields, both machine-written

To detect drift between a record and the code it describes, a record that concerns code declares that
code **once** and carries a single anchor hash:

```yaml
code: src/core.py            # what this record concerns — a file, a dir, or a dir/** glob
hash: "sha256:3af9…"         # ← the anchor. YOU NEVER TYPE THIS — the tool stamps it.
```

- **`code:`** — you write this: a single, **cohesive** target (one file, one directory, or one
  `dir/**` glob). Omit it for a pure-intent record (a charter, a thesis decision) that concerns no
  specific code.
- **The anchor** is one of two, and **the tool writes it, never you**:
  - `hash:` — a content hash of the concerned file(s). For a record about what the code *says*.
  - `shape:` — a child-name fingerprint of a subtree (content-blind). For a record about *arrangement*
    (a `component.md`). A file changing *inside* the subtree does not trip it; a move/rename/merge does.

Stamp it by running, from the repo root:

```
python3 tools/aims_anchor.py .capsa/decisions/0001-core-owns-math
```

The tool reads `code:` from the record, computes the right anchor (content by default; `shape:` for a
`component.md`, or force with `--shape`/`--content`), and writes the single `hash:`/`shape:` line —
preserving everything else. You never compute a hash or write that line by hand.

## `code:` is a single cohesive target — and that is a design signal

`code:` names **one** unit on purpose. If you find you cannot name a record's code as a single cohesive
target — if the concern is scattered across an arbitrary *subset* of files in a directory (A, C, F but
not B, D, E) — **do not list the scattered paths.** That inability is an architecture smell: the
concern lacks a single home (shotgun surgery), or the directory is over-generic and mixes unrelated
things. The fix is in the **code** — give the concern its own module/directory so it *can* be named as
one unit — after which the anchor is again a single `code:` + one hash. The format's simplicity is
deliberate: it makes poor cohesion visible instead of absorbing it. (See
`../skills/aims-guide/references/design-record.md`.)

## Two rules that keep the capsule trustworthy

1. **`decisions/` are append-only.** To change a decision, write a new one that supersedes it; the body
   of the new record names the one it replaces. Never rewrite a decided record.
2. **Anchor on filing** — run `aims_anchor.py` the moment you file a record that has a `code:`. Never by
   hand.

## Reading — the surfacing rule

At a node, read by placement: every normative record on the walk to the capsule root (decisions,
requirements, `component.md`) plus in-scope insights — not the whole capsule. If the read-time hook
flags a record as possibly stale, re-verify it against the current code before relying on it.

## Not in the passive layer — enforcement

A content invariant ("core stays pure") is just a record with `code: core/**` and a content anchor:
when core changes, you are told to re-verify. *Automatically* deciding whether a change broke the rule
needs code analysis — an opt-in fitness-function (a linter) emitting capsa `X-` findings, never part of
this passive format.
