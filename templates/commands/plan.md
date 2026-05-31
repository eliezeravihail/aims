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

4. **Draft the plan.** Six required sections, fixed order, **no
   global length cap** (per ADR-0011):

   1. **Executive summary** — one short block (3–5 bullets or one
      paragraph) stating the problem and the chosen approach.
      Heading and body in the configured language.
      Read the language code from `.claude/aims-summary-lang`
      (single line; default `en` if file missing). Substitute the
      heading per this map; unknown codes fall back to `en`:
      - `en` → `## Executive summary`
      - `he` → `## תקציר מנהלים`

   2. **Technical design** — **content-triggered shape**:
      - *Mechanical change* (config flip, rename, file move,
        dependency bump): one bullet, `before → after`, with
        `file:line`.
      - *Refactor without new logic*: before/after signatures or
        a diff sketch.
      - *New algorithm, new data structure, new geometric
        computation, new state machine*: pseudo-code or actual
        code, with arg/return types and a concrete worked example.
        Edge-case enumeration goes inline OR under "Open design
        questions". If in doubt about a step's category, expand.

   3. **Open design questions** — every algorithmic step in
      Technical design either resolves its edge cases inline or
      lists them here. Distinct from Risks: this section is
      "what we didn't fully specify yet"; Risks is "what could
      go wrong even if our spec holds". Closing the plan with
      open questions is OK; closing without realizing you have
      any is the failure mode this section prevents.

   4. **Tests to add** — assertion shape per test, no code.
      Format: `- Given <input>: assert <expected output / invariant>.`

   5. **Risks** — env assumptions, perf regressions, integration
      surprises — failures that survive a correct spec.

   6. **Documentation actions** — structured checklist consumed
      by Phase 4:

      ```
      - ADRs to draft (proposed status):
        - [ ] ADR-NNNN — <title>
      - Plan status: completed | superseded | aborted; append ## Outcome.
      - Memory nodes to flag dirty: <list of docs/memory/ paths>
      - CLAUDE.md sections to update: <list, or "none">
      - External (optional): changelog, release notes, Slack, etc.
      ```

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

## <Executive summary | תקציר מנהלים>   ← heading per .claude/aims-summary-lang
- <problem in one bullet>
- <approach in one bullet>
- <main risk + expected outcome>

## Technical design
<content-triggered: one bullet per mechanical step;
 full pseudo-code for new algorithms / data structures / state machines>

## Open design questions
- <edge case not yet resolved, or "none">

## Tests to add
- Given <input>: assert <expected output / invariant>.

## Risks
- <what could go wrong even if the spec holds>

## Documentation actions
- ADRs to draft (proposed status):
  - [ ] ADR-NNNN — <title>
- Plan status: completed | superseded | aborted; append `## Outcome`.
- Memory nodes to flag dirty: <list of docs/memory/ paths>
- CLAUDE.md sections to update: <list, or "none">
- External (optional): changelog, release notes, Slack, etc.
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
3. **Auto-decide ADRs.** Parse `## Documentation actions` →
   `ADRs to draft` sub-list. For each unchecked item:
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
