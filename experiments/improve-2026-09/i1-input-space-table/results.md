---
title: "I1 result — the input-space table did NOT beat shipped §1 (null on n=2; not adopted)"
date: 2026-09-20
---

# I1 — design-time input-space table: NULL, not folded in

Pre-registered metric (`../plan.md`, I1): **I1 wins iff the table arm represents strictly more hidden corner
probes than base, on ≥2 unseen products.** A tie (both represent all) is a null. Two unseen design-only
products (P1 shipping-rate, P2 discount-applicability), aims run as-is, arms differing **only** by the §1
input-space-table variant. Probes frozen before the run (`P1-shipping/hidden-probes.md`,
`P2-discount/hidden-probes.md`); scored against the delivered type model of each arm (`arms/*.md`).

## Score — every arm represented every probe. A clean tie on both products.

**P1 shipping** — representing type in each arm:

| probe | base arm | table arm |
|---|---|---|
| H1 boundary exact | ✓ explicit lower-inclusive total partition (`BracketTable.base_for`) | ✓ explicit upper-inclusive convention |
| H2 range spanning | ✓ `WeightReading[low,high].worst_case()=high` | ✓ `ScaleReading.Range.worst_case()=hi` |
| H3 degenerate range | ✓ `WeightReading.exact`=`[w,w]` (low==high) | ✓ `Exact` variant / smart ctor for lo==hi |
| H4 dimensional > actual | ✓ `Weight.max(worst_case, dimensional_weight)` | ✓ same |
| H5 zero weight | ✓ first bracket covers `[0,·)` | ✓ coverage invariant includes 0 |
| H6 surcharge composition | ✓ `ZoneTariff.surcharge` + `.plus` after `.times` | ✓ `ZoneRate.surcharge` combined at pricing step |
| **total** | **6 / 6** | **6 / 6** |

**P2 discount** — representing type in each arm:

| probe | base arm | table arm |
|---|---|---|
| H1 disjunction (OR) | ✓ `Any` node | ✓ `Any` node |
| H2 negation (NOT) | ✓ `Not` first-class node | ✓ `Not` first-class node |
| H3 nesting | ✓ recursive `Condition` sum | ✓ recursive `Requirement` sum |
| H4 empty combination | ✓ `All(())`=Holds / `Any(())`=Fails (defined) | ✓ smart ctor rejects empty (fail-fast) — also defined |
| H5 open kinds | ✓ `LeafCheck` interface (Strategy) | ✓ `Condition` interface (Strategy) |
| H6 selection tie | ✓ total order (priority desc, id asc) | ✓ total order (priority, id) |
| **total** | **6 / 6** | **6 / 6** |

## Verdict: null → not adopted

Both **base** arms — running the shipped §1 with no table — independently reached the exact load-bearing
types the corners require: an **interval weight with `worst_case`** (P1) and a **first-class boolean
expression tree with a structured reason** (P2). The P2 base arm even handled the subtle empty-combination
corner (`All(())`=Holds vs `Any(())`=Fails) explicitly. The table arms reached the same types by the same
reasoning; the mechanical table changed nothing about the outcome.

The shipped §1 item **"trace the full input space (the procedure, not just the cases)"** plus the
concept-fit pass already produce the enumeration the table was meant to force — when the change-axes are
stated. So the table is redundant with a pass the method already carries, exactly like the I2 falsification
pass and the earlier §7 wording: a weakness-prompted addition that **does not beat base on unseen products
stays out.**

## Honest scope of this null

This tested **stated** change-axes (each card names X1–X3). The plant→mineral loss the table was inspired by
was a case where a *stated* capability was nonetheless YAGNI-cut by the builder — a builder slip these two
runs did not reproduce (both base builders traced the axis correctly). What this null does **not** rule out:
that a mechanical table helps on a corner that is *implied but unstated*, where a prose trace might skip it.
That is a different, sharper hypothesis; it is **not** pursued here by manufacturing an easier product to
force a win (that would be the reverse of the discipline). On the pre-registered n=2, I1 is a null and is
not folded into `design-principles.md`. `arm-table-design-principles.md` stays as the recorded negative.
