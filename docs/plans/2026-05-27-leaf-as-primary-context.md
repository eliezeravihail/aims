# Plan: Implement ADR-0008 — leaf as primary context interface
Status: in-progress
Started: 2026-05-27

## Context

ADR-0008 refines ADR-0007's leaf body. Existing state:

- All leaves under `docs/memory/{installer,hooks,memory,discipline}` use
  the 5-section ADR-0007 schema with empty sections.
- `.claude/memory/consolidate.sh:75-115` prompt names five sections and
  produces nothing for the empty ones.
- `.claude/memory/new-node.sh:50-91` scaffolds the 5-section body.
- `.claude/memory/lint.sh` checks `code:`, `external_refs:`,
  `claude_md_refs:` existence — not section presence, not commit
  validity, not pointer relativity.
- `.claude/hooks/stop-consolidate.sh` does not pass the session
  transcript to `consolidate.sh`.

## Goal

Every existing leaf, every newly-scaffolded leaf, and every
consolidation pass produces a six-section working brief whose
in-project pointers are repo-relative and whose `Known issues > fixed`
entries map to real commits.

## Options considered

- **A — Schema migration script + prompt/lint/scaffold updates (chosen).**
  Migrate existing leaves once via a mechanical heading-rewrite, then
  update the surrounding machinery (scaffold, prompt, lint, init,
  done, stop hook) so the new schema is the working norm.
- **B — Defer migration; only update going-forward leaves.** Rejected
  — existing leaves stay broken; consolidation hits a schema mismatch.
- **C — Have the LLM migrate each existing leaf via a consolidation
  pass.** Rejected — wastes API calls on a deterministic rewrite and
  risks the LLM inventing content for the new sections.

## Decision

Option A.

## Steps

1. Update `templates/memory/new-node.sh` and the dogfood copy
   `.claude/memory/new-node.sh` to scaffold the six-section body in
   ADR-0008 order: Purpose, Design rationale, Invariants & gotchas,
   Known issues, Pointers, Open questions.

2. Run a one-off shell migration over every `docs/memory/**/*.md` with
   `node:` in frontmatter. Headings only — no body content changes:
   - `Logical rules & invariants` → `Invariants & gotchas`
   - `Editing considerations` → `Design rationale`
   - insert empty `## Known issues` between `Invariants & gotchas`
     and `Deliberations & history`
   - `Deliberations & history` → `Pointers`
   - keep `Open questions`
   After migration: `grep -c '^## ' <leaf>` must return 6.

3. Rewrite the prompt in `templates/memory/consolidate.sh` +
   `.claude/memory/consolidate.sh` to:
   - name six sections with one-line guidance each, drawn from
     ADR-0008
   - state the ~1–2 KB target and the "if it bulges, suggest
     split/ADR" guidance
   - state the repo-relative rule (no absolute paths; no host-bound
     URLs back to the same repo)
   - consume a new `$TRANSCRIPT_URLS` block (line-separated) and add
     only the URLs clearly about the leaf's code to
     `Pointers > External`

4. Modify `.claude/hooks/stop-consolidate.sh` and
   `templates/hooks/stop-consolidate.sh` to read `transcript_path`
   from the JSON payload on stdin, extract URLs via
   `grep -oE 'https?://[^[:space:]"<>)]+'`, deduplicate, and pass via
   env var `AIMS_TRANSCRIPT_URLS` to each `consolidate.sh` invocation.
   Empty/unreadable transcript → empty URL list, no abort.

5. Extend `templates/memory/lint.sh` + `.claude/memory/lint.sh` with
   three informational checks (exit 0):
   - **Sections:** the six headings exist verbatim and in order.
   - **Known-issues commits:** for each SHA in
     `Known issues > fixed`, `git cat-file -e <sha>` passes AND
     `git show --name-only <sha>` touches at least one path from the
     leaf's `code:` list. Shallow-clone failures are warnings.
   - **Pointer portability:** no line under `## Pointers` or
     `## Known issues` is absolute (`^/`, `^~/`) or matches the host
     prefix of `git remote get-url origin`.

6. Rewrite Step 4 of `templates/commands/memory-init.md` so cold-start
   seeds all six sections:
   - `git log --follow` per `code:` path → anchor commits to
     `Pointers > Commits`; commits with "fix" subjects → candidates
     for `Known issues > fixed`
   - ADRs whose body references the leaf's code paths →
     `Pointers > ADRs`
   - `Invariants & gotchas` from comments + CLAUDE.md sections in
     `claude_md_refs:`
   - leave `Design rationale` and `Open questions` empty unless
     a source explicitly grounds them
   - add a Hard rule: no absolute paths, no host-bound URLs

7. Extend the health report in `templates/commands/done.md`:
   - list leaves > 4 KB
   - list lint failures from step 5

8. Mirror every `templates/...` change to `.claude/...`. Commit per
   logical step or one consolidated commit. Push to
   `claude/stoic-goodall-ScbPt`. PR #13 carries it.

## Verification

- `bash -n templates/hooks/*.sh templates/memory/*.sh .claude/hooks/*.sh .claude/memory/*.sh` — passes.
- `bash .claude/memory/lint.sh` — no failures on migrated leaves.
- Migrated `docs/memory/installer/init-workflow.md` shows six headings
  in correct order.
- `for f in docs/memory/**/*.md; do n=$(grep -cE '^## ' "$f"); [ "$n" = 6 ] || echo "$f: $n sections"; done` — silent.
- `bash .claude/memory/new-node.sh test/scratch module` in a scratch
  dir produces a six-section leaf; cleanup after.
- A manual consolidation (with `ANTHROPIC_API_KEY`) on a touched leaf
  produces output starting with `---` and containing all six section
  headings.
- Temporarily inserting `/abs/path.md` into a leaf's `Pointers`
  triggers a lint warning; removing it restores green.

## Risks / unknowns

- `transcript_path` may be absent for short sessions — degrade
  gracefully with an empty URL list.
- The one-off migration mis-handling custom prose is caught by the
  PR diff before commit.
- Shallow clones may not contain referenced commits — treat as
  warning, not error.
- URL extraction is text-naive; the LLM filters during consolidation.

## ADRs to record after implementation

- [ ] Promote ADR-0008 from `proposed` to `accepted` in `/done` once
      verification passes. No new ADRs.
