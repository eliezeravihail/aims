---
title: "BP21 — does the code-first gate stop records restating the code, without losing what the code cannot hold?"
date: 2026-09-22
goal: 2 (knowledge that does not belong to the code)
---

# The gap this tests

aims' second goal is **knowledge that does not belong to the code** (`../../../goals.md`). The filing
guidance did not enforce the *"does not belong to the code"* part. `design-record.md` asked **which home**
(companion vs root record) and whether the knowledge was **durable**, but never **should this be in the
code instead**. Its only nearby clause — *"if the code and its own documentation already carry it, do not
file it"* — is a **redundancy** test, not a **placement** test, and it sat in the last section.

The fix (`../../../decisions/0022-…`) adds a **First gate**: before choosing a home, ask whether a
docstring, a comment, a name, a signature or a test should carry it. One-line test: *if you could delete
the entry, write it as a docstring, and lose nothing, it was a docstring.*

# The control, and why it is clean

`../bp19-aims-filed-records/build/flags.py.md` was filed **by the real skill, before this gate existed**,
for exactly this `flags.py`. It is an uncontaminated before-arm: 13 entries, 54 lines.

# Run 1 — the gap is real (blind), but the run was confounded

A blind auditor was given `flags.py`, `test_flags.py`, and two anonymized candidate documents — no labels,
no provenance — and asked, per entry: **is this recoverable from the code?**, requiring a `file:line` quote
for every RECOVERABLE verdict.

| | entries | RECOVERABLE | PARTLY | NOT-RECOVERABLE |
|---|---|---|---|---|
| **X** = filed under the **old** guidance | 13 | **8 (62%)** | 2 | 3 |
| **Y** = filed under the **new** gate | 1 | 0 | 0 | 1 |

**The gap is confirmed, blind and with citations.** Eight of the old companion's thirteen entries restate
the module's own docstrings — e.g. its *"the product rule is an ordering over the verdicts that apply…
nothing answered, so it is off"* against `flags.py:176-177` *"The strongest verdict among the rules that
apply decides it. A flag no rule speaks about is off."* I verified one independently before trusting the
judge: `flags.py:103` does carry the `hash()`-is-salted rationale, and `test_flags.py:140` pins it with
`PYTHONHASHSEED`.

**But run 1 cannot credit the gate**, and the judge said so plainly: *"Y's ratio is entirely an artifact of
length… 100% non-recoverable across a single bullet is not a quality signal — it is what happens when a
file contains one bullet."* The confound is **mine**: I handed the new arm only **4** design-history items,
**3** of which the code carries. It never held the material behind X's genuinely valuable entries. The
judge also named the live risk precisely — *"Y has no Insights and no Decisions sections at all… as
documentation of this module it is radically incomplete."*

# Run 2 — matched history, prediction fixed in advance

Same code, same guidance, same instructions. The arm now gets the **full** design history: **14 items**
(a–n) in one undifferentiated list, the code-carried and the non-recoverable mixed together, with nothing
marking which is which. Prediction recorded before the arm ran ([`run2/PREREGISTERED.md`](run2/PREREGISTERED.md)):
**drop a–h (8, the code carries them), keep i–n (6, it cannot).** Stated as falsifiable either way — the
gate *fails* if it also drops the rejected alternatives or the unproven assumptions.

**Result: 8/8 dropped, 6/6 kept. The prediction matched exactly.**

| kept | what it is |
|---|---|
| i | the rejected if-chain `Resolver`, and the failure mode that rejected it |
| j | the rejected `Decision(ON/OFF)` enum |
| k | the rejected value-object / exception types |
| l | 10_000 vs 100 buckets — the counterfactual *and* its irreversibility |
| m | three behaviours **never confirmed with anyone**, stated as unproven |
| n | the dropped flag→rules index, its price, and the unproven "rule sets stay small" assumption |

Dropped, each with the docstring/guard/test that already carries it: the precedence-one-home framing,
order-independence, the `hash()` rationale, abstention/default-off, the bucket contract,
validate-at-construction, the frozenset copy.

# The convergent check that makes this more than n=1

The run-1 judge, **blind, and before run 2 existed**, wrote what the ideal file would be:

> *"If the two were merged, the right file would be X's entries 9–13 plus Y's single entry — six bullets,
> no restatement."*

That is **exactly** what the gate produced: X's 9, 10, 11, 12, 13 (= i, j, k, l, m) plus the index (= n).
Six bullets, no restatement. An auditor who did not know the gate existed, reasoning only from "what can a
reader not get from the code", independently specified the output the gate generates.

# Verdict

**The gate passes.** It removes restatement (62% → 0% of entries) and, on matched material, keeps every
category the code cannot hold — including the two the run-1 judge called the most valuable in either file:
the rejected alternatives and the labelled unproven assumptions.

# Limits, honestly

- **n = 1 product, one module, one filing agent per arm.** Directional. `PROTOCOL.md` §3 wants n ≥ 2 for a
  load-bearing wording change.
- **The history was handed to the arm as a list.** A real session derives it from its own work, where the
  code-carried items are exactly the ones freshest in mind and hardest to let go of. Untested.
- **The failure mode run 1 exposed is not disproven, only unobserved here** — a gate that reads as "file
  less" could suppress a rejected alternative nobody wrote down. Run 2 had the alternatives spelled out in
  its input; an agent that must *remember* them may drop them. This is the next test.
- **Both runs used the same model.** A weaker executor may read the gate as permission to file nothing.
