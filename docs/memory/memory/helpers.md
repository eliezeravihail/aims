---
node: memory/helpers
kind: module
code:
  - templates/memory/_lib.sh
  - templates/memory/mark.sh
  - templates/memory/new-node.sh
  - templates/memory/find-dirty.sh
  - templates/memory/lint.sh
  - templates/memory/check-refs.sh
  - templates/memory/consolidate.sh
  - templates/memory/classify-inbox.sh
  - templates/memory/doctor.sh
  - .claude/memory/_lib.sh
  - .claude/memory/doctor.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
parents: []
children: []
related:
  - memory/phase-a-marker
  - memory/phase-b-consolidation
claude_md_refs:
  - "Plugin-specific notes (not from template)"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: the design these helpers implement }
  - { path: tests/marker.sh, kind: test, why: covers mark/find-dirty + the marker hook }
  - { path: tests/consolidate.sh, kind: test, why: covers consolidate.sh + the Stop hook against a mocked Anthropic endpoint }
  - { path: docs/adr/0014-code-globs-are-fnmatch-globs.md, kind: adr, why: path_matches now treats every code: entry as an fnmatch glob }
owners:
  - ema
dirty: true
last_touched: 2026-06-11T07:23:19Z
last_consolidated: 2026-06-01T06:52:29Z
---

## Purpose

The bash helpers that form the deterministic substrate for the memory
tree. `_lib.sh` owns the frontmatter parsing/edit primitives
(`fm_get`, `fm_set`, `fm_list`, `list_leaves`, `path_matches`,
`now_iso`). Eight thin commands sit on top: `mark`, `new-node`,
`find-dirty`, `lint`, `check-refs`, `doctor`, `consolidate`,
`classify-inbox`. All are POSIX-friendly (mawk/BSD-awk compatible).
No external network call lives in any helper.

## Design rationale

- `consolidate.sh` and `classify-inbox.sh` emit prompt text only
  (ADR-0009); the active Claude Code session executes the work.
  Keeps every helper pure-bash and credential-free.
- `mark.sh` carries two modes — `mark.sh <path>` flips dirty for
  every node that references `<path>`; `mark.sh <node> consolidated`
  flips clean. Both modes route through the same `fm_set` primitives
  for consistency.
- `doctor.sh` reports node count, dirty count, last-consolidated age,
  lint summary, >4 KB node count, and **inert count** (module nodes
  with `code: []`) — every signal a maintainer needs without any
  "missing key" caveat.
- `new-node.sh` takes optional trailing `code:` globs
  (`new-node.sh <path> <kind> [glob ...]`) and renders them as a YAML
  block list; module nodes must get ≥1 so the marker can track them
  (ADR-0012). `lint.sh` flags any `module` node left at `code: []` as
  an inert node.
- `path_matches` in `_lib.sh` accepts both relative and absolute
  needles — defense in depth against a future hook (or direct
  `mark.sh` caller) that forgets to normalize. The marker still
  normalizes first; this is the belt under the suspenders.
- `path_matches` evaluates each `code:` entry as an **fnmatch glob**
  via bash `case`-glob (ADR-0014). Exact strings still match (they're
  trivial globs); `:line-range` suffixes still take the prefix branch.
  Greedy `*` (no FNM_PATHNAME) is documented — `src/*.py` matches
  `src/loaders/json_loader.py`; over-marking is acceptable, silent
  staleness is not.

## Invariants & gotchas

- The marker MUST normalize absolute `tool_input.file_path` against
  `git rev-parse --show-toplevel` before passing to `mark.sh`;
  otherwise the skip-list (`.claude/*`, `docs/memory/*`) misses and
  every edit leaks into `_inbox.md`. `path_matches` will also catch
  the absolute form as a fallback, but the marker is the canonical
  normalization point.
- Only `mark.sh consolidated` may write
  `dirty/last_touched/last_consolidated`. Other helpers (and the
  in-band model executing consolidation prompts) MUST leave that
  frontmatter alone. `mark.sh consolidated` also `rm -f`s the
  `<leaf>.lock` sidecar (ADR-0019).
- **Multi-session mutex (ADR-0019, supersedes ADR-0018):** a sidecar
  `<leaf>.lock` next to each node is the per-leaf mutex. The Stop hook
  acquires via `set -C` (`O_EXCL`) writing the SESSION_ID inside; a
  `trap` releases on any abnormal exit. The pre-write hook refuses
  Edit/Write to any locked node held by a different fresh session.
  Stale locks (mtime > `AIMS_LOCK_TTL_SEC`, default 600s) are
  abandoned. The `consolidating_by:` frontmatter field from ADR-0018
  is gone; the `consolidating_by` mention above is historical.
- A `module` node with `code: []` is **inert**: the marker can never
  flag it dirty, so it never consolidates (ADR-0012). If a node tracks
  no code it must be `kind: topic`/`decision`, not `module`. `lint.sh`
  enforces this; the freshness probe in `/install-on` Phase 5 reads
  `last_consolidated` (never file mtime — a clone resets mtimes).
- `consolidate.sh` caps each per-source diff at 8 KB so the assembled
  Stop-hook prompt stays bounded even with many dirty nodes.
- All helpers exit 0 on a missing `docs/memory/` so the plugin is
  safe to install in projects that haven't run `/memory-init` yet.

## Known issues

- fixed: helpers used to gate work on `ANTHROPIC_API_KEY` and call
  `api.anthropic.com` via `curl`; removed in favor of prompt
  builders consumed in-band (commit 0c0852f).

## Pointers

- ADR-0007 — design these helpers implement.
- ADR-0008 — node body schema enforced by `lint.sh` and produced by
  the `consolidate.sh` prompt.
- ADR-0009 — removed the LLM/curl path from `consolidate.sh` and
  `classify-inbox.sh`.
- ADR-0012 — `new-node.sh` glob args, mandatory `code:` for module
  nodes, `lint.sh`/`doctor.sh` inert reporting.
- ADR-0014 — `code:` entries are fnmatch globs (the matcher change
  in `path_matches`).
- ADR-0018 — superseded; in-frontmatter `consolidating_by` claim.
- ADR-0019 — sidecar `<leaf>.lock` files as the per-node mutex;
  `mark.sh consolidated` removes the sidecar.
- `templates/memory/_lib.sh` — shared primitives.

## Open questions
