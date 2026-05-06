# ADR-0003: Hooks default to nudge, planning lock always blocks
Status: accepted
Date: 2026-05-06
Supersedes: —
Superseded by: —

## Context

The plugin installs three hooks via `/init-workflow`: `SessionStart`
(informational), `UserPromptSubmit` (trigger nudges), and `PreToolUse` on
Edit/Write (the only one that can actually block work).

Two questions arose during design:

1. Should the `PreToolUse` hook block writes by default, or only nudge?
2. How do we make `/plan`'s read-only exploration enforceable, given that
   nothing in Claude Code natively prevents Edit/Write while a slash
   command is running?

Aggressive defaults risk a "hook that wants to be off" — users disable it,
then lose the value entirely. Permissive defaults risk discipline that
nobody actually follows. And `/plan` is worthless if the model can simply
write files mid-exploration.

## Decision

We split the two cases:

1. **The planning lock always blocks.**
   `/plan` creates `.claude/.planning-lock` as its first action. The
   `PreToolUse` hook checks for this file unconditionally and exits 2
   when present, regardless of mode. This is non-negotiable: it's the
   only mechanism that makes `/plan` actually read-only.

2. **The source-path check defaults to `nudge`.**
   The check that requires an in-progress plan when editing `src/`/`lib/`
   /`app/` is gated by `.claude/ais-mode`. Default value, written by
   `/init-workflow`, is `nudge` — the hook prints a warning to stderr
   but exits 0 (allows the edit). Users can upgrade to `block` once they
   feel the pain themselves.

## Consequences

- ✅ `/plan` is meaningfully read-only. Edit attempts during planning fail
  deterministically without LLM judgment.
- ✅ New users don't get blocked from doing trivial work. The plugin
  earns trust via reminders before it imposes constraints.
- ✅ Mode change is a single line: `echo block > .claude/ais-mode`.
  No re-init, no settings.json edit.
- ⚠️ Users who never upgrade to `block` get less protection than they
  could. We accept this — better a hook that's on in nudge mode than
  one that's off because it was too aggressive.
- 🔒 The lock file is a project-level concern, not user-level. Two
  parallel `/plan` invocations in the same checkout would collide.
  We accept this; nested planning is rare and the failure is loud.

## Alternatives considered

- **Block by default everywhere** — rejected: too aggressive for new
  users, especially in repos that don't fit the `src/`/`lib/`/`app/`
  layout assumption.
- **Nudge-only, including the lock** — rejected: defeats the purpose of
  `/plan`. The lock must be enforceable.
- **No lock, rely on prompt discipline** — rejected: the model can and
  does forget across long sessions. Deterministic enforcement is cheap.
- **Three-tier mode (off / nudge / block)** — `off` is included as a
  configurable in `/init-workflow` (it skips installing the hooks), but
  the post-install runtime mode toggle is binary (nudge | block) to keep
  the CLAUDE.md doc and `.claude/ais-mode` simple.

## Verification

- `templates/hooks/pre-write.sh:38-47` checks `.claude/.planning-lock`
  unconditionally and exits 2 before any mode-gated logic.
- `templates/hooks/pre-write.sh:22-23,50` reads `.claude/ais-mode`
  (default `nudge`) and short-circuits to allow when mode != block.
- `templates/CLAUDE.md.tmpl` "Hooks" section documents both behaviors.
