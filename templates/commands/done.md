---
description: Close an active plan — verify steps, run checks, prompt for ADRs
argument-hint: "[plan-id or filename; default: latest in-progress]"
model: opus
---

# /done

You are closing a plan. Argument: **$ARGUMENTS** (may be empty → most recent
in-progress plan in `docs/plans/`).

## Steps

1. **Locate the plan.**
   - If $ARGUMENTS given: match `docs/plans/*<arg>*.md`. Error if 0 or >1 match.
   - Else: pick the file in `docs/plans/` with `Status: in-progress` and the
     latest `Started:` date. Error if none.

2. **Read the plan and verify each step.**
   For each numbered step, ask: was it implemented? cite `file:line` or
   commit hash. If a step is unchecked and undone, **do not close** — list
   what's missing and stop.

3. **Run verification commands** listed in the plan's `## Verification`
   section. Capture pass/fail. If anything fails, **do not close** — surface
   the failures and stop.

4. **Check for ADR-worthy decisions.**
   Re-read the plan's `## ADRs to record after implementation` checklist.
   For each unticked item, ask the user:
   `ADR for "<item>"?  [yes → /adr | no → mark won't-record | defer]`

5. **Update the plan file.**
   - Set `Status: completed`.
   - Append a `## Outcome` section: short summary of what shipped, any
     deviations from the plan, and links to ADRs created.
   - Append `## Closing checks` with the verification command outputs
     (pass/fail per command).

6. **CLAUDE.md hygiene check.**
   Ask: did this work establish any new convention worth recording in
   CLAUDE.md? (e.g., new build command, directory layout, naming rule.)
   If yes, propose the diff and ask for approval before merging.

7. **Memory consolidation (ADR-0007 / ADR-0008).**
   If `docs/memory/` exists:
   - **Propagate plan + new ADRs into the tree.** Build the bridge
     context by concatenating: this plan file's body, plus each ADR
     created in step 4. Export it as `AIMS_EXTRA_CONTEXT` so the
     consolidator can mine it for invariants, design rationale, and
     fixed-bug entries:
     ```
     ctx=$(cat docs/plans/<this-plan>.md \
                $(for n in <new-adrs>; do echo docs/adr/$n-*.md; done))
     AIMS_EXTRA_CONTEXT="$ctx" \
       bash .claude/hooks/stop-consolidate.sh --force
     ```
     The `--force` bypasses the per-session throttle. If no ADRs
     were created, pass only the plan body.
   - Run `bash .claude/memory/classify-inbox.sh` if `_inbox.md` is
     non-empty.  Apply confident `existing-node` proposals via Edit;
     for `new-node` and `uncertain` proposals, ask the user via
     `AskUserQuestion` before acting.
   - Detect new CLAUDE.md sections changed during this plan that
     aren't yet linked from any node:
     ```
     git log --since="<plan-started-date>" --pretty=format: --name-only \
       -- CLAUDE.md | sort -u
     ```
     If CLAUDE.md changed and no node references the new section,
     offer to add a `claude_md_refs:` entry to the most relevant
     node.
   - **Node health (ADR-0008 ~1–2 KB target):** list any node files
     larger than 4 KB. For each, ask the user whether to split into
     sibling nodes or extract content to an ADR.
     ```
     find docs/memory -name '*.md' -not -name 'README.md' \
       -not -name '_inbox.md' -size +4k -printf '%p %s\n'
     ```
   - **Lint pass:** run `bash .claude/memory/lint.sh`. Surface every
     reported issue (orphan refs, section/order violations,
     non-portable pointers, fixed-bug commits not in git, parent
     cycles). Offer to fix each interactively.
   - **Pipeline health:** run `bash .claude/memory/doctor.sh` and
     include its output verbatim in the final report. If
     `ANTHROPIC_API_KEY` is absent, warn the user that propagation
     was skipped and the tree did not absorb this plan's content.

8. **Final report.**

   ```
   Plan: docs/plans/YYYY-MM-DD-<slug>.md → completed
   Verification: <N pass / M fail>
   ADRs created: ADR-NNNN, ADR-MMMM
   CLAUDE.md: unchanged | +<sections>
   Memory: <N nodes consolidated, M inbox entries classified,
           K nodes >4KB flagged, L lint issues>
   ```

## Hard rules

- Do **not** close a plan with failing verification. Tell the user what
  needs fixing first.
- Do **not** retroactively edit any past ADR. Closing the plan can *create*
  new ADRs, never edit old ones.
- If the planning lock `.claude/.planning-lock` still exists for some reason,
  remove it as part of cleanup.
