---
description: Plan non-trivial work before implementation (read-only, ends with ExitPlanMode + persisted plan)
argument-hint: "<task description>"
model: opus
---

# /plan

You are entering a **planning session** for the task: **$ARGUMENTS**

Planning produces a durable artifact and uses Claude Code's plan-mode discipline.

## Discipline (mandatory)

1. **Create the planning lock** as your very first step:
   ```bash
   mkdir -p .claude && touch .claude/.planning-lock
   ```
   This signals other hooks that planning is in progress; the `pre-write` hook
   blocks Edit/Write while it exists. Do not skip this.

2. **Read-only exploration only.** Allowed: Read, Grep, Glob, Bash (read-only),
   WebFetch, WebSearch. **Forbidden:** Edit, Write, MultiEdit, NotebookEdit, or
   any Bash that mutates files. If you need to test a hypothesis, run it in
   `/tmp` or describe the experiment without performing it.

3. **Investigate before deciding.** Read the existing code paths, related ADRs
   (`docs/adr/`), and any prior plan files (`docs/plans/`). Cite specific
   `file:line` references in the plan.

4. **Draft the plan** in your reasoning, covering:
   - **Context** — what's true today; constraints discovered.
   - **Goal** — measurable, in one sentence.
   - **Options considered** — at least two; why each was kept or discarded.
   - **Decision** — the chosen approach.
   - **Steps** — ordered, each independently verifiable.
   - **Verification** — exact commands or tests that prove success.
   - **Risks / unknowns** — what could still go wrong.
   - **ADR-worthy?** — if yes, list the decisions that warrant `/adr` after.

5. **Present via `ExitPlanMode`.** When the plan is ready, call ExitPlanMode
   with the full plan text. The user will approve, edit, or reject.

## After approval — materialize the plan

Once the user approves via ExitPlanMode:

1. Compute slug: lowercase, hyphenated, ≤6 words from $ARGUMENTS.
2. Compute filename: `docs/plans/$(date +%Y-%m-%d)-<slug>.md`
3. Create `docs/plans/` if missing.
4. Write the approved plan to that file using this template:

```markdown
# Plan: <title from $ARGUMENTS>
Status: in-progress
Started: YYYY-MM-DD

## Context
…

## Goal
…

## Options considered
- **A**: … (rejected because …)
- **B**: … (chosen because …)

## Steps
1. …
2. …

## Verification
- `<command or test>`
- …

## Risks / unknowns
…

## ADRs to record after implementation
- [ ] …
```

5. **Remove the planning lock**:
   ```bash
   rm -f .claude/.planning-lock
   ```
6. Print: `Plan saved to docs/plans/<filename>. Implementation can begin.`

## If the user rejects ExitPlanMode

Iterate on the plan. Do not remove the lock. Do not write any files.

## If the user aborts

Remove the lock (`rm -f .claude/.planning-lock`) and print `Plan aborted.`

## Notes

- This command runs on Opus regardless of session model — planning warrants
  the deeper reasoning.
- The plan file is the contract for implementation. The next session can pick
  it up from disk; context compaction will not erase it.
- Closing the plan happens via `/done <plan-id>`.
