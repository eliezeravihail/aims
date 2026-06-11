# ADR-0020: Hooks inform, they never block

Status: accepted (amended by 0026)
Date: 2026-06-02
Supersedes: ADR-0017 (in full), ADR-0019 (repurposed — see below)
Superseded by: —

## Context

aims enforced "plan before you edit" with a global filesystem lock
(`.claude/.planning-lock`): the `pre-write` PreToolUse hook returned exit 2
(hard block) on every Edit/Write while the lock existed (ADR-0015 auto-engage,
ADR-0017 carve-out for plan drafts). The memory subsystem added a per-leaf
sidecar `.lock` mutex that also hard-blocked concurrent node edits (ADR-0018 →
ADR-0019). In practice this produced a recurring class of friction: a path-
normalization bug made the lock block even the plan draft the carve-out was meant
to allow (esp. on Windows drive-letter paths); orphaned locks survived across
sessions; the prompt-submit router created locks on misclassified (often non-
English) prompts. The guiding intent of aims is **order and awareness, not
coercion** — a tool that can stop you from working contradicts that. Empirically
(probe 2026-06-02) and per the Claude Code hooks docs, hook `additionalContext`
reaches the model on `UserPromptSubmit`, `PostToolUse`, and `PreToolUse` (on
allow) — so awareness can be injected without any block.

## Decision

We will make every aims hook **inform, never block**: no hook returns a blocking
exit code for discipline reasons, and there is no `.planning-lock`, no `block`
mode, and no node hard-lock. A hook's only output is **factual** injected
context. The planning convention is injected as a factual note by `prompt-submit`
(UserPromptSubmit) and `pre-write` (PreToolUse, once per session on the first
no-plan source edit). Memory-node freshness is driven by `post-edit-marker`
(PostToolUse): it marks leaves dirty, injects a factual note naming the node to
update, and **repurposes the ADR-0019 sidecar `.lock`** from a hard mutex into an
**advisory marker** (session-id + mtime) — same session refreshes silently,
another session's marker older than `AIMS_NODE_LOCK_STALE_SEC` (default 3600s) is
taken over, a fresher one is reported so the model asks the user. This applies to
all aims hooks; consuming-project source and tests are untouched.

## Consequences

- ✅ The entire friction class disappears (path-normalization deadlock, orphan-
  lock ritual, auto-lock on misclassified prompts) — there is nothing to block.
- ✅ Project-agnostic: "source" is defined by exclusion (anything outside `docs/`,
  `tests/`, `*.md`, `.claude/`); no consuming-project path is hardcoded.
- ✅ Awareness is delivered at the moment of change (PostToolUse) and at prompt
  time (UserPromptSubmit) — both confirmed to reach the model.
- ✅ Cross-platform: `pre-write`/`post-edit-marker` now normalize Windows drive-
  letter / backslash paths and git-bash MSYS form (fixes the ADR-0017 carve-out
  bug at the root).
- ⚠️ Discipline is no longer enforced — the model can edit source without a plan
  or skip a node update. Accepted: the charter chooses informed order over
  coercion; the advisory `.lock` audit + review catch lapses after the fact.
- ⚠️ Injected text must be phrased as fact, never an imperative command, or
  Claude's prompt-injection defense surfaces it to the user. Standing authoring
  constraint on every hook message.
- 🔒 Rules out global write-locks and any exit-2 discipline gate in aims hooks.

## Alternatives considered

- **Keep the lock, fix the path bug**: rejected — even a correct global lock
  coerces, against the charter.
- **Declaration gate** (block source edits unless the editor declares
  `elementary:`/`bugfix:`): rejected — still coercion in a lighter coat.
- **Imperative reminders** ("CRITICAL: run /plan"): rejected — imperative hook
  text trips Claude's prompt-injection defense and is shown to the user instead
  of treated as context (verified 2026-06-02).

## Verification

- `bash tests/router-auto-plan.sh` — asserts the router never creates a lock and
  injects a factual note for actionable intents.
- `bash tests/marker.sh` — asserts post-edit marks dirty, injects a factual node
  note, and the advisory-marker concurrency behaves as specified.
- `bash tests/pre-write-inform.sh` — asserts no hook exits non-zero for any source
  edit and no `.planning-lock` is ever created.
- `grep -rnE 'exit 2' templates/hooks/*.sh` returns nothing.
