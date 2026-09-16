# Results — v3 (post concept-fit pass), design-only, three-way vs OpenSpec

> **⚠️ Unresolved validity threat.** `decisions/0007-aims-vs-openspec-pilot-findings.md` already documents,
> in the pricing-cart's own vocabulary, the exact fault v3 exists to test whether the concept-fit pass
> fixes: *"tax folded into the explanation chain ... dissolved aims' own delta-sum invariant into per-kind
> folds."* It sat in the same repo the v3 design arms were rooted in to read the method files, and
> `SKILL.md` itself tells them to read root records for context — so they had a path to their own answer
> key. Whether either arm took it was never checked. **The fix is narrow: don't leave a worked example that
> matches an in-flight test's exact scenario reachable from the design arm's root while that test runs.**
> Until re-run that way, the finding below is unconfirmed.

Design-only pilot re-run after adding the **concept-fit pass** to `references/review.md` (a decomposition
modelled as a movement, or the reverse, is a latent-architectural fault to catch *in the design*). Two aims
arms — **single** (Guide+Worker) and **panel** (ADR 0005 panel-plan) — against the existing **OpenSpec**
arm. All three evolved the same product across three stages (base pricing → explanations + non-stackable
promotions → a second tax market). Judged blind (A/B/C), mapping sealed until every reading was in.

Mapping (unsealed after judging): **A = aims-panel · B = aims-single · C = OpenSpec.**

## M1 — survival (change absorption across the two evolutions; lower better)

| arm | reopened+discarded | note |
|---|---|---|
| **aims-panel** | **1** | one boolean on a promotion supertype across both changes; both forces absorbed additively beside untouched seams |
| aims-single | 5 | explanation force inverted its stage-1 "price is a number the outcomes describe" bet (result types reshaped) |
| OpenSpec | 5 | later tax change reached into foundations the others kept stable — the `money.quantize` kernel, the `price` seam, the catalogue structure |

Trajectory: v1 aims survival was **worst (11)**; v2 was **best-tied (5)**; v3 **aims-panel = 1, decisively best.**

## Correctness gate

All three price every stated case C1–C6 to the cent, and agree with each other and independent decimal
recomputation on every adversarial input the judges tried. **No wrong number in any arm.** The v1/v2 fatal
weakness — tax folded into the explanation ledger as a movement (`Adjustment(delta=0)`) — is **absent from
both aims arms**: both modelled tax as a *decomposition beside* the promotion walk, joined at the shared
final. aims-panel sharpened it further (NORTH tax = a *movement* that adds VAT; SOUTH tax = a *decomposition*
that splits gross), modelling each market by its kind. This is the concept-fit pass doing its job at design
time.

## The two substantive judges split

Same method-neutral rubric (consequence-first: M1+M2+M3 decide; M4 only breaks ties / flags pervasive
integrity faults), opposite priors, both blind.

| judge (prior) | ranking | deciding measure |
|---|---|---|
| skeptic-of-deferral (hard on M3 blast-radius, M4 hiddenness) | **aims-panel ≫ aims-single > OpenSpec** | M1 (survival) places aims-panel first by a wide margin; M3 places aims-single above OpenSpec |
| skeptic-of-clean (hard on M2 accidental complexity) | **OpenSpec > aims-panel > aims-single** | M2 — OpenSpec's single-mechanism discipline (one promotion interface, one parameterised tax policy) yields fewer problem-unforced types |

The split is real and it is about **M2 vs M3**:
- Under M2 (accidental complexity), OpenSpec's single parameterised mechanism reads leaner than the aims
  arms' "two-implementations-behind-a-seam" families (LineAdjustment/CartAdjustment; NorthTax/SouthTax).
  The skeptic-of-clean judge gave the aims arms' self-narrated "principled split" **zero credit** and counted
  the type families as unforced.
- Under M3 (forward blast radius over three pre-registered changes), the same aims seams pay off: OpenSpec
  folded the tax rate into a **scalar** and money into **raw `Decimal` with no value type**, so a per-line
  reduced VAT rate and a second currency reopen seams the aims arms absorb locally.

So the leanness OpenSpec is credited for on M2 is, in part, the same folding the other judge penalises on M3.
Whether NorthTax/SouthTax is "correct genericity" (they genuinely differ in kind — add-VAT vs split-gross —
so a describable second implementation exists) or "ceremony" is exactly what the two judges disagree on.

## Fault flagged in the winning aims arm (verify)

The skeptic-of-clean judge found a substantive fault in **aims-panel**: under a multi-line SOUTH cart with a
cart-scoped discount, the per-line *explanation* appears to reconcile to the line's post-line-discount cost
(a COFFEE line explanation ending 12.00) rather than to the line's *settled* final / tax base (10.80). If
real, it dents aims-panel's flagship "explanation reconciles by construction" claim and is a
pervasive-leaning (every multi-line cart with a cart discount), moderately-hidden fault. The skeptic-of-
deferral judge did not flag it. **Status: to verify against the design text — a genuine latent fault, or a
judge misreading of the settlement/explanation split.** Recording it honestly either way.

## Bottom line (honest)

- **Change absorption: aims now leads, clearly** — aims-panel's survival of 1 across two unforeseen changes
  is the strongest single result the method has produced, and beats OpenSpec (5). This is the metric aims
  most directly targets, and the panel-plan arm is where it shows.
- **The v1/v2 architectural fault is gone**, in both aims arms, caused (not merely measured) by the
  concept-fit pass at design time.
- **Overall design quality is a split, not a clean win.** aims wins under a consequence/future-cost lens;
  OpenSpec wins under an accidental-complexity/leanness lens. The honest claim is *"aims materially improved
  change-absorption and eliminated the concept fault; on minimal-machinery it still trades against a
  single-mechanism spec method, judge-dependent"* — not "aims beats OpenSpec."
- Design-only cost stayed low (no implementation), as intended.
