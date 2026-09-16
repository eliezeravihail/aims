# Verdict 2 — Adversarial stress-test of "P wins"

Charge: attack the first pass's ranking of P first, which treated P's "tax folded into the explanation
ledger" as recorded-but-consequence-free and therefore barred from deciding. I recompute M2 and M3 from
the texts, test the fault against the pre-registered changes plus two of my own, classify it
local-vs-pervasive, and re-read the M1 input for comparability.

Structural fact the whole thing turns on:

- **P** fuses tax INTO the discount ledger. Tax is an `Adjustment` with a new `AdjustmentStatus.TAX`
  member and a `tax_amount` field, appended to `Explanation.adjustments`, and `Explanation.final` is
  redefined to equal **gross** (the tax-inclusive amount). INV-7: `list_total + sum(a.delta) == final
  (== gross) ... no synthetic rounding line`. So in P the customer-paid total is a *projection of the
  discount ledger*.
- **Q** and **R** keep tax in a SEPARATE account joined to the explanation at exactly one number. Q: the
  `Explanation` has three kinds only (`LIST_PRICE/PROMOTION/NOT_APPLIED`), tax lives in a `TaxView`,
  `Explanation.final == amount == taxable_amount` (pre-tax), and I26 guarantees "the journal is identical
  in every market." R: Decision 15, "Tax is a second account, joined to the explanation at exactly one
  number," `TaxFigure.basis_amount == ledger.current`. In both, the discount ledger's sum-invariant does
  NOT span tax.

That is the seam under test: in P the price the customer pays is defined through the discount ledger; in
Q/R it is defined beside it.

---

## M2 — Accidental complexity (recomputed; lower better)

Test applied: would *every* correct design of this exact product need it? If a shared/simpler mechanism
prices every stated case, the heavier one is accidental.

| Design | Accidental item | Why not forced |
|---|---|---|
| **P** | Tax smeared into the discount `Adjustment` — `AdjustmentStatus.TAX`, `Adjustment.tax_amount`, and `Market.tax_entry()` whose sole job is to mint a ledger entry for tax | The requirement is "show the tax." A separate tax account (Q/R) satisfies every case without widening the discount Adjustment or adding a method to produce ledger entries. Machinery serving P's fusion choice, not the problem. |
| | (P has NO per-market catalog, NO routing guard, NO `MarketMismatchError`, NO quarantine machinery — it shares one catalog and hard-fails a bad file) | These absences are leanness, counted in P's favour below. |
| **P total** | **≈ 2** | |
| **Q** | Per-market catalog files + `[settings].market` header + per-file validation | A **shared** catalog prices every stated case (P proves it: shared `SAVE10`/`COFFEE3` price C1–C6). Per-market files are a commercial premise the recap never states. |
| | `MarketMismatchError` + routing guard I30 | Exist only *because* there are per-market files. This is almost verbatim the rubric's worked example of accidental complexity. |
| | Quarantine machinery — `LoadResult`/`rejected`, `CodeStatus.UNAVAILABLE`, `check-catalogue` | Graceful degradation of a malformed catalog is not forced; P hard-fails and is still correct. |
| | `Quote.payable` restating `quote.tax.payable` (I31) | Q itself calls it "the only restatement in the contract"; product-instructed (Q30), defended, but redundant. (Half-count.) |
| **Q total** | **≈ 4** | |
| **R** | Per-market catalogue files + market header | Same as Q: shared catalogue prices every case. |
| | Refuse-foreign-catalogue guard (Decision 12) + its own distinct exit status | Same origin as Q's guard. |
| | Quarantine machinery — `LoadResult.rejected`, `check-catalogue`, `UNAVAILABLE` | Not forced. |
| | `MarketRegistry` passed as a third `price()` argument | A market table is forced; the registry indirection is a choice (minor). |
| **R total** | **≈ 4** | |

**M2: P ≈ 2, Q ≈ 4, R ≈ 4 — P leads.** Caveat stated plainly: P's lead rests mostly on the per-market
catalogue judgment, which is contestable — but by the rubric's strict "would every correct design need
it?" test, the shared catalog is sufficient, so the per-market file + guard + mismatch-error triad is
accidental for Q and R. P's own accidental item (tax-in-Adjustment) is the very fault under scrutiny.

---

## M3 — Blast radius of the next change (recomputed; count named components reopened, quote the seam)

| Change | P | Q | R |
|---|---|---|---|
| **C-next-1** reduced per-product VAT (rate per-line + product metadata) | **4** — `model` (metadata); `market` (rate per-line); `result` (`PricedLine.tax` flips `None`→breakdown in a cart-level market; `Adjustment`/`Explanation` tail); `pricing` (tax pass now appends per-line tax entries where none existed; **INV-7/INV-8/INV-10-N reopen**) | **4** — `model`; `market` (`tax_rate`→`rate_for(line)`); `tax` (cart `TaxView` "becomes a list"); `explain` (assemble it). **journal/engine/rules/Explanation CLOSED** (I26) | **4** — `models`; `markets`/`TaxPolicy`; `tax`; `engine` tax assembly / `TaxFigure`. **ledger/rules CLOSED** |
| **C-next-2** customer-dependent eligibility | **2** — `pricing`/engine + `catalog` (customer_id already carried). Tax untouched → coupling does NOT bite | **2** — `engine` + `catalog` | **2–3** — `engine` + `catalogue` + `rules` |
| **C-next-3** second currency | **3–4** — `money` (quantum), `market` (currency), `result`/`model` (currency field), `cli` | **2** — `money`; `market` (profile already carries `currency` + `minor_units`, §5.8/§7.5) | **3** — `money`, `markets`/`TaxPolicy` (R explicitly **excluded** currency — "a market declares a tax law, not a currency"), `models` |
| **Invented D1** a second stacked tax (levy/city tax on top of VAT) | **~4 + 2 public seams** — because gross = `list + sum(ledger deltas)`, the levy MUST be a second ledger entry: `Explanation`/**INV-7/INV-8** reopen (two tax steps, `final` = grand total); `TaxBreakdown`/**INV-9** (`net+tax==gross` → two taxes); `AdjustmentStatus.TAX`/`tax_amount` (singular → which tax?); `market`, `pricing` | **~3** — extend `TaxView` (two tax fields or chained) + `tax` + `market`/profile. **Explanation/journal CLOSED** | **~3** — extend `TaxFigure` + `tax` + `markets`. **ledger CLOSED** |
| **Invented D2** per-discount tax breakdown (tax on each discount) | **~2, roughly neutral / slight P advantage** — P's `Adjustment` is *already* tax-aware (`tax_amount`), so populate it on APPLIED entries; entangles INV-7 semantics but adds no type | **~2** — `TaxView` on `CodeResult`, one new `tax_for` call site (Q35) | **~2** — same as Q |
| **M3 total (C-next-1..3)** | **≈ 9** | **≈ 8** | **≈ 9–10** |

**M3: Q ≈ 8 (lowest), P ≈ 9, R ≈ 9–10 — Q leads the forward measure the rubric calls "the real test."**

---

## Answers to the charge

### (1) Is P's tax-in-ledger fault genuinely consequence-free, or will it bite? — It BITES.

Not consequence-free. The coupling bites on exactly the class of change that alters **how tax composes
into the final customer-paid total**, and one such change is *pre-registered*:

- **C-next-1 bites (pre-registered).** A reduced per-product rate in a cart-level (NORTH-like) market
  breaks P's single cart VAT entry and forces per-line tax figures. P's own contract makes NORTH lines
  carry none: `PricedLine.tax` is `None`, INV-10-N says tax is "computed once at cart; lines carry no
  per-line tax." To support the change P must reopen the *discount explanation ledger* — append per-line
  tax entries to line explanations that structurally have none, flip `PricedLine.tax`, and restate
  **INV-7 / INV-8 / INV-10-N**. Q's and R's discount ledgers stay closed by construction: Q's I26 —
  *"the journal is identical in every market"* — and R's Decision 15 second account. The count ties at 4,
  but P's 4 lands on the ledger and its sum-invariant (the product's crown jewel, pinned by every
  discount acceptance case), while Q/R's 4 are confined to the tax subsystem.
- **Invented D1 (second stacked tax) bites hardest.** P defines `gross = list + sum(ledger deltas)`, so a
  second tax MUST become a second ledger entry — reopening **INV-7/INV-8**, `TaxBreakdown`/**INV-9**
  (`net + tax == gross` no longer holds with two taxes), and the singular `tax_amount`/`TAX` status.
  Q/R add a parallel tax figure and leave the ledger untouched. This is the coupling in its purest form.
- **C-next-2 does NOT bite** (tax untouched) and **D2 (tax-on-discount) is roughly neutral / slightly
  favours P** (its `Adjustment` is already tax-aware). Stated so the finding is honest: the fault has a
  *bounded, specific* trigger — changes to tax composition — not a universal one. But that trigger set
  includes a pre-registered change.

The seam P must reopen, quoted: INV-7 *"list_total + sum(a.delta) == final(== gross) ... no synthetic
rounding line"* and §7 step 10 *"append it to that line's explanation and set line.explanation.final =
bd.gross."* The corresponding Q seam that stays closed: I26 *"the journal is identical in every
market."* P even shows the fusion at work in its own C1: the cart explanation deltas sum to
`-2.50 + 3.83 = +1.33` — neither the discount nor a clean quantity — accepted only because P redefined
the invariant to sum-to-gross. That redefinition is what future tax-composition changes reopen.

**Verdict on (1): the fault is NOT consequence-free. Its cost is already visible in M3 (it is why P ties
rather than leads C-next-1 and would lose D1).**

### (2) Does the fault meet the PERVASIVE threshold? — YES, on both criteria.

The fix (separate tax from the ledger, i.e. adopt Q/R's shape) touches:
1. `result.py` — remove `AdjustmentStatus.TAX`, remove `Adjustment.tax_amount`, change `Explanation.final`
   from "== gross" to "== amount/net".
2. `pricing.py` — tax pass steps 10–12 stop appending tax entries to explanations; produce a separate
   tax account.
3. `market.py` — `tax_entry()` (returns an `Adjustment`) is removed/rebuilt.
4. Public seam: `Explanation.final`'s shipped contract ("== gross", the customer-paid amount) and the
   `Adjustment`/`AdjustmentStatus` type (a shipped enum member + field) both change.

That is **≥ 3 named components AND a public-seam change** — pervasive on *both* independent tests. Per the
rubric, "M4 may ... downgrade a design carrying a PERVASIVE integrity fault," so the fault is **eligible
to move the ranking**. The first pass's classification of it as a barred local blemish is the error.

Contrast — Q's cited blemish, `Quote.payable` restating `quote.tax.payable`: fix touches **one field in
`explain`**, no seam change. **LOCAL BLEMISH — recorded, cannot move the ranking.** R carries no
comparable integrity fault (tax is a clean second account).

### (3) Is M1 (P=5, Q=9, R=8) trustworthy for a fair comparison? — Only partly. Discount P's lead.

M1 is a survival count; a low count is a virtue only if the surviving design did the same job. From the
texts, P has *structurally fewer seams to survive*:
- Tax **fused** into the ledger — one fewer component than Q's/R's separate `tax`.
- **One shared catalog** — no per-market file, no routing guard, no `MarketMismatchError` seam.
- **Hard-fail** on a bad catalog — no quarantine / `LoadResult` seam.
- **More deferred to the implementer** (P §13 leaves the intermediate type, the tax-entry plumbing, the
  rate representation, the `Adjustment.label` typing all open).

Roughly three named seams that Q/R carry, P simply does not have — so P mechanically reopens fewer across
two evolutions. That is "fewer parts," not demonstrably "absorbs change better." I therefore **discount
P's M1 lead**: of the 4-point gap over Q, ~2–3 points are explained by smaller surface, leaving a
comparable gap of ~1–2. Per the charge, "a survival count on a design that did less is not a virtue."

---

## Local-vs-pervasive classification (mandatory)

| Fault | Fix touches | Seam change? | Class |
|---|---|---|---|
| **P: tax modelled as a movement inside the discount ledger** (TAX status + `tax_amount` in `Adjustment`; `Explanation.final == gross`; INV-7 spans tax) | `result.py`, `pricing.py`, `market.py` (≥3) | Yes — `Explanation.final` contract + `Adjustment`/`AdjustmentStatus` shipped type | **PERVASIVE** — may move the ranking |
| **Q: `Quote.payable` restates `quote.tax.payable`** | one field in `explain` | No | **LOCAL BLEMISH** — recorded, cannot rank |
| **R: none material** (tax is a clean second account, `net+tax==payable` owned in `tax`) | — | — | — |

---

## Verdict

**The contested call does not survive. Verdict: Q — narrowly, flipping from P.**

Recomputed consequence measures:

| | M1 (given) | M2 (mine) | M3 (mine) |
|---|---|---|---|
| P | 5 *(discounted for comparability toward ~7–8)* | **2** | 9 |
| Q | 9 | 4 | **8** |
| R | 8 | 4 | 9–10 |

At face value P sums best, driven almost entirely by M1. But M1 is inflated (charge 3): P did modestly
less — fused tax, shared catalog, hard-fail, more deferred — so it had fewer seams to survive. De-inflate
M1 and **P and Q are level on M1–M3**: P keeps a real but soft M2 edge (leanness, on the contestable
per-market-catalogue reading); Q takes M3 (the forward measure the rubric elevates above retrospective
M1). At that near-tie, M4 is the tiebreak the rubric explicitly allows — and P carries the **sole
pervasive integrity fault**, whose cost is not merely cosmetic but already shows up in M3 (C-next-1, and
D1). Q's only blemish is local.

**Which measure flips it: M3, reinforced by M4.** M3 is where P's tax-in-ledger coupling is paid for —
Q's seams keep every tax-composition change (C-next-1, a second tax) out of the discount ledger, which P
cannot. M4 confirms the fault is pervasive, not the barred local blemish the first pass assumed, so the
rubric permits it to decide the P/Q near-tie. M1, the measure that carried P's first-place finish, is the
one I discount for non-comparability.

Honest confidence: this is close to a P/Q wash, not a rout — P's leanness (M2) is genuine and its M1
number is real if partly circumstantial. R is a clean, integrity-sound third, edged out by Q on M3 and on
currency-readiness (R excluded currency outright). But the specific thing the first pass did — rank P
first while barring its tax-in-ledger fault as consequence-free — is wrong twice over: the fault is
pervasive, and its consequence is visible on the forward measure. Corrected, Q leads.
