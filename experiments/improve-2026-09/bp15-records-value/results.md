---
title: "BP15 result — NULL, and the null is about the experiment design: the decisions were industry norms"
date: 2026-09-22
---

# Result: 4/4 in both arms — no signal

| arm | decision survival |
|---|---|
| r1 / r2 / r3 (code **+ records**) | **4/4 each** |
| n1 / n2 / n3 (code only) | **4/4 each** |

The no-records arm preserved every documented decision, and said so unprompted — it reported being "careful to
preserve" the idempotent replay, the sorted payee order, and the degenerate zero-weight case.

# Why the experiment could not have detected anything (the real finding)

Each of the three "doubt-laden" decisions was in fact an **accepted norm of the field**, and/or visible in the
code as behavior to preserve:

- **0001 (tie-break by `payee_id`)** — deterministic sorting for reproducibility is standard practice, *and*
  the tie-break is literally in the code (`sort(key=lambda t: (-r, id))`). No arm rewrote `_allocate`; they all
  wrapped it, so the tie-break survived for free.
- **0002 (retain zero rows)** — "do not silently drop rows" is the default expectation, and nothing in the
  change request tempted filtering.
- **0003 (repeat settle returns the stored result)** — this is the canonical payments **idempotency-key**
  pattern. A competent engineer preserves it without being told.

A record can only be load-bearing where the **competent default points the other way**. Documenting the norm
proves nothing: the no-record arm reaches the same place by professional instinct. This is I5's confound in a
new costume — not "records don't work", but "this test cannot see whether they work".

# The corrected design (BP15b)

Decisions must be **counter-normative**, so that absent the record the modifier actively "fixes" them, and the
code must *look like a defect*:

| # | decision (against the norm) | the code looks like | rationale that lives ONLY in the record | how the change stresses it |
|---|---|---|---|---|
| C1 | a repeat settlement **recomputes and overwrites** | a missing-idempotency bug | upstream issues corrections; the downstream ledger is append-only, latest-wins | modifier adds an idempotency guard |
| C2 | the remainder goes to the **largest-share payee** | a systematic-bias / fairness bug | contractual: the lead partner absorbs rounding | modifier "fixes" it to id-order or round-robin |
| C3 | zero-amount rows are **dropped** | silently discarding data | the payment rail rejects zero-amount transfers | the fee pushes payees to zero → modifier restores the rows |

Same measurement (decision-survival probes never shown to the arms, plus a blind §0–§14 read). Same blind
arms. The difference is that a wrong choice is now the *default* choice, so the record has something to carry.

# Status
Recorded as a null **about the instrument**, not about the record layer. BP15b is the valid test.

# ADDENDUM — the blind design-quality read: records 37/40 vs no-records 25/40

Decision-survival was null (norms), but the **correct measure** — a blind §0–§14-style design rubric scored
from the code — found a real difference. The judge was blind to arms and independently discovered the six
files were only two distinct texts:

| blind label | actually | rubric total (/40) |
|---|---|---|
| A, C, E | **r1/r2/r3 — with records** | **37** |
| B, D, F | **n1/n2/n3 — no records** | **25** |

**The property the judge named as decisive:** whether the preview path *can physically reach* the settlement
store. The records arm made `settle_preview` a free function with no `self` — structurally unable to touch
`_done`; the no-records arm made it an instance method, separated by discipline only. That is precisely what
`decisions/0003` instructed ("a preview must not write to the store and must not read a stored result; keep
the paying path and the previewing path distinct"). **The record produced the structure.**

Honest caveats:
- **n=1 per arm, not 3.** Each agent emitted byte-identical output across its three directories, so this is
  one design per arm — suggestive, not a rate. BP15b re-runs with an independent agent per directory.
- Both arms failed **Open/Closed equally** (a second deduction reopens the owner in both) — the records did
  not buy extensibility here.
- The no-records arm was **ahead on one point**: it validated the `platform_fee_bps` range, which the records
  arm left open (a fee > 10000 bps silently yields negative amounts that still sum correctly).

**Reading:** on this product the record layer did not change whether *norms* survived — it changed the
**design quality of the new code**, by telling the modifier what the new entry point was allowed to touch.
