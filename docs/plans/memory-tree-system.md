# Plan: Tree-based memory system (ADR-0007)
Status: in-progress
Started: 2026-05-25

## Context

ADR-0007 supersedes ADR-0006. aims adopts a navigable hierarchical
memory under `docs/memory/`, built once by an LLM at project init,
navigated by the model on demand (memory_20250818 if exposed, else
Read/Glob), and maintained automatically by a two-phase hook system:
cheap marker on every Edit/Write, batched LLM consolidation on Stop
and `/done`.

What aims already has that this plan does NOT touch:
- The four discipline commands (`/plan`, `/adr`, `/grunt`, `/done`).
- The router hook (`prompt-submit.sh`) — unchanged.
- The planning lock (`pre-write.sh`) — unchanged.
- `/init-workflow` — extended only with a memory-tree opt-in question
  and a new file-copy table row, not refactored.

What this plan adds:
- A new top-level layer (`docs/memory/`) and three new commands
  (`/memory-init`, `/remember`, and an extension to `/done`).
- One new hook (`post-edit-marker.sh`) and one extended hook
  (`session-stop.sh` for consolidation; the existing `session-start.sh`
  for the README surface).
- A small `templates/memory/` directory of bash helpers — no
  embedding, no math, just frontmatter manipulation.

## Goal

Ship a tree-based memory layer such that, in a freshly-bootstrapped
target with `ANTHROPIC_API_KEY` set:

(a) Running `/memory-init` proposes a tree under `docs/memory/` from
the codebase scan and writes it after the user approves.
(b) Source edits during a session flip `dirty: true` in any leaf whose
`code:` list references the changed path (<100ms total per edit).
(c) Edits to source files not referenced by any leaf accumulate in
`docs/memory/_inbox.md` for later classification.
(d) Session Stop AND `/done` consolidate dirty leaves and the inbox
into actual content updates via Sonnet/Opus.
(e) `/remember <note>` appends a note to the right leaf (or creates
a new leaf) via Haiku.
(f) `tests/marker.sh` and `tests/consolidate.sh` pass end-to-end with
mocked Anthropic.

## Options considered

- **A — Single-phase: LLM call on every edit.** Rejected. Per-edit
  ~1.5s latency + per-edit cost are both unacceptable for a hook
  meant to fire on every Edit/Write.
- **B — Two-phase: marker (bash) + consolidation (LLM at Stop/done).**
  Chosen. Cheap per-edit, automatic at session boundaries.
- **C — Manual maintenance only.** Rejected — user explicitly
  required automation.

## Leaf content schema (firmed-up since ADR-0007 draft)

Every leaf has the fixed shape documented in ADR-0007 § "Leaf content
schema":

- **Frontmatter** (required keys: `node`, `kind`, `code`; optional:
  `commits`, `sessions`, `related`, `owners`; system-managed:
  `dirty`, `last_touched`, `last_consolidated`).
- **Body** — five named sections, fixed names, each may be empty:
  `## Purpose`, `## Logical rules & invariants`,
  `## Editing considerations`, `## Deliberations & history`,
  `## Open questions`.
- `commits:` carries only anchor SHAs (curated, ~5-10 max);
  no `{sha, why}` tuples — the commit message itself holds the
  reason. The git log holds the non-anchor history.
- `kind: module|decision|topic|runbook` is a hint about which body
  section dominates, not a schema variant.
- **No size cap** on leaves. Splitting into sub-leaves is a
  deliberate edit, not a lint rule.

The helpers and hooks below assume this shape.

## Steps

Independently verifiable; order matters only where called out.

### 1. Helper scripts under `templates/memory/`

Pure bash; no math, no embeddings. All operate on the schema above.

- `mark.sh <changed_path>` — for each leaf under `docs/memory/`
  whose frontmatter `code:` list includes `<changed_path>` (or a
  prefix match for paths with `:line` ranges), set `dirty: true`
  and update `last_touched`. If no leaf matches, append the path
  to `docs/memory/_inbox.md`. Output: count of leaves marked.
- `new-leaf.sh <node-path> <kind>` — scaffold a new leaf with the
  required frontmatter keys and the five empty body sections.
  Idempotent: refuses if the leaf already exists.
- `find-dirty.sh` — print, one per line, the relative path of every
  leaf with `dirty: true`. Empty output if nothing dirty.
- `lint.sh` — for every leaf, check that each path in `code:`
  exists; report orphans. Exit 0 (informational).
- `consolidate.sh <leaf_path>` — given a dirty leaf, build the
  Sonnet/Opus request (current body + diffs of referenced sources
  since `last_touched`), POST to Anthropic, write back the updated
  body, set `dirty: false`. Fallback: if no `ANTHROPIC_API_KEY`,
  print "skipping consolidation" to stderr and exit 0.
- `classify-inbox.sh` — read `_inbox.md`, call Sonnet/Opus to
  propose for each entry: `existing-leaf <path>` or `new-leaf
  <proposed-path>`. Print proposals as TSV for `/done` to act on.

Verify: `bash -n templates/memory/*.sh` clean. Each script's
`--help` (if no args) prints usage and exits 0.

### 2. Cold-start command `templates/commands/memory-init.md`

Sonnet, idempotent. Reads the codebase via Glob/Read, classifies
modules into 5–10 domain tags (interface/network/implementation/
documentation by default; refined to project specifics), drafts
`docs/memory/README.md` plus per-tag `README.md` plus leaf stubs
for the most prominent modules with `code:` frontmatter populated.

Discipline:
- Read-only scan first (no writes during exploration).
- Diff preview via `AskUserQuestion` before writing.
- Refusal if `docs/memory/` already non-empty — instead suggest
  manual extension or a separate `/memory-augment` (out of scope
  for this plan).

Verify: file exists with the right Sonnet frontmatter; dry-run
on a small fake project produces a sensible tree.

### 3. Edit-marker hook `templates/hooks/post-edit-marker.sh`

PostToolUse hook on `Edit|Write|MultiEdit|NotebookEdit`. Reads
the tool's input JSON from stdin (per Claude Code's hook contract),
extracts the file path, invokes `templates/memory/mark.sh`.
Never blocks. Always exits 0. Errors to stderr only.

Verify: `bash -n templates/hooks/post-edit-marker.sh`. Smoke test:
seed a leaf with `code: [src/foo.py]`, simulate a hook invocation
for `src/foo.py`, assert `dirty: true` after.

### 4. Stop-hook consolidation `templates/hooks/session-stop.sh`

New hook (was deferred from the prior plan, now repurposed):

- Read every dirty leaf via `find-dirty.sh`.
- For each, call `consolidate.sh <leaf>`.
- Run `classify-inbox.sh` over `_inbox.md`; for clear matches,
  apply automatically; for uncertain matches, leave the inbox
  entries pending (the user will see them at next `/done`).
- Print a one-line summary to stderr:
  `[aims-memory] consolidated N leaves, classified M inbox items.`

Never blocks. Always exits 0. Tolerates missing API key (skips
LLM steps, leaves `dirty: true` intact).

Verify: `bash -n templates/hooks/session-stop.sh`. With mocked
Anthropic: seed two dirty leaves, run the hook, assert both are
clean and bodies updated.

### 5. SessionStart hook update `templates/hooks/session-start.sh`

Extend the existing hook to additionally surface
`docs/memory/README.md` if present (capped at 2KB). This is the
top-level "tag list" the model will navigate from.

Verify: existing tests still pass; add: when `docs/memory/README.md`
exists, the hook's stdout contains the README's first heading.

### 6. New command `templates/commands/remember.md`

Haiku. Takes a note in `$ARGUMENTS`. Asks the model (still Haiku,
same call) to:
- pick the best-fit existing leaf, OR
- propose a new leaf path,
then append the note to the leaf's body in a `## Notes` section
(create the section if missing).

Verify: file exists with Haiku frontmatter; dry-run on a seeded
tree picks a sensible leaf.

### 7. `/done` extension `templates/commands/done.md`

Add a "before reporting" step:
- Invoke `bash .claude/hooks/session-stop.sh` directly (consolidation).
- Print the consolidation summary as part of the `/done` report.
- For any classify-inbox results that need user input, ask via
  `AskUserQuestion` before finalizing.

Verify: read existing done.md; the added section is at the right
place; running `/done` on a seeded tree triggers consolidation.

### 8. Settings wiring `templates/settings.json.tmpl`

Add two hook entries:

```json
"PostToolUse": [
  { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [{ "type": "command", "command": "bash .claude/hooks/post-edit-marker.sh" }] }
],
"Stop": [
  { "hooks": [{ "type": "command", "command": "bash .claude/hooks/session-stop.sh" }] }
]
```

Note: the PreToolUse entry for `pre-write.sh` stays. PostToolUse is
a separate event and they do not conflict.

Verify: `jq . templates/settings.json.tmpl` parses cleanly; the
existing PreToolUse entry is unchanged.

### 9. `init-workflow.md` extension

Phase 2 gains question 7:

> **Memory tree** — install the navigable memory layer (ADR-0007)?
> enable (default; copies hooks and `/memory-init`, scaffolds
> `docs/memory/`) | skip.

Phase 4 file table gains rows for `post-edit-marker.sh`,
`session-stop.sh`, `memory-init.md`, `remember.md`, and the
`templates/memory/*.sh` helpers.

Phase 5 doctor report gains a memory line:

```
memory tree: enabled | skipped
             (if enabled: run `/memory-init` to populate)
```

`.gitignore` gains no new entries — the memory tree is fully
committed (per ADR-0008's spirit; the embeddings cache that needed
gitignoring in ADR-0006 does not exist in this design).

Verify: dry-run `/init-workflow` against a fresh test project;
inspect the result.

### 10. `templates/CLAUDE.md.tmpl` section

Add a `## Memory tree` section: what it is, how it builds
(`/memory-init`), how it maintains itself (the two-phase hook),
how to navigate (the model uses Read/Glob or memory_20250818;
the user can `cat` any leaf to read it directly).

### 11. Dogfood

Per the repo's CLAUDE.md "Plugin-specific notes":
- Copy `templates/memory/*.sh` → `.claude/memory/`
- Copy new hooks → `.claude/hooks/`
- Copy `/memory-init` and `/remember` to `.claude/commands/`
- Update `.claude/settings.json` to match
- Run `/memory-init` on this very repo to produce
  `aims/docs/memory/` from the existing source

### 12. Tests under `tests/`

Two smoke tests, both with a mocked Anthropic endpoint (Python
http.server, as we did in the abandoned recall test):

- `tests/marker.sh`: seed leaves with `code:` lists, simulate
  PostToolUse hook invocations for various paths, assert exact
  dirty/inbox state after.
- `tests/consolidate.sh`: seed dirty leaves with stale bodies,
  run `session-stop.sh` against the mock, assert bodies updated
  and `dirty: false`.

Verify: both scripts exit 0.

### 13. ADRs to record after implementation

- [ ] Update ADR-0007 status `proposed → accepted` once the
      implementation lands and tests pass.
- [ ] ADR-0009 (optional): "Memory consolidation runs at Stop,
      not per-edit" — if the trade-off needs its own record
      separate from ADR-0007's body.

## Verification

End-to-end commands:

- `bash -n templates/memory/*.sh templates/hooks/*.sh .claude/memory/
  *.sh .claude/hooks/*.sh` — all shell scripts parse.
- `bash tests/marker.sh && bash tests/consolidate.sh` — both pass.
- Manual: run `/memory-init` against this repo's source, confirm a
  sensible tree drops under `docs/memory/`. Then make a small edit
  to a `src/` file (well, this repo has no `src/`, so to a template
  file instead), confirm the relevant leaf flips dirty within 100ms.
  Then end the session, confirm consolidation runs and the leaf is
  no longer dirty.

## Risks / unknowns

- **memory_20250818 exposure in Claude Code**: unclear if/how this
  tool is exposed in the CLI. If it is not, Read/Glob is the
  effective access path. The file layout is identical; behaviour
  is the same. ADR-0007 calls this out; nothing to do here beyond
  verify during step 11.
- **LLM diff-aware updates may be brittle**: passing a diff of a
  source file to Sonnet and asking it to update prose-form notes
  is more art than science. The fallback is to leave `dirty: true`
  and let the user notice. Tune the consolidation prompt over the
  first weeks of dogfooding.
- **`code:` drift**: a leaf's source paths become stale when files
  are renamed/moved. `lint.sh` will surface this; we don't try to
  auto-rename. Manual fix on first `/done` after the rename.
- **Cold-start over-categorization**: the LLM might propose too
  many tags (one per file = useless) or too few (everything in
  `documentation/` = useless). Diff preview at step 2 lets the
  user push back. If it consistently misbehaves, tighten the
  `/memory-init` prompt with a "5–10 tags, no more" hard rule.
- **Two-phase race**: marker runs sync after every edit; if the
  user closes Claude Code mid-edit, consolidation never fires.
  Next session's Stop will pick up the dirty markers. Acceptable.

## ADRs to record after implementation

- [ ] ADR-0007 status `proposed → accepted` when implementation
      lands and both smoke tests pass.
- [ ] Optional ADR-0009 documenting the two-phase choice if it
      proves controversial in review.
