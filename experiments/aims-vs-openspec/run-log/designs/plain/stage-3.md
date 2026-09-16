# Cart Pricing Service — Architecture (Stage 3)

Status: **stage 3 closed.** All eleven stage-3 questions answered by the product owner and folded in
(§13.4); three were delegated back to engineering and are recorded with their reasoning rather than left
as assumptions. Complete and self-contained: this document supersedes stages 1 and 2 as the description
of the product and needs no other document to be read alongside it. Every stage-1 and stage-2 product
answer is still in force and restated here (§13.1, §13.2). No implementation.

Substrate: Python 3.11+, standard library only, single process, **single currency** (Q26), no
persistence, no network, no UI, no database. `decimal.Decimal` available.

---

## 1. What this service is

One question, answered purely: **given a cart, some codes and the market it is being priced for, what
does each line cost, what does the cart cost, how much of that is tax, and why?**

It is a *calculator*, not a workflow. It holds no state between calls, talks to nothing, and has exactly
two inputs — the **cart** (from the caller, per request, and as of this stage naming the market it is
for) and the **catalog** (a file the product owner edits, one per market). That shape is still the single
most important structural fact about the system:

- A pure function `price(cart, catalog) -> Quote` is the whole product. Everything else is an adapter.
- Because it is pure, it is exhaustively testable without fixtures, clocks, servers or mocks.
- Because the catalog is data, adding a code is an edit, not a deploy.

### 1.1 The stage-3 requirement, and the one structural decision it forces

We now sell into two countries whose tax law disagrees about almost everything that matters:

| | **NORTH** | **SOUTH** |
|---|---|---|
| What a listed price means | tax-**exclusive** | tax-**inclusive** |
| VAT rate | 17% | 20% |
| What promotions act on | the listed (net) amount | the listed (gross) amount |
| Where tax is rounded | once, at the **cart** | per **line** |
| Rounding mode for tax | half-**up** | half-**even** |
| Per-line tax reported | no | **yes — the invoice requires it** |
| The cart's tax is | computed from the cart amount | the **sum of the line figures** |

Four independent axes, two settings each. The naive response is two pricing paths — a `NorthPricer` and
a `SouthPricer`, or a market flag threaded through the engine — and it is wrong for a reason that is
visible before any code is written: **the promotion arithmetic is identical in both markets.**

That is not a coincidence, it is what the product owner said. *"Promotions apply to the gross
(tax-inclusive) amount, exactly as a customer would expect — 10% off a 12.00 shelf price is 1.20."* In
NORTH, promotions apply to the listed amount and 10% off a 12.50 shelf price is 1.25. In both markets
the pipeline takes the numbers on the shelf, applies promotions to them, and stops. The pipeline never
needs to know which convention those numbers follow, because it treats them identically either way.

So the decision that shapes this stage is a negative one:

> **The engine, the rules, the journal, the allocator and the exclusion contest do not know that tax
> exists.** They are byte-for-byte the stage-2 components. Market-awareness is confined to one new,
> downstream, pure component (`tax`, §4.8) and one new piece of configuration (`market`, §4.2).

Everything in the tax requirement then lands as *a second reading of a number the pipeline already
produced*, and the four axes above become four fields of one data value (§2.2), not four branches.

### 1.2 Why tax is not an adjustment

The obvious alternative — and the one stage 2's own extension table predicted (*"Tax / shipping: new
phases after 30"*) — is to make tax a phase, so that it becomes an ordinary row in the explanation with
a delta and a running balance. Stage 3 rejects that prediction, having now seen the actual requirement.

**The journal records *movements of price*. Tax is not a movement; it is a *decomposition* of a price
that has already been reached.**

- In SOUTH nothing moves at all. The 1.80 of tax inside a 10.80 shelf price was always there; it was
  there before the promotion, it is there after, and no step of the calculation put it there. An
  adjustment row with a delta of anything at all would be a fabrication, and a row with a delta of
  `0.00` would be padding — which §2.3 forbids by construction.
- In NORTH something does look like a movement: `+3.83` on top of `22.50`. But making it a row breaks
  the property the product owner bought stage 2 for: *the deltas add up to what came off*. On C1 the
  deltas would sum to `-2.50 + 3.83 = +1.33`, a number that is neither what came off nor what is owed.
- And a design that models NORTH's tax as an adjustment must model SOUTH's as something else, so it
  carries two structures for one concept before the third country has even been named.

One structure covers both: a **`TaxView`** (§2.4) attached to a final amount, saying what that amount is
made of. It has the same shape in NORTH and SOUTH, and one identity holds in both:

> `net + tax == payable`

In NORTH, `payable` is the amount plus tax. In SOUTH, `payable` *is* the amount and `net` is what is left
when the tax is taken out. Same fields, same identity, opposite treatment — one enum member apart.

### 1.3 "An explanation that cannot account for the tax is not an explanation"

The product owner's constraint is honoured without touching the adjustment chain. The explanation ends
exactly where the tax begins, and that junction is an invariant, not a convention:

> **I22: a `TaxView`'s `taxable_amount` is the `final` of the explanation it accompanies.**

So the account is continuous. A customer asking about a SOUTH line is told: *list 12.00; SAVE10 took
1.20; that leaves 10.80; of that 10.80, 1.80 is VAT at 20% and 9.00 is the price before tax.* Every
figure in that sentence is a published field, and the join between the two halves is checked. The
support view (§4.10) is required to render both halves together, which is where "wherever support will
see it" is discharged for tax as it already is for non-events.

What the explanation does **not** do is pretend tax was a step. That distinction is the whole of §1.2 and
it is the first thing a reviewer should agree or disagree with.

### 1.4 The stage-2 property, restated and still true

Stage 2's centre was: **the explanation is not derived from the amounts; the amounts are derived from the
explanation.** Pricing writes one append-only record — the **journal** (§4.7) — and every promotion-side
money figure is a fold of it, computed nowhere else.

Stage 3 keeps this exactly, and adds one carefully-bounded exception, stated as an invariant rather than
left implicit:

> **I14 (restated): every money figure in a `Quote` is either a fold of the journal, or a function of one
> such fold and the `MarketProfile`, computed in `tax` and nowhere else.**

There are still exactly two places a money figure can be born, and both are single modules with no other
callers. "The explanation and the amount disagree" and "the invoice and the tax figure disagree" are both
unrepresentable for the same reason: there is one source for each, and the second one is a pure function
of the first.

### 1.5 Entry point: library first, thin CLI adapter

**Decision (kept from stage 1).** Ship a library (`pricing.price`) with a thin CLI wrapper. Not an HTTP
endpoint. The substrate forbids the network, so a "local HTTP endpoint" would only be a loopback socket
wrapping the same function while adding a server lifecycle, port config, request framing and a second
error channel to get right.

```
python -m pricing price    --catalog north.toml --cart cart.json   # JSON quote on stdout
python -m pricing validate --catalog north.toml [--strict]         # lint the promo file
python -m pricing explain  --catalog north.toml --cart cart.json   # the explanation, rendered
```

The signature of `price()` is **unchanged** at this stage — `price(cart, catalog) -> Quote`. There is no
`--market` flag and no market parameter: the **cart** names its market (§2.3) and the **catalog** names
the market it prices for (§7.5), and `price()` refuses the pair if they disagree (I30). A process that
serves both countries loads two catalogs and routes each cart to the matching one; routing is the
caller's job, and mis-routing is the one mistake the guard exists to make impossible.

If HTTP is later required, it is a new adapter module over the same `price()` call, with no change to the
core. That is the intended seam, not a hypothetical one.

### 1.6 A note on retention

There is no persistence in the substrate, and none is added. The explanation *and now the tax view*
travel **inside the quote**, as data, so a caller that stores the quote has stored the working. It stays
valid and legible a year later without re-running pricing against a catalog that has since changed —
and, newly important, without needing today's market profile table to interpret it: each `TaxView`
carries its own `rate`, `treatment` and `derivation`, so a quote from before a rate change still explains
itself (§2.4). That is what an audit needs, and it is why these are values in the response rather than
log lines.

The quote still carries **no version stamp** — no catalog revision, no quote id, no timestamp (PO at
stage 2: *not now, build for today*). Two of the three would require something the substrate does not
have; the third is a field this service could only copy from its caller. §9 records what it costs.

---

## 2. The contract

Everything crossing a boundary is an immutable, `frozen=True` dataclass. Money is `decimal.Decimal`,
never `float`, and never at the boundary as a float — see §5.

### 2.1 Five words for money, fixed once

Stage 2 had two words, `gross` and `net`, and both are now ambiguous: in SOUTH, "gross" is what the
product owner calls a tax-*inclusive* amount, while stage 2 used it for "before discounts"; and a field
called `net` that contains tax would be actively misleading on a SOUTH invoice. Stage 2 established the
principle that resolves this — *the field name carries the convention* (§5.5's sign rule) — so the
vocabulary is fixed here, once, and every field name in the contract obeys it:

| Word | Means | NORTH | SOUTH |
|---|---|---|---|
| **list** | `unit_price × quantity`, before any promotion, in the market's own convention | tax-exclusive | tax-inclusive |
| **amount** | after every promotion, in the market's own convention. What the pipeline computes and what the explanation's `final` is | tax-exclusive | tax-inclusive |
| **tax** | the VAT figure for the thing it is attached to | 17% of `amount` | the 20% already inside `amount` |
| **net** | `amount` excluding tax | `== amount` | `amount − tax` |
| **payable** | `amount` including tax | `amount + tax` | `== amount` |

`net + tax == payable` in both markets, always (I21). `amount` is whichever of `net` and `payable` the
market's listing convention names (I23) — that single sentence is the entire difference between the two
tax regimes as far as the output shape is concerned.

**`gross` and `net` as stage-2 field names are retired.** `LineQuote.gross` becomes `list_amount`,
`LineQuote.net` becomes `amount`, `Quote.gross_subtotal` becomes `list_subtotal`, `Quote.total` becomes
`amount`. §2.7 is the migration table; the values are unchanged to the cent in NORTH (C6), only the
spellings move.

### 2.2 The market

```python
class TaxTreatment(StrEnum):
    EXCLUSIVE   # listed prices carry no tax; tax is added to reach what is payable
    INCLUSIVE   # listed prices already contain tax; tax is extracted from what is payable

class TaxGranularity(StrEnum):
    CART        # one tax figure, computed and rounded once from the cart amount
    LINE        # one tax figure per line; the cart's tax is their sum

class TaxRounding(StrEnum):
    HALF_UP
    HALF_EVEN

@dataclass(frozen=True)
class MarketProfile:
    id: str                      # "NORTH" | "SOUTH" — echoed into every Quote
    currency: str                # three uppercase letters
    minor_units: int             # 2 for both markets today (§5.7)
    tax_rate: Decimal            # percent, normalised to 4dp: 17.0000 / 20.0000
    treatment: TaxTreatment
    granularity: TaxGranularity
    rounding: TaxRounding
```

The two profiles in force:

| | `NORTH` | `SOUTH` |
|---|---|---|
| `tax_rate` | `17.0000` | `20.0000` |
| `treatment` | `EXCLUSIVE` | `INCLUSIVE` |
| `granularity` | `CART` | `LINE` |
| `rounding` | `HALF_UP` | `HALF_EVEN` |

**The profile table is code, not catalog.** A catalog selects a market by name (`[settings].market =
"SOUTH"`); it cannot state a rate, a treatment or a rounding mode. This is deliberate and it is the one
place this design takes editing power *away* from the product owner:

- A promotion is merchandising, and a typo in one costs a discount. A tax regime is law, and a typo in
  one mis-states what we owe a tax authority on every invoice we issue. The blast radius is not
  comparable, and §7.4's quarantine — *one bad entry must not stop the shop* — is the wrong instinct for
  a field where the safe behaviour is to stop the shop.
- The four axes are not independent in practice: a jurisdiction's rate, treatment, granularity and
  rounding mode arrive together, from the same statute. Letting them be set separately in a file invites
  a combination no country actually has.
- Rate changes need an *effective date*, and the substrate has no clock. Making a rate change a release
  keeps that honest rather than pretending a file edit can be scheduled. (Q34: *not now — build for
  today*, so no dated-rate machinery is built; §9 prices it if the day comes.)

**Why a profile of four named axes rather than two hard-coded market implementations.** Because the axes
are real and orthogonal in tax law — tax-exclusive jurisdictions that round per line exist, as do
tax-inclusive ones that round per cart — and because a third market is obviously coming. But the
generality is bounded: the profile is a *closed table of named markets*, so adding one is a reviewed code
change with a test row, not a configuration surface. Nobody can construct a market at runtime.

### 2.3 Input

```python
@dataclass(frozen=True)
class CartLine:
    sku: str                 # non-empty, case-sensitive
    unit_price: Decimal      # >= 0, at the market's quantum — the listed price, per unit
    quantity: int            # >= 1

@dataclass(frozen=True)
class Cart:
    customer_id: str
    market: str              # which market this cart is priced for: "NORTH" | "SOUTH"
    lines: tuple[CartLine, ...]
    codes: tuple[str, ...]   # as typed by the customer, in entry order
```

**The cart says which market it is for** (Q28: *a cart is for one market, and it tells you which*). This
is the one place stage 3's first draft had the shape wrong, and the product owner's answer is the better
one: `unit_price` means something different in the two countries — a shelf price containing 20% VAT in
SOUTH, one excluding 17% in NORTH — so a cart that does not name its market is a cart whose prices cannot
be interpreted without knowing which file is about to price them. Now it is self-describing, which also
means a cart that is stored, logged or replayed still means something a year later.

**The catalog also names a market** (§7.5), because there is one promotions file per market (Q27) and its
`AMT` amounts are stated in that market's currency and convention. So the fact is stated twice, by two
parties, for two different reasons — the cart says *what it is*, the file says *what it prices for* — and
`price()` requires them to agree:

> **A cart whose market differs from the catalog's is refused: `price()` raises `MarketMismatchError` and
> produces no quote** (I30, §8).

This is not the "two sources of truth" stage 1 rejected when it kept currency out of the cart. There, a
per-request field would have been a second place to *state* a fact nothing else knew, bought for a
capability nobody had asked for. Here two independent parties genuinely know it and neither is derived
from the other, so requiring agreement is a **total guard against the one new mistake this system can
make**: routing a SOUTH basket to `north.toml`. Unguarded, that request prices silently — wrong rate,
wrong treatment, wrong offers — and is invoiced. Guarded, it cannot be answered at all. A redundancy that
exists to be checked is not the same thing as a redundancy that exists to be trusted.

Lines are **not** keyed by SKU: the same SKU may legitimately appear twice. Promotions that care about
SKU aggregate across lines themselves (§6.3).

Entry order of `codes` is load-bearing: it breaks ties in the exclusion contest (§6.5) and fixes the
order of per-code verdicts (I6).

A cart is priced **for exactly one market**. There is no per-line market and no mixed cart; a basket
spanning two countries is two carts, each naming its own market and each priced against its own catalog,
by a caller that knows it has two shipments.

### 2.4 The tax view — the new output structure

```python
class TaxDerivation(StrEnum):
    COMPUTED       # rounded once from the amount this view describes
    SUM_OF_LINES   # the exact sum of the per-line tax figures; never recomputed from the cart amount

@dataclass(frozen=True)
class TaxView:
    treatment: TaxTreatment
    rate: Decimal            # percent, as applied, 4dp — e.g. 20.0000
    derivation: TaxDerivation
    taxable_amount: Decimal  # what the tax describes; == the accompanying explanation's `final`
    tax: Decimal             # >= 0
    net: Decimal             # taxable_amount excluding tax
    payable: Decimal         # taxable_amount including tax
```

Read as the product owner stated it:

| Case | treatment | rate | derivation | taxable | tax | net | payable |
|---|---|---|---|---|---|---|---|
| C1 cart (NORTH) | EXCLUSIVE | 17 | COMPUTED | `22.50` | `3.83` | `22.50` | `26.33` |
| C2 line (SOUTH) | INCLUSIVE | 20 | COMPUTED | `10.80` | `1.80` | `9.00` | `10.80` |
| C3 cart (SOUTH) | INCLUSIVE | 20 | SUM_OF_LINES | `0.60` | `0.10` | `0.50` | `0.60` |

**Why four money fields when two would do.** `net`, `tax` and `payable` are one identity apart, and
`taxable_amount` equals one of `net`/`payable` by treatment. They are all published for the reason stage
2 published `running`: they are emitted by the same single computation, so they cannot disagree, and
each has a distinct reader who should not have to do arithmetic to get it. The SOUTH invoice needs `net`
and `tax` side by side; the customer needs `payable`; the auditor needs `taxable_amount` and `rate` to
check the working; and the invariant checker gets three redundant statements of one truth (I21, I22,
I23), which is how a bug that satisfies one gets caught by another.

**Why `rate`, `treatment` and `derivation` are carried on the value rather than looked up.** A stored
quote must explain itself a year later, after a rate change, without the reader holding the profile table
that was in force when it was priced (§1.6). `derivation` in particular is the field that answers the
question C4 will provoke in support: *the cart tax is 0.06, but 20% of 0.45 is 0.08 — which is right?*
`SUM_OF_LINES` is the answer, stated on the value itself.

**There is no `TaxView` for a NORTH line.** `LineQuote.tax` is `TaxView | None`, and it is `None` exactly
when the market's granularity is `CART`. NORTH's VAT is a single cart-level charge that is rounded once;
there is no per-line figure, and the alternative — allocating the cart VAT down to lines by largest
remainder so that something appears in the field — would manufacture per-line numbers nobody asked for,
that no NORTH invoice prints, and that a reader would reasonably mistake for authoritative. Stage 2
removed `LineQuote.attribution` on exactly this principle: a field with no consumer is future confusion.
Confirmed by the product owner at Q31: *no — only SOUTH invoices have to show it.*

### 2.5 The explanation

```python
class AdjustmentKind(StrEnum):
    LIST_PRICE   # the opening basis; delta is always 0.00
    PROMOTION    # a promotion that moved money; delta is negative (or 0.00 — see below)
    NOT_APPLIED  # a promotion set aside for a non-stackable rival; delta is always 0.00

@dataclass(frozen=True)
class Adjustment:
    kind: AdjustmentKind
    code: str | None            # customer's spelling; None if and only if kind is LIST_PRICE
    label: str | None           # the catalog's customer-ready line; None for LIST_PRICE
    delta: Decimal              # signed, at the market's quantum. Negative = money off.
    running: Decimal            # the amount after this adjustment
    superseded_by: str | None   # set if and only if kind is NOT_APPLIED
    forgone_delta: Decimal | None  # NOT_APPLIED: the (negative) delta it would have contributed

@dataclass(frozen=True)
class Explanation:
    basis: Decimal                        # the list amount this explanation starts from
    final: Decimal                        # the amount it ends at
    adjustments: tuple[Adjustment, ...]   # ordered; adjustments[0].kind is always LIST_PRICE
```

**Unchanged from stage 2, deliberately and completely.** No tax field, no tax row, no new kind. The tax
account is `TaxView`, attached beside the explanation on the same `LineQuote`/`Quote` and joined to it by
I22 (§1.2, §1.3).

Case B1 (NORTH), and case C2 (SOUTH) read identically in shape:

| kind | code | delta | running |
|---|---|---|---|
| LIST_PRICE | — | `0.00` | `12.00` |
| PROMOTION | SAVE10 | `-1.20` | `10.80` |

`sum(delta) = -1.20 = final - basis`. ✔ And `10.80` is then handed to the tax view.

**Why the opening entry carries a delta of `0.00`.** (PO at stage 2, Q21: *the deltas add up to what came
off, and it has to be clear what we started from.*) Those are two requirements, simultaneously satisfiable
only if the opening entry is an opening *balance* rather than a movement — the first line of a ledger,
stating where the account stood before anything happened. The deltas sum to what came off while the
starting point is stated on the opening row's `running`. `Explanation.basis` states it a second time,
from the same fold, so the two cannot disagree (I10), and the support view leads with it (§4.10).

**There is deliberately no `RESIDUAL` / `ROUNDING` kind, and no `TAX` kind.** The enum has three members.
An engineer who needs a residual has found a bug in the allocator (§5.3); an engineer who needs a tax row
has not read §1.2. This is the type-level form of the PO's *"no rounding line that exists to make the
arithmetic close"*.

A `PROMOTION` adjustment may carry a delta of `0.00` only when a promotion genuinely applied and was worth
nothing on this cart; it is never used as padding.

**What an adjustment carries is exactly the code, the promotion's name (`label`, from the catalog) and
the money** — confirmed at Q25, *code, name and amount is enough* — so there is no catalog-authored "why
this one didn't apply" sentence and no free text anywhere in the explanation.

### 2.6 Output

```python
@dataclass(frozen=True)
class LineQuote:
    sku: str
    quantity: int
    unit_price: Decimal
    list_amount: Decimal                 # unit_price * quantity, market convention
    line_discount: Decimal               # positive magnitude, from line-targeted promos (BOGO)
    allocated_cart_discount: Decimal     # positive magnitude, this line's share of cart-wide promos
    amount: Decimal                      # list_amount - the two discounts, >= 0
    explanation: Explanation             # basis == list_amount, final == amount
    tax: TaxView | None                  # present iff market granularity is LINE (§2.4)

@dataclass(frozen=True)
class Quote:
    market: str                          # the MarketProfile id, e.g. "SOUTH"
    currency: str                        # from the market profile (§7.5)
    lines: tuple[LineQuote, ...]         # same order and arity as cart.lines
    list_subtotal: Decimal
    total_discount: Decimal              # positive magnitude
    amount: Decimal                      # >= 0; == sum(line.amount); the explanation's `final`
    payable: Decimal                     # what the customer pays; == tax.payable (I31)
    explanation: Explanation             # basis == list_subtotal, final == amount
    tax: TaxView                         # always present
    code_results: tuple[CodeResult, ...] # one per submitted code, in submission order
```

**`amount` is the line price** in the market's own convention: the number the promotion pipeline produced,
the number the line explanation ends at, and the number the line taxes are computed from. The line
amounts add up to the cart amount exactly (I3), which is why every cart-wide discount is *allocated* down
to the lines (§5.3).

**`payable` is the number the customer pays, and it is a top-level field because the product owner asked
for it to be the obvious one** (Q30: *just make the number the customer pays the obvious one*). It
restates `quote.tax.payable` — a restatement this design would normally refuse — but "obvious" is the
requirement, and a figure nested two levels inside a structure named `tax` is not obvious to anyone
rendering a basket. The restatement is safe for the same reason stage 2 published `basis` twice: it is one
value, emitted by one computation, asserted equal (I31), and not a second calculation. In NORTH `payable`
is `26.33` where `amount` is `22.50`; in SOUTH the two are equal.

The alternative — making `amount` itself mean "what is payable" — was rejected. `amount` is what the
explanation's `final` is (I22), and in NORTH the explanation ends at `22.50`; a headline field claiming
`26.33` above working that stops at `22.50` is exactly the disagreement stage 2 exists to prevent. The
customer's number and the explanation's number are different numbers in a tax-exclusive market, and the
honest thing is to publish both and name them accurately.

**There is no `LineQuote.payable`.** In SOUTH it would equal `line.amount` exactly; in NORTH it would not
exist at all, because NORTH lines carry no tax (Q31). Adding it would reintroduce the per-line `None` that
Q31 has just settled, in exchange for a field that is either a duplicate or absent.

**In SOUTH the line amounts also add up to what is owed**, because `payable == amount` there. **In NORTH
they do not**, and that is correct rather than a regression: a tax-exclusive invoice lists net line
amounts and charges VAT once at the foot. The product owner's stage-1 rule — *the line prices have to add
up to the total* — is preserved as `sum(line.amount) == quote.amount`, the rule about the pipeline;
`quote.payable` is a further, single, stated charge on top.

`line_discount` and `allocated_cart_discount` are folds of the journal, not separately accumulated
figures. They stay separate rather than summed because on a return of a single line, the line-level part
travels with the line while the cart-level part has to be recomputed against what remains in the order.

### 2.7 Migration from the stage-2 payload

| Stage 2 | Stage 3 | NORTH value |
|---|---|---|
| `LineQuote.gross` | `LineQuote.list_amount` | identical |
| `LineQuote.net` | `LineQuote.amount` | identical |
| `Quote.gross_subtotal` | `Quote.list_subtotal` | identical |
| `Quote.total` | `Quote.amount` | identical |
| — | `Cart.market`, `Quote.market`, `Quote.payable`, `Quote.tax`, `LineQuote.tax` | new |
| everything else | unchanged | identical |

Every NORTH figure a caller reads today is present under a new name with the same value, to the cent
(C6). The renames are not cosmetic: `net` holding a tax-inclusive amount, or `gross` meaning
"before discounts" next to a product owner who uses it to mean "including tax", is precisely the class of
naming bug this design spends §5.5 and §2.1 preventing.

**No compatibility layer is built.** Q29: *nothing is live yet; nobody is reading those names.* So the
rename is taken outright rather than carried as aliases with a deletion date — the same treatment stage 2
gave `LineQuote.attribution` once it was confirmed unread. A deprecation shim for a name nothing has ever
depended on is pure cost, and this stage is the last cheap moment to get the vocabulary right.

### 2.8 Per-code verdicts

```python
class CodeStatus(StrEnum):
    APPLIED         # changed the price; amount says by how much
    CAPPED          # applied, but limited by the zero floor (requested > amount)
    SUPERSEDED      # qualified, but a non-stackable rival gave a larger discount (§6.5)
    NO_EFFECT       # recognised and eligible, but worth 0.00 on this cart
    NOT_APPLICABLE  # recognised, but its conditions are not met (e.g. SKU not in cart)
    UNKNOWN         # no such code in the catalog (includes retired codes, §7.5)
    UNAVAILABLE     # in the catalog but quarantined as malformed (§7.4) - an internal fault
    DUPLICATE       # same code entered more than once; counted once (§6.4)

@dataclass(frozen=True)
class CodeResult:
    code: str                # echoed exactly as the customer typed it (§6.4)
    status: CodeStatus       # the machine-readable verdict - the field to branch on
    amount: Decimal          # positive magnitude actually taken off; 0.00 unless APPLIED/CAPPED
    requested_amount: Decimal | None   # the amount proposed but not received (CAPPED, SUPERSEDED)
    superseded_by: str | None          # set if and only if status is SUPERSEDED
    label: str | None        # the catalog's own description, when the code resolved (§7.1)
    detail: str              # internal explanation - diagnostics only, never displayed
```

**Unchanged from stage 2.** `CodeResult.amount` is a discount in the market's own convention: in SOUTH it
is a gross discount (SAVE10 on a 12.00 shelf price is `1.20`, not `1.00`), because that is what the
promotion took off and what the customer sees come off. No tax component of a discount is published —
Q35: *not now, build for today* — and §9 prices it for the day SOUTH's invoice regime asks.

**Rule: one code in, exactly one verdict out, in the order submitted.** The arity of `code_results` is
checked against the arity of `cart.codes` (I6). A code that is unknown, inapplicable, superseded or
worthless is *data in the response*, never an exception, never a log line only.

`SUPERSEDED`'s two companion fields carry the rest of support's sentence — `superseded_by` names the
winning code in the customer's own spelling, and `requested_amount` is what the losing code would have
taken off. `requested_amount` is reused rather than duplicated across `CAPPED` and `SUPERSEDED`, with one
meaning for both: *the amount this code proposed and did not receive.*

`UNKNOWN` and `UNAVAILABLE` may read identically to the customer but are opposite operationally:
`UNKNOWN` is a customer typo, `UNAVAILABLE` means a live promotion is broken and someone should be paged.

**The front end writes what the customer sees; this service does not.**

- `status` is the contract — a closed enum, the thing to branch on.
- `label` is the catalog's own line, the one customer-ready string in the payload. It is `None` exactly
  when no promotion resolved. It appears in `Adjustment` too, so an explanation renders as
  "10% off everything − 2.45" without the renderer holding a copy of the promotion list.
- `detail` is for engineers and support tooling and is deliberately **not** a stable interface.

---

## 3. Invariants — the acceptance surface

Each has exactly one owner who is capable of violating it; the component boundaries in §4 are chosen so
that this is true. I1–I20 are stage 2's, restated under the new names; I21–I29 are new.

| # | Invariant | Owned by |
|---|---|---|
| I1 | Every money value in a `Quote` is a `Decimal` at the market's quantum (`0.01` for both markets today) | `money` |
| I2 | `line.amount == line.list_amount - line.line_discount - line.allocated_cart_discount`, and `>= 0` | `journal` |
| I3 | `sum(line.amount) == quote.amount` — exactly, no drift | `journal` (allocation) |
| I4 | `quote.amount >= 0` | `journal` (cap at application) |
| I5 | `quote.total_discount == quote.list_subtotal - quote.amount` | `journal` |
| I6 | `len(code_results) == len(cart.codes)`, same order, same spelling | `journal` (resolutions) |
| I7 | Sum of `amount` over APPLIED/CAPPED results `== total_discount` | `explain` |
| I8 | Same (cart, catalog) ⇒ byte-identical quote. No dict/set iteration order, no clock, no RNG | `engine` |
| I9 | No promotion input — however malformed — raises out of `price()`; malformed *carts* always do | `engine` |
| I10 | Every `Explanation` starts with a `LIST_PRICE` adjustment whose `delta == 0.00` and `running == basis`, and it is the only one | `explain` |
| I11 | `sum(a.delta) == final - basis`, exactly, for every line explanation and the cart explanation | `explain` |
| I12 | `adjustments[i].running == adjustments[i-1].running + adjustments[i].delta` for `i > 0`; `adjustments[-1].running == final` | `explain` |
| I13 | For every journal entry, its cart-level delta `== sum` of its per-line deltas | `journal` |
| I14 | Every money figure in the `Quote` is a fold of the journal, or a function of such a fold and the `MarketProfile` computed in `tax` | boundary (§4.9) |
| I15 | Adjustment order == journal append order == the order the engine acted. The projector never sorts | `explain` |
| I16 | No adjustment exists whose purpose is to reconcile, and none represents tax: `AdjustmentKind` has three members | `model` |
| I17 | At most one promotion marked non-stackable is `APPLIED` or `CAPPED` in a quote | `engine` |
| I18 | Every `SUPERSEDED` result names a code that is `APPLIED`/`CAPPED` in the same quote, whose `amount` is `>=` the superseded code's `requested_amount`; if equal, the winner's submission index is lower | `engine` |
| I19 | `result.amount == -adjustment.delta` for the entry that realised it; `result.requested_amount == -adjustment.forgone_delta` where both exist | `explain` |
| I20 | Every submitted code appears exactly once in the support view, in one of its two code sections | `api` / `cli` |
| **I21** | For every `TaxView`: `net + tax == payable`, exactly, and `tax >= 0` | `tax` |
| **I22** | For every `TaxView`: `taxable_amount == amount` of the `LineQuote`/`Quote` it is attached to `== explanation.final` of the same object | `tax` |
| **I23** | `treatment == EXCLUSIVE` ⇒ `net == taxable_amount`; `treatment == INCLUSIVE` ⇒ `payable == taxable_amount` | `tax` |
| **I24** | `granularity == LINE` ⇒ every line has a `TaxView` and `quote.tax.tax == sum(line.tax.tax)` exactly, with `derivation == SUM_OF_LINES`; `granularity == CART` ⇒ every `line.tax is None` and `quote.tax.derivation == COMPUTED` | `tax` |
| **I25** | Under `LINE` granularity, no tax figure anywhere in the quote is rounded from a cart-level amount | `tax` |
| **I26** | Nothing upstream of `tax` reads `treatment`, `rate`, `granularity` or `rounding`. For one cart and one set of promotions, the journal is identical in every market | boundary (§4.8) |
| **I27** | Tax is computed exactly once per thing it describes, from that thing's `amount` and the profile alone — never from a list amount, a discount, an intermediate subtotal, or another tax figure | `tax` |
| **I28** | Every tax figure is the correctly-rounded value of the exact rational `amount × rate / d`, independent of any `Decimal` context precision | `money` |
| **I29** | A NORTH quote with its tax fields removed and §2.7's renames undone is value-identical to the stage-2 quote for the same cart and catalog | boundary |
| **I30** | `cart.market == catalog.profile.id == quote.market`. A cart whose market differs from the catalog's is refused: `price()` raises and produces no quote | `engine` (entry check) |
| **I31** | `quote.payable == quote.tax.payable`, exactly | `explain` |
| **I32** | Every rendering this service produces states both the tax paid and the amount payable | `api` / `cli` |

**I13 is why I3 and I7 come free.** The journal is a matrix whose rows are adjustments and whose columns
are lines (§4.7); I13 says every row's margin agrees. Given I13, I3 is a theorem —
`sum(amounts) = sum(lists) + sum(all deltas) = list_subtotal - total_discount = amount` — and I7 likewise,
because `code_results` is a projection of the same rows.

**I14 is the stage-2 invariant, widened by exactly one clause and no more.** It is enforced by the fact
that `Adjustment`, `LineQuote`, `Quote` and `TaxView` are constructed in exactly two places — `explain`
and `tax` — from exactly two inputs — the journal and the profile. It cannot be unit-tested into
existence; it is kept by not adding a third constructor. That is the single most important thing for a
reviewer to check in this design.

**I26 is the stage-3 invariant.** It is the checkable form of §1.1's claim that the promotion pipeline is
market-blind, and it is verified two ways: by reading imports (no module before `tax` in §4's diagram may
import the tax fields of `MarketProfile`) and by a test that prices the same cart under both profiles and
asserts the journals are equal (case F7).

**I30 is a guard, not a redundancy.** Two parties independently know which market a request is for — the
cart, because it is a basket of that country's shelf prices, and the catalog, because it holds that
country's offers. Neither is computed from the other, so their agreement is real information, and the one
mistake this system can now make is to route a cart to the wrong file. I30 makes that mistake
unanswerable rather than merely unlikely. It is checked once, at the entry to `price()`, before any
promotion is resolved and before any money is touched.

**I31 is the only restatement in the contract, and it is there on instruction.** Q30 asked for the number
the customer pays to be the obvious one; `payable` is that number at the top level, and I31 is what stops
it from ever being a second calculation (§2.6).

**I24 and I25 are the same fact said twice on purpose.** I24 states the sum; I25 forbids the shortcut.
They are separate because C4 is precisely the case where a later reader, seeing that `quote.tax.tax` is
"just 20% of the cart", replaces the sum with a cart-level computation and changes 0.06 into 0.08 on
every small-line invoice we issue. A rule that only says "these must be equal" would be satisfied by that
change on most carts and fail only on the ones nobody generated.

**I28 matters more than it looks.** SOUTH's tax is `amount × 20 / 120`, a division that does not
terminate for most inputs, so "round half-even" is only well defined against the *true* ratio. A
computation that first truncates the quotient to some working precision and then rounds can turn a value
that is not a half into one that looks like a half, and half-even then rounds it the wrong way. §5.7
fixes this with exact integer arithmetic, and I28 is the statement that no `getcontext().prec` anywhere
can change a published tax figure.

I8 remains a stated product requirement. It is why ordering is a fixed table rather than submission order
(§6.1), why allocation ties break on line index (§5.3), why the contest's tie-break is a total order
(§6.5), why the market profile table is static data, why tax rounding is integer arithmetic (§5.7), and
why no clock or random source may enter the core.

---

## 4. Components and seams

Dependencies point one way only. Nothing to the left imports anything to its right.

```
        money ──────────────────────────────────────────────────────────┐
          │   quantisation, exact-ratio rounding, largest-remainder       │
          ▼                                                              │
        market ── MarketProfile; the closed table of named markets       │
          │                                                              │
          ▼                                                              │
        model ── Cart / Quote / Explanation / TaxView (frozen data)      │ used by
          │                                                              │ all
          ├──────────────► catalog ── file → PromotionDef + market name  │
          │                  │         + diagnostics                     │
          │                  ▼                                           │
          │                rules ── one evaluator per kind               │
          │                  │      pure: snapshot → Proposal            │
          │                  ▼                                           │
          └──────────────► engine ── pipeline, dedupe, contest, cap      │
                             │                                           │
                             ▼                                           │
                          journal ── the only mutable thing;             │
                             │        append-only record ────────────────┘
                             │
                             ├──────► tax ── (amount, profile) → TaxView (pure)
                             │                    │
                             ▼                    ▼
                          explain ── journal + tax → Quote + Explanations (pure)
                             │
                             ▼
                          api / cli  (I/O lives here and nowhere else)
```

Two components are new — `market` (§4.2) and `tax` (§4.8) — and both sit at the edges: one is
configuration read at load time, the other is a pure function applied after everything else is decided.
**`catalog`, `rules`, `engine` and `journal` are unchanged from stage 2.** That is the second time a
stage has landed without touching the engine, and it is the evidence that the seams are in the right
place; §4.5 says why it was not luck.

### 4.1 `money` — the arithmetic authority

Owns: the quantum, the rounding operations, the multiplication and percentage helpers, the
largest-remainder allocator, and the exact-ratio rounding of §5.7. Owns nothing about promotions and
nothing about markets — it is handed a mode and a quantum, it does not choose them.

Why it is its own component: rounding is the classic leak. If `quantize` calls are sprinkled through rule
code, every new rule is a fresh chance to round in a new place and break I3. Code review can grep for
stray `quantize` outside this module.

**Stage 3 gives up one stage-2 claim and must say so.** Stage 2 said this module held "one
`ROUND_HALF_UP`, one `Decimal('0.01')`". It no longer does: there are now two rounding modes and, in
principle, a per-market quantum. The claim is replaced by something weaker but still checkable —
**one rounding *function*, whose mode is an argument, and a table (§5.2) that says which call site passes
which mode.** The greppable property survives: every rounding in the system is a call into this module,
and every call site's mode is named in one table rather than chosen locally.

This component is also why "no rounding line" is achievable at all: the allocator is the only place a
money figure is divided into parts, and it is defined to produce parts that sum exactly to the whole
(§5.3). Tax is never divided — it is either computed once (CART) or summed from figures that are each
computed once (LINE) — so it adds no new residue risk (§5.6).

### 4.2 `market` — the closed table of tax regimes

Owns the `MarketProfile` dataclass of §2.2, the enums, and the **static, exhaustive table** of named
markets. Two entries today: `NORTH` and `SOUTH`. It imports `decimal` and nothing else.

Its whole interface is one lookup:

```python
def profile(name: str) -> MarketProfile: ...   # raises on an unknown name
```

Owning the table here rather than in `catalog` keeps `catalog` a file parser — it resolves a name and
carries the result, exactly as it carries a validated `PromotionDef` — and keeps the profile reachable by
`tax` without `tax` depending on the catalog.

**Why this module cannot be edited by the product owner.** §2.2 argues it; the structural consequence is
that an unknown market name is a **deployment fault** that fails like an unreadable catalog file (§8),
not a quarantinable entry. There is no "quarantine the market and price at list" behaviour, because a
cart priced with no tax regime is a cart priced wrongly and shipped.

### 4.3 `model` — the vocabulary

Owns the frozen dataclasses of §2 and cart-shape validation only (non-empty SKU, `quantity >= 1`,
`unit_price >= 0` and at the market's quantum, and `market` being a name the profile table knows). It
knows nothing about promotions, so the request shape can be validated by a caller before any catalog is
loaded — which is now more useful than it was, since validating a cart resolves its market and therefore
its quantum.

Note the direction of the dependency: `model` may import `market` (it is to the left in the diagram), so
"is this a real market?" is answerable here. "Does it match the catalog's?" is not — that needs both
inputs and so belongs at the entry to `price()` (§4.6, I30). It owns I16, in the sense that the shape of
`AdjustmentKind` is what makes both a reconciliation line and a tax row unrepresentable.

**A quantity of 0 is rejected as a malformed cart** rather than priced at `0.00` or dropped. Dropping it
would break the one-for-one correspondence between `quote.lines` and `cart.lines` that the caller relies
on to render its own basket; pricing it keeps a line the customer is not buying on the invoice, lets it
soak up an allocated share of a cart discount, and — new at this stage — would put a `0.00` tax line on a
SOUTH invoice for something nobody bought. Negative quantities are rejected for the same reason: a return
is not a cart line with a minus sign in front of it.

### 4.4 `catalog` — file to definitions, with diagnostics

Owns the on-disk format, its parsing, its validation, and the quarantine policy. Produces an immutable
`PromotionCatalog` — now carrying a resolved `MarketProfile` — plus a list of `CatalogDiagnostic`. Owns
no arithmetic.

The critical seam: **the catalog never hands the engine a definition it has not validated.** A `PCT` that
reached the engine is guaranteed to have a percent in range and a usable identity; the percent rule
therefore contains no defensive checks, and "is this file sane" is answerable offline by `validate`
without a cart (§7.4).

Stage 3 adds one required settings key (`market`) and removes one (`currency`, now supplied by the
profile — §7.5). It adds no new validation *shape*.

### 4.5 `rules` — one pure evaluator per promotion kind

Each kind implements:

```python
class Rule(Protocol):
    kind: ClassVar[str]           # "PCT" | "AMT" | "BOGO"
    phase: ClassVar[Phase]        # when it gets to act (§6.1)
    def evaluate(self, defn: PromotionDef, view: CartView) -> Proposal | NotApplicable: ...
```

`CartView` is a **read-only snapshot** of the journal's current fold: per-line list amount, per-line
current amount, SKU→line index, per-SKU quantity still being paid for (§6.3), and the running subtotal.
`Proposal` is one of:

```python
CartProposal(amount: Decimal)                         # PCT, AMT — engine allocates it (§5.3)
LineProposal(items: tuple[tuple[int, Decimal], ...])  # BOGO — (line index, amount)
NotApplicable(detail: str)                            # explains itself
```

**A rule proposes, it never mutates, and it never decides whether it is allowed.** Capping at the zero
floor, ordering, deduplication, exclusion and verdict recording all live in the engine.

**`CartView` carries no tax information and no market profile, and this is the load-bearing omission of
stage 3.** A rule cannot ask what the tax rate is, cannot ask whether prices include tax, and therefore
cannot behave differently in the two markets — which is exactly the product owner's requirement, since a
promotion acts on the listed amount in both. Had `CartView` exposed the profile "in case a rule needs it",
the first SOUTH-specific rule would have been written within a month and I26 would have been unenforceable
thereafter.

**This component required no change in stage 2 and none in stage 3.** Two consecutive stages of new
product landing without touching the evaluators is not luck: it is what "a rule computes a number from a
snapshot" buys. Tax changes what the numbers *mean*, not how a discount is computed from them, and a
component that only sees numbers is immune to a change of meaning.

A rule may return a `Proposal` of `0.00`; the engine turns that into `NO_EFFECT`, distinct from
`NOT_APPLICABLE` (conditions not met at all). Customer service needs that difference, and §6.5 needs it
to decide who enters a contest.

### 4.6 `engine` — the orchestrator, and the only place promotion policy lives

Owns, in order (§6.6 states the walk precisely): resolve each submitted code against the catalog; dedupe
(§6.4); order the survivors into the pipeline (§6.1); walk it, holding the exclusion contest at the first
contender (§6.5); cap and append each proposal through the journal; record one resolution per submitted
code.

The engine **never constructs an `Explanation`, a `LineQuote`, a `Quote` or a `TaxView`.** It writes
journal entries. That restriction is I14.

The engine **never reads the market's tax fields.** It passes the profile through to `explain` untouched,
in the same way it passes the currency. That restriction is I26.

It does own one new step, before everything else: **the market check.** `cart.market` and
`catalog.profile.id` must be equal, or `price()` raises `MarketMismatchError` (I30). It is the first
thing the function does, it reads no tax field to do it (a string comparison), and it happens before a
single code is resolved — so a mis-routed request consumes no pricing and produces no partial answer.

### 4.7 `journal` — the single mutable object, and the record of truth

A **record** from which the accumulation is derived, not "a total plus some notes about it".

```python
@dataclass(frozen=True)
class Entry:                        # one row of the matrix; one act of the engine
    seq: int                        # append order — the "when"
    source: Source                  # PROMOTION | NOT_APPLIED
    scope: Scope                    # LINE | CART  (which discount bucket it folds into)
    code: str | None                # customer's spelling
    canonical: str | None
    label: str | None
    parts: tuple[Decimal, ...]      # one signed delta per cart line, aligned to cart.lines
    superseded_by: str | None
    forgone_delta: Decimal | None

@dataclass(frozen=True)
class Resolution:                   # one per submitted code, in submission order
    submission_index: int
    code: str                       # customer's spelling
    status: CodeStatus
    entry_seq: int | None           # the entry that realised it, if any
    requested_amount: Decimal | None
    label: str | None
    detail: str
```

The journal holds `opening: tuple[Decimal, ...]` (the per-line list amounts), an append-only `entries`
list, and an append-only `resolutions` list. It is the **only** mutable state in the system and it never
escapes the call.

**The matrix.** `opening` is the header row; each entry is a row of per-line deltas. Case B2 in full:

| row | COFFEE line | WIDGET line | row total |
|---|---|---|---|
| opening (list) | `16.00` | `12.50` | `28.50` |
| COFFEE3 | `-4.00` | `0.00` | `-4.00` |
| SAVE10 | `-1.20` | `-1.25` | `-2.45` |
| **column total (amount)** | **`10.80`** | **`11.25`** | **`22.05`** |

Read down a column and you have that line's explanation; read across a row and you have that promotion's
cart-level delta; read the margins and they agree because I13 says every row sums. **This is the whole of
stage 2 in one table**, and it is why "the explanation and the amount disagree" has no representation.

**Stage 3's tax figures are a function of the column totals, and of nothing else in this table.** They
are not a row. A tax row would have to have per-line parts in a market that has no per-line tax (NORTH)
and would have to describe a movement in a market where nothing moved (SOUTH) — §1.2.

Interface, all of it:

```python
def would_take(self, proposal: Proposal) -> tuple[Decimal, ...]   # pure: capped per-line parts
def append(self, entry: Entry) -> None                            # the only mutator of entries
def resolve(self, resolution: Resolution) -> None                 # the only mutator of resolutions
def view(self) -> CartView                                        # the fold, for rules
```

**`append` does not cap and `would_take` does not mutate**, and application is defined as
`append(entry_from(would_take(p)))`. There is exactly one capping function, used both to measure a
contender (§6.5) and to apply a winner, so the number that wins a contest and the number that lands in
the journal are produced by the same code.

The fold may be cached for O(1) access by `view`, but the cache is written **only** by `append`. A cached
fold writable from anywhere else is a second source of truth wearing a performance costume.

I2, I3, I4, I5, I6 and I13 are enforced here, in two mutators, rather than in every rule.

### 4.8 `tax` — the market's arithmetic, and the only market-aware component

A pure function of two arguments and nothing else:

```python
def tax_for(amount: Decimal, profile: MarketProfile) -> TaxView: ...
def cart_tax(amount: Decimal, line_views: Sequence[TaxView], profile: MarketProfile) -> TaxView: ...
```

`tax_for` computes one figure from one amount (§5.7 is the arithmetic). `cart_tax` implements the one
branch in the entire system that the market decides:

- `granularity == LINE` — the cart's `tax` is `sum(v.tax for v in line_views)`, `derivation` is
  `SUM_OF_LINES`, and **the cart amount is never passed through `tax_for`**. This is C3, C4 and I25.
- `granularity == CART` — `line_views` is empty, the cart's tax is `tax_for(amount, profile)` and
  `derivation` is `COMPUTED`. This is C1.

Everything else — `net`, `payable`, `taxable_amount` — follows from `treatment` by the identity of §2.1,
computed once here, which is what makes I21 and I23 unbreakable rather than merely tested.

**Why this is a component and not three lines inside `explain`.** Three reasons, in order of weight:

1. **It is the only place the market's tax fields may be read** (I26). A boundary makes that checkable by
   reading imports, exactly as stage 2 made "no second computation path" checkable by making `explain`
   the only constructor of `Quote`. A rule buried inside a larger module is a rule that gets relaxed.
2. **It is where the third market lands.** When a country arrives with a reduced rate for food, or
   rounding at the invoice rather than the line, the change is a new profile plus a branch here, and the
   reviewer knows before opening the diff that nothing else can have moved.
3. **It is exhaustively testable on its own**, against a table of amounts and profiles, with no cart, no
   catalog and no journal. The boundary tables of §11 are unit tests of this function.

**What it may not do.** It may not see the journal, a `PromotionDef`, a `CodeResult` or a list amount
(I27). Its only inputs are a final amount and a profile. This is what stops the single most plausible
future bug in a tax system: computing tax on a pre-discount figure, or on a per-promotion figure, and
publishing a number that does not correspond to anything the customer is paying.

### 4.9 `explain` — the projector

A pure function `project(journal, cart, profile) -> Quote`. It reads the journal, calls `tax`, and
constructs everything the caller sees: both kinds of `Explanation`, every `LineQuote`, the `Quote`, and
every `CodeResult`. It performs no pricing decision and no tax arithmetic of its own.

Four projections of one record:

| Output | Projection |
|---|---|
| line `i`'s explanation | `opening[i]`, then every entry with `parts[i] != 0.00`, in `seq` order |
| the cart explanation | `sum(opening)`, then every entry, in `seq` order, delta = `sum(parts)` |
| `code_results` | `resolutions` in submission order, amounts read from the linked entry |
| every `TaxView` | `tax.tax_for` / `tax.cart_tax` over the amounts the first two produced |

Rules the projector owns:

- **It never sorts** (I15). Entry order is append order is the order things happened.
- **It never computes a money figure that is not a sum of `parts`** (I14). `amount`, `line_discount`,
  `allocated_cart_discount`, `total_discount` and every `CodeResult.amount` are folds. The tax figures
  are the one exception and they are obtained by *calling `tax`*, never by arithmetic written here.
- **Sign conversion happens here and only here**, under the naming rule of §5.5: journal deltas are
  signed, the summary fields are positive magnitudes. Asserted as I19. Tax figures are magnitudes and are
  born that way, so they pass through untouched.
- **A line omits entries whose part is `0.00`** — the COFFEE3 row does not appear on the WIDGET line's
  explanation, because it did not move that line's price. This is the PO's rule verbatim (Q19). The cart
  explanation keeps everything, so nothing is lost. Not-applied entries have all-zero parts and so appear
  only in the cart explanation, which is also where the supersession happened.
- **The line tax views are computed before the cart tax view**, because under `LINE` granularity the
  latter is the sum of the former. The ordering is forced by the data, not chosen.
- **`Quote.payable` is copied from `quote.tax.payable`**, in one assignment, immediately after the cart
  tax view is built. It is never computed as `amount + tax` here or anywhere else; there is one
  subtraction-or-addition of tax in the system and it lives in `tax` (I31).

Putting the projector behind its own boundary is what makes I14 checkable by reading imports rather than
by testing outputs: if `Quote(` appears anywhere outside this module, or `TaxView(` anywhere outside
`tax`, the invariant is gone.

### 4.10 `api` / `cli` — adapters

JSON in, JSON out; string→`Decimal` at the edge; exit codes; file reading. The only module permitted to
touch the filesystem or `sys`. `price()` itself takes an already-parsed cart and catalog.

In JSON, every money value is a **string** (`"-2.50"`, `"22.05"`, `"3.83"`), including deltas and every
tax figure, for the reason in §5.1. `rate` is published as a fixed 4dp string (`"20.0000"`) rather than
trimmed, because a fixed form is what makes byte-identical output checkable (I8). An explanation
serialises as an ordered array, and array order is part of the contract. `LineQuote.tax` serialises as
`null` in NORTH, not as an object of zeros.

`Quote.payable` is serialised adjacent to `amount`, not nested inside the tax object, for the reason it
exists at all (§2.6). No stage-2 key spellings are emitted: nothing reads them (Q29).

#### The support view

The product owner's stage-2 answer to "where do unknown, duplicate and inapplicable codes get reported?"
was *wherever support will see it* (Q20), and stage 3 adds *tax is part of what a customer asks about*.
Support will not read JSON; they will read a rendered page. So the obligation lands on the renderer, and
the rendering is specified here rather than left to whoever writes the adapter.

`python -m pricing explain` and any support tool built on this service render **five parts, in this
order**:

1. **What we started from** — the list subtotal, alone on its own line ("List price 28.50"), with the
   market named ("NORTH — prices exclude VAT" / "SOUTH — prices include VAT"). Required by Q21 and,
   for the market line, by the fact that the same numbers mean different things in the two countries.
2. **What came off** — the explanation, in order, one row per adjustment: code, name, delta, running
   balance. A superseded row also names the code that beat it and what it would have given.
3. **Codes that did not change the price** — every submitted code with no adjustment of its own:
   `NO_EFFECT`, `NOT_APPLICABLE`, `UNKNOWN`, `UNAVAILABLE`, `DUPLICATE`. Each with its status and, where
   it resolved, its name.
4. **The tax** — and this part's shape is dictated by granularity, not by taste:
   - `CART` (NORTH): one row. *"VAT at 17% on 22.50 — 3.83."*
   - `LINE` (SOUTH): **one row per line, then their sum**. *"SACHET 0.15 → VAT 0.02; CLIP 0.45 → VAT
     0.08; cart VAT 0.10."* The per-line rows are not optional and the sum is not to be re-derived from
     the cart amount.
5. **What is owed** — `quote.payable`, with the tax restated beside it ("of which VAT 3.83"), so the
   last line of the page answers both "what do I pay?" and "what tax did I pay?" without a reader
   scrolling back to part 4.

**Part 4 is rendered as a sum in SOUTH because C4 is a support ticket waiting to happen.** Three sachets
at 0.15 carry 0.06 of VAT, while 20% of the 0.45 cart is 0.08. A support agent shown only "cart VAT 0.06"
will check it by hand, get 0.08, and escalate a bug that does not exist. Showing the three 0.02 rows and
their total answers the question before it is asked, and it is the same principle as part 3: the screen
is where "wherever support will see it" is discharged. I25 makes the figure right; part 4 makes it
defensible.

**Parts 4 and 5 are where Q32 lands.** The product owner's answer was *keep the working adding up; where
the tax sits is your call, as long as the customer can see what tax they paid.* The first clause is what
keeps tax out of the adjustment chain (§1.2) — the rows that sum stay exactly the rows that sum. The
second clause is a requirement about what reaches a person, so it is discharged the same way Q20's was:
on the renderer. I32 is that obligation — every rendering this service produces states the tax paid and
the amount payable — and the payload makes both reachable with no arithmetic, as `quote.tax` and
`quote.payable`. A front end that shows a price and not its tax is now failing a stated requirement, and
it has no excuse of having to compute anything.

Parts 2 and 3 between them cannot drop a code: part 2 is a projection of the journal, part 3 is every
`CodeResult` with no linked entry, and I6 fixes the arity of `code_results` at exactly the number of
codes submitted. That is I20.

---

## 5. Money

### 5.1 Representation

`decimal.Decimal` throughout, constructed **only from strings or integers**. Floats are rejected at the
boundary with an input fault rather than silently accepted, because `0.1 + 0.2` is how pricing services
end up a cent short and nobody finds out for a quarter. JSON input therefore carries prices as strings
(`"12.50"`). Internal arithmetic runs in a `localcontext()` with ample precision and `InvalidOperation` /
`DivisionByZero` trapped — an arithmetic surprise should be a loud crash in development, never a wrong
price in production.

Tax is the one computation that does **not** rely on that context at all; see §5.7 and I28.

### 5.2 Where rounding happens — exactly four places, each with a named mode

| # | Where | What is rounded | Mode | Market-dependent? |
|---|---|---|---|---|
| 1 | Catalog load | percent → 4dp, amount → the market's quantum | exact (rejects anything that would lose a digit) | no |
| 2 | Proposal | a promotion's discount, before the engine sees it | `HALF_UP` | **no** |
| 3 | Allocation | a cart discount split into per-line parts | exact-sum, largest remainder (§5.3) | no |
| 4 | **Tax** | a tax figure, from a final amount | **profile's `rounding`** | **yes** |

Nowhere else. A line's list amount is `unit_price × quantity` — a value at the quantum times an integer,
exact in `Decimal`, needing no rounding.

**Step 2 stays `HALF_UP` in both markets.** SOUTH's half-even applies to *tax*, which is what the product
owner specified; a 10% promotion on a 12.00 SOUTH shelf price is `1.20` either way, and on `2.445` it is
`2.45` in both countries. Making a promotion's rounding market-dependent would mean the same offer takes
a different amount off in two countries for reasons no customer could be told, and it would break I26 by
putting a market decision back inside the pipeline. **Confirmed at Q33: *tax only*.** That answer is what
makes the market-blind pipeline (I26) a product fact rather than an engineering convenience — had
half-even reached promotion amounts, the two markets would have stopped sharing a pipeline result and
§1.1's whole argument would have had to be rebuilt.

`HALF_UP` at step 2 is kept for the stage-1 reason: a 10%-off figure of `2.445` shown as `2.44` reads as
short-changing, and half-up is what a person computes by hand when checking their receipt — which is
literally what support will do, against the explanation.

### 5.3 Allocating a cart-wide discount back to lines

A cart-wide discount (`PCT`, `AMT`) is one number, but I3 and I13 demand the parts sum to it. The
**largest-remainder (Hamilton) method** over current line amounts:

1. For each line, `exact_i = discount * amount_i / subtotal`.
2. Take `floor_i = exact_i` truncated to the quantum; give each line that much.
3. Rank lines by the discarded fraction, descending; ties broken by **ascending line index** (I8). Hand
   out the leftover cents, one each, down that ranking.
4. Cap each line's share at that line's current amount; any cent that cannot land moves to the next line
   in the ranking.

Properties: the parts sum to the whole exactly (I13 ⇒ I3), no line goes negative (I2), each line's share
is within one cent of its proportional fair share, and the outcome is independent of dict ordering (I8).

Worked example — `5.00` off lines of `3.33 / 3.33 / 3.34`: exact shares `1.665 / 1.665 / 1.670`; floors
`1.66 / 1.66 / 1.67` = `4.99`; one cent left; remainders tie at `.5`, `.5`, `0`, so the lowest index wins
and line 1 gets `1.67`. Amounts `1.66 / 1.67 / 1.67`, total `5.00`. A naive per-line `round(pct * amount)`
gives `4.99`, violates I3, and produces an explanation whose deltas do not sum.

**Allocation is now also what makes SOUTH's per-line tax well defined.** The invoice's tax figures are
computed from the post-allocation line amounts, so a cart-wide discount has to land on real lines before
any tax can be quoted for them. Case F1 is the trace: the allocator's extra cent moves a line amount, and
therefore the tax on that line. This is correct — the tax must describe what the line actually charges —
and it is a second, independent reason the allocator may never park a remainder anywhere but on a line.

### 5.4 The zero floor

Capping happens at the moment of application, in the journal: a proposal is reduced to the money actually
available, and **only the reduced figure is ever journalled**. It is not a `max(0, total)` at the end: a
late clamp would leave `code_results` claiming a discount that was never given (breaking I7), line
amounts that do not sum to the cart amount (breaking I3), and an explanation whose deltas overshoot the
final price (breaking I11).

**The journal records what was given, never what was asked for.** The asked-for figure lives on the
`Resolution` as `requested_amount`, outside the money column entirely, so it can never contaminate a sum.
For A7, TENOFF reports `amount=1.00, requested_amount=10.00`, the explanation shows a single `-1.00`
delta, and the cart amount is `0.00`.

A cart amount of `0.00` is a **valid, returnable result, not an error**. Its tax is `0.00` in both
markets — trivially in NORTH (17% of nothing) and structurally in SOUTH (a zero gross contains zero tax),
so `net`, `tax` and `payable` are all `0.00` and I21 holds (F2, F3). Pricing never refuses a cart for
being worth nothing and never substitutes a minimum charge; anything downstream that cannot take a
zero-value order makes that call with full information.

### 5.5 Signs: one lexical rule

The explanation needs signed movements (the product owner writes `-2.50`); the summary fields are named
for quantities that are naturally positive. The convention is carried by the **name of the field**:

> **Anything named `delta` is a signed movement — negative means money came off.
> Anything named `amount`, `discount` or `tax` is a non-negative magnitude.**

That is the whole rule, it covers every money field in the contract, and it is mechanically checkable.
`Adjustment.delta` and `Adjustment.forgone_delta` are signed; `CodeResult.amount`,
`CodeResult.requested_amount`, `line_discount`, `allocated_cart_discount`, `total_discount` and
`TaxView.tax` are magnitudes. `list_amount`, `amount`, `basis`, `running`, `taxable_amount`, `net` and
`payable` are prices, and prices are never negative (I2, I4, I21).

The conversion between the two happens at exactly one point — the projector (§4.9) — and is asserted by
I19. Tax never needs conversion: it is born as a magnitude in `tax` and published as one.

### 5.6 "No residue", re-proved with tax in the picture

Stage 2's §5.2 doubled as the proof obligation for the product owner's *"no rounding line that exists to
make the arithmetic close"*. Tax could have broken it in two ways; neither is reachable:

- **A cart tax that does not match the sum of its parts.** Under `LINE` granularity the cart tax *is
  defined as* the sum (I24), so there is nothing to reconcile. Under `CART` granularity there are no
  parts to sum. The failure mode — round per line, round the cart independently, then add a cent
  somewhere to close the gap — requires both a per-line figure and an independent cart figure, and no
  market profile produces both.
- **Line `net` figures that do not sum to the cart `net`.** In SOUTH, `net_i = amount_i − tax_i`, and the
  cart's `net = amount − tax` where `amount = Σ amount_i` (I3) and `tax = Σ tax_i` (I24). Subtraction
  distributes, so `Σ net_i = net` exactly, with no rounding in the step. C4 is the check: three lines of
  `0.13` net sum to `0.39`, and the cart's `0.45 − 0.06` is also `0.39`.

A residue could only arise where a rounded figure is derived from another rounded figure and the
difference is dropped. Step 2 of §5.2 produces a figure from scratch; step 3 redistributes its own
remainder; step 4 is never divided. Hence no reconciliation line is needed anywhere, which is what lets
§2.5's enum omit one.

### 5.7 Exact tax rounding, and why `Decimal` precision may not decide a tax figure

NORTH's tax is `amount × 17 / 100`, which terminates. SOUTH's is `amount × 20 / 120`, which mostly does
not. "Round half-even to the cent" is only well defined against the **true** ratio, and a computation
that truncates the quotient to a working precision before rounding can turn a non-half into an apparent
half — at which point half-even rounds it the wrong way, silently, on some fraction of invoices.

So the tax figure is defined by integer arithmetic on the exact rational, with no `Decimal` context
involved:

Let `a` be the amount in minor units (an integer, since amounts are at the quantum), and let the profile's
`tax_rate` be `R / 10^4` with `R` an integer (rates are normalised to 4dp at §5.2 step 1). Then the tax,
in minor units, is the correctly-rounded value of `N / D` where

```
N = a * R
D = 10^6              if treatment is EXCLUSIVE   ( tax = amount * rate/100 )
D = 10^6 + R          if treatment is INCLUSIVE   ( tax = amount * rate/(100+rate) )
```

and rounding is `q, rem = divmod(N, D)` followed by:

```
2*rem  > D   -> q + 1
2*rem  < D   -> q
2*rem == D   -> HALF_UP: q + 1;  HALF_EVEN: q if q is even else q + 1
```

All of it is integer arithmetic, so it is exact, it is unaffected by `getcontext().prec`, and "is this
exactly a half?" is answered by an integer comparison rather than by inspecting a truncated decimal
expansion. That is I28.

The four worked cases, in full:

| Case | `a` | `R` | `D` | `N` | `q`, `rem` | half? | mode | tax |
|---|---|---|---|---|---|---|---|---|
| C1 NORTH cart `22.50` | `2250` | `170000` | `10^6` | `382 500 000` | `382`, `500 000` | yes (`2·rem == D`) | HALF_UP | `383` = `3.83` |
| C3 SOUTH line `0.15` | `15` | `200000` | `1 200 000` | `3 000 000` | `2`, `600 000` | yes | HALF_EVEN, `2` even | `2` = `0.02` |
| C3 SOUTH line `0.45` | `45` | `200000` | `1 200 000` | `9 000 000` | `7`, `600 000` | yes | HALF_EVEN, `7` odd | `8` = `0.08` |
| C2 SOUTH line `10.80` | `1080` | `200000` | `1 200 000` | `216 000 000` | `180`, `0` | no | — | `180` = `1.80` |

**This is also the answer to "why is SOUTH's mode half-even at all?"** — it is the product owner's
requirement, and it only ever bites on an exact half, which under a `/6` divisor happens for amounts of
`0.03`, `0.09`, `0.15`, `0.21`, … That set is small, entirely enumerable, and is the boundary table in
§11. Half-even and half-up differ on every one of them, and on nothing else, which makes the choice of
mode a directly testable fact rather than a matter of belief.

### 5.8 The quantum

Both markets use two minor units, so `Decimal('0.01')` is the quantum everywhere today. It is carried on
the profile (`minor_units`) rather than as a module constant so that the invariants can be *stated*
against the market rather than against the number 2 — which is what stage 2 flagged as the thing a second
currency breaks.

**This is not a claim that a 0- or 3-decimal market is free.** It is a claim that the quantum has one
home. A market with no minor units would additionally need: catalog `amount` validation at the new
quantum, the allocator's "leftover cents" to be leftover minor units, the JSON string format, and a
review of every rule that assumes a fractional price. §9 prices it honestly rather than implying it is a
field.

---

## 6. Promotion semantics

**Nothing in this section is market-dependent.** Every rule below behaves identically in NORTH and SOUTH,
operating on the market's listed amounts (I26). This is the section that did not change.

### 6.1 Ordering: phases, declared by kind

Order is not a property of a code and not of the order the customer typed things. It is a property of the
**kind**, in a table owned by the engine:

| Phase | Kind | Acts on |
|---|---|---|
| 10 — `LINE_ITEM` | BOGO | individual lines |
| 20 — `CART_PERCENT` | PCT | running subtotal after phase 10 |
| 30 — `CART_AMOUNT` | AMT | running subtotal after phase 20 |

Case A5/B2 forces 10 before 20: `COFFEE3` then `SAVE10` gives `24.50 − 2.45 = 22.05` ✔. Running phase 20
first is not merely a different order, it is ill-defined — the free coffee would have to be valued either
at list or at its already-discounted price. Line-level offers change *what the cart contains*; cart-level
offers price *what it contains*. That reason generalises to every future kind, which is why phase is
declared by kind rather than argued case by case.

There is **no tax phase**, and the table is not where tax would go if there were one (§1.2).

20 before 30 is not forced by any case; the product owner is indifferent as long as the same cart always
gives the same answer. Percentage-first is the chosen entry (on `25.00`: `12.50` rather than `13.50`),
because a fixed amount behaves like a voucher redeemed against what is finally owed, and it is the
customer-favourable reading. It is a one-line edit to the table.

Within a phase, codes are processed in **submission order** — the only ordering input the customer has,
and a total order, so it is deterministic. The pair `(phase, submission_index)` is a total order over the
codes on a cart; call it the **pipeline order**. It is the order the engine walks, the order entries are
appended, and hence the order of the explanation (I15).

Multiple PCT codes **compound**: 10% then 10% off `100.00` takes `19.00`, not `20.00`. The explanation
shows this honestly as two entries of `-10.00` and `-9.00`.

### 6.2 PCT and AMT

- **PCT(percent)** — `amount = quantise(running_subtotal × percent / 100, HALF_UP)`. Zero subtotal ⇒
  `NO_EFFECT`. In SOUTH this is a percentage of the gross, which is what the product owner specified and
  what a customer expects: 10% off a 12.00 shelf price is `1.20`.
- **AMT(amount)** — proposes the fixed amount; the journal caps it at the remaining subtotal. In SOUTH a
  `10.00 off` voucher takes `10.00` off the gross, so the customer's bill falls by exactly `10.00`. (That
  it therefore surrenders `10.00 × 20/120 = 1.67` of tax rather than `2.00` is a consequence of the
  product owner's rule, not a decision this design makes.)

Both are `CartProposal`s and are allocated across lines by §5.3.

### 6.3 BOGO

Parameters: `sku` and `n` (the "buy" count).

**Free units = `floor(paid_qty_of_sku / n)`**: three coffees with `COFFEE3` means one is free; 4 gives 1,
6 gives 2. Each free unit is valued at the **lowest** unit price among that SKU's still-paid units — the
listed unit price, which in SOUTH is the gross shelf price, so C5's four coffees at a 4.00 shelf price
give a `4.00` discount and a `12.00` gross line. The discount is attributed to the lines holding the
units, lowest line index first, which is also the shape of that entry's `parts` row. Aggregation is
**across lines by SKU**, so splitting a SKU over two lines can neither farm extra free units nor lose
earned ones.

Free units are removed by *value*, never by quantity: the line keeps quantity 4 and gains a `4.00`
discount. The customer still receives four coffees, so the quantity must not be edited — and on a SOUTH
invoice the tax on that line is the tax inside `12.00`, which is what the customer actually pays for four
coffees, not the tax on three.

If the SKU is absent, or the paid quantity is `< n`, the code reports `NOT_APPLICABLE` with a detail
naming the SKU and what was needed.

**Two BOGO codes on the same SKU both apply**, and the naive interaction is dangerous — evaluated
independently against the original quantity, two "every 2nd free" codes on a quantity of 4 award 4 free
units and give the line away:

| qty | codes | independent | sequential (chosen) |
|---|---|---|---|
| 6 | n=3, n=5 | 3 free | 2 free |
| 4 | n=2, n=2 | **4 free — entire line** | 3 free |
| 12 | n=3, n=4 | 7 free | 6 free |

**Rule: BOGO codes in phase 10 are evaluated sequentially in submission order, and each sees only the
units still being paid for.** *A coffee we already gave away shouldn't earn another one.* That sentence is
the rule — a free unit is not consideration, so it cannot count towards the next offer's threshold — and
it is worth keeping verbatim in the code, because it generalises to every line-level offer added later
and is the thing a future reader needs in order not to "fix" the sequencing.

This is why `CartView` exposes *current* paid quantity per SKU rather than the cart's original quantity.

### 6.4 Duplicate codes

A code entered twice **counts once, and the customer is told**. The first occurrence is evaluated
normally; each later occurrence gets a `DUPLICATE` resolution and **no journal entry** — nothing happened
to the money, so nothing appears in the explanation (§6.7).

Deduplication happens in the engine, before the pipeline is ordered, comparing the resolved catalog code —
so the same promotion entered under two spellings is still caught, and it is caught before the exclusion
contest, so a non-stackable code cannot supersede itself.

Code matching is **case-insensitive and whitespace-trimmed** on lookup — `save10`, ` SAVE10 ` and `SAVE10`
are one code. Copy-paste carries spaces and phone keyboards capitalise unbidden; neither should cost a
customer their discount. Results echo the customer's spelling verbatim. Catalog keys are canonical and
uppercase; `validate` rejects two keys that differ only by case.

### 6.5 Non-stackable promotions — the exclusion contest

A promotion definition may be marked `stackable = false` (§7.3). The engine owns the whole of this rule;
no rule class knows the flag exists.

**Definitions.** A **contender** is a submitted code that resolved to a non-stackable definition and
survived dedupe and quarantine. The **contest point** is the pipeline slot of the *first* contender in
pipeline order; everything earlier has already been applied, so contenders are measured against a
realistic cart, not against list price.

**The contest, at the contest point:**

1. Evaluate every contender — including those whose own slot is later — against the **same** `CartView`.
   This is speculative and provably free of side effects, because `evaluate` is pure (§4.5).
2. Pass each resulting proposal through `journal.would_take` to get the parts that *would* land. A
   contender's **value** is the magnitude of their sum: what the customer would actually receive, not
   what the promotion notionally claims.
   - `NotApplicable` ⇒ resolution `NOT_APPLICABLE`; the contender leaves the contest.
   - value `0.00` ⇒ resolution `NO_EFFECT`, `superseded_by` left `None`; the contender leaves the contest.
     The product owner's words are the specification: *it wasn't beaten by anything — it just saved them
     nothing. Say that.* Marking it `SUPERSEDED` would tell the customer they lost a contest they were
     never in, and would make `superseded_by` unreliable as the answer to "which code beat mine?".
3. Rank the survivors by `(value descending, submission_index ascending)`. This is a total order, so the
   outcome is deterministic (I8), and its second key is the product owner's tie rule: *if they tie, apply
   the one the customer entered first*.
4. **Zero survivors** — nothing applies and nobody is superseded.
5. **One survivor** — it applies at the contest point, with the proposal that was measured. Nobody is
   marked superseded: a code that did not qualify did not lose a contest.
6. **Two or more survivors** — the first in the ranking wins and applies at the contest point with the
   very proposal that was measured; every other survivor gets a `NOT_APPLIED` journal entry (all-zero
   parts, `superseded_by` = the winner's code as the customer typed it, `forgone_delta` = the negative of
   its own measured value) and a `SUPERSEDED` resolution.
7. The group's entries are appended in **submission order**, so the narrative reads in the order the
   customer entered their codes. Only the winner's entry has non-zero parts.
8. Every contender's own later pipeline slot is **skipped**. The walk continues with the remaining
   stackable codes.

**The contest is decided on gross value in SOUTH, because that is the only value the engine can see**
(I26). "Largest discount" therefore means the largest amount off the shelf price, which is the largest
amount the customer's bill falls by — the reading a customer would give it. It is worth noting explicitly
that this could differ from "the largest reduction in tax-exclusive value" if two contenders ever carried
different rates. They cannot: one rate applies to the whole cart, so the two readings coincide exactly and
no decision is being deferred. Q36 confirms that per-product rates are *not now*, so this stays closed;
§9 records that it reopens on the day they arrive, which is the main reason that row in §9 is priced the
way it is.

**Measure and apply are one act.** The winner is applied with the proposal that won, at the moment it
won; it is never re-evaluated. This is what makes the explanation truthful: "TENOFF beat SAVE10 because
it was worth 10.00 rather than 5.00" is backed by `-10.00` being literally the delta in the journal.

**Which slot the winner applies at — engineering's call (Q18).** The winner applies at the *earliest
contender's* slot, so a group behaves as a single promotion occupying the earliest slot any of its
members would have occupied. This keeps the engine a **single forward walk** with no deferred work. The
alternative — measure at the contest point but apply in the winner's own, later phase — needs the engine
to carry a pending decision across slots and then answer a question with no good answer: by the time the
winner's slot arrives the cart may have shrunk, so either the frozen figure is applied and may exceed the
money available, or it is re-evaluated and the number that won is no longer the number that lands.

**Scope of exclusion.** *Non-stackable only means it can't sit next to another non-stackable one* (Q16),
and *one rule: two of them can't sit together — nothing more elaborate* (Q17). So a non-stackable
promotion still combines freely with stackable ones, all non-stackable promotions on a cart form one
group, there are no named groups, no per-promotion exclusion lists and no priority field (§7.6), and at
most one non-stackable promotion applies to a cart (I17).

### 6.6 The engine walk, end to end

The whole of the engine's policy, in order. Every step is deterministic, and no step reads a tax field.

1. **Resolve.** For each submitted code, in submission order: trim and uppercase, look up. Not found ⇒
   `UNKNOWN`. Quarantined ⇒ `UNAVAILABLE`. Write the resolution; no entry.
2. **Dedupe.** Second and later occurrences of the same canonical code ⇒ `DUPLICATE`; no entry.
3. **Order.** Sort the survivors by `(phase(kind), submission_index)` — the pipeline.
4. **Walk.** For each slot in pipeline order:
   - If the code was already resolved by a contest, skip it.
   - If the code is a contender and the contest has not yet been held, hold it (§6.5) and continue.
   - Otherwise evaluate the rule against `journal.view()`; `NotApplicable` ⇒ `NOT_APPLICABLE` resolution,
     no entry; a `0.00` proposal ⇒ `NO_EFFECT` resolution, no entry; otherwise
     `append(entry_from(would_take(proposal)))` and resolve `APPLIED`, or `CAPPED` if `would_take`
     reduced it.
5. **Project.** Hand the journal and the market profile to `explain` (§4.9), which computes the tax views
   through `tax` (§4.8). The engine returns whatever comes back and touches no money figure itself.

Step 5 is the only step that changed in stage 3, and only in what it passes along.

### 6.7 What appears in the explanation, and what does not

**An entry is written when the engine acts on the money at a slot** — either it moved money, or it decided
not to move money that a rival moved instead. That is the whole rule:

| Outcome | In the explanation | In `code_results` |
|---|---|---|
| APPLIED / CAPPED | yes, with its delta | yes |
| SUPERSEDED | yes, `NOT_APPLIED`, delta `0.00`, naming the winner | yes |
| NO_EFFECT | no | yes |
| NOT_APPLICABLE | no | yes |
| UNKNOWN / UNAVAILABLE / DUPLICATE | no | yes |
| **tax** | **no — it is the `TaxView` beside the explanation (§1.2)** | n/a |

The dividing line: **the explanation answers "why is this 22.05?"; `code_results` answers "what became of
each code I entered?"; the tax view answers "what is the 22.05 made of?"** Three questions, three
structures, one set of numbers underneath them. Conflating any two makes the merged one worse at both
jobs — the rows of an explanation are the rows that sum, and padding them with non-events or with a tax
line buries the adjustments that actually set the price.

Every outcome is reported somewhere in the response, always, and now also somewhere on the rendered page
(I20). There is no silently-ignored category and no logging-only path (§8).

---

## 7. The promotion catalog

### 7.1 Format: TOML, read with `tomllib`

**Decision.** TOML, parsed by the 3.11 standard-library `tomllib`. No new dependency.

Non-engineers edit this file constantly. Against JSON, TOML gives comments (so a retired code can be left
in place with a note and a date), no trailing-comma or missing-brace traps, no quoting of keys, and diffs
that stay readable in a pull request. Against YAML it gives a stdlib parser and no Norway problem.

```toml
# south.toml — settings, then one table per code. Edit freely; run `validate` before shipping.

[settings]
market = "SOUTH"        # which country's tax law this catalog prices for (§7.5)
                        # NOTE: prices in a SOUTH cart INCLUDE 20% VAT. Promotions act on that
                        # shelf price: 10% off a 12.00 shelf price is 1.20.

[promotions.SAVE10]
kind      = "PCT"
percent   = "10"          # quoted: money and rates are never TOML floats
label     = "10% off everything"
stackable = false         # cannot be combined with another non-stackable promotion (§6.5)

[promotions.TENOFF]
kind      = "AMT"
amount    = "10.00"       # in SOUTH this is 10.00 off the shelf price, i.e. off the gross
label     = "10.00 off your order"
stackable = false

[promotions.COFFEE3]
kind  = "BOGO"
sku   = "COFFEE"
n     = 3
label = "Buy 3 coffees, get one free"
# stackable omitted => true

# Retiring a code = delete it (or comment it out, which is the same thing to the loader).
```

Promotions live under `[promotions.…]` rather than at the top level so that settings and codes cannot
collide: without it, a promotion legitimately named `SETTINGS` would silently become configuration.

### 7.2 Numbers are strings, and the loader enforces it

`percent = 10.5` is a TOML float, i.e. an IEEE double, i.e. the beginning of a rounding bug. The loader
**rejects floats for any money or rate field** with a diagnostic naming the fix. Counts (`n`) are
integers; `stackable` is a boolean.

### 7.3 `stackable`

- Type: TOML **boolean**. Optional, **defaulting to `true`**, so every promotion written before stage 2
  keeps its exact meaning and no existing catalog needs editing for it.
- Named for the property, not its absence: `stackable = false` reads better than `non_stackable = true`,
  and the engine never has to write `if not defn.non_stackable`.
- The unknown-key rule catches `stackble` rather than silently making a promotion stackable, which is
  exactly the typo that would be most expensive.

There is deliberately no check that a catalog contains at least two non-stackable promotions: one is a
perfectly ordinary state, and inventing a warning for it would train people to ignore warnings.

### 7.4 Validation and quarantine

Per code, the loader checks: the table name is a well-formed code; `kind` is known; the parameters for
that kind are present, correctly typed and in range (`0 <= percent <= 100`, `amount > 0`, `n >= 1`);
`stackable`, if present, is a boolean; there are no unknown keys; and `label` is present and non-empty.

`label` is **mandatory**, not decoration. The front end composes customer wording from `status` and
`label`, and the explanation carries `label` as its only human-readable field.

Two behaviours from one pass:

- **`validate` (CLI)** reports *every* diagnostic with its code and field; `--strict` makes warnings
  fatal. This is the pre-ship check and the CI gate. It now also prints the resolved market and its tax
  regime in one line at the top — *"SOUTH: prices include VAT at 20%, rounded half-even per line"* —
  because the single most consequential thing in the file is a five-letter word in `[settings]`, and a
  linter that says nothing about it invites the mistake it exists to catch.
- **`price` (runtime)** *quarantines* a bad promotion entry: it is excluded from the catalog, any cart
  using it gets `UNAVAILABLE`, and the rest of the cart prices normally. A typo in one promotion must
  never take down pricing for every customer.

A quarantined non-stackable promotion is not a contender and supersedes nobody — it never reaches the
pipeline. A broken promotion must not silently suppress a working one.

**`[settings]` is not quarantinable**, and stage 3 makes that rule carry much more weight: a missing or
unknown `market` is a deployment fault and `price()` raises, exactly as for an unreadable file. There is
no default market and no "price at list and carry on". A cart priced under the wrong tax regime is a cart
priced wrongly, invoiced wrongly and shipped, and the mistake is discovered by a tax authority rather
than by a customer. This is the one place in the design where failing loudly is unambiguously better than
degrading gracefully, and it is worth stating as a decision (§12) rather than leaving as a consequence.

### 7.5 The market setting, the currency, and retiring a code

**`[settings].market` is required.** It takes one of the names in the profile table (§2.2) and nothing
else — no rate, no treatment, no rounding mode. §2.2 argues why those are code; §7.4 says what happens
when the name is wrong. It is also one half of the guard: the cart names its market too, and the pair
must agree (§2.3, I30).

**`[settings].currency` is removed.** The currency comes from the market profile. Q26 confirms both
markets use the same currency, so this move is **not forced** by the requirement and is worth stating as
a choice rather than a consequence: with one currency in play, stage 1's `[settings].currency` would
still work. It is removed because there are now two catalog files, and a per-file currency is two places
to write one fact — two places that can drift, in a system where nothing would notice if they did.
Putting it on the profile gives it one home, in code, where the two market entries cannot disagree
because they are read from the same table. `currency` is still a field on `Quote`, copied from the
profile; the service does not convert, compare or interpret it.

This also closes a risk stage 2 flagged explicitly — though not quite in the way stage 2 expected. Stage 2
said a second currency "is genuinely a redesign, not a field: prices, promotion amounts, minor units and
rounding all become currency-dependent — flagged so it is never mistaken for a small change." What
actually arrived was a second *market* with the same currency, and the redesign it demanded was precisely
the one predicted for a second currency: a profile carrying currency, minor units, rate and rounding,
resolved once and read by one downstream component. The flag was planted on the wrong noun and still
caught the right change, which is the most one can ask of a flag.

**Retirement is deletion**: remove the table from the file — or comment it out, which the loader cannot
tell apart and which preserves the history for whoever reads the file next. A customer who then enters
the code gets `UNKNOWN`. This is the reason there is **no `enabled = false` flag**: two mechanisms for
"this code is over" means every future question has to be answered twice.

**One catalog prices one market** — confirmed at Q27: *one file per market; they run different offers.*
That answer is stronger than the argument this design had prepared. The prepared argument was mechanical
(`10.00 off` is not the same offer off gross as off net, so a shared file would need per-market amounts
anyway, and sharing would buy nothing while costing an override mechanism). The actual reason is
commercial: the two countries **run different promotions**. A shared file would therefore have been mostly
overrides, i.e. two files wearing one filename. `SAVE10` in `north.toml` and `SAVE10` in `south.toml` are
two promotions that happen to share a name, and nothing in this design makes them the same thing.

### 7.6 What the catalog deliberately does not have

No date ranges, no enable/disable flag, no per-customer eligibility, no usage limits, no named
stacking-exclusion groups, no priority field — and, new at this stage, **no tax fields of any kind**: no
rate, no per-promotion tax treatment, no per-SKU rate override. All are plausible next requests
(`customer_id` is carried through the model as the hook for the third), but none was asked for, and each
would add a clock, a store, a constraint solver, or — for the tax ones — an editable surface over
something that is law. §9 states what each would cost.

Declined at stage 2 and still absent by decision rather than omission: **named exclusion groups** (Q17 —
*one rule: two of them can't sit together, nothing more elaborate*) and **a catalog-authored "why this
didn't apply" line** (Q25 — *code, name and amount is enough*). A **priority** field is not added because
the tie-break is already specified (largest discount, then entry order) and a priority field would be a
second, silently-overriding answer to the same question.

---

## 8. Failure model

Three categories, deliberately different, because conflating them is what makes pricing services either
brittle or silently wrong.

**Input faults — raise.** A malformed cart (negative quantity, a price not at the market's quantum, float
money, missing SKU, a `market` the profile table does not know). These are caller bugs; the service must
not invent a price for a cart it does not understand. A single `CartValidationError` carrying a list of
field-level problems, so the caller learns everything wrong at once.

**Routing faults — raise.** `cart.market != catalog.profile.id`. Both inputs are individually valid and
the request is still unanswerable, which is why this is worth naming rather than folding into the
category above: neither party is wrong, the *pairing* is. `MarketMismatchError` names both markets and
is raised at the entry to `price()`, before any code is resolved (I30, §4.6). There is no "price it under
the catalog's market and note the discrepancy" behaviour, and no preference order between the two
sources: a SOUTH basket priced at NORTH rates with NORTH offers is wrong in four independent ways and
would be discovered by a tax authority rather than by a customer.

**Deployment faults — raise.** An unreadable or unparseable catalog file; a missing or unknown
`[settings].market`. The process is misconfigured, and every cart it prices would be priced wrongly. It
must not run. This category grew at stage 3 and is the more important half of §7.4's argument.

**Promotion outcomes — report.** Unknown, quarantined, inapplicable, duplicated, zero-valued, capped,
superseded. These are *normal business results of a normal request*. They travel in `code_results`, the
cart still prices, and the caller can render them next to the promo box.

There is no "silently ignore" category and no logging-only path. Anything the service decides
about a code is in the response; anything it decides about the price is in the explanation; anything it
decides about the tax is in the tax view.

**Invariant violations.** I10–I31 are cheap to check and are checked before the `Quote` is returned —
I10–I19 in `explain`, I21–I28 across `explain` and `tax` — raising an internal error rather than shipping
a quote that does not add up. This is the one place the design prefers a crash to an answer: a wrong
price that is correctly explained is a pricing bug, but a right price with a broken explanation is the
bug the product owner refunded a customer over, and a tax figure that does not match the invoice it is
printed on is the bug a tax authority finds. Neither may leave the process. The check is
O(lines × entries) over data already in hand.

I20 is the exception: it is a property of a rendering, so it cannot be checked in `explain` and is
instead a test obligation on the adapter (§11). That asymmetry is honest — the core can guarantee every
code is *in* the response; only the adapter can guarantee it reaches the screen.

### 8.1 Scale and limits

No cart-size or code-count limit is imposed. Pricing is a single in-memory pass: `O(L × C)` for `L` lines
and `C` codes, with one `O(L log L)` sort per cart-wide code for the allocation ranking. The journal adds
one `L`-wide row per applied code; the contest adds one extra evaluation per contender, once. Tax adds
`O(L)` integer divisions and no allocation. The invariant check is one more pass over the same matrix. A
500-line cart with 20 codes remains microseconds of arithmetic.

The catalog is parsed **once per process** and the resulting `PromotionCatalog` — including its resolved
`MarketProfile` — is immutable and shared across calls, so catalog size does not appear in the per-cart
cost. A size limit belongs at the caller's request boundary, where a rejection can be explained.

---

## 9. Extension scenarios — what changes when the product owner asks for…

| Request | Change |
|---|---|
| A new code of an existing kind | Edit the market's catalog. No code, no deploy. |
| Mark an existing code non-stackable | Edit the catalog. No code, no deploy. |
| **A third market** | One row in the profile table (§2.2) + one acceptance row per case. If its four axes are among the existing enum members, that is the whole change. |
| **A market whose rate changes (20% → 21%)** (declined for now, Q34) | One field in the profile table; a release. Deliberately not a file edit (§2.2). If it must take effect at a *moment* rather than at a deploy, that is the `as_of` change below — a parameter on `price()`, not a config change. Nothing is built for it today. |
| **Tax-exclusive *and* per-line (a fourth combination)** | Nothing. `EXCLUSIVE` × `LINE` already composes: `tax_for` per line, `cart_tax` sums. The combination is untested until a market needs it, and §11 says to add the table then. |
| **Reduced or zero rates per product (food, books)** (declined for now, Q36) | The real cost, and the one extension that moves a seam. The rate stops being a cart-level fact: `MarketProfile.tax_rate` becomes `rate_for(line)`, needing product metadata the cart does not carry (the same missing input as "PCT on one category"). Under `LINE` granularity the rest is free — each line already gets its own `tax_for`. Under `CART` granularity it means one rounded figure per rate group and a cart `TaxView` that becomes a list. It is also what would reopen §6.5's "largest discount means gross or net?" question, which is closed only because one rate applies to the whole cart. |
| **Tax shown on each discount line** (declined for now, Q35) | A `TaxView` on `CodeResult`, computed by the same `tax_for` from the discount magnitude. No new arithmetic, one new call site, and a product decision about which rate applies to a cart-wide discount. |
| Per-line tax in NORTH (declined, Q31) | Either a profile change to `LINE` granularity — which changes the cart figure, so it is a product decision, not a display one — or an allocation of the cart VAT across lines, which invents per-line figures (§2.4). |
| "Buy X get Y free" (cross-SKU) | New rule class + catalog schema fragment + a phase-10 entry. Engine untouched; it journals, explains and taxes itself for free. |
| "PCT on one category only" | New rule; needs product metadata the cart does not carry — that is the real cost. |
| Reverse PCT/AMT ordering | One entry in the engine's phase table. |
| Codes with start/end dates | `as_of: datetime` parameter on `price()`, injected by the caller (never `now()` inside the core, or I8 dies), plus two catalog fields and an eligibility check. The same parameter is what a dated tax-rate change would need. |
| Per-customer eligibility | Engine gains a `customer_id` check against catalog criteria; the field is already in the model. |
| "Best of" across *all* promotions | The contest already is a best-of over a set. Widening the set is a change to how contenders are selected, not to the mechanism. |
| A "what if" / counterfactual API | Cheap: run `price()` on variant carts and compare. Purity is the feature. |
| Shipping | A new phase after 30 **if it is a charge that promotions can discount**; a second `TaxView`-like decomposition if it is taxed separately. The distinction is §1.2's, and it should be settled before anything is built. |
| Named exclusion groups (declined, Q17) | Catalog field + a group key in the contest's step 1. |
| A version stamp for auditors (declined, Q24) | A field on `Quote`, filled by the caller that knows its own catalog revision. No clock and no store enters the core. |
| Show the explanation to customers, not just support | No core change: it is already a value in the payload with `label` as its human-readable field. |
| HTTP front end | New adapter beside `cli`. Core untouched. |
| **A market with no minor units** (JPY-like) | `minor_units = 0` on the profile covers the quantum, but not the rest: catalog `amount` validation, the allocator's leftover unit, the JSON format, and every rule that assumes a fractional price all need review. Priced honestly here so it is never quoted as a field (§5.8). |

The first five rows are the measure of this stage: an entire second tax regime landed as **one data row
and one new pure function**, and the next two likely requests after it are a row and a call site.

Four rows are marked *declined for now* because the product owner answered *not now — build for today* to
each (Q34, Q35, Q36) or *no* (Q31). They are listed rather than deleted for the reason stage 2 gave: a
request that has been priced before it arrives is not a gap in the design, and the estimate is cheaper to
write now, with the reasoning fresh, than under pressure later. Nothing is built, stubbed or hooked for
any of them — in particular there is no `as_of` parameter, no per-line rate field, and no `CodeResult`
tax field anywhere in the contract.

---

## 10. The acceptance cases, traced

### 10.1 Stage-3 cases — the product owner's table

| # | Market | Trace | Result |
|---|---|---|---|
| C1 | NORTH | list `12.50 × 2 = 25.00`. SAVE10 PCT 10% → `2.50`, parts `(-2.50)`, amount `22.50`. Cart tax: `a=2250`, `D=10^6`, `N=382 500 000` → `q=382 rem=500 000`, exact half, HALF_UP → `383` | amount `22.50`; tax `3.83`; net `22.50`; payable `26.33`; `derivation=COMPUTED`; every `line.tax is None` ✔ |
| C2 | SOUTH | list `12.00`. SAVE10 PCT 10% of the **gross** → `1.20`, amount `10.80`. Line tax: `a=1080`, `D=1 200 000`, `N=216 000 000` → `q=180 rem=0` | line: tax `1.80`, net `9.00`, payable `10.80`. Cart tax `1.80`, `derivation=SUM_OF_LINES` ✔ |
| C3 | SOUTH | no codes; amounts `0.15` and `0.45`. `15 → q=2 rem=600 000`, exact half, HALF_EVEN, `2` even → `2`. `45 → q=7 rem=600 000`, exact half, `7` odd → `8` | line taxes `0.02` and `0.08`; cart tax `0.10`; cart amount `0.60`, net `0.50` ✔ |
| C4 | SOUTH | three lines of `0.15`, each `→ 0.02` by the same half-even step | each line tax `0.02`; cart tax `0.06`, **not** `0.08`; cart amount `0.45`, net `0.39` = `0.13 × 3` ✔ |
| C5 | SOUTH | list `4.00 × 4 = 16.00`. COFFEE3 phase 10: `4 // 3 = 1` free at the lowest paid **shelf** price `4.00`, parts `(-4.00)`, amount `12.00`. `a=1200 → q=200 rem=0` | gross `12.00`; tax `2.00`; net `10.00`; payable `12.00` ✔ |
| C6 | NORTH | every case in §10.2, priced under the NORTH profile | promotion figures identical to stage 2 to the cent; `tax` and `payable` are new columns ✔ |

Every SOUTH row above also has `quote.payable == quote.amount` (INCLUSIVE), and every NORTH row has
`quote.payable == quote.amount + quote.tax.tax`. C1's `payable` is `26.33` — the figure the product owner
called "total", published at the top level under the name it is owed by (§2.6, Q30).

C4 is the case the architecture exists for. The cart's tax is `0.06` because I24 defines it as the sum of
the line figures and I25 forbids the cart-level shortcut that would give `0.08`. Note that the cart's
`net` of `0.39` is *also* the sum of the three line `net`s — §5.6 shows why that is exact rather than
lucky.

### 10.2 Stage-1 and stage-2 cases under NORTH, still binding (C6)

Promotion columns are stage 2's, unchanged. Tax and payable are new.

| # | Trace | Amount | Tax @17% | Payable |
|---|---|---|---|---|
| A1 | list `12.50 × 2`; no codes | `25.00` | `4.25` | `29.25` |
| A2 | SAVE10 → `2.50` | `22.50` | `3.83` | `26.33` |
| A3 | TENOFF `10.00` ≤ subtotal | `15.00` | `2.55` | `17.55` |
| A4 | COFFEE qty 4, `4 // 3 = 1` free at `4.00` | `12.00` | `2.04` | `14.04` |
| A5 / B2 | phase 10 COFFEE3 `-4.00`; phase 20 SAVE10 `-2.45` allocated `1.20`/`1.25` | `22.05` | `3.75` | `25.80` |
| A6 | NOPE not in catalog; no entry, one resolution | `12.50` | `2.13` | `14.63` |
| A7 | subtotal `1.00`; TENOFF proposes `10.00`, `would_take` returns `(-1.00)`; `CAPPED 1.00 / requested 10.00` | `0.00` | `0.00` | `0.00` |
| B1 | SAVE10 on `25.00`; explanation `LIST 0.00→25.00`, `SAVE10 -2.50→22.50` | `22.50` | `3.83` | `26.33` |
| B3 | both non-stackable on `50.00`; TENOFF `10.00` beats SAVE10 `5.00`; SAVE10 `SUPERSEDED`, forgone `-5.00` | `40.00` | `6.80` | `46.80` |
| B4 | on `150.00`, SAVE10 `15.00` beats TENOFF `10.00` | `135.00` | `22.95` | `157.95` |
| B5 | on `100.00` both `10.00`; tie broken by submission index ⇒ SAVE10 | `90.00` | `15.30` | `105.30` |
| B6 | no `stackable = false` in the catalog ⇒ zero contenders ⇒ the walk is byte-for-byte the stage-1 walk | — | — | — |
| D1 | SAVE10 twice; second `DUPLICATE`, one adjustment | `22.50` | `3.83` | `26.33` |
| D2 | two different 10% codes on `100.00`; explanation `-10.00` then `-9.00` | `81.00` | `13.77` | `94.77` |
| D3 | COFFEE `4.00 ×6`, COFFEE3 + COFFEE5 ⇒ 2 free; COFFEE5 `NOT_APPLICABLE` | `16.00` | `2.72` | `18.72` |
| D4 | SAVE10 + TENOFF (both stackable), either order | `12.50` | `2.13` | `14.63` |
| D5 | WIDGET `1.00`, GIZMO `1.00`, TENOFF; parts `(-1.00, -1.00)`; `CAPPED 2.00 / requested 10.00` | `0.00` | `0.00` | `0.00` |
| E1–E7 | the contest cases | as stage 2 | 17% of each | — |

A1 and A6 pin the degenerate explanation: a single `LIST_PRICE` adjustment, `sum(deltas) == 0.00 ==
final - basis`. A7 and D5 pin the zero floor, and now also pin tax at the floor: `0.00 + 0.00 = 0.00`
satisfies I21 trivially and there is no minimum charge.

### 10.3 Cases the stage-3 rules newly pin down

These follow from decisions above and belong in the suite beside C1–C6.

| # | Market | Cart | Codes | Result | From |
|---|---|---|---|---|---|
| F1 | SOUTH | `3.33`, `3.33`, `3.34` | FIVEOFF (AMT `5.00`) | allocation `1.67/1.66/1.67` ⇒ amounts `1.66/1.67/1.67`; line taxes `0.28/0.28/0.28`; **cart tax `0.84`**, where a cart-level computation would give `0.83`; line nets `1.38/1.39/1.39` sum to the cart net `4.16` | §5.3 × I24, I25 |
| F2 | SOUTH | `1.00` | TENOFF | amount `0.00`; tax `0.00`; net `0.00`; payable `0.00`; TENOFF `CAPPED 1.00 / requested 10.00` | §5.4, I21 |
| F3 | NORTH | `1.00` | TENOFF | amount `0.00`; tax `0.00`; payable `0.00` | §5.4 |
| F4 | SOUTH | `50.00` | SAVE10 (NS), TENOFF (NS) | contest values are the **gross** discounts `5.00` and `10.00`; TENOFF wins; tax never enters the contest and the journals match F4's NORTH twin exactly | §6.5, I26 |
| F5 | SOUTH | one line, no codes | — | the half-even boundary table below | §5.7 |
| F6 | NORTH | one line, no codes | — | the half-up boundary table below | §5.7 |
| F7 | both | WIDGET `12.00 × 1` | SAVE10 | **identical journals**: opening `(12.00)`, one entry `(-1.20)`, amount `10.80`, identical explanations. NORTH: tax `1.84`, net `10.80`, payable `12.64`. SOUTH: tax `1.80`, net `9.00`, payable `10.80` | I26 |
| F8 | — | any | — | a catalog whose `[settings].market` is missing or unknown ⇒ `price()` raises; no quote, no default | §7.4, §8 |
| F9 | — | a cart marked `SOUTH` | any | priced against `north.toml` ⇒ `MarketMismatchError`; no quote, no partial answer, and the error names both markets. The mirror case (`NORTH` cart, `south.toml`) behaves identically | §2.3, I30 |
| F10 | — | a cart whose `market` is `"NORTHH"`, `""` or `"north"` | any | rejected as a malformed cart before any catalog is consulted — the profile table is the only source of valid names, and lookup is exact | §4.3, §8 |

**F5 — SOUTH half-even boundary table.** The only amounts where the mode can matter are those for which
`a/6` is an exact half, i.e. `a ≡ 3 (mod 6)`. This table *is* the specification of "half-even", and half
of its rows differ under half-up, which is what makes the mode testable rather than merely asserted.

| amount | exact tax | half-even (ours) | half-up (wrong here) |
|---|---|---|---|
| `0.03` | `0.005` | **`0.00`** | `0.01` |
| `0.09` | `0.015` | `0.02` | `0.02` |
| `0.15` | `0.025` | **`0.02`** | `0.03` |
| `0.21` | `0.035` | `0.04` | `0.04` |
| `0.27` | `0.045` | **`0.04`** | `0.05` |
| `0.33` | `0.055` | `0.06` | `0.06` |
| `0.39` | `0.065` | **`0.06`** | `0.07` |
| `0.45` | `0.075` | `0.08` | `0.08` |

**F6 — NORTH half-up boundary table.** The mode can only matter where `17a/100` is an exact half, i.e.
`a ≡ 50 (mod 100)`.

| amount | exact tax | half-up (ours) | half-even (wrong here) |
|---|---|---|---|
| `0.50` | `0.085` | **`0.09`** | `0.08` |
| `1.50` | `0.255` | `0.26` | `0.26` |
| `2.50` | `0.425` | **`0.43`** | `0.42` |
| `4.50` | `0.765` | **`0.77`** | `0.76` |
| `22.50` | `3.825` | **`3.83`** | `3.82` |

The last row is C1. The two tables together are the whole observable content of "the markets round
differently", and both are unit tests of `tax_for` alone — no cart, no catalog, no journal.

---

## 11. How this should be tested (for the build stage, not built here)

- **The cases** of §10, table-driven, **each pinned to a market** — necessary, nowhere near sufficient.
- **The market-isolation property (I26)**, which is the stage-3 test that would catch the stage-3
  regression: price every generated cart under both profiles and assert the two journals are *equal* —
  same opening, same entries, same parts, same resolutions — and that the quotes differ only in
  `market`, `currency` and the tax fields. A single `if profile.treatment == ...` leaking into a rule or
  the engine fails this on the first cart with a promotion.
- **Invariant properties** over generated carts and code sets: I2–I28 must hold for *every* input,
  including carts of 40 lines at `0.01`, quantities of 1, codes repeated five times, and every ordering
  of the same code set.
- **The agreement property, as a fuzz oracle**: for every generated quote, recompute every money figure
  independently from the explanation alone — `final = basis + sum(deltas)` per line, `amount = sum(line
  finals)`, `code amount = -delta` — and assert equality with the published fields. This is the test that
  would have caught the bug that caused the refund.
- **The tax-agreement oracle**, its stage-3 twin: recompute every tax figure from `taxable_amount` and
  the profile by an independent high-precision `Decimal` route, and assert it equals the published
  integer-derived figure. Two methods, one answer — and the `Decimal` route is run at several context
  precisions to demonstrate I28.
- **The per-line-sum property (I24, I25)**, generated adversarially: carts of many small lines, where the
  sum of rounded line taxes provably differs from the cart-level rounding. The generator must be asserted
  to *produce* such carts — a property that never sees a divergent cart has not tested anything. C4 and
  F1 are the two hand-checked members of that family.
- **The boundary tables** F5 and F6, verbatim, as unit tests of `tax_for` with no cart involved. They
  are the specification of the two rounding modes, and they belong in the repo as tables.
- **The `net` distributivity property**: `sum(line.net) == quote.tax.net` in SOUTH, for every generated
  cart. This is §5.6's proof restated as a test, and it is the one that fails if anyone ever rounds `net`
  independently instead of subtracting.
- **The residue property**: for every entry, `sum(parts) == the proposal's capped amount`; no
  `Adjustment` has a `code` that is not in `cart.codes`; and `AdjustmentKind` has exactly three members.
  A reconciliation line or a tax row would have to appear as a mismatched row sum, a nameless adjustment,
  or a fourth enum member — all three checkable.
- **The contest property** (I18): over random non-stackable sets, the applied contender's amount is `>=`
  every superseded contender's `requested_amount`, and on equality its submission index is lower.
  **Contest × cap** (E3): the winner is chosen on capped value. **Contest × market** (F4): the outcome is
  identical in both markets.
- **Order fidelity** (I15): shuffle the input codes and assert the explanation order tracks pipeline
  order, and that the amounts do not change except through the §6.5 tie-break.
- **Catalog fuzzing**: every field missing, mistyped, floated, out of range, duplicated, plus `stackable`
  as a string / number / null — assert the service always prices and always quarantines. Separately:
  `market` missing, misspelled, lowercase, an empty string, a name not in the table — assert `price()`
  **raises every time** and never falls back to a default (F8, F10).
- **The routing guard (I30)**, as a property rather than two examples: for every generated cart and every
  pair of catalogs, `price()` returns a quote if and only if the markets match, and the quote's `market`
  equals both. The negative half matters more than the positive half — a guard only ever tested on
  matching pairs is not tested — so the generator must produce mismatched pairs deliberately (F9).
- **`payable` agreement (I31)**: over every generated quote, `quote.payable == quote.tax.payable`, and in
  SOUTH additionally `== quote.amount`. Cheap, and it is the field most likely to be "helpfully"
  recomputed as `amount + tax` by a later reader — which is wrong in SOUTH.
- **The BOGO boundary table** — quantities `n−1`, `n`, `n+1`, `2n`, `2n+1` against `floor(qty / n)`; for
  `COFFEE3` that is 2→0, 3→1, 4→1, 6→2, 7→2 free. Plus a second table for two stacked BOGOs on one SKU.
- **The support view** (I20, I32 and §4.10 part 4): every submitted code appears exactly once across the
  two code sections; part 2 contains exactly the codes with a journal entry; under `LINE` granularity
  part 4 contains exactly one row per line plus a total; and **every** rendered quote states a tax figure
  and an amount payable, in both markets, including when both are `0.00` (I32, and the renderer half of
  Q32's *as long as the customer can see what tax they paid*). A golden-file render of C4 is worth
  keeping, because "cart VAT 0.06" next to three `0.02` rows is the artefact that stops the escalation.
- **Determinism**: price the same input twice in one process and once in a fresh one; bytes must match,
  explanations and tax views included. Run once with a deliberately mangled `getcontext().prec` to
  demonstrate that no tax figure moves (I28).

---

## 12. Decisions at a glance

Stage-3 decisions first, then the stage-1 and stage-2 decisions still in force.

| Decision | Alternative rejected | Because |
|---|---|---|
| **Tax is a decomposition of a final amount, not an adjustment** | A tax phase after 30, producing an explanation row | SOUTH's tax is not a movement — it was always inside the shelf price; NORTH's as a row would make the deltas sum to neither what came off nor what is owed. One structure covers both markets (§1.2) |
| **The promotion pipeline is market-blind** (I26) | A market flag threaded through the engine, or two pricer implementations | The product owner's own rule is that promotions act on the listed amount in both markets — so the pipeline is *already* identical, and a flag would only create places for it to stop being |
| **`CartView` exposes no profile and no rate** | Pass it "in case a rule needs it" | The first market-specific rule would be written within a month, and I26 would be unenforceable thereafter |
| **`MarketProfile` is four named axes, in a closed table in code** | Two hard-coded market classes; or the rate and mode as catalog fields | The axes are real and orthogonal in tax law and a third market is coming — but a tax regime is law, not merchandising, and a typo in a rate mis-states what we owe on every invoice |
| **The cart names its market, the catalog names its market, and `price()` refuses a mismatch** (Q28) | Market on the catalog alone; or on the cart alone | *A cart is for one market, and it tells you which* — and `unit_price` is uninterpretable without it. The catalog must also name one, since there is one file per market. Two independent statements of a fact neither derives from the other make the guard total, and mis-routing is the one new mistake this system can make |
| **`Quote.payable` is a top-level field** (Q30) | Leave it nested inside `tax`; or redefine `amount` to mean "payable" | *Make the number the customer pays the obvious one.* Nested two levels inside `tax` is not obvious; redefining `amount` would put a headline figure of `26.33` above working that ends at `22.50` |
| **No compatibility aliases for the renamed fields** (Q29) | Emit both spellings for a release | Nothing is live and nothing reads the old names; a shim for a dependency that has never existed is pure cost |
| **An unknown or missing `market` is a deployment fault; `price()` raises** | Default to NORTH; or quarantine and price at list | Quarantine is right for one broken promotion and wrong for a tax regime: a cart priced under no regime is invoiced wrongly and shipped, and found by a tax authority rather than a customer |
| **`TaxView` has one shape in both markets, with `net + tax == payable` always** | Separate `vat_added` / `vat_included` structures | The treatments differ by one enum member; two structures would be two renderers, two test suites and two places for the third market to land |
| **Cart tax under `LINE` granularity is the sum of line taxes, never recomputed** (I24, I25) | Round the cart amount once, allocate the difference | C4: three sachets carry `0.06`, not `0.08`. The product owner stated it; stating it twice (a sum rule and a prohibition) is what stops a later "simplification" |
| **No per-line `TaxView` in NORTH; the field is `None`** | Allocate the cart VAT down to the lines | It would manufacture per-line figures no NORTH invoice prints and a reader would take as authoritative — the reason stage 2 deleted `attribution` (Q31 confirms) |
| **Tax rounding is exact integer arithmetic on the true rational** | `Decimal.quantize` on a divided quotient | `20/120` does not terminate; truncating first can turn a non-half into an apparent half, and half-even then rounds it the wrong way — silently, on a fraction of invoices (I28) |
| **Promotion rounding stays `HALF_UP` in both markets** | Make step 2 of §5.2 follow the market's mode | The product owner specified half-even for *tax*; the same offer must not take a different amount off in two countries, and it would put a market decision back inside the pipeline |
| **`tax` is its own component, downstream of everything** | Three lines inside `explain` | It is the only place the market's tax fields may be read (checkable by imports), the place the third market lands, and testable with no cart at all |
| **`gross`/`net` renamed to `list_amount`/`amount`; `net` reserved for "excluding tax"** | Keep stage-2 names | A field called `net` holding a tax-inclusive amount is the naming bug §5.5 exists to prevent; legacy keys, if needed, are one adapter concern (§2.7) |
| **Currency moves from `[settings]` into the market profile** | Keep both | Stage 1 rejected a second place to state the currency; the market now determines it, so a separate field *is* the second place |
| **`validate` prints the resolved market and its regime** | Stay silent about settings | The most consequential thing in the file is a five-letter word, and a linter that says nothing about it invites the mistake it exists to catch |
| **The amounts are a fold of the explanation, not vice versa** | Compute amounts, then build a narrative beside them | Two paths drift; that drift is the stated deal-breaker. One record, four projections |
| **`explain` is the only constructor of `Quote`; `tax` the only constructor of `TaxView`** | Let the engine assemble the output | Makes "no second computation path" (I14) checkable by reading imports, not by testing outputs |
| **The journal is append-only, written only where the engine acts** | A mutable running total with notes attached | "In the order it happened" is then free, not maintained |
| **Opening adjustment has delta `0.00`; `basis` also published** | Opening delta `= +basis` | Deltas must add up to *what came off*, and *what we started from* must be clear; only an opening balance satisfies both |
| **No `RESIDUAL`, `ROUNDING` or `TAX` adjustment kind** | A reconciliation line; a tax row | The allocator makes parts sum exactly and tax is not a movement; an unrepresentable plug line is stronger than a rule against writing one |
| **Line explanations omit zero-share entries** | Every applied code on every line | *If it didn't change that line's price, it doesn't need to be on that line* |
| **Contest measures with the same `would_take` that applies, on capped value** | A separate "estimate" path; comparing notional value | One capping function: the number that wins is the number that lands (E3) |
| **Contest held at the first contender's slot; winner applies there** | Measure early, apply in the winner's own phase | Keeps the engine a single forward walk; applying later means a stale figure or a re-evaluation |
| **Contenders worth `0.00` leave as `NO_EFFECT`, `superseded_by` `None`** | Let them contest and be superseded | *It wasn't beaten by anything — it just saved them nothing.* It keeps `superseded_by` reliable |
| **One global exclusion group; non-stackable excludes only other non-stackables** | Named groups, priority fields, excluding everything | *One rule: two of them can't sit together. Nothing more elaborate.* |
| **Non-events reported in the support view, not in the explanation** | Zero-delta entries for unknown / duplicate codes | The explanation's rows stay exactly the rows that sum; the screen is where support sees everything |
| **Signed `delta`, positive `amount`/`discount`/`tax`, by a naming rule** | One signed convention throughout | A `total_discount` of `-2.45` reads like a credit; one negation in one module bridges them |
| **Invariant check before returning** | Trust the construction | A right price with a broken explanation caused a refund; a tax figure that does not match its invoice is found by a tax authority |
| Pure `price(cart, catalog)` library + thin CLI | Local HTTP endpoint | No network in substrate; purity is testability — and is what makes the contest's speculative evaluation free |
| `Decimal` from strings only, floats rejected at the edge | Integer cents at the boundary | Keeps the quantum contract visible at every boundary; cents push the formatting bug to every caller |
| Rules propose, engine disposes | Rules mutate a running total | A bad rule cannot break the total — and it is why `rules` needed no change in stage 2 *or* stage 3 |
| Cart discounts allocated to lines (largest remainder) | Subtract from the total only | Lines must sum to the total, deltas must sum with no residue, and per-line tax needs real per-line amounts |
| Cap at application, in the journal | `max(0, total)` at the end | A late clamp makes the verdicts, the explanation and the tax all lie |
| Phase table keyed by kind | Order = submission order | Two customers typing the same codes in different orders must be charged the same |
| One verdict per submitted code | Error list | Impossible to silently drop a code; arity is checkable |
| Quarantine bad *promotion* entries at runtime, fail loudly in `validate` | Refuse to start | One typo must not stop the shop — but see the market decision above for where that stops applying |
| TOML via stdlib `tomllib` | JSON | The file's audience is non-engineers editing constantly |
| Stacked BOGOs consume units sequentially | Each evaluated against original quantity | Independent evaluation can give a line away |
| Retirement = delete the entry; no `enabled` flag | A disable flag | Two mechanisms for "this code is over" |
| Zero/negative quantity rejects the cart | Price it at 0.00, or drop the line | Keeps line-for-line correspondence with the caller's basket — and keeps phantom `0.00` VAT lines off a SOUTH invoice |
| No cart-size limit | A defensive cap | One linear in-memory pass |
| `status` + `label` are the interface; `detail` is unstable internal prose | One human-readable message per code | The front end owns customer wording |
| `label` mandatory in the catalog | Optional, with the code as fallback | The storefront and the explanation both depend on it |
| A `0.00` total is a normal result | Refuse, or impose a minimum charge | Pricing must return the number downstream needs in order to decide |
| One catalog per market | A shared file with per-market overrides | `10.00 off` is a different offer in two currencies and conventions; sharing buys nothing and costs an override mechanism |

---

## 13. Product answers — all closed

### 13.1 Stage-1 answers — closed, and still in force

| Q | Answer | Where it lives |
|---|---|---|
| Q1 BOGO at quantity 3 | One is free — `floor(qty / n)` | §6.3, boundary table §11 |
| Q2 PCT vs AMT order | Indifferent; must be repeatable | §6.1 |
| Q3 Two 10% codes | 19%, compounded | §6.1, case D2 |
| Q4 Two BOGOs on one SKU | Both apply | §6.3 |
| Q5 Line price | What the customer pays; lines add up to the total | §2.6, I3, §5.3 |
| Q6 Duplicate code | Count once, tell the customer | §6.4 |
| Q7 Rounding | To the cent, same answer twice | §5.2, I1, I8 |
| Q8 Retiring a code | Delete it; `UNKNOWN` is the right message | §7.5 |
| Q9 Zero-quantity line | Engineering's call ⇒ reject as malformed | §4.3 |
| Q10 Currency | One currency, 2dp; configuration our call | §7.5 — now supplied by the market profile |
| Q11 Cart size | Engineering's call ⇒ no limit, linear pass | §8.1 |
| Q12 Stacked BOGO magnitude | Two — a coffee already given away doesn't earn another | §6.3 |
| Q13 Zero-value orders | Fine, it happens | §5.4 |
| Q14 Code matching | Customers type them however they like | §6.4 |
| Q15 Wording | Ours is internal; the front end writes the customer's | §2.8, §7.4 |

Q5 is the one stage 3 refines rather than changes: "the lines add up to the total" is now stated as
`sum(line.amount) == quote.amount`, which is exactly what it always meant, and in NORTH the VAT is a
further single charge on top of that sum, published as `quote.payable` because Q30 asked for the figure
the customer pays to be the obvious one.

Q10's answer — *one currency, and how to configure it is your call* — is what makes moving the currency
into the market profile a configuration decision rather than a reopened product question.

### 13.2 Stage-2 answers — closed, and still in force

| Q | Answer | Where it lives |
|---|---|---|
| Q16 What "non-stackable" excludes | Only another non-stackable | §6.5 |
| Q17 One group or named groups | One rule: two of them can't sit together | §6.5, §7.6 |
| Q18 Which slot the winner applies at | Engineering's call ⇒ the earliest contender's slot | §6.5 |
| Q19 A promotion worth `0.00` on a line | If it didn't change that line's price, it isn't on that line | §4.9 |
| Q20 Where non-events are reported | Ours to place ⇒ `code_results`, and part 3 of the support view | §4.10, §6.7, I20 |
| Q21 The shape of the opening entry | Deltas add up to what came off; what we started from must be clear | §2.5, I10–I12 |
| Q22 `LineQuote.attribution` | Nothing reads it ⇒ removed outright | stage 2 |
| Q23 Sign convention | Engineering's call ⇒ `delta` signed, `amount`/`discount` magnitudes | §5.5, I19 |
| Q24 A stamp for auditors | Not now — build for today | §1.6, §9 |
| Q25 A catalog-authored "why not" line | Code, name and amount is enough | §2.5, §7.6 |

Q21 is the answer stage 3 leans on hardest. *The deltas add up to what came off* is the single sentence
that rules tax out of the adjustment chain (§1.2): a `+3.83` row would make them add up to something
else. Had the answer been "the deltas add up to what is owed", stage 3 would look different.

Q22 is the precedent for §2.4's `None`: a field with no consumer and a plausible-looking value is worse
than no field.

### 13.3 What stage 3 decided on engineering's authority

Recorded here rather than left as assumptions, each with one place to change it if the product owner
disagrees:

| | Decision | Explicitly delegated? | Where the argument is |
|---|---|---|---|
| a | Tax is a `TaxView` beside the explanation, not a row inside it | yes — Q32, *where the tax sits is your call* | §1.2, §4.10, §6.7 |
| b | `payable` is promoted to a top-level field rather than `amount` being redefined | yes — Q30, *make it the obvious one* | §2.6, I31 |
| c | No compatibility aliases; the rename is taken outright | yes — Q29, *nobody is reading those names* | §2.7 |
| d | The mismatch guard raises, with no preference order between cart and catalog | implied by Q28 | §2.3, §8, I30 |
| e | The rate, treatment, granularity and rounding are code, not catalog | no | §2.2, §7.4 |
| f | Tax arithmetic is exact integer rounding of the true rational | no | §5.7 |
| g | Currency moves into the market profile | no | §7.5 |

(e), (f) and (g) were not put to the product owner. (f) is a correctness requirement with no product
content — there is no version of "round half-even" that wants the other answer. (e) and (g) are
configuration decisions sitting inside answers already given: Q34 says rate changes are not a concern
today, and Q10 said currency configuration was ours to place. Each is recorded here with one place to
change it.

### 13.4 Stage-3 answers — all closed

| Q | Answer | Where it lives |
|---|---|---|
| Q26 Currency in SOUTH | Same currency in both; that isn't changing | §7.5 — currency on the profile, both entries agree; substrate line restored |
| Q27 One promotions file per market | One file per market; they run different offers | §7.5 |
| Q28 Market on the deployment or the request | A cart is for one market, and it tells you which | §2.3 — `Cart.market`, plus the catalog's, plus the guard (I30) |
| Q29 Old JSON key names | Nothing is live; nobody is reading those names | §2.7 — rename taken outright, no aliases |
| Q30 Which number is "the total" | Nothing is live. Make the number the customer pays the obvious one | §2.6 — `Quote.payable` at the top level (I31) |
| Q31 Per-line tax in NORTH | No. Only SOUTH invoices have to show it | §2.4 — `LineQuote.tax is None` in NORTH |
| Q32 Tax beside the explanation or inside it | Keep the working adding up. Where the tax sits is ours, as long as the customer can see what tax they paid | §1.2 (beside), §4.10 + I32 (visible) |
| Q33 Half-even beyond tax | Tax only | §5.2 — step 2 stays `HALF_UP` in both markets |
| Q34 A VAT rate changing | Not now — build for today | §2.2, §9 — no dated-rate machinery, no `as_of` |
| Q35 The tax element of each discount | Not now — build for today | §9 — priced, not built |
| Q36 Reduced or zero rates per product | Not now — build for today | §9 — priced, not built; the rate stays a cart-level fact |

**Three of these changed the design rather than confirming it, and one of them changed its shape.**

**Q28 is the one that moved a boundary.** The draft had the market on the catalog alone, reasoning from
stage 1's argument against a per-request currency: a second place to state a fact is a place for it to
disagree. The product owner's answer — *a cart is for one market, and it tells you which* — is right for
a reason the draft had underweighted: `unit_price` is **uninterpretable** without a market. A bare `12.00`
is a tax-exclusive price in one country and a tax-inclusive price in the other, so a cart that does not
say which is not a well-formed request; it is a request that only means something while it happens to be
next to the right file. Making the cart self-describing also makes it storable and replayable.

That answer plus Q27 (one file per market) then produces the situation stage 1 warned about — two parties
stating one fact — and the resolution is to treat the redundancy as a **guard rather than a duplication**
(§2.3, I30). The distinction is worth keeping in the design's vocabulary: stage 1 rejected a second
statement of a fact *nothing else knew*, which buys only a reconciliation path. Here two parties genuinely
and independently know it, so requiring agreement costs one string comparison and closes the one failure
this system newly admits — a SOUTH basket routed to `north.toml`, priced at the wrong rate with the wrong
offers, and invoiced. `MarketMismatchError` gets its own category in §8 because neither input is wrong;
the pairing is.

**Q30 added a field.** `Quote.payable` restates `quote.tax.payable`, which this design would normally
refuse to do — but the instruction was that the number the customer pays should be *obvious*, and a figure
nested inside a structure called `tax` is not. The restatement is made safe the way stage 2 made `basis`
safe: one value, one computation, one equality invariant (I31). What was *not* done is the tempting
version — redefining `amount` to mean "payable" — because `amount` is where the explanation ends (I22),
and in NORTH a headline `26.33` sitting above working that stops at `22.50` is the precise disagreement
stage 2 exists to prevent. Two different numbers, two accurate names.

**Q32 confirmed the stage's central decision while delegating its placement.** *Keep the working adding
up* is what rules tax out of the adjustment chain: a `+3.83` row makes C1's deltas sum to `+1.33`, which
is neither what came off nor what is owed (§1.2). *As long as the customer can see what tax they paid* is
a requirement about a screen, not a payload, and is discharged the way Q20's was — on the renderer, as
I32, with both figures reachable in the payload without arithmetic. The two clauses together are exactly
the split this design already had: the explanation is the working, the `TaxView` is the decomposition, and
the renderer shows both.

**Five answers confirmed choices the design had already made**, which is the useful outcome: Q26, Q27,
Q29, Q31 and Q33 each removed an alternative rather than a line of code. Q33 is the most load-bearing of
them — had half-even reached promotion amounts, the market-blind pipeline of §1.1 would have had to be
rebuilt, and the claim that "an entire second tax regime landed as one data row and one pure function"
would have been false.

**Q34, Q35 and Q36 were all *not now — build for today***, the same answer stage 2 gave to a version
stamp. They are kept as priced rows in §9 and as nothing else: there is no `as_of` parameter, no per-line
rate field, no `CodeResult` tax field, and no configuration surface for any of them. Q36 in particular
keeps the tax rate a **cart-level fact**, which is what lets §6.5's contest compare gross values without
a product question attached.

### 13.5 Nothing is open

Every product decision in this document traces to an answer in §13.1, §13.2 or §13.4, or to an explicitly
delegated engineering call recorded with its reasoning in §13.3.

The mechanism is the part worth defending in review, and it is not open:

> **One append-only journal, market-blind, whose fold is the price; four projections of it, one of which
> is a pure function of the market profile; and no second computation path anywhere.**

Every answer in §13.4 changed *what goes into the profile*, *what the request must state*, or *what is
shown from the quote*. None of them touched that mechanism, and none of them can make the explanation,
the invoice and the tax figure disagree — because all three are the same numbers read in different
directions, and the one new number in the system is derived from the others by a function with a single
call site.

What that does not mean is that nothing will change. The requests most likely to arrive next are visible
from here — a third market, a rate change with an effective date, reduced rates per product, tax on each
discount line — and §9 states what each costs before anyone has to estimate it under pressure. Three of
the four are a profile row or a call site. The fourth, per-product rates, is the one that moves a seam,
and it is flagged as such precisely so it is never quoted as a field.

The build can start from this document. §3's invariants and §10's traced cases, taken together, are the
acceptance criteria; §11 says what the test suite has to cover beyond them.
