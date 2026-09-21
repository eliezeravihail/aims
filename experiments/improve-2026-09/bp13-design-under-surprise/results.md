---
title: "BP13 result — design quality is real and invisible to tests, but only the RIGHT surprise reveals it (reopen 4/4 vs 0/2)"
date: 2026-09-21
---

# BP13 — measuring design quality, not test-pass

Prompted by a correct critique: functional tests are a **floor, not the target**; a capable model makes tests
pass with any design. BP13 took **4 builds that all pass the tests but are badly designed** (the type-switch /
anemic-rules builds the aims review flagged in BP9) and asked whether the review's design verdict is *real* — by
hitting them with a surprise change and measuring the **design shape**, not test-pass.

## Part 1 — the wrong surprise (and my prediction failed, informatively)

Surprise change: add the **stacking policy** (priority + exclusivity). Prediction: the type-switch builds would
be forced to **reopen** `Engine.total`.

**Wrong.** All 4 type-switch builds **extended at a seam, 0 reopens, 19/19** — opus found a clever workaround: it
sorted the rules and detected each rule's contribution with a **before/after snapshot of the shared accumulator**
(`before = total_discount; … if rule.exclusive and total_discount != before: break`), wrapping the untouched
`isinstance` chain. So **both** proxies — test-pass **and** reopened-owner count — **tied**. Neither separated
good design from bad.

But the code tells the truth the metrics missed: the type-switch is **still there**, now carrying a delta-trick
on top — the design got **more** convoluted, not equal. The lesson: **reopened-owner is only a valid
design-quality signal on a change that actually exercises the design's weak axis.** Stacking wasn't it; a
capable model routed around it.

## Part 2 — the right surprise: add a new rule kind (the axis the review named)

The type-switch design's real defect (which BP9's review named: §7 OCP / §8 type-code-switch) is that it is
**not closed to new rule kinds** — dispatch is by type *inside* the engine. So the revealing surprise is
**"add a new rule kind"** (`PercentOffOrder(percent)`). Applied to the 4 type-switch builds and, as controls, 2
**polymorphic** builds (BP7 opus arms).

| build | dispatch style | tests after (stage1+2+3) | add-a-rule-kind → engine? |
|---|---|---|---|
| b1–b4 | `isinstance` type-switch | **22/22 each** | **REOPENED `Engine.total`** (new `elif` branch) — 4/4 |
| p1, p2 | polymorphic `rule.discount()` | **22/22 each** | **extended, class only, engine untouched** — 0/2 |

**Decisive: 4/4 reopen vs 0/2, at identical test-pass (22/22 everywhere).** A new rule kind in a type-switch
build *requires* editing the engine (a new `elif isinstance(rule, PercentOffOrder)`); in a polymorphic build it
is a new class the engine never sees. The two designs are **indistinguishable by tests** and were even
indistinguishable by the *wrong* change (Part 1) — and are **cleanly separated by the right one.**

## What this establishes (and it is the campaign's real point, corrected)

1. **Test-pass is a floor. It never separated the builds — all six are 22/22 throughout.** Reporting
   "correctness ties" as a finding was measuring the floor. Corrected.
2. **Design quality is real and consequential**, but a coarse proxy (reopened-owner) only reveals it on a
   change that hits the design's weak axis. The generic "does it extend" question is gameable by a capable
   model (Part 1); the change-axis-specific question is not (Part 2).
3. **aims' review is the instrument that names that axis in advance.** In BP9 the review flagged these exact
   builds as §7/§8 rigid — *before* any change, from the code alone, while the tests were green. BP13 Part 2
   **confirms that verdict was real**: the flagged builds reopen on precisely the axis the review named; the
   unflagged builds don't. So aims' review measures a design-quality difference that **functional tests are
   structurally blind to**, and it predicts real future cost (the reopen when a new rule kind arrives).

This is the honest, corrected shape of aims' value: not a test-pass edge (there is none to have), but a
**design-quality edge the review surfaces and tests cannot** — flexibility to the *foreseeable* change, which
is exactly what the review reasons about (§7's "foreseeable X-item"). n: 4 type-switch + 2 polymorphic, one
product; the mechanism (type-dispatch is not closed to new kinds) is general, not statistical.
