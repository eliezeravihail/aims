# Quality / ownership reading — blind designs P, Q, R (checkout pricing, stage 3)

Read as an invariant-ownership / correctness-of-encapsulation reviewer: hard on leaks across
seams, on a rule enforced in more than one place, and on an implementation type escaping a
boundary. Not impressed by volume. Every load-bearing claim carries a quotation; self-claims are
verified, not trusted.

The stage's whole weight lands on one seam: **where does tax sit relative to the promotion
explanation, and who owns the "deltas sum exactly to the difference" invariant once tax exists?**
That question, and the C4 case (`three 0.15 lines give 0.06, not 0.08`), separate the three.

---

## Design P

### 1. Code smells (feature envy, shotgun surgery, god object, anemic, primitive obsession)

- **Shotgun surgery / rule enforced in >1 place — the defining smell here.** P folds tax into the
  price-movement ledger, and the deltas-sum invariant loses its single owner:
  `| INV-7 | ... **now including the tax entry** | \`PricingEngine\` ledger + \`Allocator\` + market
  tax entry |`. Three co-owners for the one invariant the product was bought for. A change to how
  tax joins the walk now potentially touches the engine, the allocator's residue story, and the
  market at once.
- **Primitive obsession (minor):** the rounding mode crosses as a bare stdlib string —
  `def __init__(self, amount..., rounding: str = ROUND_HALF_UP)` and `gross.fraction(1, 6,
  ROUND_HALF_EVEN)`. Q and R both give the mode a named closed type (`TaxRounding` / `Rounding`
  enum); P leaves it a `str`. Removable local blemish, not verdict-deciding.
- **Not anemic; not a god object.** `Market` carries real behaviour (`line_tax`/`cart_tax`/
  `tax_entry`), the engine stays focused ("The engine's reasons to change are unchanged ...; tax is
  not among them"). Good.

### 2. Interfaces & encapsulation

- `Market(Protocol)` is a genuine abstraction, not decorative: "The two markets are not two values
  of a rate; they differ in *structure* — additive vs embedded, cart-level-once vs per-line-summed
  ... A describable third market ... is easy to name." Two real, structurally-different
  implementations already satisfy §2.
- **But the encapsulation leak is that the market speaks the *ledger's* vocabulary.**
  `def tax_entry(self, breakdown: TaxBreakdown) -> Adjustment | None` — the market *constructs* an
  `Adjustment`, the engine's own output type, and the engine appends it: "it *appends* the
  market-supplied tax entry ... the **content** of the tax entry (its delta and tax amount) is the
  market's." So `Adjustment` now has two constructors (engine and market) and the deltas-sum
  invariant is co-authored. Q and R keep the tax component returning *its own* type and never
  touching the ledger; P does not.
- **`Adjustment` is overloaded with a per-variant field.** `tax_amount: Money | None = None # TAX
  only`, sitting beside `superseded_by`/`would_be_delta` (`SUPERSEDED only`). Three optional fields,
  each meaningful for exactly one status — a flat record standing in for a discriminated union, the
  §3 "cram a foreign field into the richer type" shape. Of the three designs P's adjustment record
  is the most foreign-field-laden, and it is so *because* it absorbed tax.
- Tell-Don't-Ask is otherwise honoured: "it is *told* the tax picture and never inspects a rate or a
  mode to compute tax itself."

### 3. Genericity calibration (§2 floor/ceiling)

- The `Market` Protocol is defensible by the two-implementations test, but arguably **over-generic
  for what varies**: P itself lists the variation as `additive vs embedded, cart-level-once vs
  per-line-summed, half-up vs half-even` — which is exactly four data axes. Q and R prove that
  variation is fully data-expressible by deriving all of it from a profile in one function; against
  that proof, two hand-written `Market` classes are a heavier abstraction than the concept needs.
  Not wrong (a third market = one class), but not the tightest fit.
- **Credit under the subtractive pass:** P alone declines the per-market-file machinery —
  "The promotions catalog is **shared** across markets" — so it carries no `MarketMismatchError`, no
  routing-fault category, no cross-check guard that Q and R both build. For a reviewer running the
  subtractive pass this is real: P removed a whole guard+error+fault-class because its model gives
  routing nothing to get wrong. It offsets, but does not erase, the ledger-fold cost, because the
  fold touches the *core* invariant and the *core* output type.

### 4. Cohesion & coupling

- The market/tax concern is cohesive (rate, inclusivity, rounding mode+level, and explanation
  placement all in `Market`). But its coupling to `result.Adjustment` and its co-ownership of INV-7
  is the coupling that bites: "the market owns *everything* about tax ... and *nothing* about
  discounts" is overstated, since via `tax_entry` it owns a slice of the discount ledger's type.

### 5. Naming & reasonable-reader (§11)

- **A real surprise: a frozen structure is mutated in prose.** `class Explanation:` is
  `@dataclass(frozen=True)` with `final: Money`, yet §7 says "set `line.explanation.final =
  bd.gross`" and "set `cart.explanation.final = cbd.gross`". A reasonable reader takes that as
  in-place mutation of a frozen field (it must really be reconstruction). The append-then-set-final
  idiom reads as ledger mutation and undercuts the "amount is a projection of its explanation"
  claim at exactly the tax step.
- `AdjustmentStatus.TAX` with `delta` sometimes `+VAT` and sometimes `ZERO` (with `tax_amount`
  carrying the real figure) is a status whose `delta` means different things by market — a reader
  must know the market to read the row.

### 6. Single responsibility & size (§8, §12)

- Most compact of the three and mostly well-sectioned; each module's one reason to change is
  stated. The SRP crack is INV-7's three owners (above), not module sprawl.

**P in one line:** a genuine market abstraction, admirably lean on the catalog side — but it made
tax a delta in the price ledger, which splits the deltas-sum invariant across three owners, overloads
`Adjustment` with a tax-only field, and lets the market author the ledger's own type.

---

## Design Q

### 1. Code smells

- **Strong on shotgun surgery / single ownership:** "Each has exactly one owner who is capable of
  violating it; the component boundaries in §4 are chosen so that this is true." And the tax concern
  is quarantined: "**CartView carries no tax information and no market profile, and this is the
  load-bearing omission of stage 3.**"
- **No god object, not anemic.** Journal/ledger carries behaviour; rules propose, engine disposes.
- **The one place the subtractive pass bites: redundant stored money on the tax value.** `TaxView`
  stores `taxable_amount`, `tax`, `net`, `payable` as four separate `Decimal` fields and then keeps
  them honest by assertion: "the invariant checker gets three redundant statements of one truth
  (I21, I22, I23)." That is a stored redundancy that must be reconciled — the reviewer's least
  favourite pattern — where R derives the same fields (see verdict).

### 2. Interfaces & encapsulation

- **Best single-construction discipline of the three, and it's import-checkable.** "`Adjustment`,
  `LineQuote`, `Quote` and `TaxView` are constructed in exactly two places — `explain` and `tax`
  ... It cannot be unit-tested into existence; it is kept by not adding a third constructor." And
  "if `Quote(` appears anywhere outside this module, or `TaxView(` anywhere outside `tax`, the
  invariant is gone."
- **Tax is a separate account, not a ledger row** — the correct seam: "The journal records
  *movements of price*. Tax is not a movement; it is a *decomposition* of a price that has already
  been reached." The adjustment enum stays honest: "`AdjustmentKind` has three members ... An
  engineer who needs a tax row has not read §1.2."
- The tax value is well-segregated (§3): it exposes only `treatment`, `rate`, `derivation` plus the
  money — the fields a stored quote needs to re-explain itself — not the whole profile.

### 3. Genericity calibration

- Markets as a **closed data table**, not classes: "a tax regime is law, not merchandising ... a
  *closed table of named markets*, so adding one is a reviewed code change with a test row, not a
  configuration surface." Correctly calibrated — the variation is data, and Q represents it as data.
- `MarketMismatchError` / I30 earns its place as a guard, not ceremony: "Two parties independently
  know which market a request is for ... requiring agreement is a **total guard against the one new
  mistake this system can make**." Verified: neither party derives the fact, so the redundancy is a
  check, not duplication.

### 4. Cohesion & coupling

- Dependencies point one way; the market-blindness claim is stated as a *checkable* property:
  "**Nothing upstream of `tax` reads `treatment`, `rate`, `granularity` or `rounding`** ... a test
  that prices the same cart under both profiles and asserts the journals are equal (case F7)." This
  is the cleanest formulation of the market-blind pipeline among the three.

### 5. Naming & reasonable-reader

- Vocabulary is spent deliberately (§2.1 "five words for money, fixed once"; the `delta`-signed /
  `amount`-magnitude lexical rule of §5.5). `payable` is promoted to top level on instruction and
  the restatement is named and bounded: "**I31 is the only restatement in the contract, and it is
  there on instruction.**" No surprises.

### 6. Single responsibility & size

- **Longest doc by ~60%, and the length is decidedness, not indecision** ("§13.5 Nothing is open").
  But some of the bulk is invariant-machinery for guarantees R obtains structurally — "I24 and I25
  are the same fact said twice on purpose", plus the three-field tax redundancy. Thorough and
  correct; slightly more scaffolding than the guarantee strictly needs.

**Q in one line:** the tightest single-construction / import-checkable ownership story, tax correctly
kept off the ledger — but it stores the tax identity as redundant fields and checks it, instead of
deriving it, which is the one place it stops short of its own projection doctrine.

---

## Design R

### 1. Code smells

- **No rule enforced twice; the identities are single-owned by *construction*.** "`current` is a
  projection, not a field. There is no second copy of the amount to drift, so 'the explanation and
  the amount disagree' is not a bug we test for — it is a state the type cannot hold." The same
  discipline is extended to tax (see §2).
- Not anemic (ledgers, tax figures carry projection behaviour), no god object; `money`, `allocation`,
  `ledger`, `tax` are leaves that "know nothing about promotions."
- **Primitive obsession avoided** on the rounding mode: `rounding: Rounding # HALF_UP | HALF_EVEN,
  from the money module` — a named closed type, where P used a bare `str`.

### 2. Interfaces & encapsulation

- **The decisive property: every reconciling identity is a single-owner projection — price *and*
  tax.** For price: `current` is derived (above). For tax: `TaxFigure.net`/`payable` are
  `@property`, and R says so in the same breath as the ledger — "`net + tax == payable` is
  arithmetic the type performs rather than an invariant the code maintains — the same discipline as
  `Ledger.current`." There is no constructor argument for `net` or `payable`, so a disagreeing tax
  figure is unrepresentable, not merely detected.
- **Two accounts joined at one number, one owner each.** "the two accounts join at one number that
  exists once"; `basis_amount` "is the ledger's `current`, not a copy computed alongside it." Tax is
  kept off the chain for the same structural reason Q gives: "Putting tax in the chain would break
  the delta-sum rule in one market, invent a code-less step in both."
- **The `net + tax == payable` identity has exactly one home, by explicit design choice against the
  two-class temptation:** "One function with one branch keeps `net + tax == payable` in a single
  place for both markets ... A `NorthTax` and a `SouthTax` class would give that invariant two
  places to be true differently, and the third country would add a third." This is the ownership
  argument stated as a first principle.

### 3. Genericity calibration

- **C4 made structurally unreachable, not merely tested** — on the exact case the stage exists for:
  "Making the cart figure a *different constructor* — one that takes line figures and cannot take an
  amount — means the wrong number is not merely forbidden, it is *unreachable*: there is no code
  path in which a per-line market rounds at the cart."
  - *Self-claim checked and lightly overstated:* the signature is
    `cart_tax = CartTax.summed(line_taxes, cart_ledger.current)` — `summed` *does* receive the cart
    amount (as `basis_amount` for the net/payable projections). What is genuinely unreachable is
    rounding it: `summed` computes `tax = sum(t.tax for t in line_taxes)` with "no `assess()` call,
    no rounding, at the cart." So "cannot take an amount" is imprecise; "cannot round an amount" is
    the true and still-strong claim. Noted per the rules, not verdict-changing.
- Markets as a declared table beside code (Decision 16), same correct calibration as Q, with the
  registry passed in ("`price()` takes what it depends on") rather than imported.

### 4. Cohesion & coupling

- Market-blindness stated as a structural fact: "The fold's code contains the word 'market' exactly
  nowhere, and that absence is the whole compatibility guarantee." `money` owns the single rounding
  site; `tax` owns `net + tax == payable`; `allocation` owns parts-sum-to-whole — "Every money
  guarantee this service makes is one of those four, composed by the engine." Clean leaf cohesion.

### 5. Naming & reasonable-reader

- Three-column result named explicitly per market, tax derivation carried so a figure is
  reproducible: "*17% of 22.50, added, half-up, once for the cart* can be reproduced by a support
  agent with a calculator, and a `SUMMED` cart figure tells an auditor why it is not what rounding
  the cart would have given." No surprises; the `source: FIGURED | SUMMED` field pre-answers the C4
  support ticket.
- Minor ISP note: `TaxFigure` carries the whole `policy: TaxPolicy` (dragging `market`, `name`,
  `level` into any consumer of a figure), where Q exposes only the three facts a reader needs. A
  small counter-point to Q's tighter segregation — outweighed by the projection edge.

### 6. Single responsibility & size

- More compact than Q while making the *stronger* structural guarantee. Prose-heavy Decisions/Risks
  sections are discussion, not machinery; the subtractive pass finds little unpaid ceremony (even
  `allocation` for a future cart-level per-line tax is named and *not built*: "Not built, because
  nobody has asked").

**R in one line:** the one design that applies its own projection doctrine uniformly — price and tax
are both derived, both single-owned, C4 is unreachable rather than tested — at lower page-count than Q.

---

## Verdict

**R**, narrowly over Q, with P third.

**The deciding property: every reconciling identity in the system is owned in exactly one place *as a
derivation*, never as a stored value that must be checked against another.**

- **R** holds it completely. The price identity is a projection (`current` is not a field), and R
  extends the *same* discipline to the new stage-3 identity: `TaxFigure.net`/`payable` are
  `@property` computed from `basis_amount` + `tax`, "the same discipline as `Ledger.current`", and
  the C4 cart figure is built by a constructor that cannot round an amount — unrepresentable, not
  tested. `net + tax == payable` lives in "a single place for both markets", explicitly to deny the
  two-class future where it would be "true differently" in two spots.
- **Q** holds it for price but *concedes it for tax*: `TaxView` stores `taxable_amount`, `net`,
  `payable` as separate fields and keeps `net + tax == payable` true by asserted invariant (I21),
  accepting "three redundant statements of one truth" as a cross-check. That is the reviewer's
  least-favourite shape — a stored redundancy reconciled by a runtime check — and it is the one
  place Q stops short of the projection doctrine it champions everywhere else. Q's compensating
  strengths are real (import-checkable single construction of `Quote`/`TaxView`; tighter field
  segregation on the tax value; the crispest market-blindness test), which is why this is narrow,
  not decisive.
- **P** breaks the property at the core: by folding tax into the delta ledger it gives INV-7 three
  co-owners (`PricingEngine ledger + Allocator + market tax entry`), gives `Adjustment` two
  constructors (engine and market) plus a status-only `tax_amount` field, and — at the tax step —
  reads as mutating a `frozen=True` `Explanation.final`. P earns genuine credit for the leanest
  catalog model (a shared catalog that deletes the whole mismatch-guard class), but that economy is
  at the seam; the invariant fracture is at the centre.

No design is unsound. The order is a cleanliness ordering on one axis the disposition privileges:
who owns the money identities, and whether they are made unrepresentable-when-wrong or merely
checked. R > Q > P on exactly that.
