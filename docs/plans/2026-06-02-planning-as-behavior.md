# Plan: Planning as behavior; /plan dispatches Opus subagent
Status: completed
Started: 2026-06-02
Completed: 2026-06-02

## TL;DR

Planning becomes a *behavior* on every actionable prompt, not a command
the user must remember. The hook injection describes the planning flow
factually so the assistant runs it inline whenever a non-trivial change
is requested. The `/plan` slash command shrinks to an **optional Opus
shortcut**: it dispatches Phase 1-2 (read-only discovery + draft write)
to a `model: opus` general-purpose subagent and resumes the main session
for Phase 3 onward — so users on Sonnet/Haiku can request a one-shot
Opus planning pass without switching their whole session. Recorded as
ADR-0022 (planning-as-behavior; /plan → subagent). The session
discovered this plan AFTER editing (user called it out) — this draft
is therefore retroactive and reflects what's already on disk plus
what's still pending.

## Changes

### templates/hooks/prompt-submit.sh — extended router_text (already applied)

```sh
    router_text="[aims] Project convention: for a non-trivial change, plan before implementing — read-only discovery, then a \`Status: draft\` plan written to \`docs/plans/\`, then user approval, then implementation, then inline close-out (verify, ADR-if-warranted, mark completed, refresh memory). The full flow is documented in \`.claude/commands/plan.md\`. Planning is the *behavior*; the \`/plan\` slash command is an OPTIONAL shortcut that dispatches the planning pass to an Opus subagent — use it when the current model is not Opus and the task warrants careful planning. If you (the assistant) are not running on Opus and this prompt looks like a non-trivial change, ask the user ONCE via AskUserQuestion whether to use \`/plan\` for an Opus planner; otherwise just plan inline. (Informational; nothing is blocked.)"
```

### templates/hooks/session-start.sh — convention bullet rewrite (already applied)

```sh
       - For a non-trivial change, the assistant plans before implementing —
         read-only discovery, then a Status: draft plan in docs/plans/, then
         user approval, then implementation, then inline close-out. The full
         flow is in .claude/commands/plan.md. The /plan slash command is an
         OPTIONAL shortcut that dispatches Phase 1-2 to an Opus subagent —
         use it when the current model is not Opus and planning quality
         matters; otherwise plan inline.
```

### templates/commands/plan.md — full rewrite (already applied)

Frontmatter loses `model: opus` (no main-session switch).
Body restructures around two steps:

1. **Step 1 — Spawn the Opus planner.** Inline the Phase 1-2 brief as
   the prompt to an Agent call with
   `subagent_type: "general-purpose"`, `model: "opus"`. Subagent
   returns the draft path + a short summary + any open design questions.
2. **Step 2 — Resume Phase 3 → 5 in the main session.** Approval gate,
   implementation, close-out — all on whatever model the main session
   is on. ADR creation in close-out may itself dispatch to Opus if
   needed.

Hard rule added: "This command does NOT switch the main session model.
Only the Phase 1-2 Agent subagent runs on Opus."

### CLAUDE.md — Workflow + Models policy (already applied)

Workflow section reframed:
- Planning is a behavior, documented in `.claude/commands/plan.md`.
- `/plan` is optional, dispatches to Opus subagent.
- Models policy: planning quality scales with model; assistant asks once
  when not on Opus and prompt looks non-trivial.

### .claude/hooks/prompt-submit.sh, .claude/hooks/session-start.sh, .claude/commands/plan.md — mirror refresh (PENDING)

```sh
for f in prompt-submit.sh session-start.sh; do
  cp templates/hooks/$f .claude/hooks/$f
done
cp templates/commands/plan.md .claude/commands/plan.md
```

### docs/adr/0022-planning-as-behavior-plan-dispatches-opus.md — new ADR (PENDING)

```markdown
# ADR-0022: Planning is a behavior; /plan dispatches an Opus subagent
Status: proposed
Date: 2026-06-02

## Context
Until now /plan was the sole entry to designed change: a slash command
with `model: opus` frontmatter that took over the whole session. The
hook only INFORMED about the convention. Users hit two pain points:
(a) they had to remember /plan, (b) /plan switched the whole session
to Opus even if they only wanted Opus for the planning pass itself.

## Decision
Planning is a project *behavior*: when the prompt-submit router
classifies a prompt as actionable (bug/feature/refactor/decision/
mechanical/ambiguous), the hook injection describes the full planning
flow as a project convention. The assistant runs the flow inline.

`/plan` is repositioned as an Opus shortcut. Its body spawns a
`general-purpose` subagent with `model: opus` to run Phase 1-2 (read-
only discovery + draft write). The main session resumes for Phase 3
(approval), Phase 4 (implementation), Phase 5 (close-out). No
`model: opus` frontmatter on the command itself.

If the current model is not Opus and the prompt looks non-trivial, the
assistant asks ONCE whether to use /plan; the user can opt for Opus
planning or for plan-inline-on-current-model.

## Consequences
- ✅ Planning happens naturally; no need to remember /plan.
- ✅ Users on Sonnet/Haiku can get an Opus planning pass without
  switching their whole session.
- ✅ Implementation + close-out cost is unchanged — they run on the
  session's current model.
- ⚠️ Subagent dispatch loses some of the main-session context; the
  brief includes $ARGUMENTS plus everything the subagent reads from
  disk. Acceptable since planning is read-only and the artifact (the
  draft on disk) is the contract for Phase 3 onward.
- 🔒 Rules out the "all of /plan runs on Opus" design; close-out and
  ADR writing now run on the main-session model unless the assistant
  dispatches them too.

## Alternatives considered
- **Keep /plan as session-wide Opus switch.** Rejected — forces Opus
  on phases that don't need it (implementation, mechanical edits).
- **Make the hook injection imperative ("you MUST plan").** Rejected —
  trips Claude's prompt-injection defense (ADR-0020).
- **Drop /plan entirely.** Rejected — Sonnet/Haiku users still want a
  one-shot Opus planning escape hatch.

## Verification
- `grep -n 'planning is the \*behavior\*' templates/hooks/prompt-submit.sh`
  finds the new router_text.
- `grep -n 'subagent_type.*general-purpose' templates/commands/plan.md`
  finds the dispatch instruction.
- `grep -n 'model: opus' templates/commands/plan.md` is empty (no
  frontmatter switch).
```

### docs/adr/README.md — index row (PENDING)

```markdown
| 0022 | Planning is a behavior; /plan dispatches an Opus subagent | proposed | 2026-06-02 |
```

### README.md — Workflow section (PENDING — light touch)

Update the workflow/hooks section to reflect that planning is a
behavior; /plan is the optional Opus shortcut. One short paragraph.

## Open design questions

- Should the assistant always ask before dispatching to Opus, or
  proceed silently when on a small model and a non-trivial prompt
  arrives? Current plan: ask ONCE per session (user can answer "skip
  asking" and we cache that for the session). For now: ask every time
  the router classifies a non-trivial prompt while on non-Opus.
- The Agent tool's `model` parameter — verified callable per the
  in-prompt tool documentation. If the harness rejects `model: opus`
  override, fall back to `subagent_type: "Plan"` (the built-in
  planner agent) and accept its tool restrictions (no Write — main
  session writes the draft from the subagent's structured return).

## Verification

- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → OK
- `bash .claude/memory/lint.sh` → clean
- `grep -L 'model: opus' templates/commands/plan.md` confirms removal
- `grep -n 'general-purpose' templates/commands/plan.md` confirms
  dispatch instruction
- Manual: trigger an actionable prompt on a fresh Sonnet session and
  confirm the assistant asks once about /plan; trigger one on Opus
  and confirm it plans inline without asking.

## Close-out checklist

- ADR: WRITE — 0022-planning-as-behavior-plan-dispatches-opus
- Nodes: UPDATE — docs/memory/discipline/plan.md,
  docs/memory/hooks/prompt-submit.md, docs/memory/hooks/session-start.md
  (the Stop hook will surface the dirty set; consolidation happens in
  close-out)
- CLAUDE.md: UPDATE — Workflow + Models policy (already applied)
- Tests: EXISTING cover it (router-auto-plan.sh, inform-never-block.sh)
  — the new convention text doesn't break invariants those check.
- TODO: NONE

## Risks / unknowns

- Subagent `model: opus` override may be harness-specific; verify on
  first use. Fallback noted in Open questions.
- Two convention texts (prompt-submit + session-start) must stay in
  sync; if they drift the assistant gets mixed signals. Future cleanup
  could DRY them via a shared file sourced by both hooks — out of
  scope here.

## Outcome

ADR-0022 records the decision. The `prompt-submit` router_text now
describes the full planning behavior factually (`templates/hooks/
prompt-submit.sh:218`). `session-start` carries the same convention
under "Project conventions (factual)". `templates/commands/plan.md`
no longer carries `model: opus` frontmatter and dispatches Phase 1-2
to a `general-purpose` Agent subagent with `model: "opus"`. The main
session resumes for Phase 3 → 5. `.claude/` mirrors refreshed.
README (Workflow / What you get) and CLAUDE.md (Workflow / Models
policy) updated.

Open design question resolved (user choice): when the current model
is not Opus and the prompt looks non-trivial, the assistant asks
**every time** before planning — no per-session caching.

## Closing checks

- ADR: WROTE — 0022-planning-as-behavior-plan-dispatches-opus
- Nodes: UPDATED — discipline/plan, hooks/prompt-submit,
  hooks/session-start (body text refreshed for ADR-0022);
  memory/phase-a-marker, memory/phase-b-consolidation (dirty from
  prior commit; no design change — marked consolidated)
- CLAUDE.md: UPDATED — Workflow + Models policy
- Tests: EXISTING — `bash -n` syntax OK on all hooks/tests;
  `bash .claude/memory/lint.sh` clean (15 nodes, 0 dirty);
  `tests/inform-never-block.sh` 26/27 (pre-existing test bug: passes
  plain text to a hook that reads JSON via jq — unrelated to this
  change; logged as Known issue for a future cleanup);
  `tests/router-auto-plan.sh` all passing
- TODO: NONE

Verification commands (all passed):
- `grep -L 'model: opus' templates/commands/plan.md` → listed (no
  frontmatter switch).
- `grep -c 'subagent_type.*general-purpose' templates/commands/plan.md`
  → 1 (dispatch present).
- `grep -c 'Planning is the' templates/hooks/prompt-submit.sh` → 1.
- `grep -c 'plans before implementing' templates/hooks/session-start.sh`
  → 1.
- `diff -q templates/hooks/*.sh .claude/hooks/*.sh` → mirrors match.
