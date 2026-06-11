# ADR-0014: `code:` entries are matched as fnmatch globs
Status: accepted
Date: 2026-05-31
Supersedes: —
Superseded by: —

## Context

ADR-0012 declared every memory node carries one or more `code:` entries
naming the source it owns. The intent was glob-friendly: a node for an
adapter family should be able to say `src/loaders/*.py` and have *every*
loader edit flag it dirty. The marker pipeline did not enforce that
intent — `path_matches` in `templates/memory/_lib.sh` did literal string
equality (plus a `:line-range` prefix), so `src/loaders/json_loader.py`
edited under a `src/loaders/*.py` node fell through to `_inbox.md`.

This was a silent rot mode: tests stayed green because the unit-level
marker tests only covered exact paths and the prefix branch, and node
authors saw "matches sometimes" without realising the failure shape was
"literal-only." The fix has to ship in `_lib.sh` (one function) and the
marker pipeline must continue to skip out-of-repo and absolute-path edge
cases that have been hardened over the last few PRs.

## Decision

We will treat every `code:` entry as an **fnmatch glob**, evaluated by
bash `case`-glob. Exact strings still match (they're trivial globs), the
existing `path:line-range` prefix branch still wins for explicit ranges,
and a third clause now matches the bare path against the entry as a
glob. The absolute-path defensive retry path gets the same three clauses
so repo-rooted absolute paths behave identically.

This boundary covers `code:` entries only. CLAUDE.md refs, ADR
back-references, and inbox lines stay literal — they're human-curated
prose, not match patterns.

## Consequences

- ✅ Adapter / loader / handler families can be expressed as one node.
- ✅ Refactors that split a file (`foo.py` → `foo/a.py` + `foo/b.py`) do
  not orphan the node if `code:` is `foo/*.py`.
- ⚠️ Bash `case`-glob `*` does **not** stop at `/` — `src/*.py` matches
  `src/loaders/json_loader.py`. This is the POSIX default (no
  `FNM_PATHNAME`); we accept over-marking (false `dirty:true`) over
  under-marking (silent staleness). Authors who want depth-1 matching
  should use `src/loaders/*.py`, not `src/*.py`.
- 🔒 Rules out a future `**`-style depth-aware syntax without a second
  ADR — once `*` is greedy across `/`, switching it would silently break
  existing nodes.

## Alternatives considered

- **Keep literal matching, document `code:` as exact-only.** Rejected:
  the only realistic way to keep up is one node per file, which defeats
  the whole memory-tree-as-navigation premise.
- **Lift the matcher to Python fnmatch.** Rejected: marker hook is the
  hot path for every edit, must stay shell-only and dependency-free.
- **`**`-style recursive glob with `extglob` / `globstar`.** Rejected
  for v1: requires `shopt -s globstar` semantics that don't map cleanly
  to `case`-glob, so the matcher would need a manual recursion split.
  Open-question note in the plan tracks this for a future iteration.

## Verification

- `bash tests/marker.sh` case 10: a node with `code: src/loaders/*.py`
  must flip `dirty:true` on `src/loaders/json_loader.py` and must NOT
  leak the path into `_inbox.md`.
- Code anchor: `templates/memory/_lib.sh:path_matches` carries a
  `# shellcheck disable=SC2254` and a comment pointing at this ADR.
