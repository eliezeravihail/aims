# ADR-0022: Planning is a behavior; `/plan` dispatches an Opus subagent
Status: proposed
Date: 2026-06-02
Supersedes: —
Superseded by: —

## Context

Until 2026-06-02, `/plan` was the sole entry to designed change: a slash
command with `model: opus` frontmatter that took over the whole session.
The `prompt-submit` hook only INFORMED about the convention with a
single sentence ("non-trivial changes are designed via `/plan`"). Two
pain points emerged:

1. The user had to remember `/plan`. On a Sonnet or Haiku session in
   the middle of unrelated work, an actionable prompt arrived and the
   assistant jumped to editing because the hook awareness alone wasn't
   directive enough.
2. `/plan` switched the WHOLE session to Opus, including implementation
   and close-out — phases that don't need Opus and cost more on it.

The hook architecture (ADR-0020) requires injections to be factual, not
imperative, so the fix can't be "tell the model to use `/plan`."

## Decision

Planning becomes a project **behavior**:

- The `prompt-submit` router injection now describes the full planning
  flow factually as a project convention. When the router classifies a
  prompt as actionable (`bug` / `feature` / `refactor` / `decision` /
  `mechanical` / `ambiguous`), the injection states what the assistant
  does for non-trivial changes: read-only discovery → draft to
  `docs/plans/` → user approval → implementation → inline close-out.
  No imperative phrasing; the convention is descriptive (`templates/
  hooks/prompt-submit.sh:218`).
- `session-start` carries the same convention in its standing-
  conventions block so a resumed session inherits it.

`/plan` is repositioned as an Opus shortcut. Its body now spawns a
`general-purpose` subagent with `model: "opus"` to run Phase 1-2
(read-only discovery + draft write). The main session resumes for
Phase 3 (approval), Phase 4 (implementation), Phase 5 (close-out).
No `model: opus` frontmatter on the command itself — the main session
keeps whatever model the user picked.

When the current model is not Opus and the prompt looks non-trivial,
the assistant asks the user **every time** via `AskUserQuestion`
whether to use `/plan` for an Opus planner or to plan inline on the
current model (per user preference: explicit consent over per-session
caching).

Boundary: this applies only to non-trivial prompts the router flags as
actionable. Trivial edits, mechanical renames already in flight, and
plain questions remain inline.

## Consequences

- ✅ Planning happens by default without remembering `/plan`.
- ✅ Sonnet/Haiku users get a one-shot Opus planning escape hatch
  without paying Opus rates for the whole session.
- ✅ Implementation + close-out cost stays on the session's current
  model.
- ⚠️ Subagent dispatch loses some of the main-session context; the
  brief is `$ARGUMENTS` plus whatever the subagent reads from disk.
  Acceptable since Phase 1 is read-only and the draft on disk is the
  contract for Phase 3 onward.
- ⚠️ User is asked every time on non-Opus models. May feel noisy in
  rapid-fire sessions; deferred (no per-session caching, by request).
- 🔒 Rules out the "all of `/plan` runs on Opus" design — close-out
  and ADR writing now run on the main-session model unless the
  assistant chooses to dispatch them too.

## Alternatives considered

- **Keep `/plan` as a session-wide Opus switch.** Rejected — forces
  Opus on phases that don't need it.
- **Make the hook injection imperative ("you MUST plan").** Rejected
  — trips Claude's prompt-injection defense (ADR-0020) and surfaces
  the injection to the user as quoted text instead of context.
- **Drop `/plan` entirely.** Rejected — Sonnet/Haiku users still want
  an explicit Opus planning escape hatch.
- **Ask once per session, cache the answer.** Rejected by user
  preference: explicit consent on every non-trivial prompt.

## Verification

- `grep -L 'model: opus' templates/commands/plan.md` lists the file
  (frontmatter no longer switches the session model).
- `grep -c 'subagent_type.*general-purpose' templates/commands/plan.md`
  ≥ 1 (dispatch instruction present).
- `grep -c 'Planning is the \*behavior\*' templates/hooks/prompt-submit.sh`
  ≥ 1 (router_text rewritten).
- The same convention bullet appears in `templates/hooks/session-start.sh`
  under "Project conventions (factual)".
- `.claude/hooks/` mirrors match `templates/hooks/`.
