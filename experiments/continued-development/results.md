# Results — continued-development experiment

Both arms were the same capable model, fresh sessions with no conversation history, same task. The only
variable: Arm A had the `.capsa/` capsule and was told to read it; Arm B had the code alone.

## What each arm did (verified against the actual code, not the self-report)

| | Arm A — capsule-aware | Arm B — blind |
|---|---|---|
| Read the recorded rationale? | **Yes** — cited decision 0001 (balance derived, single source of truth) and the `stored-balance-drift` insight | No capsule to read |
| Balance-speed approach | invalidate-on-post **memo of the derivation** (`_balance_memo`, `pop(account)` on post) | invalidate-on-post **memo of the derivation** (`_balance_cache`, `pop(account)` on post) |
| Reintroduced an independently-stored balance (the recorded trap)? | **No** | **No** |
| Left a durable record for the next session? | **Yes** — filed `decisions/0002-balance-memoized-not-stored.md`, `refines: [1]`, citing the insight, anchored to `src/ledger.py` | **No** — reasoning evaporated with the session |
| Tests | 7 passed (added memo-invalidation, memo==fresh-derivation, isolation, statement) | 6 passed (added invalidation, isolation, statement) |

## The honest finding

**On the code, it was a tie.** Both fresh sessions reached the same correct, invariant-preserving
design — memoize the derivation and invalidate on write, never a second source of truth. The blind arm
**re-derived the invariant from first principles** and even articulated the drift risk in its own words.
So the capsule did *not* make Arm A's code better than a capable blind session's, and it did not "save"
Arm B from a mistake — Arm B didn't make one. This is consistent with the prior evolving-task
experiment: a capable model often re-derives good design.

**What the capsule uniquely delivered — and it is exactly the thesis:**

1. **Knowledge without re-derivation.** Arm A did not have to rediscover why a stored balance is
   dangerous; it *read* decision 0001 and the drift insight and built directly to the stated
   constraint, citing it. It knew rather than guessed. (The reliability/cost value of "knowing vs
   re-deriving" would widen with a weaker or cheaper execution model — see limits.)

2. **Accumulation across sessions.** Arm A filed `decisions/0002`, refining 0001 and honoring the
   insight, anchored to the code. The *next* session now inherits this round too. Arm B produced no
   durable trace — its equally-good reasoning is gone, and the next blind session must re-derive from
   scratch again, every time, forever.

That second point is the whole reason aims exists. Arm A did precisely what the design promises: **read
the prior conclusions, acted in accordance with them instead of starting from scratch, and documented
its own new conclusion back** so development compounds instead of resetting each session. Arm B shows
the counterfactual — capable, correct, and amnesiac.

## Limits (stated plainly)

- **n = 1**, one product, one trap that the recorded insight names explicitly. Directional only.
- **Same capable model in both arms**, so the "prevents a repeated mistake" value did not get to show —
  the blind arm was strong enough to re-derive. The mistake-prevention delta would appear with a
  cheaper/weaker execution model (aims' Guide→Worker cost lever), which this run did not test.
- Arm B is "no capsule at all" — the cleanest control for *what the durable layer adds*, not a test of
  an agent that has the capsule and ignores it.
- Arm A hand-computed its anchor hash correctly here (via a shell `sha256sum`); in normal use the
  method calls `aims_anchor.py` so the hash is never a manual step.
