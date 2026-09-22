# The aims record format — the shape of a record

Design knowledge lives **in the code tree**, so the one directory structure is both the code graph and
the knowledge tree — understanding and navigation come from the structure itself, and you never read the
whole project to find what bears on the file in front of you.

This file defines **what a record looks like** and how its anchor is derived — the contract the tools
(`anchor.py`, the staleness hook) implement.

> **Which home a given piece of knowledge belongs in, whether it belongs in a record at all, and who files
> it when, is `skills/aims-guide/references/design-record.md`.** That file owns the filing decision; this
> one owns the shape. Its **first gate** governs everything below: a record holds only what the code
> *cannot* — anything a docstring, a comment, a name, a signature or a test could carry belongs there
> instead, and the shape described here is no licence to fill a section that has nothing of that kind in it.

A record holds discussions and decisions **not evident from the code itself**, and sits next to what they
are about — a file, a folder, or the project. Anything the code can say belongs in the code's own
documentation instead. (`skills/aims-guide/references/design-record.md` owns that decision; this file owns
the shapes below.)

## 1. A file companion — `<file>.md` beside `<file>`

A companion is named for its source file plus `.md`, sitting right next to it:

```
src/render.py
src/render.py.md      ← everything known about render.py
```

Its body is three sections — you read the whole companion whenever you touch the file, because it is all
about that file:

```markdown
---
title: "render.py"
date: 2026-08-12
---
## Insights
- Canvas was tried first and dropped: its text nodes rasterise, so a zoomed page lost the labels.
## Decisions
- render never generates — it takes a finished maze. This rules out the "render(seed)" convenience
  overload that has now been asked for twice.
## Discussions
- PNG output was weighed and dropped: not crisp when zoomed. Worth revisiting only if pages go to print.
```

Notice what the example does **not** contain: that `render` takes a maze and returns SVG (the signature
says so), or that it validates its input (a guard says so). Each entry is something no reader could
recover from the code — a failed attempt, what a choice forecloses, a road not taken and its trigger.

- The frontmatter is just `title` + `date`; the body is the three sections. Leave a section empty
  (or omit it) until it has content.
- **Insights** — what was learned about this file (what was tried, what failed, why) — not a description
  of what the code does, which a reader can already see.
- **Decisions** — file-level choices, the rule they impose and **what they rule out** (append-only: to
  change one, add a new bullet that supersedes the old, naming it — never rewrite). A rule the code
  itself enforces is a docstring, not a Decision.
- **Discussions** — trade-offs weighed, options considered, the road not taken. An assumption the file
  rests on but which was never proven belongs here too, stated as unproven — a Decision or an Insight
  claims something is known, and an unproven premise recorded as knowledge is how a later session
  inherits a guess as a fact.

## 2. A directory record — `<dir>.md` beside `<dir>`

Same three sections, for knowledge true of every file in that directory and of nothing else
(`src/parsers/` → `src/parsers.md`). It carries **no anchor**: `.md` stripped names a directory, not a
file, so the derivation below files it as a system record — which is what it is.

## 3. A project record at the repo root

One record per concern, not tied to any single file:

- `goals.md` — what the product is for, use scenarios, non-goals.
- `architecture.md` — boundaries, seams, invariants, change axes — the shape of the system.
- `base-dependencies.md` — the foundational substrate (language, framework, the pervasive base).
- `dependencies.md` — the replaceable dependencies: what each is for, and what is known about it that a
  caller must respect (a defect to guard against, a constraint it imposes). Reach for it when the knowledge
  is true of *the dependency*, whether or not its use is confined to one boundary.
- `decisions/NNNN-slug.md` — system-wide **ADRs** (append-only; supersede, never rewrite). Frontmatter is
  `title` + `date`, plus an optional `supersedes:` naming the ADR this one replaces. An ADR that *corrects*
  an earlier one without replacing it carries no `supersedes:`.

## The anchor — one derivation, machine-stamped

A record `X.md` **anchors to a sibling file named `X`** (its own name with `.md` removed) when that file
exists; otherwise it is a system record and carries no anchor:

- `render.py.md` → `.md` stripped is `render.py`, which exists → a content `hash:` of `render.py`.
- `guide.md.md` → `.md` stripped is `guide.md`, which exists → a content `hash:` of `guide.md`. A shipped
  Markdown file earns a companion the same way any other file does; the double extension is the rule
  applying, not a slip.
- `goals.md` / `architecture.md` → `goals` / `architecture` do not exist → **no anchor** (intent, not
  tied to one file).

Stamp it on filing with the anchor tool (its invocation is owned by
`skills/aims-guide/references/design-record.md` — `.aims/anchor.py` in an installed project) — it writes
the single `hash:` line; you never compute a hash. A read-time hook re-hashes the sibling and, on drift,
advises *"re-verify"*; it never blocks. Because the pairing is by name, renaming the source and its
companion **together** keeps them in sync with nothing to update; renaming only the source flags the
orphaned companion. A companion flagged stale on read is *possibly* out of date; re-verify against the
current code before relying on it.

---

*Lineage: the record grammar (knowledge co-located with code, anchored to it) grew out of an earlier
standalone format; it is developed here now, under aims. MIT.*
