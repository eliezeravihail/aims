---
description: Plan non-trivial work; read-only; ends with persisted plan + inline close-out after implementation
argument-hint: "<task description>"
model: opus
---

# /plan

You are entering a **planning session** for: **$ARGUMENTS**

Planning produces a durable artifact in `docs/plans/`. Implementation,
verification, ADR creation, and memory consolidation all happen inline
after the plan is approved — there is no separate `/done`.

## Phase 1 — Plan (read-only)

1. **Create the planning lock** as your very first step:
   ```bash
   mkdir -p .claude && touch .claude/.planning-lock
   ```
   The `pre-write` hook blocks Edit/Write while it exists. Do not skip.

2. **Read-only exploration only.** Allowed: Read, Grep, Glob, Bash
   (read-only), WebFetch, WebSearch. **Forbidden**: Edit, Write,
   MultiEdit, NotebookEdit, mutating Bash. Hypotheses go in `/tmp`.

3. **Investigate** existing code, ADRs (`docs/adr/`), prior plans
   (`docs/plans/`). Cite `file:line`.

4. **Draft the plan**. Required sections (target ≤80 lines):
   - `## TL;DR` — **one paragraph** summarizing what + why + how.
   - `## Goal` — measurable, one sentence.
   - `## Decision` — chosen approach (key choices in bullets).
   - `## Steps` — ordered, each independently verifiable.
   - `## Verification` — exact commands or tests that prove success.
   - `## Risks / unknowns` — what could go wrong.
   - `## ADRs to record after implementation` — checklist; one line
     per candidate.

   **Conditional**: include `## Options considered` only if more than
   one real option was weighed. Otherwise fold a one-line "Why not X"
   into the TL;DR.

5. **Present** the plan inline in your message and ask the user to
   approve / edit / abort. (Native ExitPlanMode is unavailable when
   this command is invoked via slash command alone — the planning
   lock is what enforces read-only.)

## Phase 2 — Materialize (after approval)

1. Compute slug: lowercase, hyphenated, ≤6 words from `$ARGUMENTS`.
2. Filename: `docs/plans/$(date +%Y-%m-%d)-<slug>.md`.
3. Create `docs/plans/` if missing.
4. Write the approved plan using this template:

```markdown
# Plan: <title>
Status: in-progress
Started: YYYY-MM-DD

## TL;DR
<one paragraph>

## Goal
…

## Decision
…

## Steps
1. …

## Verification
- `<command>`

## Risks / unknowns
…

## ADRs to record after implementation
- [ ] …
```

5. Remove the lock: `rm -f .claude/.planning-lock`.
6. Print: `Plan saved to docs/plans/<filename>. Implementation can begin.`

## Phase 3 — Implement

You (or the next session) implement step by step, editing files
normally. The `post-edit-marker` hook flags dirty memory nodes as you
work. Nothing special required.

## Phase 4 — Close-out (inline, when implementation is done)

Triggered automatically when:
- An in-progress plan exists in `docs/plans/`, AND
- The implementation steps appear complete (every step has cited
  changes or you believe it's done), AND
- The Stop hook nudge has fired (`see stop-consolidate.sh`).

You may also trigger it yourself when you finish a plan; do not wait
for the hook if you know you're done.

### Close-out steps

1. **Verify steps.** Walk each step; cite `file:line` or commit hash
   for completion. If any step is undone, list what's missing and
   stop — do not close.
2. **Run verification.** Execute every command in `## Verification`.
   Capture pass/fail. If any fail, stop — do not close.
3. **Auto-decide ADRs.** For each item in
   `## ADRs to record after implementation`:
   - **Create the ADR** (status: proposed) when the change is a
     clear architectural commitment: new dependency, new module
     boundary, new invariant, supersedes a prior ADR, or the entry
     itself is unambiguous.
   - **Skip silently** when the change is a bug fix, refactor with
     no interface change, doc-only, test-only, or mechanical.
   - **Ask** (single `AskUserQuestion`) when borderline.

   ADR creation logic (no `/adr` command needed):
   - Compute `NNNN` = max of `docs/adr/NNNN-*.md` + 1 (4 digits).
   - Use `docs/adr/_template.md`; status `proposed`; date today.
   - Append a row to `docs/adr/README.md` index.
   - If superseding: write `Supersedes: ADR-MMMM` in the new ADR
     and edit the old ADR's status pointer (status-only edit is
     allowed; body never changes).
4. **Update the plan file.**
   - `Status: completed`.
   - Append `## Outcome` — short summary + links to any ADRs.
   - Append `## Closing checks` — verification command outputs.
5. **CLAUDE.md hygiene.** If this work established a new convention
   (build command, layout rule, naming convention), propose a diff
   and ask before merging.
6. **Memory consolidation (ADR-0007/0008/0009).** If `docs/memory/`
   exists:
   - For each node whose `code:` overlaps a file this plan
     touched: read the prompt from
     `bash .claude/memory/consolidate.sh <node>`, plus the plan
     body + any new ADR bodies, and Edit the node body per the
     ADR-0008 schema. Finish each with
     `bash .claude/memory/mark.sh <node> consolidated`.
   - Process `_inbox.md` if non-empty: read the prompt from
     `bash .claude/memory/classify-inbox.sh`. Apply confident
     `existing-node` proposals via Edit; for `new-node` or
     `uncertain`, ask via `AskUserQuestion`.
   - Detect new CLAUDE.md sections changed in this plan that no
     node references; offer to add a `claude_md_refs:` entry.
   - Flag nodes > 4 KB; ask whether to split or extract to ADR.
   - Run `bash .claude/memory/lint.sh` and surface issues.
   - Run `bash .claude/memory/doctor.sh` and include verbatim.
7. **Final report.**
   ```
   Plan: docs/plans/<file> → completed
   Verification: <N pass / M fail>
   ADRs created: ADR-NNNN (+ list)
   CLAUDE.md: unchanged | +<sections>
   Memory: <N consolidated, M inbox, K >4KB, L lint issues>
   ```

## If user rejects the draft

Iterate. Do not remove the lock. Do not write any files.

## If user aborts

`rm -f .claude/.planning-lock` and print `Plan aborted.`

## Hard rules

- Do **not** close a plan with failing verification.
- Do **not** retroactively edit any past ADR body — status pointer only.
- If the planning lock still exists at close-out time, remove it.
- This command runs on Opus regardless of session model.
- The plan file is the contract for implementation. Context
  compaction won't erase it — next session can pick it up from disk.
