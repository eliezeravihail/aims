---
title: "the aims-vs-OpenSpec trail after v2/v3 — improved, but the clean negative still stands"
date: 2026-09-16
---

**Context.** `decisions/0007` recorded the aims-vs-OpenSpec pilot's finding: **no design advantage for
aims**, survival reopened the most (11), the pre-registered falsifier fired. Those counts were the **v1**
run. Two further runs have since happened (`experiments/aims-vs-openspec/results-v3.md`, `run-log-v2/`),
and `0007` carries no pointer to them — a navigator following the ADR trail would inherit v1's counts as
the whole story. This ADR supersedes `0007`'s *finality*, not its caution.

**What changed since 0007.**
- **v2** (`design-principles.md` §2 sharpened): survival churn roughly halved (11 → 5), but design quality
  stayed a wash — the interface-cram fault persisted because the check still fired only after the interface
  existed.
- **v3** (the **concept-fit pass** added to `references/review.md`, run on the design before code): the
  v1/v2 architectural fault — tax modelled as a movement / folded into the explanation chain — is **gone**
  from both aims arms; survival trajectory reached **1** for the panel arm (11 → 5 → 1). The concept-fit
  pass *caused* (not merely measured) the fault's elimination.

**Decision — the honest net, so a later session reads it correctly.**

1. **0007's central caution STILL STANDS: do not claim a design-quality advantage for aims.** The one
   *clean* blind test (v1) came back negative, and nothing clean has overturned it. What v2/v3 robustly
   show is narrower and real: **change-absorption improved**, and the concept-fit pass **eliminated the
   named architectural fault**.
2. **v3 is not clean, and its win is not bankable.** The v3 arms could reach `decisions/0007`, which names
   the exact fault being tested for, in this domain's own words — answer leakage. So v3's "aims-panel
   decisively best" is **unconfirmed**, and it is not evidence of a design advantage on its own.
3. **The confirming run is owed, not done.** An isolated re-run (`results-v4.md`, arms with no access to
   the fault-naming records) would settle whether the v3 improvement survives without leakage. It **does
   not exist yet**. Until it does, the standing reading is: *improved change-absorption + a caused fault
   elimination, on an overall advantage that remains unproven/contested* — a judge-dependent split, not a
   win.

**Consequences.**
- `0007` is not rewritten (append-only); this ADR is its forward pointer and the two are read together.
- `goals.md` and `results-v3.md` are corrected to stop citing `results-v4.md` as an existing supersession —
  it is named as owed future work, not a filed result.
- The claim `README`/`goals` make to a prospective user must match this: aims has been blind-tested once
  cleanly and lost on design; later runs improved change-absorption and removed a fault but are not a clean
  win. Overclaiming here is the exact failure the self-review (`reviews/2026-09-16-aims-self-review.md`)
  found.

**Alternatives.**
- *Let `results-v3.md`'s "decisive best" stand as the current headline* — rejected: it is a flawed run by
  the project's own flag; treating it as the result would be reading the evidence the way `0007` §"Treat
  the loss as a rubric artifact" already rejected, in the opposite direction.
- *Write `0009` only once `results-v4.md` exists* — rejected: the dangling pointer and the missing forward
  link are wrong **now**; recording the honest interim state is better than leaving `0007` reading as final.
