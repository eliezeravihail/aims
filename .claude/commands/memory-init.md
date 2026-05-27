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

For each approved node:

- Run `bash .claude/memory/new-node.sh <node> <kind>` to scaffold it
  (this produces ADR-0008's six-section body and the
  `parents:`/`children:` frontmatter fields, both empty).
- Edit the scaffolded file to populate:
  - `code:` — the source paths discovered in step 2.
  - `parents:` — repo-relative paths to any in-project documents
    that conceptually define this node (other nodes, ADRs that
    constrain it, plans that scoped it, the parent source module).
    Heterogeneous and may be empty.
  - `children:` — repo-relative paths to memory nodes that
    conceptually depend on this one (node paths only).
  - `claude_md_refs:` — relevant CLAUDE.md heading strings (verbatim).
  - `external_refs:` — ADRs / plans / user-memory files covering
    this node's domain.
  - `## Purpose` — one paragraph from the scan.
  - `## Design rationale` — 2–4 bullets explaining why the code is
    shaped this way. Source ONLY from explicit ADRs, plan documents,
    or comments in the code; if none of these exist, leave empty.
    Each bullet may end with a repo-relative pointer.
  - `## Invariants & gotchas` — invariants stated in comments,
    CLAUDE.md sections under `claude_md_refs:`, or ADR bodies that
    reference the node's `code:` paths.
  - `## Known issues` — for each `code:` path, scan `git log --follow`
    for commits whose subject starts with `fix` / `bug:` / matches
    `revert`. One line per commit:
    `- fixed: <subject> — <short SHA>`. Skip commits older than
    ~12 months unless they introduced an invariant still cited
    today. Leave `open:` entries empty (humans add those manually).
  - `## Pointers` — populate by source:
    * ADRs: every ADR whose body mentions any `code:` path of this
      node.
    * Plans: every `docs/plans/*.md` whose body mentions any
      `code:` path.
    * Commits: the 2–5 anchor commits — first introduction, last
      significant refactor. Use short SHAs.
    * External: leave empty at cold-start (URLs accumulate during
      consolidation from session transcripts).
  - `## Open questions` — only if a comment, ADR, or plan explicitly
    leaves something open. Do not invent.

Target ~1–2 KB per node. If the scan would produce significantly
more, prefer splitting into sibling nodes over packing.

Write `docs/memory/README.md` and per-tag READMEs last (they
reference the nodes you just wrote).

### 5. Verify

- Run `bash .claude/memory/lint.sh` — must report no orphans, no
  section/order violations, no non-portable pointers.
- Print a summary: `N nodes seeded across M tags; K
  claude_md_refs linked; J external_refs linked; P parents, C children.`

## Hard rules

- **No content duplication.** Never copy text from CLAUDE.md, ADRs,
  or plans into the tree. Reference by heading / path only.
- **No invention.** If a section isn't visible from the code or
  existing docs, leave it empty. The tree learns via consolidations
  after real edits land.
- **All in-project pointers are repo-relative.** No absolute paths
  (no leading `/` or `~/`). No URLs to this repo's host that point
  back into the same repo (use `docs/adr/NNNN-...md`, not
  `https://github.com/<org>/<repo>/blob/.../docs/adr/NNNN-...md`).
  Commit SHAs and external URLs (Slack, third-party docs) are fine.
- **Diff preview is mandatory.** Do not skip the user approval step,
  even if the proposed tree feels obviously right.
- **Refuse if `docs/memory/` is non-empty** (excluding README.md /
  _inbox.md). Re-seeding clobbers history.
