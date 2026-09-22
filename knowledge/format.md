# The aims record format — knowledge co-located with code

Design knowledge lives **in the code tree**, so the one directory structure is both the code graph and
the knowledge tree — understanding and navigation come from the structure itself, and you never read the
whole project to find what bears on the file in front of you. There are exactly two homes.

## 1. File-level — a companion beside a source file that has earned one

**Most files never get a companion.** One appears only when there is something durable worth recording about
that file — never mechanically, never as a matter of course. When a file has earned one, it is a
**companion record with the same name plus `.md`**, sitting right next to it:

```
src/render.py
src/render.py.md      ← everything known about render.py
```

The companion holds what is known about *that one file*, under three required sections — you read the
whole companion whenever you touch the file, because it is all about that file:

```markdown
---
title: "render.py"
date: 2026-08-12
---
## Insights
- SVG was chosen over canvas because the pages are static.
## Decisions
- render must not know how the maze was generated (it takes a finished maze).
## Discussions
- Considered PNG; dropped — not crisp when zoomed.
```

- The frontmatter is just `title` + `date`; the body is the three sections. Leave a section empty
  (or omit it) until it has content.
- **Insights** — what was learned about this file (what was tried, what failed, why).
- **Decisions** — file-level choices and the rule they impose (append-only: to change one, add a new
  bullet that supersedes the old, naming it — never rewrite).
- **Discussions** — trade-offs weighed, options considered, the road not taken. An assumption the file
  rests on but which was never proven belongs here too, stated as unproven — a Decision or an Insight
  claims something is known, and an unproven premise recorded as knowledge is how a later session
  inherits a guess as a fact.

## 2. System-level — cross-cutting records at the repo root

Knowledge that is *not* about one file lives at the repo root, one record per concern:

- `goals.md` — what the product is for, use scenarios, non-goals.
- `architecture.md` — boundaries, seams, invariants, change axes — the shape of the system.
- `base-dependencies.md` — the foundational substrate (language, framework, the pervasive base).
- `dependencies.md` — the confined, replaceable dependencies and what each is for.
- `decisions/NNNN-slug.md` — system-wide **ADRs** (append-only; supersede, never rewrite).

## The anchor — one derivation, machine-stamped

A record `X.md` **anchors to a sibling file named `X`** (its own name with `.md` removed) when that file
exists; otherwise it is a system record and carries no anchor:

- `render.py.md` → `.md` stripped is `render.py`, which exists → a content `hash:` of `render.py`.
- `goals.md` / `architecture.md` → `goals` / `architecture` do not exist → **no anchor** (intent, not
  tied to one file).

Stamp it on filing with the anchor tool (its invocation is owned by
`skills/aims-guide/references/design-record.md` — `.aims/anchor.py` in an installed project) — it writes
the single `hash:` line; you never compute a hash. A read-time hook re-hashes the sibling and, on drift, advises *"re-verify"*; it
never blocks. Because the pairing is by name, renaming the source and its companion **together** keeps
them in sync with nothing to update; renaming only the source flags the orphaned companion.

## How to write — the instruction

- **First ask whether it needs recording at all.** Most files never earn a companion. If the code and its
  own documentation already carry it, do not file it.
- Knowledge **about one file** → its companion `<file>.md`, in the Insights / Decisions / Discussions
  sections. Do not put it at the root.
- Knowledge that is **cross-cutting** (a goal, the architecture, a dependency choice, a system ADR) →
  the matching root record. Do not scatter it into file companions.
- **The test when it is unclear: how many files does it bind?** Knowledge that governs **one** file is
  file-level and belongs in that companion — *even when the reason for it is system-wide* (an external
  consumer, a contract, a past incident). An external justification does not promote a decision to an ADR.
  Knowledge that binds **several** files at once is system-level → `architecture.md` or an ADR.
- Anchor every companion on filing. System records take no anchor.

## Reading — navigate, don't read everything

To understand a file, open its companion — all of it, it is small and entirely about that file. For
system context, read the root records (`goals.md`, `architecture.md`, the relevant ADR). That is the
whole point: relevant knowledge is found by **navigating to the file or the root record**, never by
reading the whole project. A companion flagged stale on read is *possibly* out of date; re-verify
against the current code before relying on it.

---

*Lineage: the record grammar (knowledge co-located with code, anchored to it) grew out of an earlier
standalone format; it is developed here now, under aims. MIT.*
