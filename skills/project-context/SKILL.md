---
name: project-context
description: |
  Shared project-structure cache. Every agent loads this skill at step 0 of
  its procedure, BEFORE any wide Grep/Glob/Read. The skill owns one file —
  `.claude.md` at the project root — that summarises the target codebase so
  each isolated subagent does not rediscover the project from scratch.
  Invoke when: you are about to read files in a project you don't yet
  understand; you are the Executor at the top of /project:experts; an agent
  has emitted `advisory: "project-context-missing"` or `"project-context-stale"`.
---

# Project Context

A deterministic, human-readable map of the target codebase, cached at
`.claude.md`. Reading a 200–500-line markdown file is cheaper than each
agent crawling the filesystem with Grep and Read.

This skill defines three procedures:
1. **Read** — the normal path; load `.claude.md` and navigate to relevant sections.
2. **Bootstrap** — runs once, when `.claude.md` doesn't exist; builds it from ground-truth sources.
3. **Refresh** — runs on demand or after staleness detection; updates the file in place.

## The `.claude.md` file — canonical layout

```markdown
# Project Context
<!-- Generated: <ISO 8601 UTC>  |  Source of truth: <see list below>  |  Root: <abs path> -->

## Layout
One line per top-level directory: purpose in ≤ 12 words.

## Modules
One subsection per module (unit the code is organised into). Each subsection:
### <module id>
- **Path:** `<relative path>`
- **Language:** <python | ts | go | rust | cpp | mixed | ...>
- **Public API:** `<exported symbols / entrypoints>` — one line
- **Depends on:** `<other module ids>` — comma-separated, empty if none
- **Tests:** `<relative path to the module's tests>` or `none`
- **Notes:** invariants, non-obvious contracts, known gotchas (≤ 3 lines)

## Test layout
- **Framework:** <pytest | vitest | jest | go test | ... | none-detected>
- **Test dirs:** `<paths>`
- **Pattern:** `<glob>`

## Conventions
Only what is actually enforced in this repo, not generalities. Examples:
- Commits: Conventional Commits, scope required.
- Python: black-formatted, line length 100.
- Imports: absolute only, relative imports forbidden.

## Known invariants
System-wide truths a new contributor must not break. ≤ 10 bullets.

## Sources consulted
One line per source the Bootstrap/Refresh procedure actually read. Makes
the document auditable:
- `pyproject.toml` (Python project metadata)
- `pytest --collect-only` (test inventory)
- `package.json`, etc.
```

## Source-of-truth priority

When building or refreshing, prefer deterministic sources over inference:

| Ecosystem | Primary source                                   | Secondary                              |
|-----------|--------------------------------------------------|----------------------------------------|
| CMake     | `CMakeLists.txt` targets (or SPADE graph if available) | filesystem walk                  |
| Python    | `pyproject.toml` + `pytest --collect-only`       | AST import walk                        |
| Node/TS   | `package.json` + `tsc --listFiles`               | `madge` or regex on `import` lines     |
| Rust      | `cargo metadata --format-version 1`              | filesystem walk                        |
| Go        | `go list ./...`                                  | `go mod graph`                         |
| Mixed / none | filesystem walk + language detection          | regex on import statements             |

Record which sources were used in `Sources consulted`.

## Procedure — Read (the common case)

1. `Read .claude.md`. If the file does not exist, STOP the Read procedure and emit in your envelope:
   ```
   "advisory": "project-context-missing"
   ```
   The Executor will run Bootstrap and re-dispatch you.
2. Locate the section relevant to your task (usually a module subsection or the test layout).
3. Use the section's `Path` / `Depends on` / `Tests` fields to target your subsequent file reads — do **not** Grep the whole repo.
4. Check the `Generated:` header. If the timestamp is older than `git log -1 --format=%ct` on any file listed in the relevant section's `Path`, add to your envelope:
   ```
   "advisory": "project-context-stale", "stale_paths": ["..."]
   ```
   But continue anyway — a stale context is still better than none.

## Procedure — Bootstrap (runs when `.claude.md` is missing)

Only the Executor (or an agent the Executor dispatched specifically for this
purpose) should run Bootstrap. Workers asked to do their normal task must
NOT run Bootstrap — they emit the `project-context-missing` advisory and
stop.

1. Detect project ecosystem (look for `CMakeLists.txt`, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, …). Record in the header `Source of truth` field.
2. Extract the graph using the ecosystem's primary source (see table above). If the primary source fails, fall back to secondary.
3. Identify modules from the extracted data — prefer the ecosystem's unit (Python package, npm package, CMake target, Go package) over directories.
4. Identify the test framework and test layout from config (`pytest.ini`, `jest.config.*`, etc.). If no tests exist, write `none-detected` and list where tests should go based on ecosystem convention.
5. Write `.claude.md` using the canonical layout above. Keep it under 500 lines — if it grows larger, summarise aggressively; detail belongs in the files themselves, not in the context cache.
6. Do NOT attempt semantic summaries of code ("this function is elegant"). Record structure, paths, and declared contracts only.

## Procedure — Refresh (runs on demand or after staleness advisory)

Identical to Bootstrap except:
1. Read the existing `.claude.md` first.
2. Preserve any hand-edited content in the `Conventions` and `Known invariants` sections unless you can prove it is wrong from ground truth.
3. Re-extract all other sections from sources.
4. Update `Generated:` timestamp.

## What NOT to put in `.claude.md`

- Full file listings (that's what Grep/Glob are for).
- Code snippets or function bodies.
- Narrative commentary on code quality.
- Anything not directly useful for "where is X, and what does it depend on".

The file exists to make `Read` / `Grep` / `Glob` **targeted**, not to replace them.

## Gitignore policy

`.claude.md` is derived data — add it to `.gitignore`. Two people working in
the same repo may see slightly different files at the same commit (different
detection orders, different local tooling) and that's fine; the file is
per-checkout, not per-commit.
