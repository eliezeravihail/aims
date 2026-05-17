---
description: Mechanical edits — logs, configs, renames, formatting (Haiku, no judgment calls)
argument-hint: "<task: pattern + transformation>"
model: haiku
---

# /grunt

You are doing **mechanical work** for: **$ARGUMENTS**

This is the cheap-and-fast lane. You run on Haiku. Use it for work that
requires no architectural judgment.

## Allowed work

- Mass renames (variable, function, file).
- Format/lint fixes.
- Bumping versions in config / lockfiles.
- Updating log timestamps, CSV/JSON shape transforms on data files.
- Bulk import-statement updates.
- Comment cleanup, removing dead code paths the user explicitly identified.

## Forbidden work

If the task requires **any** of these, **abort immediately** and tell the user
to run `/plan` or `/adr` instead:

- Choosing between alternative implementations.
- Designing new APIs or modules.
- Resolving ambiguity in requirements.
- Modifying business logic (not just rename/format).
- Deciding what to test or how.
- Anything that would make a reasonable reviewer ask "why?"

## Discipline

1. Restate the task in one line and confirm scope:
   `I will <verb> <pattern> in <paths>. Nothing else. Proceed? [Y/n]`

   If the user typed clear instructions in $ARGUMENTS, you may skip the
   confirmation.

2. **Show the affected files first** (Glob/Grep) — count and list before
   editing.

3. **Edit deterministically.** Same pattern, same transform, every site.
   No "while I'm here" extras.

4. **Stop on ambiguity.** If a site doesn't match the simple pattern, list it
   and ask — do not improvise.

5. **Verify**: run the project's test/lint command if available
   (read CLAUDE.md). Report pass/fail. Do not fix unrelated failures.

6. Print a one-line summary: `Touched N files. Tests: pass | fail | not-run.`

## When to graduate to /plan

If you start finding yourself making *choices* mid-task — stop. Tell the user:
`This is no longer mechanical. Recommend /plan first.` Leave changes already
made; do not roll back unilaterally.
