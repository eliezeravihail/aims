# Plan: Fix #17 — marker absolute-path leak + consolidate working-tree diff
Status: in-progress
Started: 2026-05-27

## Context

Issue #17 documents two bugs in the memory pipeline:

1. **`post-edit-marker` passes an absolute path to `mark.sh`**
   (`.claude/hooks/post-edit-marker.sh:43`). `extract_path` returns
   `tool_input.file_path` verbatim, which Claude Code emits as absolute.
   `_lib.sh:path_matches` (line 152) compares exact strings, but every
   `code:` entry is relative (per ADR-0008). Net effect: every edit falls
   through to `mark.sh`'s "unknown path" branch and leaks an absolute path
   into `_inbox.md`. ADR-0007's "automatic maintenance" is effectively
   non-functional.
   - Secondary issue: the skip-list at `post-edit-marker.sh:38-41`
     (`.claude/*`, `docs/memory/*`) uses relative globs and never matches
     the absolute path — so edits under `.claude/` also leak.
   - Existing `tests/marker.sh` only feeds *relative* paths, which is why
     the regression was not caught.

2. **`consolidate.sh` only emits committed diffs**
   (`.claude/memory/consolidate.sh:46`). The `git log --since=…` call shows
   nothing for working-tree changes, so a mid-session Stop-throttled
   consolidation receives only the node body — the context value is gone.
   `/done` runs after commits so it is unaffected, but the in-band
   consolidation flow from ADR-0009 is degraded.

## Goal

After the fix, editing `templates/hooks/foo.sh` mid-session marks the
matching memory leaf `dirty: true` and the throttled Stop consolidation
prompt includes both the committed diff *and* the working-tree diff.

## Options considered

- **A**: Fix the marker only, defer the diff issue. Rejected — user
  asked for a combined fix; both bugs together neutralize the same flow.
- **B**: Normalize in the marker; leave `path_matches` strict. Rejected —
  3 extra lines of defense-in-depth in `path_matches` prevent regression
  if a future hook forgets to normalize.
- **C (chosen)**: Normalize in the marker + relaxed `path_matches` +
  emit a separate working-tree diff section in `consolidate.sh`.

## Steps

1. `templates/hooks/post-edit-marker.sh`: after `extract_path`, resolve
   `repo_root = git rev-parse --show-toplevel` (fallback `pwd`) and
   strip the prefix from `target`. Bail out if `target` is absolute but
   outside the repo. Place this *before* the skip-list so the relative
   globs (`.claude/*`, `docs/memory/*`) start matching.
2. `templates/memory/_lib.sh`: harden `path_matches` so an absolute
   `needle` is retried after stripping the repo root. (Defense in depth;
   no recursion risk because the second call is on a relative needle.)
3. `templates/memory/consolidate.sh`: replace the single `git log` block
   with two captures — `committed` (`git log --since=… -p`) capped at 4 KB
   and `uncommitted` (`git diff HEAD --`) capped at 4 KB — labeled
   `=== committed since last_touched ===` and
   `=== uncommitted (working tree + index) ===`. Total cap unchanged
   at 8 KB.
4. `tests/marker.sh`: add cases that send absolute paths
   (`$REPO_ROOT/src/foo.py` should mark dirty;
   `$REPO_ROOT/.claude/settings.json` should be skipped, not added to
   the inbox).
5. `tests/consolidate.sh`: if reasonably possible, add a case that
   modifies a referenced file without committing and asserts the
   `=== uncommitted` section appears in the rendered prompt.
6. Mirror all three `templates/*` changes to their `.claude/*`
   counterparts (dogfood requirement from CLAUDE.md).
7. No ADR needed — these are implementation fixes; ADR-0007/0008/0009
   stand as written.

## Verification

- `bash -n templates/hooks/*.sh .claude/hooks/*.sh templates/memory/*.sh .claude/memory/*.sh`
- `bash tests/marker.sh` — all cases (including new absolute-path ones) pass.
- `bash tests/consolidate.sh` — passes (no regression).
- End-to-end smoke:
  ```
  echo "# touch" >> templates/hooks/prompt-submit.sh
  printf '{"tool_input":{"file_path":"%s/templates/hooks/prompt-submit.sh"}}' "$(pwd)" \
    | bash .claude/hooks/post-edit-marker.sh
  bash .claude/memory/find-dirty.sh   # expect hooks/prompt-submit.md
  git checkout templates/hooks/prompt-submit.sh
  ```
- `bash .claude/memory/lint.sh` — clean.

## Risks / unknowns

- `git rev-parse --show-toplevel` outside a repo → fallback to `pwd`;
  acceptable since `mark.sh` itself tolerates missing git.
- Symlinked repo paths: `--show-toplevel` returns canonical path; if
  Claude Code emits a non-canonical symlink path the prefix strip will
  miss. Rare; acceptable.
- Working-tree diff size: 4 KB cap per source keeps total ≤ 8 KB.

## ADRs to record after implementation

- [ ] None expected.
