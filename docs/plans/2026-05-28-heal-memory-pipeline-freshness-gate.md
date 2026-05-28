# Plan: Heal the memory pipeline in /install-on + freshness gate
Status: completed
Started: 2026-05-28
Completed: 2026-05-28

## TL;DR
The memory tree is inert in practice: `new-node.sh` hardcodes `code: []`, so
cold-start (Phase 5A) creates nodes with no globs → `post-edit-marker` can
never flag them dirty → consolidation never runs → bodies stay empty forever
(exactly what metavi shows). Fix: (A) `new-node.sh` accepts code globs and
Phase 5A *must* fill them for every module node; (B) Phase 5B backfills
`code:` into existing `code: []` module nodes so a re-install heals an old
tree; (C) `lint.sh`/`doctor.sh` flag inert module nodes. Plus a **freshness
gate**: install always cold-starts a missing tree, but for an existing tree it
only audits/augments if the newest node `last_consolidated` is older than 7
days — within a week, skip all tree work and just refresh system files. Edits
land in all 3 `install-on.md` copies and the `templates/`+`.claude/` copies of
the 3 scripts (byte-identical). One ADR (extends ADR-0007).

## Changes

### templates/memory/new-node.sh  (and identical .claude/memory/new-node.sh)
Accept optional trailing `code:` globs; render them as a YAML block list
instead of the hardcoded `code: []`.

Header/usage:
```bash
# Usage:  new-node.sh <node-path> <kind> [code-glob ...]
#   <node-path>  e.g. interface/auth/oauth-callback (NO .md suffix)
#   <kind>       module | decision | topic | runbook
#   [code-glob]  zero or more repo-relative paths/globs for `code:`.
#                A `module` node should ALWAYS get >=1 — without it the
#                post-edit-marker can never flag the node dirty.
```
Arg parse (after the `kind` case-validation):
```bash
shift 2 2>/dev/null || shift "$#"   # remaining args = code: globs
code_globs=("$@")
```
Build the frontmatter fragment (replaces the literal `code: []` heredoc line):
```bash
if [ "${#code_globs[@]}" -eq 0 ]; then
  CODE_FM="code: []"
else
  CODE_FM=$(printf 'code:\n'; printf '  - %s\n' "${code_globs[@]}")
fi
```
Heredoc line `code: []` → `$CODE_FM`. (`fm_list` already parses block form.)

### templates/commands/install-on.md  (+ commands/ + .claude/ copies — byte-identical)
Rewrite Phase 5 intro to add the freshness gate; amend 5A (fill globs at
creation) and 5B (backfill inert nodes first). Phase 6 doctor block gains an
`inert nodes (code: [])` line and a `fresh … skipped` memory-tree variant.
Freshness probe uses frontmatter `last_consolidated` (NOT file mtime — a fresh
clone resets mtimes), GNU+BSD `date` forms both given.

### templates/memory/lint.sh  (+ .claude copy)
Per-leaf, after the `code:`-path existence check:
```bash
  if [ "$(fm_get "$leaf" kind)" = "module" ] && [ -z "$(fm_list "$leaf" code)" ]; then
    printf '%s: inert node — code: [] (module not tracked by post-edit-marker)\n' "$leaf"
    issues=$((issues + 1))
  fi
```

### templates/memory/doctor.sh  (+ .claude copy)
Count inert module nodes (empty `code:`); add `inert nodes (code: []): N` to
the multi-line report and `, N inert` to `--brief` when >0.

### docs/adr/0012-*.md  (new, status proposed)
Records: code globs mandatory for module nodes (cold-start fills, re-install
backfills); install gates tree work on a 7-day freshness window. Extends
ADR-0007.

## Verification
- `bash -n templates/memory/*.sh && bash -n .claude/memory/*.sh` → clean.
- `md5sum` pairs identical: `new-node.sh`, `lint.sh`, `doctor.sh`; all 3 `install-on.md`.
- Smoke: `new-node.sh tmp/x module framework/foo.py` → block `code:` with that
  glob; `new-node.sh tmp/y topic` → `code: []`.
- `bash .claude/memory/lint.sh` → still clean; `doctor.sh` → `inert nodes (code: []): 0`.

## Close-out checklist
- ADR: WRITE — 0012-memory-code-globs-mandatory-and-freshness-gate
- Nodes: UPDATE — docs/memory/memory/helpers.md, docs/memory/installer/install-on.md
- CLAUDE.md: NONE — mechanics only, no new convention surface
- Tests: N/A — no test harness; bash -n + md5sum + manual smoke per Verification
- TODO: NONE

## Risks / unknowns
- `date -d`/`-v` portability (GNU vs BSD) — both forms given; runs in-band.
- Backfill globs are inferred — mitigated by frontmatter-only edits (body
  untouched) and lint catching leftover `code: []`.

## Outcome
All four changes shipped. `new-node.sh` accepts trailing `code:` globs →
block list (verified: module form emits the list, topic form emits
`code: []`). `install-on.md` Phase 5 rewritten in all 3 byte-identical copies:
freshness gate (skip tree work if newest `last_consolidated` < 7d), cold-start
must fill globs, augment backfills inert module nodes; Phase 6 doctor gains an
`inert nodes` line. `lint.sh` flags `module` nodes with `code: []`;
`doctor.sh` reports an `inert (code: [])` count (+ `--brief` suffix). Linting
surfaced two genuinely-misclassified breadcrumb nodes (`discipline/done`,
`discipline/grunt` — retired commands, no code) → reclassified `module`→`topic`
(the correct data fix, not a lint weakening). Recorded as ADR-0012 (extends
ADR-0007). Consolidated memory/helpers + installer/install-on nodes.

## Closing checks
- `bash -n` on all template+`.claude` scripts and hooks → clean.
- `md5sum`: 3 install-on.md identical; new-node/lint/doctor template↔.claude identical.
- `lint.sh` → clean (14 nodes); `doctor.sh` → inert (code: []): 0, dirty: 0.
- Smoke: `new-node.sh x module a.py b.py` → block `code:`; `new-node.sh y topic` → `code: []`.
- Resolved checklist:
  - ADR: WROTE — 0012-memory-code-globs-mandatory-and-freshness-gate
  - Nodes: UPDATE — memory/helpers, installer/install-on (+ discipline/plan; reclassified done/grunt)
  - CLAUDE.md: NONE — mechanics only
  - Tests: N/A — no harness; bash -n + md5sum + manual smoke
  - TODO: NONE
