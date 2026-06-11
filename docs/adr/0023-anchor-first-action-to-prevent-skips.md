# ADR-0023: Anchor "first action = write draft" to prevent planning skips
Status: accepted
Date: 2026-06-02
Supersedes: —
Superseded by: —

## Context

ADR-0022 made planning a *behavior* (not a `/plan` command requirement)
and described the flow in the `prompt-submit` and `session-start` hook
injections. Despite the convention being present in the assistant's
context as a static reminder, the very next non-trivial change — the
ADR-0022 implementation itself — was carried out **without writing a
draft plan first**. The assistant proposed an approach in two
conversational sentences; the user replied "do it"; the assistant
jumped to Phase 4 (implementing edits across ~5 files) and skipped
Phase 2 (writing the `Status: draft` plan to disk) and Phase 3
(approval gate on the on-disk artifact).

Root cause: **conversational drift.** The static planning-convention
reminder arrives at `UserPromptSubmit` and `SessionStart` — moments
that feel like setup, not decision-points. When the user issues a
brief approval like `do it`, the conversational continuity makes that
read as "approve and execute" rather than "approve and transition into
the formal Phase 2 → Phase 3 sequence." The hook's reminder is true
but abstract; it doesn't anchor a concrete first action at the moment
of first source edit.

The `PreToolUse` (`pre-write`) hook already injects a generic
planning-convention reminder on the first source edit of a session
with no in-progress plan — but the reminder is the same abstract
prose, and it doesn't name the concrete trigger ("you are about to
edit X without a draft on disk").

## Decision

Two complementary mitigations, both factual and non-blocking per
ADR-0020:

1. **State-aware `pre-write` injection.** Rewrite the
   `templates/hooks/pre-write.sh` NOTE so it names (a) the specific
   file about to be edited, (b) the missing `Status: draft` /
   `Status: in-progress` plan in `docs/plans/`, and (c) the concrete
   next action ("materialize the draft BEFORE the first source
   edit"). The note also explicitly states that brief approvals
   (`yes` / `do it`) authorize entering Phase 2, not skipping to
   Phase 4. The hook still never blocks; the per-session inject-once
   marker (`.claude/.aims-plan-note-<sid>`) is preserved so it fires
   exactly once per session.

2. **CLAUDE.md self-discipline addendum.** Add a "Workflow" paragraph
   stating: *Approval is for Phase 2, not Phase 4.* A brief
   conversational `yes` to a proposal approves writing the draft —
   not the cross-file Edit/Write spree. The plan-on-disk + a
   re-confirm gate stays in force even when the conversational reply
   is brief.

Boundary: this decision targets the conversational-drift failure
mode. It does not change ADR-0020 (hooks still never block), does
not change ADR-0022 (planning is still a behavior; `/plan` is still
optional), and does not introduce a planning lock. The mitigation is
better signaling at the moment of first edit, plus codifying the
approval semantics in CLAUDE.md.

## Consequences

- ✅ The PreToolUse note now anchors to a concrete moment (specific
  file, missing plan) rather than restating an abstract convention
  the assistant already saw at session-start. Anchored signals are
  harder to drift past than ambient ones.
- ✅ CLAUDE.md codifies the approval-semantics rule, so even when the
  hook injection is skimmed, the rule is durable context for the
  session.
- ⚠️ The PreToolUse note is longer than before (~3 sentences vs 1).
  Mitigated by being concrete: a long note that names the file and
  the missing plan is more useful than a short abstract one.
- ⚠️ Per-session inject-once means a second non-trivial prompt later
  in the same session won't re-fire the anchor. The `prompt-submit`
  router still injects the planning convention for each actionable
  prompt; treating that as sufficient avoids note fatigue.
- 🔒 Does NOT introduce blocking, a planning lock, or a denial of
  the edit. ADR-0020 invariant intact.

## Alternatives considered

- **A**: Block the first source edit until a draft exists. Rejected:
  contradicts ADR-0020 (hooks inform, never block) and creates the
  exact "planning lock" failure mode the overhaul removed.
- **B**: Make the assistant re-read the planning convention on every
  Edit. Rejected: noise; defeats the per-session inject-once design.
- **C**: Detect draft *coverage* — parse `## Changes` and warn when
  the file being edited isn't listed. Out of scope: requires plan-body
  parsing in bash and incorrect rejection on legitimate refactors;
  file as TODO if the simpler anchor proves insufficient.
- **D**: Add a hard rule to CLAUDE.md only (no hook change). Rejected:
  the failure mode is precisely that the static reminder was already
  present and did not catch the moment. The hook needs to anchor to
  the file being edited.

## Verification

- `grep -F "About to edit" templates/hooks/pre-write.sh
  .claude/hooks/pre-write.sh` returns the new NOTE in both copies.
- `grep -F "Approval is for Phase 2" CLAUDE.md` returns the addendum.
- `bash tests/inform-never-block.sh` continues to pass — the hook
  still emits `permissionDecision: "allow"` and exits 0.
- Behavioral check (manual, single round): in a fresh session, request
  a non-trivial change with no `/plan`; on the first Edit attempt, the
  injected note should name the target file and the missing plan, and
  the assistant should transition to Phase 2 (write draft) rather than
  proceeding with edits.

## Amendment 2026-06-02: trivial-skip must be declared

In dogfooding ADR-0023 (a README update was about to land without a
plan), the user asked whether the skip was a forgetful drift or a
deliberate trivial-judgement. The skip was deliberate (doc-only edit,
inline-eligible per CLAUDE.md), but the *judgement was silent* — and
a silent skip is indistinguishable from the failure mode ADR-0023
addresses. Added to CLAUDE.md "Workflow": when the assistant decides
a request is inline-eligible, it states that judgement explicitly in
one short sentence before editing (e.g. *"Trivial — no plan,
proceeding inline."* / *"טריוויאלי, לא צריך תכנון, עובר לביצוע."*).
Visible judgement is correctable; silent judgement is not.
