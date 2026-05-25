---
description: Cold-start scan of the codebase to seed docs/memory/ (the aims memory tree)
argument-hint: "[focus: e.g. 'interface,implementation' to scope the scan]"
model: sonnet
---

# /memory-init

You are seeding the aims **memory tree** for this project: a navigable
markdown layer that documents the codebase's invariants, editing
considerations, and history. The design is in `docs/adr/0007-tree-based-memory-with-auto-maintenance.md`.

This command runs **once** per project. If `docs/memory/` already
contains any non-README files, refuse and tell the user to extend the
tree manually (a future `/memory-augment` will handle incremental
growth).

Argument: **$ARGUMENTS** (optional; comma-separated tag focus —
e.g. "interface,network" restricts the seed to those tags).

## Discipline

**Phase 1 is read-only.** Do not write any file in Phase 1.
The planning lock convention does not apply here, but the spirit
does: scan first, propose second, write only after approval.

## Steps

### 1. Sanity checks

- Verify `docs/adr/0007-tree-based-memory-with-auto-maintenance.md`
  exists. If not, abort: the design isn't in place.
- Verify `CLAUDE.md` exists at the repo root. If not, abort with a
  message: `/memory-init` requires CLAUDE.md so it can populate
  `claude_md_refs:` without copying content.
- Verify `docs/memory/` either does not exist OR contains only
  `README.md` / `_inbox.md`. If any leaf is present, abort.

### 2. Scan the codebase (read-only)

Use `Glob` + `Read`. Goals:

- Identify the top-level tags (5–10 max). The conservative defaults are
  `interface/`, `network/`, `implementation/`, `documentation/`. Refine
  based on what you see (e.g. a Python web app might split into
  `views/`, `models/`, `tasks/`, `infra/`).
- For each tag, identify 2–8 prominent modules worth a leaf each.
  "Prominent" = referenced from many places, or visibly central to a
  user-facing feature, or carrying invariants that aren't obvious from
  the code alone.
- Read `CLAUDE.md`. Note each heading. These become candidate values
  for `claude_md_refs:` on the seeded leaves.

### 3. Propose the tree

Produce a diff preview (use `AskUserQuestion`) showing:

- The proposed `docs/memory/README.md` (one-paragraph map + tag list).
- One proposed per-tag `README.md` (one paragraph naming the leaves).
- The proposed leaf list (just paths + `kind:` + one-line summary —
  not full bodies yet).
- For each proposed leaf: which `code:` paths it covers AND which
  CLAUDE.md headings it should reference via `claude_md_refs:`.

Let the user approve, modify, or scope down (e.g. "only seed the
interface/ tag for now"). Iterate until they approve.

### 4. Write the approved tree

For each approved leaf:

- Run `bash .claude/memory/new-leaf.sh <node> <kind>` to scaffold it.
- Edit the scaffolded file to populate:
  - `code:` — the source paths discovered in step 2.
  - `claude_md_refs:` — the relevant CLAUDE.md heading strings
    (verbatim — do NOT alter or copy the heading content).
  - `external_refs:` — point to any ADRs / plans / user-memory files
    that already cover this leaf's domain.
  - `## Purpose` — one paragraph, drawn from the read scan.
  - The other four body sections may stay empty; the model will fill
    them on subsequent consolidations as edits arrive.

Write `docs/memory/README.md` and per-tag READMEs last (they
reference the leaves you just wrote).

### 5. Verify

- Run `bash .claude/memory/lint.sh` — must report no orphans.
- Print a summary: `N leaves seeded across M tags; K
  claude_md_refs linked; J external_refs linked.`

## Hard rules

- **No content duplication.** Never copy text from CLAUDE.md, ADRs,
  or plans into the tree. Reference by heading / path only.
- **No invention.** If a leaf's `## Logical rules` isn't visible from
  the code or existing docs, leave the section empty. The tree learns
  via consolidations after real edits land.
- **Diff preview is mandatory.** Do not skip the user approval step,
  even if the proposed tree feels obviously right.
- **Refuse if `docs/memory/` is non-empty** (excluding README.md /
  _inbox.md). Re-seeding clobbers history.
