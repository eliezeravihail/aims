# ADR-0026: Stop-hook `decision: block` is the consolidation-continuation gate
Status: accepted
Date: 2026-06-11
Supersedes: —
Superseded by: —
Amends: docs/adr/0020-hooks-inform-never-block.md

## Context

ADR-0020 establishes that aims hooks **inform, never block** — they inject
factual `additionalContext` and let the user / model decide what to do. The
audit (docs/plans/2026-06-11-aims-audit-fixes-master.md) caught that the
Stop hook (`templates/hooks/stop-consolidate.sh`) emits
`{"decision":"block","reason":...}` whenever the throttle trips. Read
literally, this contradicts ADR-0020. No prior ADR documented the carve-out
that was always intended.

The reason it was always intended: blocking a *Stop* and blocking an
*Edit/Write* have **opposite valences**. Blocking an Edit/Write *refuses an
action*. Blocking a Stop *compels the model to keep working* — the Claude
Code Stop-hook contract treats `decision: block` as "do not end the turn,
here is the next instruction (`reason`)." Without it, the consolidation
prompt has nowhere to land.

## Decision

ADR-0020's "inform, never block" rule applies to the **PreToolUse-class
hooks**: `pre-write`, `post-edit-marker`, `prompt-submit`, `session-start`,
`pre-compact`, `session-end`. Those hooks must never refuse a tool call;
they only inject factual context.

The **Stop hook** is exempt. Its `decision: block` is a **continuation
signal**, not a refusal. The `reason` field carries the consolidation
prompt that the model then executes in-band. After bumping
`.last-consolidated` (the throttle state), the hook returns the block-JSON
exactly once per throttle-trip.

Hooks added in the future that use `decision: block` for *refusal-style*
gating — i.e. preventing an action — are still forbidden under ADR-0020.

## Consequences

- ✅ The Stop-hook consolidation protocol (ADR-0009) stays intact.
- ✅ The "inform, never block" promise stays true for every edit-class hook
  (the surface a user actually interacts with).
- ✅ The carve-out is now reviewable: future Stop-hook additions must
  cite this ADR rather than reinventing it.
- ⚠️ Future Stop-hook additions must NOT smuggle in refusal semantics
  under `decision: block`. The contract is *continuation*, not *refusal*.

## Pointers

- `templates/hooks/stop-consolidate.sh` — the only hook that uses this
  carve-out today.
- ADR-0009 — in-band consolidation protocol that the carve-out enables.
- ADR-0020 — the rule this ADR amends.
- ADR-0024 — mutex protocol that the Stop hook hands to the model under
  this carve-out.
