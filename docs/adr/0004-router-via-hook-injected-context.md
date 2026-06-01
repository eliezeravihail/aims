# ADR-0004: Router via hook-injected context, not orchestration
Status: superseded by ADR-0015
Date: 2026-05-06
Supersedes: —
Superseded by: ADR-0015

## Context

Users open Claude Code and paste a bug log, ask an open-ended question, or
say "build me X" — without choosing a workflow. Two failure modes follow:

- The model dives into edits prematurely (no plan, no decision record).
- The user has to remember which slash command applies, and stops using
  them when they don't.

We want the system to act like a router/secretary: detect the intent, ask
the user which workflow to apply, then run it. Doing this with another LLM
agent re-introduces the orchestration overhead ADR-0002 just rejected.

A `UserPromptSubmit` hook can run deterministic shell logic and emit
`additionalContext` that Claude Code injects into the prompt before the
model processes it. That gives us a free routing layer with no extra LLM
calls.

## Decision

The `prompt-submit.sh` hook acts as a **deterministic intent classifier**;
the running Claude session acts as the **conversational router**.

- The hook detects intent by regex against the user's prompt: `bug`,
  `feature`, `refactor`, `decision`, `mechanical`, `question`, or none.
- On a match, the hook emits a JSON object with `hookSpecificOutput
  .additionalContext` containing instructions for the model: "Call
  `AskUserQuestion` with this menu before doing anything; then proceed
  per the user's pick using the matching slash command's discipline."
- The hook **suppresses itself** in cases where routing would be noise:
  prompt starts with `/` (user already chose), a planning lock is active,
  or a short follow-up arrives during an in-progress plan.
- After the user picks an option, Claude follows that workflow's
  discipline (e.g. for `/plan`: create the lock, do read-only exploration,
  end with ExitPlanMode, then write the plan to `docs/plans/`). The model
  cannot literally invoke a slash command from inside its own turn; it
  emulates the discipline instead, which is equivalent for this purpose.

## Consequences

- ✅ Zero added LLM calls and zero added latency for the routing layer —
  the hook is a few hundred bytes of shell.
- ✅ Discipline kicks in even when the user types informally. The system
  no longer relies on the user remembering to type `/plan`.
- ✅ The router stays out of the way for follow-ups, slash-prefixed
  prompts, and ongoing plans, so it doesn't become annoying.
- ⚠️ Regex-based intent detection has false positives and false negatives.
  We accept this — the worst case is one extra `AskUserQuestion` round, or
  a missed routing opportunity that the user catches manually.
- ⚠️ The hook cannot block; if Claude ignores the injected instruction
  and dives into edits anyway, only the `pre-write` hook's planning-lock
  check (ADR-0003) catches it. We rely on that backstop.
- 🔒 Closes the door on a multi-step LLM router (an "intent agent" that
  classifies before dispatching). That would resurrect the orchestration
  costs ADR-0002 rejected.

## Alternatives considered

- **Multi-step LLM router** (small model classifies, larger model
  executes) — rejected: token amplification + a new failure surface for
  the same outcome we get from regex + injected context.
- **Skill that activates on triggers** — rejected: skills don't fire
  before the model reads the prompt, so the model could already be
  formulating a response when a skill notices the intent. The hook fires
  pre-prompt and reliably gates the model's first action.
- **Always-on AskUserQuestion**, regardless of intent — rejected as
  noise. Quick chat ("thanks, that worked") would also get routed.
- **Prompt-prefix conventions** ("bug:", "feat:") — rejected: requires
  user education and discipline; the whole point is to remove that.

## Verification

- `templates/hooks/prompt-submit.sh:52-87` contains the regex
  classification table (one branch per intent).
- `templates/hooks/prompt-submit.sh:91-122` builds the
  `additionalContext` block listing the per-intent menu.
- `templates/hooks/prompt-submit.sh:32-50` enforces the suppression rules
  (slash-prefix, planning lock, short follow-up).
- Smoke-test results recorded in PR #11 thread: 7 actionable intents
  classified correctly, 3 suppression cases stay silent.
