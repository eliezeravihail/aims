---
description: Dispatch Phase 1-2 planning to an Opus subagent; main session resumes for approval, implementation, and close-out
argument-hint: "<task description>"
---

# /plan

Plan **$ARGUMENTS** by dispatching the read-only discovery + draft-write
to an Opus subagent. The main session stays on its current model; only
Phase 1-2 (the planning itself) runs on Opus. Phase 3 onward (approval,
implementation, close-out) runs back here.

Planning is the *behavior*; this command is a shortcut for getting an
Opus planner without switching the whole session. If the main session
is already Opus, you may skip the dispatch and run the phases inline.

Plans, decisions, and insights are stored as a **Capsa capsule** at
`.capsa/` (plans → `.capsa/plans/`, ADRs → `.capsa/decisions/`, memory →
`.capsa/insights/`). aims is the active self-maintenance layer over that
passive capsule (decision 0031). The vendored `validator/validate.py`
checks conformance.

## Step 1 — Spawn the Opus planner

Call the Agent tool with:

- `subagent_type: "general-purpose"`
- `model: "opus"`
- `description: "Plan: $ARGUMENTS"`
- `prompt:` the planning brief below (Phase 1-2 only). The subagent must
  end by Writing a `status: draft` Capsa plan to disk and returning the path.

### Planner subagent prompt (paste into the Agent call)

> You are a planning subagent for the aims project. Your job is **Phase
> 1-2 only**: read-only discovery + writing a `status: draft` Capsa plan
> record. Do not modify any source. Do not run the implementation,
> approval, or close-out — those happen in the main session after you return.
>
> Task: **$ARGUMENTS**
>
> ## Phase 1 — Read-only discovery
>
> Allowed tools: Read, Grep, Glob, Bash (read-only), WebFetch, WebSearch.
> Forbidden: Edit, MultiEdit, NotebookEdit, mutating Bash. The Write tool
> is allowed ONLY for the final plan file in Phase 2.
>
> Investigate existing code, decisions (`.capsa/decisions/`), prior plans
> (`.capsa/plans/`), and relevant insights (`.capsa/insights/`). Cite
> `file:line` where it matters.
>
> Build the plan. It is read for three things: the **executive summary**,
> the **concrete code/diffs**, and the **ADR/TODO list**. Write those
> well; cut everything else. No phase narration, no restating what
> exists, no multi-option essays, no "what the user prefers" commentary.
> Prose earns its place only when a snippet can't say it.
>
> Required sections:
> - `## TL;DR` — what + why + how, one short paragraph. Goal/approach
>   fold in here. The heading **and body** are in the language stored at
>   `.claude/aims-summary-lang` (one-line file, default `en` if missing).
>   Built-in heading translations: `en` → `## TL;DR`,
>   `he` → `## תקציר מנהלים`. Unknown codes fall back to `en`. The rest
>   of the plan stays in English (identifiers, code, paths are
>   language-neutral).
> - `## Changes` — **the heart of the plan**. One subsection per file
>   touched. Each carries the **actual code/diff at full relevant
>   detail** — the snippet IS the spec. Order them so each is
>   independently verifiable; the list of changes doubles as the
>   implementation steps. Show real code, not descriptions of code.
> - `## Open design questions` — pre-implementation branches that
>   `## Changes` does NOT yet pin down: empty/edge inputs, racing
>   concurrent cases, undefined behavior on boundaries. Omit only if
>   you actually verified there are none — not "I didn't think of any."
> - `## Verification` — exact commands or tests that prove success.
> - `## Close-out checklist` — **mandatory, every line always present.**
>   One line per concern with an **explicit verdict**:
>   - `ADR: NONE — <reason>` | `ADR: WRITE — <NNNN-slug: title>`
>   - `Insights: NONE` | `Insights: UPDATE — <insight paths to consolidate>`
>   - `Charter: NONE` | `Charter: UPDATE — <section>`
>   - `Tests: <path added>` | `Tests: EXISTING cover it` | `Tests: N/A — <reason>`
>   - `TODO: NONE` | `TODO: <follow-ups left out of scope>`
> - `## Risks / unknowns` — terse bullets; omit if none.
>
> No `## Options considered` section. If you weighed alternatives, fold
> a one-line "chose X over Y because Z" into the TL;DR.
>
> ## Phase 2 — Write the draft
>
> 1. Compute slug: lowercase, hyphenated, ≤6 words from the task.
> 2. Compute the next plan id: `NNNN` = (max integer `id:` across
>    `.capsa/plans/*.md`) + 1, zero-padded to 4 digits for the filename.
> 3. Filename: `.capsa/plans/<NNNN>-<slug>.md`.
> 4. Create `.capsa/plans/` if missing.
> 5. Use the **Write tool** to materialize a conforming Capsa plan with
>    this template (frontmatter first, then the rich aims body):
>
> ```markdown
> ---
> id: <N>
> title: "<title>"
> kind: initiative
> status: draft
> opened: <YYYY-MM-DD>
> completed: null
> priority: null
> target_date: null
> milestone: null
> requirement_refs: []
> decision_refs: []
> ---
>
> ## TL;DR
> <one-paragraph executive summary in the configured language>
>
> ## Changes
>
> ### path/to/file.ext
> <one line of intent, then the actual code/diff>
> ```lang
> <real snippet>
> ```
>
> ## Open design questions
> - <pre-implementation branch>
>
> ## Verification
> - `<command>`
>
> ## Close-out checklist
> - ADR: NONE — <reason>
> - Insights: NONE
> - Charter: NONE
> - Tests: <verdict>
> - TODO: NONE
>
> ## Risks / unknowns
> - <terse, real risks only>
> ```
>
> 6. Validate the capsule still conforms:
>    `python3 validator/validate.py .capsa` (expect "conforming capsule ✔").
>
> ## Return
>
> Return ONE message containing:
> - The full path of the draft file.
> - A 2-3 line summary of the plan (TL;DR + main file(s) touched).
> - Any open design questions that need user resolution before approval.
>
> Do NOT proceed to Phase 3 (approval) — that runs in the main session.

## Step 2 — Resume in the main session (Phase 3 → 5)

When the subagent returns with the draft path:

1. Print: `Draft saved to <path>. Approve / edit / abort?`
2. Surface any open design questions the subagent flagged.

### Phase 3 — Approval gate

- **Approve** → flip the draft's frontmatter `status:` from `draft` to
  `in_progress` (Edit tool). Proceed to Phase 4.
- **Edit / iterate** → rewrite the draft in place (Write/Edit; same
  filename). Re-ask. (You may spawn the Opus planner again for a
  re-draft if helpful.)
- **Abort** → `rm -f .capsa/plans/<filename>` and print `Plan aborted.`.

### Phase 4 — Implement

Implement step by step, editing files normally. The `post-edit-marker`
hook names any insight whose `code_globs` cover a file you touch (its
staleness is then computed from `updated:` vs git). Nothing special required.

### Phase 5 — Close-out (inline, when implementation is done)

Triggered automatically when:
- An `in_progress` plan exists in `.capsa/plans/`, AND
- Implementation steps appear complete, AND
- The Stop hook nudge has fired (`see stop-consolidate.sh`).

You may trigger it yourself when you finish; do not wait for the hook.

**Close-out runs in the current main session.** If the main session is
not on Opus and the close-out involves writing an ADR, you may dispatch
ADR creation to an Opus subagent the same way — but the plan file edit,
verification, and insight consolidation happen here.

### Close-out steps

1. **Verify changes.** Walk each `## Changes` subsection; cite
   `file:line` or commit hash for completion. If any is undone, list
   what's missing and stop — do not close.
2. **Run verification.** Execute every command in `## Verification`.
   Capture pass/fail. If any fail, stop — do not close.
3. **Resolve the `## Close-out checklist`.** Walk every line; none may
   be left unaddressed. For the `ADR:` line:
   - **Create the ADR** (status: proposed) when the change is a clear
     architectural commitment: new dependency, new module boundary,
     new invariant, supersedes a prior ADR, or the entry itself is
     unambiguous. Update the line to `ADR: WROTE — NNNN-slug`.
   - **Skip — but say so explicitly** (`ADR: NONE — <reason>`) when
     the change is a bug fix, refactor with no interface change,
     doc-only, test-only, or mechanical. Never drop the line.
   - **Ask** (single `AskUserQuestion`) when borderline.

   ADR creation logic (a Capsa decision record; no `/adr` command needed):
   - Compute `NNNN` = (max integer `id:` across `.capsa/decisions/*.md`)
     + 1 (4-digit filename).
   - Write `.capsa/decisions/NNNN-slug.md` with Capsa frontmatter
     (`id`, `title`, `status: proposed`, `date: <today>`,
     `supersedes: null`, `superseded_by: null`, `tags: []`) and the body
     sections `## Context` / `## Decision` / `## Consequences` /
     `## Alternatives considered`.
   - If superseding: set `supersedes: <MMMM>` in the new decision and edit
     the old decision's `status:` → `superseded` plus `superseded_by:`
     (status/pointer edit only — never rewrite a past decision's body).
   - Validate: `python3 validator/validate.py .capsa`.
4. **Update the plan file.**
   - Frontmatter `status: completed`, `completed: <today>`.
   - Append `## Outcome` — short summary + links to any decisions.
   - Resolve `## Open design questions` (if present): each is either
     **answered inline** or **carried forward** as a `TODO:` line.
   - Append `## Closing checks` — verification command outputs and the
     resolved `## Close-out checklist`.
5. **Charter hygiene.** If this work established a new project-wide
   convention, propose a diff to `.capsa/charter.md` and ask before merging.
6. **Insight consolidation (ADR-0007/0008/0009).** If `.capsa/insights/`
   exists:
   - For each insight whose `code_globs` overlaps a file this plan
     touched: read the prompt from
     `bash .claude/memory/consolidate.sh <insight>`, plus the plan body +
     any new decision bodies, and Edit the insight body per ADR-0028.
     Finish each with `bash .claude/memory/mark.sh <insight> consolidated`
     (bumps `updated:`, clearing the computed staleness).
   - Process the inbox if non-empty: read the prompt from
     `bash .claude/memory/classify-inbox.sh`. Apply confident
     `existing-insight` proposals via Edit; for `new-insight` or
     `uncertain`, ask via `AskUserQuestion`.
   - Flag insights > 4 KB; ask whether to split or extract to a decision.
   - Run `bash .claude/memory/lint.sh` and surface issues.
   - Run `bash .claude/memory/doctor.sh` and include verbatim.
7. **Final report.** Echo the resolved checklist:
   ```
   Plan: .capsa/plans/<file> → completed
   Verification: <N pass / M fail>
   ADR:      NONE — <reason> | WROTE decision NNNN (+ list)
   Insights: NONE | <N consolidated> (+ M inbox, K >4KB, L lint issues)
   Charter:  NONE | +<sections>
   Tests:    <path> | EXISTING | N/A
   TODO:     NONE | <follow-ups>
   ```

## Hard rules

- Do **not** close a plan with failing verification.
- Do **not** retroactively edit any past decision body — status/pointer only.
- The capsule must stay conforming: run `python3 validator/validate.py
  .capsa` after writing plans or decisions.
- AIMS never creates a planning lock; planning is read-only by discipline.
- The plan file is the contract for implementation. Context compaction
  won't erase it — next session can pick it up from disk.
- This command does NOT switch the main session model. Only the Phase
  1-2 Agent subagent runs on Opus.
