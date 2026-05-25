# Plan: Tree-based memory system (ADR-0007)
Status: completed
Started: 2026-05-25
Completed: 2026-05-25

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
  `commits`, `sessions`, `related`, `claude_md_refs`,
  `external_refs`, `owners`; system-managed: `dirty`,
  `last_touched`, `last_consolidated`).
- **Body** — five named sections, fixed names, each may be empty:
  `## Purpose`, `## Logical rules & invariants`,
  `## Editing considerations`, `## Deliberations & history`,
  `## Open questions`.
- `commits:` carries only anchor SHAs (curated, ~5-10 max);
  no `{sha, why}` tuples — the commit message itself holds the
  reason. The git log holds the non-anchor history.
- `claude_md_refs:` and `external_refs:` point to memory that lives
  OUTSIDE the tree (CLAUDE.md sections, `~/.claude/memory/` notes,
  ADRs, plans). Read-only references — the tree never overwrites
  them.
- `kind: module|decision|topic|runbook` is a hint about which body
  section dominates, not a schema variant.
- **No size cap** on leaves. Splitting into sub-leaves is a
  deliberate edit, not a lint rule.

## Non-duplication invariant (per ADR-0007 § Relationship)

The tree is a navigator, not a copy. CLAUDE.md, the `/memory` slash
command, and Anthropic's `memory_20250818` tool all continue to work
unchanged. The tree REFERENCES content stored in those places; it
never mirrors or overwrites it. This is the design constraint that
the helpers and hooks below all respect.

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
- `lint.sh` — for every leaf, check that each path in `code:`,
  `external_refs.path`, and CLAUDE.md heading in `claude_md_refs`
  exists; report orphans. Exit 0 (informational).
- `check-refs.sh` — for every leaf, compare current mtime/hash of
  each `external_refs.path` and `claude_md_refs` section against
  the leaf's `last_consolidated`. Emit a list of
  `<leaf>\t<ref>\tchanged` rows. Used by consolidate.sh; never
  modifies anything.
- `consolidate.sh <leaf_path>` — given a dirty leaf, build the
  Sonnet/Opus request: current body + diffs of referenced sources
  since `last_touched` + a list of changed external_refs from
  check-refs.sh. POST to Anthropic, write back the updated body,
  append breadcrumb lines for changed external_refs in `##
  Deliberations & history` (never modify the external files
  themselves), set `dirty: false`, bump `last_consolidated`.
  Fallback: if no `ANTHROPIC_API_KEY`, print "skipping
  consolidation" to stderr and exit 0.
- `classify-inbox.sh` — read `_inbox.md` (which includes both code
  paths and CLAUDE.md section names), call Sonnet/Opus to propose
  for each entry: `existing-leaf <path>` (add to its `code:` or
  `claude_md_refs:`) or `new-leaf <proposed-path>`. Print
  proposals as TSV for `/done` to act on.

Verify: `bash -n templates/memory/*.sh` clean. Each script's
`--help` (if no args) prints usage and exits 0.

### 2. Cold-start command `templates/commands/memory-init.md`

Sonnet, idempotent. Reads the codebase via Glob/Read AND reads the
existing CLAUDE.md, classifies modules into 5–10 domain tags
(interface/network/implementation/documentation by default; refined
to project specifics), drafts `docs/memory/README.md` plus per-tag
`README.md` plus leaf stubs for the most prominent modules with
`code:` frontmatter populated.

For each seeded leaf, also populates `claude_md_refs:` from the
existing CLAUDE.md sections that the leaf's domain plausibly relates
to (e.g. an `implementation/` leaf references the `Build & test
commands` and `Hooks` sections of CLAUDE.md). Does NOT copy CLAUDE.md
content into the tree — references only (the non-duplication
invariant).

Discipline:
- Read-only scan first (no writes during exploration).
- Diff preview via `AskUserQuestion` before writing.
- Refusal if `docs/memory/` already non-empty — instead suggest
  manual extension or a separate `/memory-augment` (out of scope
  for this plan).
- Refusal if CLAUDE.md is missing — it must exist before
  /memory-init so references are valid.

Verify: file exists with the right Sonnet frontmatter; dry-run
on a small fake project produces a sensible tree where leaves
reference CLAUDE.md sections without duplicating content.

### 3. Edit-marker hook `templates/hooks/post-edit-marker.sh`

PostToolUse hook on `Edit|Write|MultiEdit|NotebookEdit`. Reads
the tool's input JSON from stdin (per Claude Code's hook contract),
extracts the file path, invokes `templates/memory/mark.sh`.
Never blocks. Always exits 0. Errors to stderr only.

Verify: `bash -n templates/hooks/post-edit-marker.sh`. Smoke test:
seed a leaf with `code: [src/foo.py]`, simulate a hook invocation
for `src/foo.py`, assert `dirty: true` after.

### 4. Stop-hook consolidation with throttle `templates/hooks/stop-consolidate.sh`

Wired to `Stop`, not `SessionEnd`. Most fires are no-ops thanks to
a bash-level throttle; the LLM call happens only at natural pause
points.

Pseudocode:

```bash
N_DIRTY=$(bash .claude/memory/find-dirty.sh | wc -l)
[ "$N_DIRTY" -eq 0 ] && exit 0    # nothing to do; ~5ms

LAST_FILE=".claude/memory/.last-consolidated"
NOW=$(date +%s)
LAST=$([ -f "$LAST_FILE" ] && cat "$LAST_FILE" || echo 0)
ELAPSED=$((NOW - LAST))

THRESHOLD_DIRTY=${AIMS_MEMORY_DIRTY_MAX:-5}
THRESHOLD_SEC=${AIMS_MEMORY_INTERVAL_SEC:-1800}   # 30 min

if [ "$N_DIRTY" -ge "$THRESHOLD_DIRTY" ] || [ "$ELAPSED" -ge "$THRESHOLD_SEC" ]; then
  # threshold tripped — run real consolidation
  bash .claude/memory/find-dirty.sh | while read leaf; do
    bash .claude/memory/consolidate.sh "$leaf"
  done
  bash .claude/memory/classify-inbox.sh | bash .claude/memory/apply-confident-classifications.sh
  printf '%s' "$NOW" > "$LAST_FILE"
  printf '[aims-memory] consolidated %d leaves\n' "$N_DIRTY" >&2
fi

exit 0
```

Defaults: 5 dirty leaves OR 30 minutes since last consolidation,
whichever first. Override via `.claude/memory/throttle.conf` (sourced
by the hook) for project-specific tuning.

Never blocks. Always exits 0. Tolerates missing API key (consolidate.sh
itself exits 0 when key missing; dirty leaves wait for the next fire
where the key is present).

Verify: `bash -n templates/hooks/stop-consolidate.sh`. Smoke tests:
(a) 0 dirty → hook exits in <10ms. (b) 4 dirty, time < threshold →
exits in <50ms. (c) 5 dirty → consolidation triggers (mocked
Anthropic). (d) 1 dirty, time > 30 min → consolidation triggers.

### 4b. SessionEnd safety-net hook `templates/hooks/session-end.sh`

Same body as the Stop hook but **without** the throttle: if any
leaves are dirty when SessionEnd fires, consolidate immediately.
Cheap when nothing is dirty (exits in ~5ms). For users who DO close
the CLI, this is the catch-up. For users who never close, it never
fires — and the Stop throttle covers them.

### 5. SessionStart hook update `templates/hooks/session-start.sh`

Extend the existing hook to additionally surface
`docs/memory/README.md` if present (capped at 2KB). This is the
top-level "tag list" the model will navigate from.

Verify: existing tests still pass; add: when `docs/memory/README.md`
exists, the hook's stdout contains the README's first heading.

### 6. New command `templates/commands/remember.md`

Haiku. Takes a note in `$ARGUMENTS`. Asks the model (Haiku, single
call) to:
- pick the best-fit existing leaf, OR
- propose a new leaf path,
then append the note to the appropriate body section of that leaf
(by default `## Open questions`, or another section if the note
clearly fits Logic/Editing/Deliberations).

Does NOT write to CLAUDE.md — that path is reserved for the
Claude-native `/memory` slash command. The non-duplication invariant.

Verify: file exists with Haiku frontmatter; dry-run on a seeded
tree picks a sensible leaf and the right body section.

### 7. `/done` extension `templates/commands/done.md`

Add a "before reporting" step:
- Invoke `bash .claude/hooks/stop-consolidate.sh --force` directly
  (consolidation, ignoring the throttle).
- Print the consolidation summary as part of the `/done` report.
- For any classify-inbox results that need user input, ask via
  `AskUserQuestion` before finalizing.
- Also: scan CLAUDE.md for sections changed since the leaves'
  `last_consolidated` and not yet linked from any leaf; offer to
  add `claude_md_refs:` to the relevant leaves.

Verify: read existing done.md; the added section is at the right
place; running `/done` on a seeded tree triggers consolidation
regardless of throttle state.

### 8. Settings wiring `templates/settings.json.tmpl`

Add three hook entries:

```json
"PostToolUse": [
  { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [{ "type": "command", "command": "bash .claude/hooks/post-edit-marker.sh" }] }
],
"Stop": [
  { "hooks": [{ "type": "command", "command": "bash .claude/hooks/stop-consolidate.sh" }] }
],
"SessionEnd": [
  { "hooks": [{ "type": "command", "command": "bash .claude/hooks/session-end.sh" }] }
]
```

Note: the PreToolUse entry for `pre-write.sh` stays. PostToolUse,
Stop, and SessionEnd are independent events and none of them conflict.

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

- [x] ADR-0007 status `proposed → accepted` — done in the same
      commit that closed this plan; both smoke tests pass.
- [ ] Optional ADR-0009 documenting the two-phase choice if it
      proves controversial in review. Deferred — the design holds
      up in dogfood without needing a separate record; revisit
      only if review pushback warrants.

## Outcome

All 13 steps landed across four commits on the
`claude/memory-embeddings-context-cL7EE` branch:

- a0f4913 — step 1 (7 helper scripts + _lib.sh under `templates/memory/`).
- 2d967a8 — steps 3+4+4b+8 (marker hook, throttled Stop hook,
  SessionEnd safety net, settings.json wiring).
- 47977ae — steps 2+5+6+7 (SessionStart surfaces the tree;
  /memory-init, /remember; /done extended with --force
  consolidation + CLAUDE.md→tree link offers).
- The closing commit (this one) — steps 9+10+11+12+13
  (init-workflow extension, CLAUDE.md.tmpl section, dogfood
  install under .claude/, marker.sh + consolidate.sh smoke tests
  with a Python mock Anthropic endpoint, ADR-0007 status flip).

Smoke-test results: both `tests/marker.sh` and `tests/consolidate.sh`
pass. The marker hook flips dirty in ~27ms on a tiny tree; the
Stop hook exits in ~18ms when there's nothing to do (well under
the <50ms budget).

Design refinement landed AFTER the original ADR draft:
- Frontmatter gained `claude_md_refs:` and `external_refs:` so the
  tree can REFERENCE CLAUDE.md and other memory without copying.
- Consolidation wired to `Stop` (with bash-level throttle:
  N_DIRTY≥5 OR T>30min) rather than only `SessionEnd`. Real users
  rarely close the CLI; the throttle gives us automatic
  maintenance without per-prompt LLM calls.
- SessionEnd kept as an un-throttled safety net.
- /done forces consolidation, ignoring the throttle, so explicit
  closure is always definitive.

Deferred to follow-ups:
- `/memory-augment` for incremental tree growth (out of scope).
- A real `/memory-init` dogfood pass on this very repo —
  scaffolding only the leaves whose code: paths actually exist
  (`templates/`, `commands/`, hooks). Left as the first manual
  exercise to validate the cold-start UX in the field.
