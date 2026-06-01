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

4. **Draft the plan**. A plan is read for three things only: the
   **executive summary**, the **concrete code/diffs**, and the
   **ADR/TODO list**. Write those well; cut everything else. No
   phase-by-phase narration, no restating what already exists, no
   multi-option essays, no "what the user prefers" meta-commentary.
   Prose earns its place only when a code snippet can't say it.

   Required sections:
   - `## TL;DR` — executive summary: what + why + how, one short
     paragraph. Goal/approach fold in here (no separate prose sections).
     Heading **and body** are in the language stored at
     `.claude/aims-summary-lang` (one-line file, default `en` if missing).
     Built-in heading translations: `en` → `## TL;DR`,
     `he` → `## תקציר מנהלים`. Unknown codes fall back to `en`.
     The rest of the plan stays in English (identifiers, code, paths
     are language-neutral).
   - `## Changes` — **the heart of the plan**. One subsection per file
     touched. Each carries the **actual code/diff at full relevant
     detail** — the snippet IS the spec. Order them so each is
     independently verifiable; the list of changes doubles as the
     implementation steps. Show real code, not descriptions of code.
   - `## Open design questions` — pre-implementation branches that
     `## Changes` does NOT yet pin down: empty/edge inputs, racing
     concurrent cases, undefined behavior on the boundary of a new
     algorithm. Omit the section only if you actually verified there
     are none — not "I didn't think of any." Distinct from `## Risks`
     (env/ops surprises) and from `## Close-out checklist` (post-
     implementation accounting). Closing a plan with open questions
     is fine; closing one without realizing you have any is the
     failure mode this section prevents.
   - `## Verification` — exact commands or tests that prove success.
   - `## Close-out checklist` — **mandatory, every line always present.**
     One line per concern with an **explicit verdict** so nothing is
     silently skipped. Write the verdict even when it's `NONE` — an
     omitted line is a bug. Fixed lines:
     - `ADR: NONE — <reason>` | `ADR: WRITE — <NNNN-slug: title>`
     - `Nodes: NONE` | `Nodes: UPDATE — <node paths to consolidate>`
     - `CLAUDE.md: NONE` | `CLAUDE.md: UPDATE — <section>`
     - `Tests: <path added>` | `Tests: EXISTING cover it` | `Tests: N/A — <reason>`
     - `TODO: NONE` | `TODO: <follow-ups left out of scope>`
   - `## Risks / unknowns` — terse bullets; include only real ones.
     Omit the section if there are none.

   **No `## Options considered` section.** If you genuinely weighed
   alternatives, fold a one-line "chose X over Y because Z" into the
   TL;DR. Never narrate the deliberation.

   No hard line cap — be as long as the code detail demands and as
   short as the prose allows. A 30-line plan that is all signal beats
   a 200-line plan padded with narration.

5. **Materialize the draft before asking approval** — the file on disk
   IS the artifact to review. See Phase 2.

## Phase 2 — Materialize draft (lock still held)

1. Compute slug: lowercase, hyphenated, ≤6 words from `$ARGUMENTS`.
2. Filename: `docs/plans/$(date -u +%Y-%m-%d)-<slug>.md`.
3. Create `docs/plans/` if missing.
4. Write the draft using a **Bash heredoc** (Write/Edit are blocked by
   the planning lock — `cat <<'EOF' > <file>` is the only path), using
   this template:

```markdown
# Plan: <title>
Status: draft
Started: YYYY-MM-DD

## TL;DR
<!-- heading per .claude/aims-summary-lang: ## TL;DR (en) | ## תקציר מנהלים (he); body in same language -->
<executive summary: what + why + how, one short paragraph>

## Changes

### path/to/file.ext
<one line of intent, then the actual code/diff at full relevant detail>
```lang
<the real snippet — this is the spec, not a description of it>
```

### path/to/other.ext
…

## Open design questions   (omit only if there genuinely are none)
- <pre-implementation branch not yet pinned down by ## Changes>

## Verification
- `<command>`

## Close-out checklist
<!-- every line MUST be present; write the verdict even when NONE -->
- ADR: NONE — <reason>            <!-- or: WRITE — NNNN-slug: title -->
- Nodes: NONE                     <!-- or: UPDATE — docs/memory/<tag>/<node>.md -->
- CLAUDE.md: NONE                 <!-- or: UPDATE — <section name> -->
- Tests: <path added>             <!-- or: EXISTING cover it / N/A — reason -->
- TODO: NONE                      <!-- or: follow-ups left out of scope -->

## Risks / unknowns   (omit if none)
- <terse, real risks only>
```

5. Print: `Draft saved to docs/plans/<filename>. Approve / edit / abort?`
6. Do **not** remove the lock yet. Do **not** edit anything else.

## Phase 3 — Approval gate

- **Approve** → flip the draft's `Status:` line from `draft` to
  `in-progress` (using `sed -i` via Bash — the lock blocks Edit, not
  Bash). Then `rm -f .claude/.planning-lock`. Then proceed to Phase 4.
- **Edit / iterate** → rewrite the draft in place (same heredoc; same
  filename). Re-ask. Lock stays.
- **Abort** → `rm -f docs/plans/<filename> .claude/.planning-lock` and
  print `Plan aborted.`.

## Phase 4 — Implement

You (or the next session) implement step by step, editing files
normally. The `post-edit-marker` hook flags dirty memory nodes as you
work. Nothing special required.

## Phase 5 — Close-out (inline, when implementation is done)

Triggered automatically when:
- An in-progress plan exists in `docs/plans/`, AND
- The implementation steps appear complete (every step has cited
  changes or you believe it's done), AND
- The Stop hook nudge has fired (`see stop-consolidate.sh`).

You may also trigger it yourself when you finish a plan; do not wait
for the hook if you know you're done.

### Close-out steps

1. **Verify changes.** Walk each `## Changes` subsection; cite
   `file:line` or commit hash for completion. If any is undone, list
   what's missing and stop — do not close.
2. **Run verification.** Execute every command in `## Verification`.
   Capture pass/fail. If any fail, stop — do not close.
3. **Resolve the `## Close-out checklist`.** Walk every line; none may
   be left unaddressed. For the `ADR:` line:
   - **Create the ADR** (status: proposed) when the change is a
     clear architectural commitment: new dependency, new module
     boundary, new invariant, supersedes a prior ADR, or the entry
     itself is unambiguous. Update the line to `ADR: WROTE — NNNN-slug`.
   - **Skip — but say so explicitly** (`ADR: NONE — <reason>`) when the
     change is a bug fix, refactor with no interface change, doc-only,
     test-only, or mechanical. Never drop the line.
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
   - Resolve `## Open design questions` (if present): each question is
     either **answered inline** (rewrite the bullet with the answer) or
     **carried forward** as a `TODO:` line in the Close-out checklist.
     An open question may not survive a closed plan unaddressed.
   - Append `## Closing checks` — verification command outputs, and the
     resolved `## Close-out checklist` (each line with its final verdict,
     e.g. `ADR: NONE — config toggle`, `Nodes: UPDATE — <tag>/<node>`).
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
7. **Final report.** Echo the resolved checklist so nothing is hidden:
   ```
   Plan: docs/plans/<file> → completed
   Verification: <N pass / M fail>
   ADR:      NONE — <reason> | WROTE ADR-NNNN (+ list)
   Nodes:    NONE | <N consolidated> (+ M inbox, K >4KB, L lint issues)
   CLAUDE.md: NONE | +<sections>
   Tests:    <path> | EXISTING | N/A
   TODO:     NONE | <follow-ups>
   ```

## Hard rules

- Do **not** close a plan with failing verification.
- Do **not** retroactively edit any past ADR body — status pointer only.
- If the planning lock still exists at close-out time, remove it.
- This command runs on Opus regardless of session model.
- The plan file is the contract for implementation. Context
  compaction won't erase it — next session can pick it up from disk.
