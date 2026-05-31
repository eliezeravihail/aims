# ADR-0016: Per-prompt memory node auto-injection
Status: proposed
Date: 2026-05-31
Supersedes: —
Superseded by: —

## Context

ADR-0007 + ADR-0008 + ADR-0012 + ADR-0014 build a curated memory tree whose
**bodies** hold the durable per-module knowledge (purpose, invariants,
pointers, known issues) and whose `code:` entries are fnmatch globs. But up
to this ADR **the bodies only reached the model when the model thought to
grep for them** — `session-start.sh` injects only the root README. A user
who opens a session and asks "what about file X?" gets the same blank stare
they'd get without aims: the model has to be told to look, even when X is
tracked by a node whose body explains exactly what X does and how to edit it.

ADR-0015 made the same hook (`prompt-submit.sh`) responsible for auto-engaging
`/plan`. Extending it with a memory scan in the same emission is the natural
splice point.

## Decision

The `UserPromptSubmit` hook (`prompt-submit.sh`) does **three jobs in one
emission**: existing router + auto-engage (ADR-0004 + ADR-0015), plus a new
**memory injector**. For every memory node whose `code:` glob is plausibly
referenced by the prompt, inject that node's body (frontmatter stripped) as
part of the single `additionalContext` block.

Glob → prompt matching (matches the fnmatch semantics of ADR-0014):

- Strip a `:line-range` suffix from each `code:` entry.
- Derive the **literal prefix** of the glob — everything before the first
  `*`, `?`, or `[`. If the prefix is ≥ 4 chars, substring-match the prompt.
- For entries that have no glob metacharacters at all (the literal == the
  entry), additionally word-match the prompt against the **bare basename**
  if it's ≥ 5 chars. This catches users who write "lint.sh" without the
  full path.

Bounds and discipline:

- **Per-session de-dup** via `.claude/memory/.injected-<session_id>` so a
  node lands at most once per session. Stale state files pruned after 7 days.
- **SIZE_CAP=8192** total injected bytes per turn.
- **No-op gates.** Skip when `docs/memory/` is missing, when `_lib.sh` isn't
  installed, when no node matches, when the prompt is shorter than 8 chars,
  or when the existing router suppressions trip (slash prompt, planning
  lock, short follow-up during an active plan, empty prompt).
- **Lock + memory are independent.** A pure-question prompt that references
  a tracked file gets memory injection only — no planning lock, no
  auto-engage text. An actionable prompt gets both.
- **Deterministic bash.** No LLM, no network — same constraint as ADR-0009.

The injection text is prefixed with an `[aims-memory]` banner instructing the
model to treat the node body as a navigator and not to restate it verbatim.

## Consequences

- ✅ The original aims promise lands: a prompt that mentions a tracked file
  arrives at the model with the node's documented context already in hand —
  no extra round-trip, no "which file?" follow-up.
- ✅ Pays off the consolidation loop directly. Empty bodies still inject
  (and do nothing useful); filled bodies become user-facing value on every
  relevant turn.
- ✅ One-emission contract keeps router + memory coherent. Lock semantics
  unchanged (only created when intent is actionable).
- ✅ Pure-question turns about files still benefit — the node body lands
  without forcing the user into the /plan flow.
- ⚠️ Literal-prefix heuristic can false-positive on common prefixes (a node
  with `code: docs/*` would inject on any prompt mentioning `docs/`).
  Mitigated by `LIT_MIN_LEN=4` and `SIZE_CAP`; worst case = one irrelevant
  body once per session per node.
- ⚠️ Token cost grows with tree size and prompt vocabulary. The cap is the
  governor; users tune `SIZE_CAP` or `AIMS_MEMORY_DIR` per project.
- 🔒 Rules out LLM-driven per-prompt retrieval (anything beyond glob
  substring matching belongs in a different ADR).

## Alternatives considered

- **SessionStart-only injection of the IDE-open file.** Rejected: Claude
  Code's SessionStart payload may not expose the open file, and a one-shot
  at session start doesn't help mid-session references.
- **Separate hook for memory injection.** Rejected: two hooks emitting
  `additionalContext` on the same event are order-dependent and fragile.
  One hook, one emission.
- **LLM-ranked retrieval.** Rejected by ADR-0009's deterministic-bash
  constraint.

## Verification

- `bash -n templates/hooks/prompt-submit.sh && bash -n .claude/hooks/prompt-submit.sh`
  → clean; `md5sum` pair identical.
- Smoke 1 — `question` intent + prompt mentioning a tracked path → emission
  contains `[aims-memory]` and the node body, NO `[aims-router]`, NO lock.
- Smoke 2 — actionable intent + tracked-path mention → emission contains
  BOTH `[aims-memory]` and `[aims-router]`; `.claude/.planning-lock` created.
- Smoke 3 — slash prompt → silent.
- Re-running the same `session_id` does not re-inject already-listed nodes
  (de-dup); state file lists every previously-injected node.
