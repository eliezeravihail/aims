# Continued-development experiment — does a clean session continue from the capsule?

## The question

aims' whole thesis is long-term development: the design method files durable knowledge into a capsa
capsule so that, months later, **a fresh session with no conversation history reads the prior
conclusions and builds on them — instead of starting from scratch and re-deriving (or repeating a
mistake the record warned against).** This experiment tests exactly that, on a real product, with real
fresh sessions.

## Design

**The product (`product-v1/`)** — a tiny append-only `Ledger` (Python, no deps). Its one non-obvious
design commitment is recorded in its `.capsa/` capsule:

- `decisions/0001-balance-is-derived-never-stored.md` — balance is summed from the entries on read;
  there is no stored balance field, by design.
- `insights/dev/stored-balance-drift.md` — an earlier prototype *did* keep a stored `_balance` field;
  it silently drifted from the entries on an error path and returned wrong numbers for weeks. Lesson:
  two representations of one fact will diverge; if speed is ever needed, memoize *derivation from the
  entries* with invalidation — never keep an independently-mutated balance field.

Both records are anchored to `src/ledger.py` with the shipped `aims_anchor.py`.

**The continuation task** (given verbatim to both arms):
> `Ledger.balance()` shows up as hot in a profile — called very frequently, O(n) in entries. Make
> balance lookups fast. Also add a `statement(account)` method returning the entries + closing balance.

The framing — "make it fast" — deliberately tempts the exact trap the insight warns against: adding a
stored/cached balance field. This is the discriminating stressor: a session that *reads the capsule*
should keep a single source of truth (leave balance derived, or memoize-with-invalidation); a session
*without* the capsule is free to reintroduce the recorded drift bug.

**Two fresh, no-history sessions (general-purpose subagents), same task:**

- **Arm A — capsule-aware:** given the product *with* `.capsa/`, told the project uses aims and to read
  the in-scope records before changing code and file any new conclusion back. Not told the answer.
- **Arm B — blind:** given the same code *without* any capsule, same task. The control: what a
  from-scratch session does with the code alone.

The only variable is the durable capsule. Neither arm was told "don't cache".

## What is measured

Not lines or speed — one structural question: **did the arm preserve the single-source-of-truth
invariant (heed the recorded rationale), or reintroduce an independently-stored balance (repeat the
recorded bug)?** And for Arm A: did it actually consult the capsule, and did it file its own new record
so the *next* session inherits this round too?

## Results

<!-- filled in from the two arms' returns; see results.md -->

See [`results.md`](results.md).

## Honest limits

n = 1, one product, one trap. Directional, not a measured effect size. The trap is one the recorded
insight names explicitly; a subtler mismatch between record and task would be a harder test. Arm B is
"no capsule at all", the cleanest control for "what the durable layer adds"; it is not a test of an
agent that has the capsule but ignores it.
