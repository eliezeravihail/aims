---
description: Incrementally grow the aims memory tree (add a tag or a single node)
argument-hint: "add tag <name> | add node <path>"
model: sonnet
---

# /memory-augment

You are extending an **existing** aims memory tree (`docs/memory/`).
For the cold-start scan use `/memory-init`. This command is the
incremental counterpart: add one tag or one node at a time.

The schema lives in
`docs/adr/0008-node-as-primary-context-interface.md`. The mechanics
(scaffolding, dirty markers, consolidation) come from
`docs/adr/0007-tree-based-memory-with-auto-maintenance.md`.

Argument: **$ARGUMENTS**.

## Argument grammar

```
/memory-augment add tag  <tag-name> [<source-subdir>]
/memory-augment add node <docs/memory/tag/slug>  [--code <code-glob>] [--kind <kind>]
```

- `<tag-name>` — top-level folder name under `docs/memory/`
  (e.g. `network`, `cli`). Must not already exist.
- `<source-subdir>` — optional; the code area this tag covers
  (e.g. `src/cli/`). Used to seed proposals. If omitted, you'll
  propose tag scope from the codebase shape.
- `<docs/memory/tag/slug>` — repo-relative target node path
  (without `.md`). The tag folder must already exist.
- `--code` — code path glob the node will reference. If omitted,
  ask the user.
- `--kind` — one of `module | decision | topic | runbook`
  (default: `module`).

## Steps

### 1. Sanity checks (read-only)

- Verify `docs/memory/` exists with a `README.md`. If not, tell
  the user to run `/memory-init` first.
- Verify `docs/adr/0008-node-as-primary-context-interface.md`
  exists. If not, abort (this command depends on the six-section
  schema).
- Parse `$ARGUMENTS`. Reject anything other than the two forms
  above with a usage message.

### 2. Mode A — `add tag <tag-name> [<source-subdir>]`

- Refuse if `docs/memory/<tag-name>/` already exists.
- Scan the source area (read-only): list 2–8 prominent modules
  worth a node each. "Prominent" = referenced from many places,
  central to a user-facing feature, or carrying invariants not
  obvious from the code.
- Present the proposal to the user via `AskUserQuestion`: tag
  description, slug list, and `code:` glob for each. The user can
  approve / edit / cut.
- On approval:
  - Create `docs/memory/<tag-name>/README.md` (short tag summary +
    one-line description of each node).
  - For each approved node, run
    `bash .claude/memory/new-node.sh <tag-name>/<slug> <kind>`.
  - Edit the root `docs/memory/README.md`: add the new tag to the
    `## Tags` list with its one-line summary.
- The scaffold leaves all six body sections empty per ADR-0008.
  Bodies fill in over time via the consolidation loop.

### 3. Mode B — `add node <docs/memory/tag/slug>`

- Refuse if the target node file already exists.
- Refuse if the parent tag folder does not exist (tell the user
  to run `add tag` first).
- If `--code` not given, ask the user for the code path glob via
  `AskUserQuestion`. Verify at least one file matches; if zero
  matches, ask whether the node should still be created (rare —
  pure topic/decision nodes).
- Run `bash .claude/memory/new-node.sh <tag>/<slug> <kind-or-module>`.
- Edit `docs/memory/<tag>/README.md`: append the new node to its
  listing with a one-line summary (ask user for wording).
- Suggest: `/remember --node <new-node-path> ...` to seed it with
  a known invariant, or wait for the next consolidation pass.

### 4. Always — lint

After any mutation, run `bash .claude/memory/lint.sh` and surface
any issue. Fix interactively (`code:` glob with zero matches, etc.)
before declaring done.

### 5. Confirm

Print a short final report:

```
memory-augment: <mode> → <what was created>
nodes added:    N
lint:           clean | <K issues>
next step:      /remember … | wait for next consolidation
```

## Hard rules

- This command **adds** structure. It does not move, rename, or
  delete existing nodes — use a plan + manual edits for those.
- Do not populate body sections from this command. Bodies are
  written by `consolidate.sh` (or explicitly by `/remember`).
- Do not duplicate `CLAUDE.md` content into the new node. Use
  `claude_md_refs:` in the frontmatter (pointers, not copies).
- All `code:` and `claude_md_refs:` values are repo-relative
  (ADR-0008 portability rule).
