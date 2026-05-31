# ADR-0015: `/plan` auto-engages on edit intents and writes a draft to disk before approval
Status: proposed
Date: 2026-05-31
Supersedes: ADR-0004
Superseded by: —

## Context

ADR-0004 routed edit-intent prompts by injecting a context menu and
asking the user to pick a workflow (`/plan`, inline, `/grunt`). The menu
turned out to be both noisy and skippable — every actionable prompt cost
the user a click, and the model could (and often did) drift past the
nudge and start editing directly. ADR-0010 narrowed the surface to
`/plan` + `/install-on`, which made the menu's "pick a workflow" choice
a no-op: there's only one workflow now.

A second issue compounded it: `/plan` itself materialized the plan to
`docs/plans/` only **after** approval. Two failure modes followed.
First, a context-compacted session that interrupted between "show plan"
and "user approves" lost the entire plan body; the next session had no
file on disk to recover from. Second, the harness's native
`ExitPlanMode` tool ran in a different code path — when the model chose
to use it, the harness presented the plan inline and the file never got
written, so close-out (Phase 4) and memory consolidation (ADR-0009)
both no-op'd because they look for `Status: in-progress` files.

## Decision

We will (1) **auto-engage** `/plan` from `prompt-submit.sh` on every
actionable intent (bug / feature / refactor / decision / mechanical /
ambiguous), reserving `question` as the sole bypass; (2) move `/plan`'s
materialize step in front of approval — Phase 2 writes the draft as
`docs/plans/<UTC-date>-<slug>.md` with `Status: draft` while the lock
is still held, Phase 3 is the approval gate that flips the status to
`in-progress` and removes the lock; and (3) add a `PostToolUse` hook on
`ExitPlanMode` (`templates/hooks/exit-plan-mode.sh`) that persists the
harness-presented plan body to the same path as a safety net. The
SessionStart hook gains an orphan-draft warning so a power-cut between
Phase 2 and Phase 3 surfaces on the next launch.

Boundary: this applies to slash-command-style harness sessions. CLI /
non-interactive callers (`bash .claude/hooks/*.sh` driven by scripts)
are not changed.

## Consequences

- ✅ One fewer click between an actionable intent and a reviewable
  draft on disk; the file IS the artifact to review.
- ✅ Plan body survives session interruption mid-Phase-2/3; the
  SessionStart warning + the lockfile together drive recovery.
- ✅ `ExitPlanMode`-style sessions no longer drop the plan on the floor.
- ⚠️ False-positive auto-engagements on imperatively-phrased questions
  ("explain the marker hook") will create a draft + lock. Mitigation:
  the per-prompt opt-out ("just patch it", `אל תתכנן`) is documented in
  the injected router text; aborting in-turn is one line of bash.
- ⚠️ Draft-on-disk before approval means an aborted plan leaves a file
  that must be `rm`-ed explicitly. The `Status: draft` warning at
  SessionStart catches that.
- 🔒 Rules out re-introducing the menu workflow without superseding
  this ADR.
- 🔒 Rules out delaying materialize past Phase 3 — that's the whole
  point of the change.

## Alternatives considered

- **Keep the menu, fix the materialize order only.** Rejected: the
  menu has zero options to choose between since ADR-0010, and the
  prompt-submit context window is precious.
- **Auto-engage but materialize after approval.** Rejected: doesn't
  fix the session-interruption hole, and doesn't help the
  `ExitPlanMode` path.
- **Drop `/plan` entirely; have the router do planning inline.**
  Rejected: keeps the Opus-vs-implementation model split (`/plan` runs
  on Opus per its frontmatter); inline planning loses that.

## Verification

- `bash tests/router-auto-plan.sh` — six cases covering auto-engage on
  bug, silence on question, suppression on slash-prefix, suppression
  during active lock, ambiguous-actionable fallback, and code-paste
  skip.
- `bash tests/exit-plan-mode.sh` — four cases covering the harness
  bridge.
- Manual: invoke a one-line edit-intent prompt and confirm the draft
  lands in `docs/plans/` BEFORE the approve/edit/abort question.
- Code anchors:
  - `templates/hooks/prompt-submit.sh` — auto-engage block
  - `templates/commands/plan.md` — Phases 2 / 3 / 4 / 5
  - `templates/hooks/exit-plan-mode.sh` — bridge hook
  - `templates/hooks/session-start.sh` — orphan-draft warning
