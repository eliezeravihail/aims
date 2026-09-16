# Continuity judging — did a later design build on an earlier recorded conclusion?

Judge's note: I did not build any of these trees. Everything below is quoted from the artifacts or
proved with `git`. Volume is not credited; only demonstrated *use* by a later session is.

## Timeline (proves what predates what)

```
arm-aims      2c905c0 21:52:38 stage-1   adfc340/fedb1f9 22:15/22:18 stage-2   c9e3002 22:52:20 stage-3
arm-openspec  c44eb88 21:52:38 stage-1   13ae8b3         22:15:21    stage-2   cf10d2b 22:52:20 stage-3
arm-plain     115f9c9 21:52:38 stage-1   f051829         22:15:21    stage-2   82af0d6 22:52:20 stage-3
```

All three arms' stage-1 commits are timestamped identically and precede every stage-2 commit, so any
stage-1 text shown below provably predates the stage-2 requirement (non-stackable promotions) and the
stage-3 requirement (markets + tax).

---

# 1. /tmp/exp/arm-aims

## 1.1 A stage-1 record that marked the shape of a change only stage 2 needed — and was used

`decisions/0003-money-as-integer-minor-units.md`, present at `stage-1`
(`git show stage-1:decisions/0003-money-as-integer-minor-units.md`), closes with:

> "Refunds/credits are a non-goal today. If they arrive, they do not bend `Money`: they need a **signed
> sibling concept**, and a superseding ADR."

Stage 2's requirement (every price arrives with an ordered list of adjustments whose deltas sum exactly
to the difference) needs precisely a signed quantity, which `Money` — non-negative by construction,
raising on underflow — cannot express. `design/stage-2.md` §3 (added at `adfc340`):

> "A subtraction whose result may be negative is not expressible in `Money` at all — by design, since
> `Money.__sub__` raises on underflow. So a signed sibling is introduced, **exactly as `decisions/0003`
> anticipated one would have to be**, and `decisions/0012` records it."

and again in the stage-2 rejected-alternatives list (§15.4):

> "Make `Money` signed instead of adding `MoneyDelta`. Rejected… `decisions/0003` anticipated a *signed
> sibling*; this is it."

This is the strongest form of evidence available in the exercise: a stage-1 record naming the shape of a
change nobody had yet asked for, and a stage-2 session citing that record by number while making exactly
that change. `git diff stage-1 stage-2 -- decisions/0003-*` shows the stage-2 session went back and
stamped the original: `> **Extended.** The signed sibling this ADR anticipated now exists:
`decisions/0012` (`MoneyDelta`). `Money` itself is unchanged`.

## 1.2 A stage-1 record that marked the address of the stage-2 change

`architecture.md` at `stage-1`, "Likely change axes", item 3:

> "**The interaction policy** — which cart promotion applies first (`canonical_order`), whether
> percentages compound…. All three are now settled by the product owner…; each remains one named
> function, so a change of mind is a superseding ADR, not a redesign."

Stage 2's exclusion rule landed in exactly one new named function. `decisions/0013` §2: "One named
function, `choose_non_stackable`, is the only place a promotion is excluded." And the stage-2
`architecture.md` re-states axis 3 with the outcome measured against the prediction:

> "…and which of several mutually exclusive codes wins (`choose_non_stackable`, called once per cart).
> … Every answer the owner gave on exclusion (§16, Q11–Q18) landed inside the last of them or its single
> call site — the evidence that it is the right address."

## 1.3 Stage 3 building on stage-1/2 records

`decisions/0015` opens: "**Extends** `0004-promotion-scope-stages-and-order.md` (the scope/stage pattern
it established is reused for tax) and `0002-entry-point-library-with-cli.md`… Nothing in either is
reversed." Its two tax-rule interfaces are explicitly modelled on stage 1's two promotion scopes: "Two
rule interfaces, **mirroring the promotion scopes**." Stage 3's `decisions/0019` reuses stage-1's
`0009` line of argument verbatim for a new case: "Reporting every code as `unknown` instead would tell
support the opposite of the truth, which is **the same line `0009` drew** between 'unknown' and
'temporarily unavailable'." And stage-1's `0005`/`0009` were re-opened and stamped at stage 3
(`git diff stage-2 stage-3 -- decisions/0005* decisions/0009*`) rather than rewritten.

## 1.4 Contradictions / tearing open

Three genuine reversals of earlier recorded conclusions. All three are marked in place on the original
record, with the original text left intact:

**(a) Allocation, stage 1 → stage 2.** `decisions/0006` at `stage-1`:

> "The cart discount is allocated across lines in proportion to each line's post-line-promotion net…"
> (one allocation, at the end of pricing)

`decisions/0011` (stage 2):

> "Supersedes the allocation clause of `0006`… (one allocation at the end of pricing → one allocation
> per cart-level promotion, at the moment it is taken)."

and it states the cost honestly: "Per-promotion allocation **can differ in the pennies** from `0006`'s
single end allocation… No acceptance case, old or new, does."

**(b) Order-independence, stage 1 → stage 2.** `decisions/0008` (stage 1) recorded the owner's "the
answer has to be the same every time for the same cart". `decisions/0013` narrows it: "**I5 is narrowed,
deliberately.** The *amounts* remain independent… what is not independent is which of two exactly-tied
codes is named as applied." `0008` carries the back-stamp: "> **Narrowed in part** by `decisions/0013`."

**(c) Rounding, stage 1 → stage 3.** `decisions/0003` (stage 1): "Rounding happens in exactly one place,
when a discount amount is computed, **ROUND_HALF_UP** to the cent." `decisions/0017` (stage 3):

> "…whose clause *'rounding happens in exactly one place, when a discount amount is computed,
> ROUND_HALF_UP to the cent'* is **superseded in part**: there is still exactly one *place* that rounds,
> but the mode is now named by the caller, because two laws round two different figures two different
> ways."

**The one bookkeeping gap I found in this arm:** `0003` was *not* back-stamped for `0017`.
`grep -c 0017 decisions/0003-money-as-integer-minor-units.md` returns `0`; line 17 of that file still
reads "ROUND_HALF_UP to the cent" with no forward pointer, while every other superseded stage-1 ADR
(`0004`, `0005`, `0006`, `0008`, `0009`) carries one. A stage-4 reader navigating to the money ADR would
read a clause that is no longer true and would only learn otherwise from `architecture.md`, which *was*
updated ("the only place that rounds — once per figure, **by the mode the caller names**"). The
append-only supersession discipline held 5 times out of 6.

## 1.5 WHY or only WHAT?

Both, in separate files, which is the arm's distinguishing structural property.

- **WHAT only** — `goals.md` invariants: "**I1** The cart total is never negative; no line cost is ever
  negative." "**I6** The per-line costs returned sum exactly to the returned cart total."
- **WHY** — every ADR carries Context / Decision / Consequences / Alternatives. `decisions/0013`:
  "A numeric priority per code in the catalogue — rejected for the reason `0004` rejected priorities: a
  structural rule in a file non-engineers edit daily." `decisions/0011`: "Reconstruct the explanation
  from the reported figures after pricing — rejected: two producers of one fact, which is the failure the
  owner named, and in general not even possible once a discount has been rounded and allocated."

### Verdict: **navigated and built on it**

---

# 2. /tmp/exp/arm-openspec

## 2.1 The `openspec/specs/` fact, stated plainly

`openspec/specs/` is **empty** — it contains only `.gitkeep`, at every tag:

```
git ls-tree -r stage-1 --name-only | grep openspec/specs/   ->  openspec/specs/.gitkeep
git ls-tree -r stage-2 --name-only | grep openspec/specs/   ->  openspec/specs/.gitkeep
git ls-tree -r stage-3 --name-only | grep openspec/specs/   ->  openspec/specs/.gitkeep
```

`openspec/changes/archive/` is likewise empty but for `.gitkeep`.

That directory is OpenSpec's durable baseline, and it is populated only by the archive step, which per
`.claude/skills/openspec-archive-change/SKILL.md` runs the spec sync and then `mv "<changeRoot>"
"<planningHome.changesDir>/archive/<target-name>"`. Nothing was implemented in this exercise, so nothing
was archived, so the baseline was never written. **This is a limitation of how the exercise was run, not
a fault of the team.** The team could not have populated `specs/` without implementing the service, which
was out of scope for all three arms equally.

What it means for what the later sessions could inherit: they inherited the **change folder**, not the
baseline. That turned out to be the *richer* of the two, because the change folder contains `design.md`
(2 400+ lines of rationale by stage 3) while the baseline would have contained only the merged
requirement text. Two consequences worth stating:

1. The later sessions got more WHY than a normally-operating OpenSpec project would have handed them.
   Had the change been archived, `design.md` would have moved to `changes/archive/` — and neither
   `.claude/skills/openspec-explore/SKILL.md` nor `.claude/skills/openspec-propose/SKILL.md` contains
   any instruction to read the archive (`grep -i archive` on both returns only the boilerplate
   store-selection paragraph). The rationale would have left the default read path.
2. Because the same change folder was edited in place three times, the durable layer holds only the
   latest state. Every superseded conclusion below survives **only in git**, not in the tree.

## 2.2 A stage-1 record that marked the shape of the stage-2 change — and was used

`proposal.md` at `stage-1` (`git show stage-1:.../proposal.md`), final bullet:

> "**Known to be coming, deliberately not built now**: limits on how many promotions may stack, and
> **codes that exclude one another**. The product owner expects both but has asked for today's
> behaviour, which is unlimited stacking with no exclusivity. The design names where they would attach
> so that building them later is an addition rather than a rework."

and `design.md` at `stage-1`, Risks section, naming the attachment point:

> "**Stacking limits and exclusivity are coming but not built** → … the seam is named so it is an
> addition later, not a rework: a limit is a filter over the resolved rules before the fold, and
> **exclusivity is a catalogue field plus the same filter**. Neither touches `money`, `allocation`, or
> the rules themselves."

Stage 2 landed the catalogue-field half exactly there — `design.md` Decision 11, "Stackability is a
catalogue modifier, not a kind and not a rule": "`stackable` is an optional boolean on any catalogue
entry, defaulting to `true` when absent" — and the stage-2 session demonstrably read the stage-1 bullet,
because it **rewrote that same bullet**:

> "**Stacking limits are still coming and still not built** → exclusivity **has now arrived** as
> non-stackability (Decisions 10 and 11); a cap on how many promotions may stack has not. The seam is
> unchanged: a limit is a filter over the resolved rules before the fold."

You cannot edit a sentence you did not read. Stage 3 continues the same discipline: Decisions 12–16 cite
Decisions 2, 5, 6, 7, 9, 10 and 14 by number ("…a code absent from a market's file is simply unknown
there, which is already what the… (Decision 7)"; "…`allocation.apportion` splits an exact amount into
parts that sum to it (Decision 2)"; "Decision 9 already argued that an explanation must be the
structure…"), and `git diff stage-1 stage-3 -- design.md` is `812` added / `77` deleted lines — stage 1's
decisions were kept and extended, not replaced.

## 2.3 Where a later stage tore open an earlier recorded conclusion

**The other half of the stage-1 prediction was rejected, and the rejection is not marked as one.**

Stage 1 (`design.md`, Risks):

> "exclusivity is a catalogue field **plus the same filter**" — i.e. "a filter over the resolved rules
> **before the fold**".

Stage 2 (`design.md`, Decision 10, "Alternatives rejected"):

> "*Filter before the fold, by declared value.* **Simple, and wrong**: a percentage has no value until
> you know the base, so the filter would have to price the cart to decide, which is the fold."

Stage 2 is right and stage 1 was wrong. What is missing is the acknowledgement: the rewritten bullet says
"The seam is unchanged" (of the stacking *limit*) and "exclusivity has now arrived", wording that reads as
continuity, while Decision 10 silently discards the mechanism the earlier record named. Because the file
was edited in place, the stage-1 claim no longer exists anywhere in the tree — only in
`git show stage-1:openspec/changes/add-cart-pricing-service/design.md`.

The same overwrite-without-marking pattern appears in the spec files. Stage 1's `promotion-rules/spec.md`
stated:

> "When a cart carries more than one code, the promotions SHALL be applied in a fixed order determined by
> the promotion's kind, **never by the order the customer typed the codes**."
> "#### Scenario: Input order does not matter — **WHEN** the same two codes are submitted in the reverse
> order — **THEN** the cart total and every line amount are identical."

The current file replaces both (`git diff stage-1 stage-2 -- .../promotion-rules/spec.md` shows them
deleted) with:

> "The order in which the customer submitted the codes SHALL affect the result in **exactly one way**: it
> breaks a tie between non-stackable promotions of equal value."
> "#### Scenario: Input order does not matter **for stackable codes**"

The new text is correct and honest on its own terms. But every capability spec in the tree is still
headed `## ADDED Requirements` at stage 3 (`grep "^## " on each spec file`: only `## Purpose` and
`## ADDED Requirements`, no `MODIFIED` or `REMOVED` sections), so the durable layer records the narrowing
as if it had always been the requirement. There is no supersession trail outside git.

## 2.4 WHY or only WHAT?

Cleanly split by file type, and the split is the interesting part:

- **WHAT only** — the capability specs, by format. `specs/market-tax/spec.md`: "Every pricing request
  SHALL name the market it is being priced for, and that market SHALL determine the tax law the result is
  computed under. There SHALL be no default market: a request that names none is malformed." Normative,
  testable, and rationale-free.
- **WHY** — `design.md`, and it is very good. Decision 10: "If the winner were compared at the
  arbitration point but applied later at its own scope position, an intervening stackable promotion could
  change what it actually takes — and then the explanation would say 'TENOFF beat SAVE10 by 10.00' while
  the line showed `-8.50`. That is precisely the disagreement the product owner says makes the feature
  worthless." Decision 11: "Why absence means stackable. Every entry written before this modifier existed
  must keep its meaning… Defaulting to non-stackable would silently turn today's stacking behaviour off."

The structural risk this exposes: the WHY lives entirely in `design.md`, which is the artifact that leaves
the default read path on archive, while the WHAT-only specs are what becomes the permanent baseline. In
this exercise that risk never fired, because nothing was archived.

### Verdict: **navigated and built on it**

(with one documented reversal of the stage-1 "filter before the fold" mechanism that the durable layer
does not record as a reversal — see 2.3.)

---

# 3. /tmp/exp/arm-plain

Its entire durable layer is `design/stage-1.md`, `stage-2.md`, `stage-3.md` — three files, 766 / 1340 /
2009 lines, each added whole in one commit, none of the earlier ones ever edited
(`git log --stat`: stage-2 and stage-3 commits touch exactly one new file each). No machinery, no hooks,
no ADR directory, no spec format.

## 3.1 The stage-1 record that marked the shape of the stage-2 change — and was used

`design/stage-1.md` §9, "Extension scenarios — what changes when the PO asks for…":

> | "Best of" instead of stacking | Engine-level: evaluate candidate subsets, keep the cheapest total.
> **Rules stay pure and unchanged — this is why they return proposals instead of mutating.** |

and §7.5, marking the absence deliberately: "No date ranges, no enable/disable flag, no per-customer
eligibility, no usage limits, **no stacking-exclusion groups**. All are plausible next requests… but none
was asked for."

Stage 2 lands the exclusion contest in the engine with the rule classes untouched, and says so in terms
that can only come from having read the stage-1 argument — `design/stage-2.md` §4.4:

> "**This component required no change at all in stage 2, and that is the largest single piece of
> evidence that the stage-1 seams were placed correctly.** The exclusion contest (§6.5) must ask 'what
> would this promotion be worth right now?' without applying it. Because `evaluate` is pure and returns a
> value, asking is free and provably side-effect-free; there is no 'dry run' mode to add, no rollback, no
> second code path. **Had rules mutated a running total, the contest would have required transactional
> state and the design would have been substantially worse.**"

That is the stage-1 sentence ("this is why they return proposals instead of mutating") cashed in, one
stage later, against the requirement it was written for.

## 3.2 A stage-1 *removal* that stage 2 found and reversed, citing it

`design/stage-1.md` §13.2 records a subtractive decision:

> "**Q4** replaced a conflict rule with an interaction rule and **removed the `SUPERSEDED` status
> entirely — a status nothing can now produce should not exist, or someone will eventually invent a use
> for it.**"

`design/stage-2.md` §2.3:

> "`SUPERSEDED` **returns to the status set, having been deliberately removed at the end of stage 1 on
> the grounds that nothing could produce it. Something can now**: it is the direct answer to 'support
> needs to tell the customer *your code was valid but the other one saved you more*'."

This is the cleanest single instance of navigation in any of the three trees: a stage-1 record of
something *deleted*, found by a session with no memory of deleting it, and reinstated with the earlier
reasoning named and correctly retired.

## 3.3 Where stage 3 tore open a stage-2 recorded conclusion — openly

`design/stage-2.md` §9 extension table:

> | Tax / shipping | **New phases after 30**; allocation is already the mechanism for apportioning them
> to lines, and each becomes an ordinary row in the explanation. |

`design/stage-3.md` §1.2, "Why tax is not an adjustment":

> "The obvious alternative — and **the one stage 2's own extension table predicted** (*'Tax / shipping:
> new phases after 30'*) — is to make tax a phase, so that it becomes an ordinary row in the explanation
> with a delta and a running balance. **Stage 3 rejects that prediction, having now seen the actual
> requirement.**
> The journal records *movements of price*. Tax is not a movement; it is a *decomposition* of a price
> that has already been reached.
> - In SOUTH nothing moves at all…
> - In NORTH something does look like a movement: `+3.83` on top of `22.50`. But making it a row breaks
>   the property the product owner bought stage 2 for: *the deltas add up to what came off*. On C1 the
>   deltas would sum to `-2.50 + 3.83 = +1.33`, a number that is neither what came off nor what is owed."

The prediction was read, quoted, and overturned with the arithmetic that disproves it. Two more reversals
are handled the same way in stage 3:

> "**Stage 3 gives up one stage-2 claim and must say so.** Stage 2 said this module held 'one
> `ROUND_HALF_UP`, one `Decimal('0.01')`'. It no longer does: there are now two rounding modes… The claim
> is replaced by something weaker but still checkable — one rounding *function*, whose mode is an
> argument, and a table (§5.2) that says which call site passes which mode."

> "This also closes a risk stage 2 flagged explicitly — though not quite in the way stage 2 expected.
> Stage 2 said a second currency 'is genuinely a redesign, not a field'… What actually arrived was a
> second *market* with the same currency, and the redesign it demanded was precisely the one predicted
> for a second currency… **The flag was planted on the wrong noun and still caught the right change**,
> which is the most one can ask of a flag."

(For the record: this is the same rounding conclusion aims tore open in `decisions/0017`, and both arms
handled it well — aims by stamping the ADR, plain by a paragraph headed "must say so".)

## 3.4 WHY or only WHAT?

Both, in one file, at different altitudes.

- **WHAT only** — §3's invariant table: "| I3 | `sum(line.net for line in lines) == quote.total` —
  exactly, no drift | `ledger` (allocation) |", "| I8 | Same (cart, catalog) ⇒ byte-identical quote. No
  dict/set iteration order, no clock, no RNG | `engine` |".
- **WHY** — §12 "Decisions at a glance" is a three-column table whose third column is literally headed
  *Because*: "| Rules propose, engine disposes | Rules mutate a running total | A bad rule then cannot
  break the total, the floor, or I3 — the property that makes a frequently-edited promo system safe |";
  "| Retirement = delete the entry; no `enabled` flag | A disable flag | Two mechanisms for 'this code is
  over' means every downstream question is answered twice |".

## 3.5 The result, stated as it falls

**This arm did not merely re-derive. It navigated.** Its own prior documents carried the conclusions, it
quoted them by section, used them where they held, and reversed them by name where they did not — with no
ADR directory, no spec schema, no anchor stamping, no hooks and no state file. **That is a real result
against the value of the other two teams' machinery, and it should be read as one.** Three plain markdown
files in a `design/` directory delivered the same continuity outcome as `decisions/0001`–`0019` plus two
hooks plus `.aims/state.md`, and as five capability specs plus a change folder plus six skills.

The honest qualifications, in both directions:

- **Cost.** Plain's continuity mechanism is total restatement. Each stage rewrites the whole document —
  766 → 1340 → 2009 lines — and each opens with the claim "supersedes stage 1/2… and needs no other
  document to be read alongside it". Every stage pays to restate everything, and the restated version is
  what the next session reads, so a conclusion dropped in restatement is gone without trace. That did not
  happen here in any case I found, but nothing structural prevents it; aims' append-only ADRs and
  in-place supersession banners are the mechanism that would.
- **The self-description is not evidence.** I did not credit "complete and self-contained" or "every
  stage-1 product answer is still in force and restated here". I credited §4.4, §2.3 and §1.2, which are
  citations of specific prior text.
- **Scale.** Three stages, one document per stage, one reader per stage. Restatement is O(n) per stage
  and a navigable record set is O(1); at three stages that difference has not yet bitten. This exercise
  cannot tell you what happens at stage 8.

### Verdict: **navigated and built on it** — and it did so with no durable-knowledge machinery at all

---

# Summary table

| Team | Verdict | Load-bearing evidence | Reversal handled? |
|---|---|---|---|
| arm-aims | **navigated and built on it** | stage-1 `decisions/0003` predicted a "signed sibling"; stage-2 §3 built `MoneyDelta` citing it by number | Yes — in-place supersession banners on `0004`,`0005`,`0006`,`0008`,`0009`; **missed on `0003`→`0017`** |
| arm-openspec | **navigated and built on it** | stage-1 `proposal.md`/`design.md` named exclusivity as "a catalogue field"; stage-2 Decision 11 built exactly that, and rewrote the stage-1 bullet in place | Partly — the "filter before the fold" half was rejected ("Simple, and wrong") with no supersession marker; specs still all under `## ADDED Requirements` |
| arm-plain | **navigated and built on it** | stage-1 §9 "rules stay pure… this is why they return proposals"; stage-2 §4.4 cashes it in. stage-2 §9 predicted "tax = new phases after 30"; stage-3 §1.2 quotes and rejects it | Yes — three explicit reversals, each headed as one ("Stage 3 gives up one stage-2 claim and must say so") |

**Fact required to be reported plainly:** `/tmp/exp/arm-openspec/openspec/specs/` is empty (only
`.gitkeep`) at all three tags. It is OpenSpec's durable baseline and is populated only when a change is
archived after implementation; nothing was implemented in this exercise, so it could not have been
populated. **This is a limitation of how the exercise was run, not a fault of that team.** Its later
sessions inherited the un-archived change folder instead — which carried *more* rationale than the
baseline would have, since `design.md` is not merged into `specs/` and leaves the default read path on
archive.

**Cross-cutting finding.** No team re-derived. All three later sessions found and used a specific prior
record. The three durable layers therefore did not differ in *whether* knowledge survived; they differed
in **what happens to a conclusion that turns out to be wrong.** aims marks it superseded in place and
keeps the original text (5 of 6 times). plain writes a paragraph saying it is giving the claim up (3 of 3
times). openspec overwrites the text, so the superseded claim survives only in git, and the spec format's
own `MODIFIED`/`REMOVED` delta markers went unused across all three stages.
