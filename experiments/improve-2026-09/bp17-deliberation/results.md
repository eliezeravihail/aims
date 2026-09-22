---
title: "[WITHDRAWN] BP17 result — NULL (4/4 both arms): the code's SHAPE encoded the decision, and the records arm misjudged its own counterfactual"
date: 2026-09-22
status: WITHDRAWN — the records in this run were written by hand, not filed by aims, so it tested that construction rather than aims (AUDIT-record-layer-claims.md).
---

# Result

| arm | append-only kept | net zero (floor) |
|---|---|---|
| r1 / r2 / r3 (records) | **4/4 each** | OK |
| n1 / n2 / n3 (no records) | **4/4 each** | OK |

Every arm appended a linked compensating entry and left the original untouched. Nobody mutated, deleted, or
flagged.

# What leaked this time: structure, not prose

The no-records arms named exactly what told them:

- n1: *"rejected because the class is an append-only journal (`_entries` is only ever appended to,
  `entries()` hands back a copy, `Settlement`/`Payout` are `frozen=True`); erasing history would also break
  the existing `get()` contract."*
- n3: *"`entries()` is a public accessor callers may already be relying on for a full record"*; a `reversed`
  flag would be *"a breaking change to the frozen dataclass."*

I removed the declarative docstrings this time, but the **shape** of the code still carried the decision:
an append-only list, frozen value objects, and a public full-history accessor. A capable reader reconstructs
the conclusion of the deliberation from the structure that the deliberation produced.

# The sharper finding: self-reported counterfactuals are wrong

Both r1 and r2 stated plainly that the record was decisive:

> *"from the module alone, mutate-in-place looks obviously simpler and I would likely have chosen it."*

**They were wrong.** Their blind counterparts, with no record at all, chose the identical design. The agents
sincerely believed the record changed their choice; the control proves it did not.

**An agent's report that "the record decided this" is not evidence that it did.** Only a control arm is. This
is a caution that applies to the whole method: every prior round where a records-arm agent cited an ADR as
decisive (BP15, BP15b, BP16, BP16b) is subject to exactly the same illusion, and in every one of those the
control also matched.

# The record-layer arc: six attempts, six nulls, six different leaks

| round | what was documented | what leaked it to the blind arm |
|---|---|---|
| I5 | a rejected trap | a visible in-code precedent |
| BP15 | three local behaviours | they were **industry norms** |
| BP15b | three counter-normative behaviours | the change **never entered that code** (wrap, not rewrite) |
| BP16 | project conventions | I wrote them into the code's **docstrings** |
| BP16b | same, docstrings stripped | **one usage example** was enough to infer them |
| BP17 | a genuine deliberation (why A not B) | the code's **structure** encoded the outcome |

# The honest conclusion

> **A well-formed codebase encodes its own decisions.** Structure, immutability, accessors, and existing
> usage all carry design intent, and a capable reader reconstructs the *conclusion* of a deliberation without
> ever seeing the deliberation.

That bounds where a record can matter to a narrow band: the code's shape must genuinely **underdetermine**
the choice *and* the rationale must be **external**. Six deliberate attempts failed to construct that band at
module scale — which is itself evidence about how narrow it is, at least for a capable reader on a small,
coherent codebase.

What this does **not** establish: that records are worthless at scale, across many hands, over long spans, or
on codebases too large or incoherent for a reader to reconstruct intent from shape. Every test here was a
single small module read in full by a strong model. That remains the untested regime — and it is the one
aims' record layer actually claims.

The one positive signal in the whole arc stays BP15/BP15b's blind design-quality read: records did not change
*which* decision was reached, but the records arms produced **structurally better new code** (33.3 vs 29.0
mean, worst case 30 vs 20) — a floor-raising effect, not a decision-changing one.
