# Verdict — checkout pricing service, blind final designs P / Q / R

Judged by consequence, per RUBRIC.md: rank on M1 + M2 + M3; M4 may only break a near-tie or downgrade a
**pervasive** integrity fault; a **local** blemish (fix <3 components, no seam change) may not move the
ranking. Every cited fault is classified LOCAL vs PERVASIVE with its fix footprint named.

One structural fact separates the field and drives most of what follows:

- **P** prices with a **single shared promotion catalog** and passes the market as a context to
  `price(cart, catalog, market)`. Tax is a *terminal entry appended to the explanation ledger* (a `TAX`
  Adjustment; `+tax` in NORTH, delta-0 with a `tax_amount` side-field in SOUTH). Market is a behavioural
  `Protocol` (`NorthMarket`/`SouthMarket`).
- **Q** and **R** both use **one promotion file per market**, a **market-mismatch error**, and a
  **routing guard**, and both model tax as a *decomposition beside the explanation* (Q `TaxView`,
  R `TaxFigure`), with the market as a 4-field data value (`MarketProfile` / `TaxPolicy`).

---

## M1 — Change absorption (given, authoritative)

| P | Q | R |
|---|---|---|
| **5** | 9 | 8 |

P absorbed the two evolutions with the fewest components/seams reopened, by a wide margin.

---

## M2 — Accidental complexity (count of machinery the problem did not force)

The forcing test: would *every* correct design of this exact product need it? The rubric's own worked
example — "a per-market catalogue file plus a market-mismatch error plus a routing guard is accidental
*iff* a single shared catalogue prices every given case" — is decidable from the text: **P's single shared
catalog prices every stated case** (C1 NORTH `SAVE10`, C2/C5 SOUTH `SAVE10`/`COFFEE3` — the same codes,
same meaning, in both markets; §3, §10). So the per-market split and its guard machinery are accidental for
the designs that carry them.

**P — 2 items (lowest).**
1. `AdjustmentStatus.TAX` — a third status class introduced solely to seat tax inside the explanation
   ledger; a decomposition-beside-explanation (Q, R) needs no tax status.
2. `Adjustment.tax_amount` + the SOUTH delta-0 "embedded VAT" entry — a field and a zero-movement ledger
   row that exist only because tax is carried as a ledger entry (`market.tax_entry`). (`Market.line_tax`/
   `cart_tax` are forced by the genuine per-line-vs-cart-once requirement; only the ledger seating is
   accidental.)

P notably **avoids** the entire per-market-catalog / mismatch-error / routing-guard cluster by pricing
from one shared catalog — the machinery the rubric names as the canonical accidental item.

**Q — ~5 items (highest).**
1. One promotion file **per market** (a shared file prices every given case).
2. `MarketMismatchError` — routing fault error class.
3. The I30 routing guard / entry check.
4. `MarketProfile.currency` — single currency is stated; Q itself concedes the move is "not forced."
5. `MarketProfile.minor_units` — both markets are 2dp today.
(Items 4–5 are accidental *for today* but buy C-next-3 resilience — see M3; the rubric counts both sides.)

**R — ~4 items (middle).**
1. One catalogue file **per market**.
2. Refusing a catalogue of another market — a distinct wiring-fault class with its own exit status.
3. The catalogue-market-match guard in `engine`.
4. `markets` registry passed as a third `price()` argument, plus the `CartTax.summed` dedicated
   constructor — mild machinery (Q and P produce the summed cart tax without a dedicated type).

**M2 ranking: P (2) < R (4) < Q (5).** Tracks M1.

---

## M3 — Blast radius of the three pre-registered changes (named components, seam quoted)

### C-next-1 — third market, reduced VAT on *some* products (rate per-line; needs product metadata the cart lacks)
This is cross-cutting for **all three**, because none carries product tax metadata on the cart today.

| | Components reopened | Seam that moves |
|---|---|---|
| **P** | `model` (CartLine gains tax-class), `market` (new reduced market), `pricing` (tax pass threads per-line metadata), `cli` — **4** | `def line_tax(self, final_listed: Money) -> TaxBreakdown \| None` widens to carry the line's product/rate |
| **Q** | `model` (CartLine metadata), `market` (`tax_rate` → `rate_for(line)`), `tax`, `explain`, `api/cli` — **5** | `def tax_for(amount, profile) -> TaxView`; `MarketProfile.tax_rate: Decimal` becomes per-line (Q §9 flags this as its one seam-mover) |
| **R** | `models`, `markets` (`TaxPolicy.rate` → per-line), `tax`, `engine`, `cli` — **5** | `assess(policy, amount)`; `TaxPolicy.rate: Decimal` becomes per-line (R §9 open item) |

P is one lower only because tax assembly lives in `pricing` (no separate `explain`/`journal` seam to cross).

### C-next-2 — customer-dependent eligibility (customer_id carried, read by nothing)

| | Components reopened | Seam |
|---|---|---|
| **P** | `promotions` (rule/CartView reads customer_id — CartView exposes no customer today), `catalog` (criterion schema), `pricing` — **3** | `Promotion.evaluate` / `CartView` gains customer context |
| **Q** | `engine` ("gains a customer_id check against catalog criteria; the field is already in the model"), `catalog` — **2** | engine resolve step |
| **R** | `engine` (eligibility filter — "the natural hook for a future eligibility rule"), `catalogue` — **2** | engine resolve / `markets.resolve` |

Q and R pre-identified the `customer_id` hook; both keep it engine-local. P routes eligibility through the
rule/CartView seam, costing one more.

### C-next-3 — second currency

| | Components reopened | Seam |
|---|---|---|
| **P** | `money` (`CENT = Decimal("0.01")` hardcoded, sole quantizer), plus a home for currency P carries nowhere (`model`/`market`), `cli`/`result` — **3–4** | `Money.__init__` / `CENT` quantum |
| **Q** | profile already carries `currency` + `minor_units` ("the quantum has one home"); a same-decimals currency is a profile row + `allocation`/`api` format review — **~2** | `MarketProfile.minor_units` (already parameterized) |
| **R** | `money` ("two decimal places", fixed; non-goal "No currency handling"), `models`, `markets`/new table, `allocation`, `cli` — **4–5** | `money.quantize` quantum |

Here Q's M2 items 4–5 pay off: the quantum/currency seam was pre-drawn, so Q has the smallest blast.

### M3 totals (lower better)
| P | Q | R |
|---|---|---|
| ~10 | **~9** | ~11 |

M3 is close between P and Q (within noise) and worst for R. Q's slight edge comes entirely from the
currency/minor_units generality that counts *against* it on M2 — the same machinery, scored on both sides.

---

## M4 — Essential-model integrity (mandatory LOCAL/PERVASIVE classification)

**Q — cleanest model.** One append-only journal; tax owned solely by `tax`; four projections; three-member
`AdjustmentKind`. The one duplication — `Quote.payable` restating `quote.tax.payable` — is a single value,
one owner (`tax`), emitted once and asserted equal (I31), added on product instruction (Q30).
*Classification: LOCAL / non-fault.* A hypothetical removal touches `model` + `explain` + `api` but changes
no concept's ownership; it is required, not a defect.

**R — clean model.** Two accounts (ledger + tax) joined at exactly one number (`basis_amount ==
ledger.current`); tax is one type (`TaxFigure`, `source ∈ {FIGURED, SUMMED}`) with `net`/`payable` as
projections. No cited integrity fault; the `markets` third argument is surface, not an altitude problem.
*Classification: no fault to rank.*

**P — one integrity fault: tax modelled at two altitudes.** Tax is both a **movement** (a `TAX` Adjustment
in the `Explanation` ledger) and a **decomposition** (`TaxBreakdown` net/tax/gross); the SOUTH tax entry is
a ledger row carrying delta 0 with the real figure in a side-channel `tax_amount` — a "movement" that moves
nothing, inside a structure P otherwise defines as a ledger of movements.
*Classification of the fix:* unseating tax from the ledger touches **`result.py`** (drop `TAX` status /
`tax_amount`, change `Explanation`), **`pricing.py`** (drop the append in steps 10–11), and **`market.py`**
(drop `tax_entry`) = **3 components, and it alters the shipped `Explanation`/`Adjustment` contract.** By the
mechanical threshold (≥3 components OR a seam change), this meets **PERVASIVE-by-footprint**.

But the rubric bars a fault from deciding the verdict unless it predicts a consequence, and requires the
consequence lens over the mechanical one:

- **It is untriggered.** None of the three pre-registered M3 changes reopens the ledger-vs-decomposition
  seating (C-next-1 flows through `line_tax`/`tax_entry` regardless; C-next-2 and C-next-3 never touch it).
- **Its measured change-absorption is the best in the field:** P's M1 is **5**, the lowest. The one prior
  reopening it forced (the rounding-mode parameter on `Money`) is already inside that count.
- Under P's stated model ("the explanation is the ordered walk list → gross"), tax as the terminal step is
  a *single coherent altitude* with the breakdown as a derived view — the same defence Q uses for
  publishing `net`/`tax`/`payable` together. So its status as a "fault" is genuinely borderline, and its
  pervasiveness is **latent, not realised**.

This is precisely the case the rubric was written for: Q and R both editorialise at length that
tax-in-the-ledger is the wrong shape (Q §1.2, R Decision 15). That is a taste-based smell. The rubric
forbids "a single removable decision" from outranking "a structurally leaner design." I record the fault and
its footprint, and **decline to rank on it.**

---

## Verdict — **P**

**Decided by M1 and M2, with M3 close enough not to overturn.**

- **M1:** P = 5, decisively below R (8) and Q (9).
- **M2:** P carries the least unforced machinery (2), because its single shared catalog avoids the
  per-market-catalog + mismatch-error + routing-guard cluster the rubric names as accidental and that both
  Q (5) and R (4) build.
- **M3:** P ≈ 10, Q ≈ 9, R ≈ 11 — P and Q within noise, R worst. Q's marginal M3 lead is bought with the
  very currency/minor_units generality that is accidental against it on M2, so it does not offset P's M1/M2
  lead.

P leads the aggregate of the three consequence measures. Its **only** integrity fault is the
tax-in-ledger seating; I have classified that fault's fix-footprint as meeting the PERVASIVE threshold
(`result.py`, `pricing.py`, `market.py` + the `Explanation` seam), **and I am explicitly declining to rank
on it** — because it is untriggered by M1's measured history and by every pre-registered M3 change, and is a
coherent single model under P's walk-to-gross framing. Letting Q's or R's articulate distaste for it invert
P would be exactly the smell-hunt-over-structure error the rubric exists to prevent.

Q is the strongest essential model (M4) and R is a competent middle; but M4 may not promote a design over
one that leads M1–M3, and neither leads the consequence measures. **The winner is P.**
