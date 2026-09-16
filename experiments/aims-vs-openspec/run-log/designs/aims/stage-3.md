# Cart pricing — architecture (stage 3)

**Status:** the complete architecture of the product as it now stands — cart pricing **for a market**,
with its explanation, promotions that can exclude one another, and the market's tax law. It supersedes
`design/stage-2.md` as the shape the first sprint builds against; stage-1 and stage-2 are kept unedited
as the record of the earlier rounds. No implementation code exists yet.

**Substrate (given, not chosen):** Python 3.11+, standard library only, single process, single
currency, no UI/network/database/persistence. `decimal.Decimal` permitted but confined.
`decisions/0001`.

**What changed and why, in one line:** we are opening in a second country whose tax law works the
other way round — listed prices already contain the tax, the tax is reported per line, and it is
rounded per line by a different rule — so *which* tax applies, *where* it is assessed and *how* it is
rounded stop being facts about the product and become the law of the **market** a cart is priced for.
A market also runs its own offers, so it has its own catalogue file. The tax is recorded as an entry
in the same explanation the amounts are computed from, because a tax figure produced beside the
amounts is the second producer of one fact that `decisions/0011` exists to prevent. `decisions/0015`,
`0016`, `0017`, `0018`, `0019`.

**The product owner's answers to the six questions this design put to them are folded in**, and where
one of them changed the design it is marked in place (§17 lists all six with what each one moved).

---

## 1. The idea in one paragraph

A cart is priced **for a market**: the law that taxes it and the offers it may use are both the
market's, and the cart names which market it is. Pricing is
still the sequence of adjustments that stage-2 made the primary artifact: an **explanation**, opened
at a list price and extended by one entry per thing that happened, whose final amount is *computed
from* its entries. Tax becomes one more thing that happens, recorded the same way — so the story of a
NORTH cart reads *25.00 → SAVE10 −2.50 → 22.50 → VAT 17% +3.83 → 26.33*, and the story of a SOUTH line
reads *12.00 → SAVE10 −1.20 → 10.80, of which VAT 20% is 1.80*. The two markets differ in exactly two
things, and both are the tax rule's own business: **what the assessment does to the amount** (NORTH
adds it on top of a tax-exclusive price; SOUTH finds it inside a tax-inclusive one, moving nothing),
and **which amounts are assessed** (NORTH: the cart's, once, rounded half-up; SOUTH: each line's,
rounded half-even, the cart's figure being their sum). Nothing else in the system knows there is more
than one country: **the promotion kinds and the contest are untouched by this stage**, and the
catalogue changes only in that there is now one file per market — a promotion takes its percentage or
its fixed amount off the amounts it is given and neither knows nor cares whether they contain tax
(*"ten off is ten off the price on the shelf, in both places"*).

```
one catalogue file per market (TOML, business-edited; a code may be marked non-stackable)
        │  catalog.load_catalogs()           ← the only module that knows the file format
        ▼
  PromotionCatalogs ── for_market(id) → PromotionCatalog ── lookup(code) → CatalogEntry
                                     │
cart (customer id, MARKET, lines, codes) ──┤
        │                            ▼
        │                    engine.price_cart()
        │   ┌────────────────────────────────────────────────────────────────┐
        │   │ 1 resolve            the market → its tax rule AND its catalogue (not priceable
        │   │                      without either); each code, in that catalogue →
        │   │                      unknown / disabled / duplicate: reported, never fatal
        │   │ 2 canonical order    the result does not depend on typing order
        │   │ 3 LINE stage         uncontested line codes: propose → commit (units become free)
        │   │ 4 THE CONTEST        every non-stackable code, any scope, against this one basket:
        │   │                      largest wins and commits here; the rest recorded superseded
        │   │ 5 CART stage         uncontested cart codes: propose → commit (money comes off)
        │   │ 6 TAX stage          the market's rule assesses the amounts it names, once, and the
        │   │                      ledger records the entry. The ledger is SEALED: nothing further
        │   │                      may be proposed or committed.
        │   │ 7 read the answer    every figure is read off an explanation
        │   └────────────────────────────────────────────────────────────────┘
        ▼
   CartLedger ──────────────► Quote
     ├─ cart Explanation  ───────► quote.explanation   (list → … → total → VAT → amount due)
     └─ LineLedger per line ─────► line.explanation    (list → … → net, of which tax)
                                          │
                                          ▼
                                   cli.py serializes to JSON
```

---

## 2. Module map

One sentence per module, stating **the single reason it would change**. If two reasons fit in one
sentence with an "and", the module is wrong.

| Module | Changes when… |
|---|---|
| `pricing/money.py` | the currency's arithmetic, rounding, or presentation rules change |
| `pricing/explanation.py` | what an account of a price is made of changes |
| `pricing/cart.py` | what a caller may ask us to price changes |
| `pricing/promotions.py` | a promotion **kind**'s own rule is added or changed |
| `pricing/market.py` | **(new)** the tax law of a market we sell in changes, or we open in a new one |
| `pricing/catalog.py` | where promotion definitions come from, or how they are written, changes |
| `promotions.<MARKET>.toml` | that market's business adds, retires, or re-marks a **code** |
| `pricing/quote.py` | what we report back changes |
| `pricing/engine.py` | how the parts of pricing interact — order, exclusion, clamping, spreading, when tax is assessed, reporting — changes |
| `pricing/cli.py` | the wire format or the command surface changes |

`market.py` is new, and it is deliberately **not** part of `engine.py`. The engine owns *when* things
happen; a market's tax law owns *what* the tax on an amount is and *what assessing it does to that
amount*. Putting the rate, the rounding mode and the inclusive/exclusive treatment in the engine would
make "how many countries do we sell in" a reason for the pipeline to change, and would put a `if
market is SOUTH` in the middle of the one module whose job is sequencing.

Dependency rules: nothing imports `cli.py`; only `catalog.py` imports `tomllib`; only `money.py` and
`catalog.py` import `decimal`; `promotions.py` imports `money.py` and `cart.py` and nothing else;
**`market.py` imports `money.py` and `cart.py` and nothing else** — in particular it does not import
`explanation.py`, because no tax rule writes an explanation, exactly as no promotion does.

**Unchanged by this stage, and that is the measurement:** `promotions.py` is not touched at all, and
`catalog.py` changes only by learning that there is one file per market — no kind, no parser, no entry
shape, no containment rule moves. A percentage code is 10% off whatever it is pointed at, and a fixed
amount is that amount off the price on the shelf, in either country.

---

## 3. Money, the change in money, and rounding

`Money` is still a **non-negative** amount in integer minor units, still the only place that rounds,
formats to 2dp, and splits an amount into parts that still sum to it (`decisions/0003`). `MoneyDelta`
is still the signed change (`decisions/0012`). Two things are new, both forced by the tax rules.

**A second rounding mode.** SOUTH rounds a line's tax **half-even**; NORTH rounds the cart's VAT
**half-up**, and a promotion's percentage keeps rounding half-up as it always has. There is still
exactly one *place* that rounds — the rule that changed is that the caller now names the mode, because
two different laws now round two different figures two different ways (`decisions/0017`).

**An exact rational portion.** Extracting tax from a tax-inclusive amount is not a percentage of that
amount: 20% VAT inside 10.80 is 10.80 × 20/120, and 20/120 has no exact decimal form. So the primitive
is "the part of this amount given by an exact fraction, rounded once", and a percentage is one case of
it.

```python
# pricing/money.py

class Rounding(Enum):
    HALF_UP   = "half_up"      # the promotion rule (decisions/0003) and NORTH's VAT
    HALF_EVEN = "half_even"    # SOUTH's per-line VAT

class Money:
    """A non-negative amount of the single currency, held as an integer number of cents."""
    # unchanged from stage-2:
    @classmethod
    def parse(cls, text: str) -> "Money": ...        # "12.50" -> 1250; exact, via Decimal
    @classmethod
    def zero(cls) -> "Money": ...
    def __add__(self, other: "Money") -> "Money": ...
    def __sub__(self, other: "Money") -> "Money": ...        # raises ArithmeticError on underflow
    def times(self, whole_units: int) -> "Money": ...        # exact; no rounding possible
    def allocate(self, weights: "Sequence[Money]") -> "list[Money]": ...
        # splits self into parts proportional to weights, summing EXACTLY to self; largest-remainder,
        # ties by index.
    def after(self, delta: "MoneyDelta") -> "Money": ...     # raises if the result would be negative
    def is_zero(self) -> bool: ...
    def format(self) -> str: ...                     # always 2dp: "12.50", "0.00"

    # new in stage 3 — THE rounding point, now with the mode named by the caller:
    def portion(self, numerator: int, denominator: int, rounding: Rounding) -> "Money": ...
        # the part of this amount given by the exact fraction numerator/denominator, rounded ONCE to
        # the cent by the named mode. Exact rational arithmetic on the minor units; no float, and no
        # intermediate sub-cent value survives the call. denominator > 0, numerator >= 0.

    def percentage(self, percent: "Percent") -> "Money": ...
        # unchanged in behaviour and signature — the discount rule, defined as
        # self.portion(*percent.as_fraction(), rounding=Rounding.HALF_UP). promotions.py is untouched.


class MoneyDelta:
    """A signed change in money, in integer minor units."""
    @classmethod
    def opening(cls, amount: Money) -> "MoneyDelta": ...     # +amount — a list price entering a ledger
    @classmethod
    def reduction(cls, amount: Money) -> "MoneyDelta": ...   # -amount — a discount
    @classmethod
    def addition(cls, amount: Money) -> "MoneyDelta": ...    # new: +amount — tax added on top
    @classmethod
    def nothing(cls) -> "MoneyDelta": ...                    # exactly zero
    @classmethod
    def between(cls, basis: Money, final: Money) -> "MoneyDelta": ...
    @classmethod
    def total(cls, deltas: "Iterable[MoneyDelta]") -> "MoneyDelta": ...   # THE sum
    def __add__(self, other: "MoneyDelta") -> "MoneyDelta": ...
    def __neg__(self) -> "MoneyDelta": ...
    def magnitude(self) -> Money: ...                # what a contest compares (§8)
    def is_reduction(self) -> bool: ...
    def is_addition(self) -> bool: ...               # new: reads a tax that was added apart from
                                                     # one that was already inside (§6, the wire format)
    def is_zero(self) -> bool: ...
    def format(self) -> str: ...                     # "-2.50", "+3.83", "0.00"


class Percent:
    """A percentage in (0, 100], exact to the written digits."""
    @classmethod
    def parse(cls, text: str) -> "Percent": ...
    def as_fraction(self) -> tuple[int, int]: ...    # new: exact (numerator, denominator) of the
                                                     # fraction of the whole: "17" -> (17, 100),
                                                     # "7.5" -> (75, 1000). Decimal stays inside.
    def format(self) -> str: ...
```

`as_fraction` is what lets a tax rule express *both* of its arithmetics without `Decimal` leaving
`money.py`: tax **on** a net amount is `portion(n, d)`; tax **within** a gross amount is
`portion(n, d + n)`, because r/(100+r) = n/(d+n). Both are exact, and each rounds exactly once.

---

## 4. The request domain — a cart is priced for a market

```python
# pricing/cart.py

class Sku:
    @classmethod
    def of(cls, raw: str) -> "Sku": ...              # normalised once: trim + case-fold

class MarketId:
    """Which market's law this cart is priced under. An identifier, not a rule."""
    @classmethod
    def of(cls, raw: str) -> "MarketId": ...         # normalised the same way (Q7)

@dataclass(frozen=True)
class CartLine:
    sku: Sku
    unit_price: Money                                # the LISTED price: tax-exclusive in NORTH,
                                                     # tax-inclusive in SOUTH. Money either way.
    quantity: int                                    # >= 1, validated here
    def gross(self) -> Money: ...                    # unit_price.times(quantity) — unchanged

@dataclass(frozen=True)
class Cart:
    customer_id: str                                 # carried, echoed, read by nothing
    market: MarketId                                 # required: an unpriced market is not a cart
    lines: tuple[CartLine, ...]
    codes: tuple[str, ...]                           # exactly as the customer typed them, in order
    # Construction raises InvalidCartError with every problem found, not the first.
```

`MarketId` lives here, beside `Sku`, because it is an **identifier the caller supplies** — the same
kind of thing as a SKU, normalised by the same rule, and validated against nothing at construction
(`cart.py` knows no more about which markets exist than it knows which SKUs exist). Binding it to the
law that governs it — **its tax rule and its catalogue of offers** — is the engine's resolve step,
exactly as binding a code to a promotion is (§9). The alternative — `Cart` holding a `Market` object
with a tax rule inside it — would put a pricing rule in the request domain and make `cart.py` import
`market.py`.

The market is **required**, with no default: *"a cart is for one market, and it tells you which"*
(Q22). `cart.py` is otherwise untouched — `CartLine.gross()` keeps its name, because the owner's
answer to Q20 keeps every figure this product already had exactly as it was (§10).

An empty cart is valid in either market and prices to 0.00, with a tax assessment of 0.00.

---

## 5. Promotions — untouched

```python
# pricing/promotions.py   — not one line of this module changes in stage 3

class PromotionCode:
    @classmethod
    def of(cls, raw: str) -> "PromotionCode": ...

class Promotion(Protocol):
    @property
    def code(self) -> PromotionCode: ...
    def describe(self) -> str: ...

class LinePromotion(Promotion, Protocol):
    @property
    def target(self) -> Sku: ...
    def free_units(self, paid_units: int) -> int: ...

class CartPromotion(Promotion, Protocol):
    def requested_discount(self, remaining: Money) -> Money: ...

@dataclass(frozen=True)
class PercentOffCart:                # kind = "PCT"
    code: PromotionCode
    percent: Percent
    def requested_discount(self, remaining: Money) -> Money:
        return remaining.percentage(self.percent)      # half-up, as it always was

@dataclass(frozen=True)
class AmountOffCart:                 # kind = "AMT"
    code: PromotionCode
    amount: Money

@dataclass(frozen=True)
class OneFreeInEveryN:               # kind = "BOGO"
    code: PromotionCode
    target: Sku
    every: int
```

This is the load-bearing claim of the stage, so it is worth stating plainly: **the product owner's
rule that "promotions apply to the gross, tax-inclusive amount, exactly as a customer would expect"
requires no change here, because a promotion has never known what the amounts it is given mean.**
`PercentOffCart` takes 10% of the remaining money; in NORTH that money is tax-exclusive and in SOUTH it
is tax-inclusive, and 10% of 12.00 is 1.20 either way (C2). `OneFreeInEveryN` frees a unit worth its
own listed price; in SOUTH that price contains tax, so the 4.00 it takes off is a gross 4.00 (C5).
`AmountOffCart` is the same story and the owner confirmed it in their own words (Q21): *"ten off is
ten off the price on the shelf, in both places — that's what the customer sees."* A fixed amount is
clamped to what remains, as it always was, and needs no notion of tax to do it.
The one thing that would have broken this is computing tax *before or during* the promotion stages —
which is why the tax stage is last and the ledger is sealed after it (§7, I14).

Non-stackability is still a property of the catalogue entry, not of a kind (§10), and the contest is
unchanged (§8).

---

## 6. The explanation — the account of one amount, including its tax

```python
# pricing/explanation.py

class Scope(Enum):
    LINE = "line"                    # the entry came from something acting on a line
    CART = "cart"                    # the entry came from something acting on the cart

class AdjustmentKind(Enum):
    LIST_PRICE  = "list_price"       # the opening entry: where the amount started
    PROMOTION   = "promotion"        # a code that actually moved money
    NOT_APPLIED = "not_applied"      # a code that qualified but was superseded by another
    TAX         = "tax"              # new: the market's tax on this amount

@dataclass(frozen=True)
class Adjustment:
    kind: AdjustmentKind
    delta: MoneyDelta                       # the exact money this contributed to the amount
    code: PromotionCode | None              # None for LIST_PRICE and TAX
    scope: Scope | None                     # None only for LIST_PRICE
    detail: str                             # the promotion's or the tax rule's own phrase
    superseded_by: PromotionCode | None     # NOT_APPLIED only
    forgone: Money | None                   # NOT_APPLIED only: what it would have saved
    tax: Money | None                       # new: TAX only — how much of the amount is tax

    # __post_init__ enforces the shape of each kind:
    #   LIST_PRICE   =>  code is None and scope is None and not delta.is_reduction()
    #   PROMOTION    =>  code is not None and scope is not None and delta.is_reduction()
    #   NOT_APPLIED  =>  delta.is_zero() and superseded_by is not None and forgone is not None
    #   TAX          =>  code is None and scope is not None and tax is not None and
    #                    (delta.is_zero() or delta == MoneyDelta.addition(tax))
    #                    — i.e. assessing tax either adds exactly the tax, or moves nothing at all.

class Explanation:
    """The ordered story of one amount: opened at a list price, then one entry per thing that happened.

    The final amount is COMPUTED from the entries. There is no stored total to disagree with them.
    """
    @classmethod
    def opened_at(cls, list_price: Money) -> "Explanation": ...
    def record(self, adjustment: Adjustment) -> "Explanation": ...   # returns a new Explanation

    @property
    def list_price(self) -> Money: ...               # the opening entry's amount
    @property
    def final(self) -> Money: ...                    # Money.zero().after(total of ALL deltas)
    @property
    def net_delta(self) -> MoneyDelta: ...           # total of the deltas AFTER the opening entry
    @property
    def tax(self) -> Money: ...                      # new: Σ of the TAX entries' `tax` amounts
    @property
    def after_promotions(self) -> Money: ...         # new: list_price + Σ PROMOTION deltas — the
                                                     # running amount at the moment every promotion
                                                     # had applied and no tax had been assessed. The
                                                     # tax entry is always last, so this is exactly
                                                     # the amount immediately before it.
    def entries(self) -> tuple[Adjustment, ...]: ...
    def steps(self) -> "Iterator[tuple[Adjustment, Money]]": ...   # each entry + the running amount
    def promotion_deltas_for(self, scope: Scope) -> MoneyDelta: ...
        # the discount folds the report uses (§9). It filters on KIND as well as scope — see below.
```

**The fold that had to be corrected.** Stage-2's `deltas_for(scope)` summed every delta of a scope,
which was safe while every non-opening entry was a promotion. It is not safe now: NORTH's VAT is a
`CART`-scoped entry of **+3.83**, and a fold that only filtered by scope would report the cart's
discount total as 1.33 (−2.50 + 3.83) instead of 2.50. So the discount folds are explicitly
`kind == PROMOTION` folds, and the tax fold is a `kind == TAX` fold. Each reported figure names the
kind of entry it is made of; no figure is "everything that happened to sum up".

Four properties hold **by construction**, not by assertion:

1. `final == list_price.after(net_delta)` and `net_delta == MoneyDelta.between(list_price, final)` —
   the deltas sum exactly to the difference, to the cent, **including the tax delta** (I8). In NORTH a
   cart's net delta can now be positive; nothing in the type or the fold cared.
2. The order of `entries()` is the order things were committed, and the tax entry is always last (§7).
3. A `NOT_APPLIED` entry contributes exactly zero, so recording what did *not* happen cannot disturb
   the arithmetic of what did.
4. **A `TAX` entry states how much of this amount is tax, and its delta says whether paying it changed
   the amount** — +tax where the market adds it to a tax-exclusive price, zero where the market's
   prices already contained it. So one kind of entry covers both laws; `after_promotions` is the
   figure this product has always reported, and `final` is what the customer pays — in NORTH they
   differ by the VAT, in SOUTH they are the same number because the tax was already inside (I13).

There is still no rounding entry and there cannot be one: every delta is exact at the moment it is
made, tax included — `Money.portion` rounds once and its result *is* the figure recorded.

---

## 7. The ledgers — the only things that can change an amount

Unchanged in substance: a ledger owns a balance **and** its explanation, and the single operation that
moves the balance is the same operation that appends the entry. Applying a promotion is still split
into **propose** (compute the whole change — clamped, spread, priced; nothing moves) and **commit**
(apply and record; nothing is recomputed), because the contest must compare two possible futures.

```python
# pricing/engine.py  (internal collaborators; none of this is public)

class Proposal(Protocol):
    @property
    def code(self) -> PromotionCode: ...
    @property
    def scope(self) -> Scope: ...
    @property
    def detail(self) -> str: ...
    def total(self) -> MoneyDelta: ...
    def line_deltas(self) -> tuple[MoneyDelta, ...]: ...
    def commit(self) -> None: ...

class LineProposal(Proposal, Protocol):
    def freed_units(self) -> tuple[int, ...]: ...

class LineLedger:
    """One cart line's running balance and its story."""
    def __init__(self, line: CartLine): ...          # explanation opened at line.gross()
    @property
    def paid_units(self) -> int: ...
    @property
    def unit_price(self) -> Money: ...
    @property
    def remaining(self) -> Money: ...                # == self.explanation.final, always
    @property
    def explanation(self) -> Explanation: ...
    def free(self, units: int, adjustment: Adjustment) -> None: ...
    def reduce(self, adjustment: Adjustment) -> None: ...
    def assess_tax(self, rule: "LineTaxRule") -> Adjustment: ...       # new
        # asks the rule for the tax on MY OWN current amount, applies the assessment's delta and
        # appends the TAX entry in one step, and returns the entry so the cart can aggregate it.
        # The ledger asks; the rule answers; the ledger records — there is no way to assess one
        # amount and record the result against another.

class CartLedger:
    """The cart's balance, its story, and every rule about how an adjustment is spread across lines."""
    def __init__(self, cart: Cart): ...
    @property
    def remaining(self) -> Money: ...                # Σ line.remaining — the basket promotions act on
    @property
    def explanation(self) -> Explanation: ...
    def paid_units(self, sku: Sku) -> int: ...

    def propose_line(self, promotion: LinePromotion) -> LineProposal: ...
    def propose_cart(self, promotion: CartPromotion) -> Proposal: ...
    def record_superseded(self, loser: Proposal, winner: PromotionCode) -> None: ...

    def assess_tax(self, rule: "TaxRule") -> None: ...                 # new — and TERMINAL
        # A LineTaxRule: every LineLedger assesses its own final amount and records its own entry;
        #   the cart then records ONE entry whose `tax` is the SUM of those entries' tax and whose
        #   delta is the sum of their deltas — an aggregate of what was assessed, never a second
        #   assessment of the cart's amount (I12). This is why C4's cart tax is 0.06 and not 0.08.
        # A CartTaxRule: the cart assesses its own amount once and records one entry; no line is
        #   touched, and no line's amount changes (the product owner's rule for NORTH).
        # Either way the ledger is SEALED afterwards: propose_line, propose_cart, record_superseded
        # and assess_tax all raise from here on (I14).

    def priced_lines(self) -> tuple[PricedLine, ...]: ...
```

**The seal is a tripwire, not a policy** — the same species as `Money.after` raising. The pipeline
already assesses tax last; the seal is what makes "no promotion is ever computed against an amount the
tax assessment has already touched" a property of the ledger rather than a fact a future reader has to
notice about the order of six lines in the engine. It costs one flag and one raise, and the rule it
protects is worth real money: in NORTH a discount committed after the VAT entry would discount the
tax, and in SOUTH a discount committed after the assessment would leave a line's reported tax
describing an amount the line no longer has.

**What the cart's balance means, precisely.** `CartLedger.remaining` is still Σ line remaining — the
cart keeps no balance of its own, which is what made I6 definitional, and it is still exactly the
basket cart promotions and the contest work from. NORTH's cart-level VAT is the one entry in the
cart's explanation that is neither a per-line aggregate nor allocated across the lines, so after it
the cart's *explanation* (26.33) and Σ line amounts (22.50) differ by exactly the cart-level tax.
That is not a leak in I6; it is I6 restated, and the restatement is forced by the product owner's two
NORTH rules — line amounts stay as they are, and VAT is rounded once at cart level (§13, I6).

---

## 8. The market and its tax law

```python
# pricing/market.py

@dataclass(frozen=True)
class TaxAssessment:
    """What a tax rule says about one amount."""
    tax: Money                       # how much tax this amount bears
    delta: MoneyDelta                # what assessing it does to the amount:
                                     #   +tax  — the price excluded the tax, so it is added
                                     #   zero  — the price already contained it, so nothing moves

class LineTaxRule(Protocol):
    """A market that assesses tax on each line's own final amount."""
    def assess_line(self, amount: Money) -> TaxAssessment: ...
    def describe(self) -> str: ...

class CartTaxRule(Protocol):
    """A market that assesses tax once, on the cart's amount after every promotion."""
    def assess_cart(self, amount: Money) -> TaxAssessment: ...
    def describe(self) -> str: ...

TaxRule = LineTaxRule | CartTaxRule


@dataclass(frozen=True)
class VatAddedToCart:
    """NORTH: listed prices exclude VAT; it is added to the discounted cart, once, rounded half-up."""
    rate: Percent
    def assess_cart(self, amount: Money) -> TaxAssessment:
        n, d = self.rate.as_fraction()
        tax = amount.portion(n, d, Rounding.HALF_UP)
        return TaxAssessment(tax=tax, delta=MoneyDelta.addition(tax))
    def describe(self) -> str:
        return f"VAT {self.rate.format()}% on the discounted cart"


@dataclass(frozen=True)
class VatIncludedInLine:
    """SOUTH: listed prices contain VAT; each line's own tax is extracted, rounded half-even."""
    rate: Percent
    def assess_line(self, amount: Money) -> TaxAssessment:
        n, d = self.rate.as_fraction()
        tax = amount.portion(n, d + n, Rounding.HALF_EVEN)       # r/(100+r)
        return TaxAssessment(tax=tax, delta=MoneyDelta.nothing())
    def describe(self) -> str:
        return f"VAT {self.rate.format()}% included in the price"


NORTH = MarketId.of("NORTH")
SOUTH = MarketId.of("SOUTH")

_MARKETS: "Mapping[MarketId, TaxRule]" = {
    NORTH: VatAddedToCart(Percent.parse("17")),
    SOUTH: VatIncludedInLine(Percent.parse("20")),
}

def tax_rule_for(market: MarketId) -> TaxRule: ...
    # raises InvalidCartError naming the market — a cart we cannot price at all is not a cart we
    # price partially (§8, the resolve step).
```

**Two protocols, one method each, named differently.** This is the shape the promotion seam already
uses (`LinePromotion.free_units` / `CartPromotion.requested_discount`) and it is used here for the
same reason: the two rules do not act on the same thing, so a single interface would have to be
`assess(amount)` plus a flag saying which amounts to pass it — and the engine would branch on the
flag, which is the rule leaking back out of its owner. Distinct method names also make the dispatch
honest at runtime: two structurally identical protocols are not distinguishable by `isinstance`.

**What a third market looks like** — the test that these interfaces are real abstractions rather than
one class in a costume. A country with tax-exclusive shelf prices that taxes **per line** (a US-style
sales tax on each line, added on top) is a `LineTaxRule` whose assessment returns a non-zero delta;
the line ledger applies it, the cart's aggregate sums the deltas as well as the taxes, and no other
module changes. A country with a **reduced rate on some SKUs** is a rule that consults the line's SKU —
still a `LineTaxRule`, still one class. Neither needs a new field on `TaxAssessment`: the type already
says the two things any assessment has to say.

**Why the rate is a parameter and the rounding mode is not.** The rate is the number the law states and
the one thing the two markets plainly share the shape of (17 vs 20). The rounding mode and the
assessment level are not independent knobs — they are *which law this is*: "rounded half-even, per
line" is inseparable from "the shelf price contains the tax and the invoice must show it". A third
market with a genuinely different combination is a third small class, which is one honest sentence in
`market.py`, not a matrix of flags nobody can read.

**Why the market table is code, not a business-edited file** — and the owner's answer (Q19): *"keep
that with the engineers. I don't want anyone editing a tax rate by hand."* `decisions/0004` and `0005`
rejected structural rules in a file non-engineers edit daily, because a typo there silently re-prices
the shop; a tax rate is the most structural number in the system, and a wrong digit misreports money to
a tax authority. Changing a rate is an edit here and a deploy.

**And no machinery for a rate that changes** — no effective dates, no rate history, no staged
switch-over: *"not now — build for today"* (Q19). When a rate changes, `VatAddedToCart(Percent.parse(
"17"))` becomes the new number. Named here so a later session does not read the absence as an oversight.

---

## 9. The engine — order, exclusion, tax, and the report

```python
# pricing/engine.py  (the public seam of the library)

def price_cart(cart: Cart, catalogs: PromotionCatalogs) -> Quote: ...
    # The one signature change in the stage: a market runs its own offers (Q21), so the caller hands
    # over the catalogues and the CART decides which one applies — the same guarantee that makes the
    # market a property of the cart rather than a parameter beside it (§16, rejected alternative 4).
```

```python
@dataclass(frozen=True)
class ResolvedCode:
    as_typed: str
    index: int                       # submission position — the report order, and the tie-break
    code: PromotionCode
    promotion: Promotion
    stackable: bool

def canonical_order(resolved: "Iterable[ResolvedCode]") -> list[ResolvedCode]: ...
    # THE ordering rule (I5): sort by (stage, kind rank, code). Never by submission order.

@dataclass(frozen=True)
class Choice:
    winner: ResolvedCode | None
    superseded: tuple[tuple[ResolvedCode, Proposal], ...]

def choose_non_stackable(
    contenders: "Sequence[tuple[ResolvedCode, Proposal]]",
) -> Choice: ...
    # THE exclusion rule: the largest discount wins; an exact tie goes to the lowest submission index.
```

### The pipeline, step by step, with the owner of each rule

| # | Step | Owner | Rule |
|---|---|---|---|
| 1 | **Resolve** | engine | **The market first, and it resolves to two things:** `tax_rule_for(cart.market)` and `catalogs.for_market(cart.market)`. Missing either one makes the cart not priceable and raises, because there is no truthful price to return — with no tax law there is no total, and with no catalogue we could not tell an unknown code from an unloaded one, which I3 forbids us to guess at. That is the opposite of a bad *code*, which I3 requires us to price around. Then each submitted code is normalised and looked up **in that market's catalogue**: found → `ResolvedCode`; defined but misconfigured → `no_effect`, "temporarily unavailable" (I7); not found → `unknown`; already resolved → counted once, the repeat reported. Nothing about a code raises (I3). |
| 2 | **Canonical order** | `canonical_order` | Line stage before cart stage; within the cart stage PCT before AMT; ties by code. The customer's typing order never reaches this (I5). |
| 3 | **Line stage** | `CartLedger` | Walk the **stackable** line-scoped codes in canonical order, proposing and committing each. Freed units are taken cheapest-unit-price first across the lines of that SKU. |
| 4 | **The contest** | `choose_non_stackable` | One contest per cart, at the boundary between the stages: every non-stackable code of either scope is proposed against this one basket, the largest wins and commits here, the rest are recorded superseded (`decisions/0013`, `0014`). Unchanged by this stage — contenders are compared on the amounts the market's prices are stated in, which is what a customer sees either way. |
| 5 | **Cart stage** | `CartLedger` | Walk the **stackable** cart-scoped codes in canonical order, each proposed against `remaining`, so two 10% codes take 19% and a fixed amount larger than the cart is clamped to it (I2). Committing splits the amount across the lines. |
| 6 | **Tax stage** | `CartLedger.assess_tax` + the market's rule | The market's rule assesses the amounts its law names — every line's final amount, or the cart's — exactly once each; the ledger records the entries and seals itself (§7). Last, always: a tax figure describes a final amount, and nothing may be taken off an amount after its tax has been stated (I12, I14). |
| 7 | **Read the answer** | `quote.py` | Every figure in the `Quote` is a fold over an explanation, named by the kind of entry it folds (§6): the figures this product already reported fold the promotion entries, and the two new ones fold the tax entry. Nothing is recomputed, so nothing can disagree. |
| 8 | **Report** | engine | One `CodeOutcome` per submitted code, in submission order: applied / superseded / no effect (with a reason) / unknown. A code's reported saving is stated in the market's own prices — in SOUTH, SAVE10 on a 12.00 shelf price saved 1.20, which is what the customer sees. |

**The contest and tax do not interact, by construction.** Every contender is compared on a proposal
made in step 4, long before any tax is assessed, so the comparison is between two discounts off the
same basket in the market's own prices. Nothing in `choose_non_stackable` mentions tax, and nothing
needs to.

---

## 10. The answer

```python
# pricing/quote.py

class CodeStatus(Enum):
    APPLIED    = "applied"
    SUPERSEDED = "superseded"
    NO_EFFECT  = "no_effect"
    UNKNOWN    = "unknown"

@dataclass(frozen=True)
class CodeOutcome:
    code: str                        # exactly as typed
    status: CodeStatus
    amount: Money | None             # APPLIED: what it actually took
    forgone: Money | None            # SUPERSEDED: what it would have saved
    superseded_by: PromotionCode | None
    detail: str

@dataclass(frozen=True)
class PricedLine:
    sku: Sku
    unit_price: Money
    quantity: int
    free_units: int
    explanation: Explanation         # THE line's price, as a story

    # every figure this product already reported, with its stage-2 name, meaning and number:
    @property
    def gross(self) -> Money: ...                  # explanation.list_price
    @property
    def net(self) -> Money: ...                    # explanation.final — what the customer pays for
                                                   # this line, the invoice figure (decisions/0010)
    @property
    def line_discount(self) -> Money: ...          # |Σ PROMOTION deltas of LINE scope|
    @property
    def cart_discount_share(self) -> Money: ...    # |Σ PROMOTION deltas of CART scope|
    # and one new one, beside them:
    @property
    def tax(self) -> Money: ...                    # explanation.tax — how much of `net` is tax.
                                                   # 0.00 in a market that taxes the cart as a whole

@dataclass(frozen=True)
class Quote:
    customer_id: str
    market: MarketId                 # echoed: it decides what every figure below means
    lines: tuple[PricedLine, ...]
    explanation: Explanation         # THE cart's price, as a story
    codes: tuple[CodeOutcome, ...]   # one per submitted code, in submission order

    # every figure this product already reported, with its stage-2 name, meaning and number:
    @property
    def subtotal(self) -> Money: ...               # explanation.list_price
    @property
    def total(self) -> Money: ...                  # explanation.after_promotions — the cart when
                                                   # every promotion has applied. C1: 22.50
    @property
    def line_discount_total(self) -> Money: ...
    @property
    def cart_discount_total(self) -> Money: ...
    # and the two new ones, beside them:
    @property
    def tax(self) -> Money: ...                    # explanation.tax. C1: 3.83
    @property
    def amount_due(self) -> Money: ...             # explanation.final — THE number the customer
                                                   # pays. C1: 26.33; C2: 10.80
```

**Nothing is renamed, and nothing an existing figure meant has changed** (Q20: *"the numbers you had
stay the numbers you had, and the tax and the amount they pay sit beside them — just make the number
the customer pays the obvious one"*). `subtotal`, `total`, `net`, `gross`, `line_discount`,
`cart_discount_share` and the two discount totals are the stage-2 figures, unchanged in name and in
value, and `total` is what it always was: **the cart when every promotion has applied**. Two figures
are added beside them: `tax`, and `amount_due` — the number the customer pays, which is the one a
caller should reach for first.

An earlier draft of this stage made `total` mean the payable and renamed the rest. The owner's answer
replaced that, and the replacement is better on its own terms: nothing that already had a number keeps
a name that now points at a different one, and the payable arrives as a field whose name can only mean
one thing. `decisions/0019` supersedes the naming clause of `decisions/0018`.

**How the two markets read.** In NORTH, `total` 22.50 + `tax` 3.83 = `amount_due` 26.33 — the tax sits
on top, and every line's `tax` is 0.00, which is the truth about a NORTH line: the market assesses VAT
on the cart, and we invent no per-line split (Q23). In SOUTH, `total` 10.80 = `amount_due` 10.80 and
`tax` 1.80 is *inside* it — so a reader who takes `amount_due` is right in both countries without
knowing which one they are in, and a reader who wants the tax reads `tax` at the level the law assesses
it. `Quote.market` is echoed so an invoice knows which template it is filling.

**A SOUTH invoice, per line, needs the line's amount and the line's tax** (Q24: *"what's on the card is
what we need"*) — `net` and `tax`, both reported, both folds. No per-line amount-excluding-tax figure
is reported, because nothing asks for one; it is a subtraction away the day something does.

**Every figure is still a fold, and now each fold names its kind.** A tax entry never enters a discount
figure, and a promotion delta never enters the tax figure (§6). `free_units` stays a stored count
because it is not money.

**Reconciliation, in both markets** (I6, I12):
- `Σ line.net == quote.total` — exactly as stage-2 stated it (I6), in both markets: a line's `net` is
  what the customer pays for that line, and the cart's `total` is what every promotion left.
- `quote.amount_due == quote.total + (tax assessed on the cart as a whole)` — that term is 0.00 in a
  per-line market, where the tax is already inside `total`.
- `quote.tax == Σ line.tax` in a per-line market (definitional: the cart's entry is built by summing
  the line entries), and is the single cart assessment in a cart-level market, where every line's
  `tax` is 0.00.

**Where this would need a third name, and why it does not yet.** If a market ever assessed tax *per
line and on top* (a sales tax added to each line), a line's `net` and the amount due for that line
would diverge, and the line would want the same pair the cart now has. The type is ready for it — the
assessment carries a delta — and the field is not there, because no market we sell in needs it.

---

## 11. The catalogue — one file per market

```toml
# promotions.SOUTH.toml — edited by SOUTH's business. Amounts and percentages are QUOTED strings.
# Each market keeps its own file: "one file per market. They run different offers." (Q21)

[SAVE10]
kind    = "PCT"
percent = "10"

[TENOFF]
kind      = "AMT"
amount    = "10.00"        # ten off the price on the shelf — in SOUTH that price contains the VAT
stackable = false

[COFFEE3]
kind  = "BOGO"
sku   = "COFFEE"
every = 3
```

**Everything about one file is unchanged:** `CatalogEntry`, `CatalogProblem`, `PromotionCatalog`, the
`kind → parser` table, `stackable` defaulting to true, a broken entry disabling one code while the rest
of the file loads (I7, `decisions/0009`), amounts written as quoted strings, and only an unreadable or
non-TOML file being fatal. No kind, no field and no containment rule moves. What is new is that there
is one such file per market, and that **the cart decides which one its codes are looked up in**:

```python
# pricing/catalog.py   (additions only; load_catalog keeps its signature and its behaviour)

class PromotionCatalogs:
    # The offers of every market we sell in — one PromotionCatalog each.
    def for_market(self, market: MarketId) -> PromotionCatalog: ...
        # raises CatalogError naming the market when we hold no catalogue for it
    @property
    def problems(self) -> tuple[tuple[MarketId, CatalogProblem], ...]: ...
        # every market's problems, tagged with the market, so the business is told which FILE to fix
    def markets(self) -> tuple[MarketId, ...]: ...

def load_catalogs(
    sources: "Mapping[MarketId, str | os.PathLike | IO[bytes]]",
) -> PromotionCatalogs: ...
    # one load_catalog per entry. Per-file containment is unchanged, so a broken entry in NORTH's
    # file disables one NORTH code and nothing else, and an unreadable NORTH file cannot stop a
    # SOUTH cart pricing.
```

**A market with no catalogue is not priceable**, and the failure is the same kind as an unreadable
file: `CatalogError`, CLI exit 2, naming the market. The alternative — price the cart and report every
code as `unknown` — would tell the customer and support something untrue: I3 requires the outcome to be
what actually happened, and `decisions/0009` already chose "temporarily unavailable" over "unknown" for
exactly this distinction. We cannot tell a code that does not exist from one we failed to load, so we
do not guess at it.

**Where file naming lives.** `catalog.py` takes a mapping of market → source and invents no filename
convention; the CLI is where `promotions.NORTH.toml` becomes a path (§12). That keeps the one module
that knows the format from also owning where files sit, and lets a catalogue store that is not a file
at all replace the loader later without touching the mapping.

**Why not one file with a market column.** It puts a structural rule in the file non-engineers edit
daily — the same reason `decisions/0004` and `0005` refused ordering priorities there — and one
market's typo could then change another market's prices. Separate files also match how the business is
organised: two teams, two sets of offers (Q21).

---

## 12. The CLI (a serialization boundary, nothing more)

```
$ python -m pricing quote --catalog NORTH=promotions.NORTH.toml \
                          --catalog SOUTH=promotions.SOUTH.toml < cart.json > quote.json
$ python -m pricing validate-catalog --catalog SOUTH=promotions.SOUTH.toml
```

`--catalog MARKET=PATH` is repeatable, and the cart picks which one applies — the CLI never has to be
told the market twice, and cannot be told it twice inconsistently. Only the cart's own market needs a
file; a cart naming a market no `--catalog` supplied exits 2, naming it.

```jsonc
// cart.json (in) — `market` is new and required
{ "customer_id": "c-123",
  "market": "NORTH",
  "lines": [ { "sku": "WIDGET", "unit_price": "12.50", "quantity": 2 } ],
  "codes": ["SAVE10"] }

// quote.json (out)  [case C1] — every earlier field keeps its name, meaning and number;
//                               `tax` and `amount_due` are the two new ones
{ "customer_id": "c-123",
  "market": "NORTH",
  "lines": [
    { "sku": "WIDGET", "unit_price": "12.50", "quantity": 2, "free_units": 0,
      "gross": "25.00", "line_discount": "0.00", "cart_discount_share": "2.50",
      "net": "22.50", "tax": "0.00",
      "explanation": [
        { "kind": "list_price", "delta": "+25.00", "amount": "25.00", "detail": "list price" },
        { "kind": "promotion",  "code": "SAVE10", "scope": "cart", "delta": "-2.50",
          "amount": "22.50", "detail": "10% off the cart" } ] } ],
  "subtotal": "25.00", "line_discount_total": "0.00", "cart_discount_total": "2.50",
  "total": "22.50", "tax": "3.83", "amount_due": "26.33",
  "explanation": [
    { "kind": "list_price", "delta": "+25.00", "amount": "25.00", "detail": "list price" },
    { "kind": "promotion",  "code": "SAVE10", "scope": "cart", "delta": "-2.50",
      "amount": "22.50", "detail": "10% off the cart" },
    { "kind": "tax", "scope": "cart", "delta": "+3.83", "tax": "3.83",
      "amount": "26.33", "detail": "VAT 17% on the discounted cart" } ],
  "codes": [ { "code": "SAVE10", "status": "applied", "amount": "2.50",
               "detail": "10% off the cart" } ] }
```

```jsonc
// quote.json (out) — SOUTH  [case C2]; the tax entry moves nothing and says what is inside,
//                    so `total` and `amount_due` are the same number
{ "customer_id": "c-9", "market": "SOUTH",
  "lines": [
    { "sku": "WIDGET", "unit_price": "12.00", "quantity": 1, "free_units": 0,
      "gross": "12.00", "line_discount": "0.00", "cart_discount_share": "1.20",
      "net": "10.80", "tax": "1.80",
      "explanation": [
        { "kind": "list_price", "delta": "+12.00", "amount": "12.00", "detail": "list price" },
        { "kind": "promotion",  "code": "SAVE10", "scope": "cart", "delta": "-1.20",
          "amount": "10.80", "detail": "10% off the cart" },
        { "kind": "tax", "scope": "line", "delta": "0.00", "tax": "1.80",
          "amount": "10.80", "detail": "VAT 20% included in the price" } ] } ],
  "subtotal": "12.00", "line_discount_total": "0.00", "cart_discount_total": "1.20",
  "total": "10.80", "tax": "1.80", "amount_due": "10.80",
  "explanation": [ "…", { "kind": "tax", "scope": "line", "delta": "0.00", "tax": "1.80",
                          "amount": "10.80", "detail": "VAT 20% included in the price" } ],
  "codes": [ { "code": "SAVE10", "status": "applied", "amount": "1.20",
               "detail": "10% off the cart" } ] }
```

`amount` on an explanation entry is the **running amount after that entry** (`steps()` serialized),
derived at serialization time and never stored. A SOUTH invoice reads each line's `net` and `tax`, and
the customer's figure is `amount_due` in either country.

Exit codes: `0` priced — including unknown codes, superseded codes, and a catalogue with broken
entries, whose problems go to stderr **tagged with the market whose file they are in**; `2` the
catalogue for the cart's market is unreadable, not valid TOML, or was not supplied; `3` the cart input
is malformed, **which now includes a missing or unknown `market`** — there is no price to return
without a tax law. `validate-catalog` is unchanged per file: strict, non-zero on any problem at all,
and it validates each `--catalog` it was given.

---

## 13. The required cases, traced through the design

### The new cases

| # | Trace | Result |
|---|---|---|
| **C1** | NORTH, WIDGET 12.50×2, SAVE10. Line explanation opened at 25.00, cart at 25.00. No line stage, no contest. Cart stage: 10% of remaining 25.00 → 2.50, allocated over weights (25.00) → 2.50 on L1; L1 remaining 22.50. Tax stage: the market's rule is a `CartTaxRule`, so the cart assesses **its own** amount once: `2250.portion(17, 100, HALF_UP)` = 382.5 → **383**; the entry's delta is **+3.83**; no line is touched; the ledger seals. | line `net` **22.50**, line `tax` **0.00**; cart story **25.00 → SAVE10 −2.50 → 22.50 → VAT 17% +3.83 → 26.33**; `total` **22.50** (the figure this product already reported, unchanged), `tax` **3.83**, `amount_due` **26.33** ✔. Deltas after the opening entry sum to +1.33 = 26.33 − 25.00 ✔ |
| **C2** | SOUTH, WIDGET 12.00×1, SAVE10. The promotion sees 12.00 and takes 10% of it — 1.20 — exactly as it does in NORTH, because it has never known what an amount means (§5). L1 remaining 10.80. Tax stage: the rule is a `LineTaxRule`, so L1 assesses **its own** final amount: `1080.portion(20, 120, HALF_EVEN)` — 20/(100+20) — = 180 exactly → **1.80**, delta **zero**; the cart records the aggregate (1.80, delta zero). | line `net` **10.80**, line `tax` **1.80**; cart `total` **10.80**, `tax` **1.80**, `amount_due` **10.80** — the tax is inside, so the payable is the same number ✔ |
| **C3** | SOUTH, SACHET 0.15×1 + CLIP 0.45×1, no codes. No promotion stage does anything. Tax stage, per line: 15×20/120 = **2.5 → half-even → 2** (0.02); 45×20/120 = **7.5 → half-even → 8** (0.08). Cart entry = their sum. | line taxes **0.02** and **0.08**; cart `tax` **0.10** ✔; cart `total` and `amount_due` both 0.60 |
| **C4** | SOUTH, three lines of 0.15. Each line assesses itself: 2.5 → **2** three times. The cart's entry is the **sum of the three line entries**, 0.06. The cart's own amount (0.45) is never assessed — `CartLedger.assess_tax` has no path that computes tax from a cart amount when the rule is a `LineTaxRule`, so the 0.075 → 0.08 answer is not reachable, not merely not chosen. | each line **0.02**, cart **0.06**, **not 0.08** ✔ (I12) |
| **C5** | SOUTH, COFFEE 4.00×4, COFFEE3. Line stage: `free_units(4) = 1`; the freed unit is priced at its own listed 4.00 — a gross 4.00, because that is what the shelf says — so the line delta is −4.00 and L1 remaining is 12.00. Tax stage: 1200×20/120 = **200** → 2.00. | line `net` **12.00**, line `tax` **2.00** ✔; cart story **16.00 → COFFEE3 −4.00 → 12.00, of which VAT 20% 2.00**; `amount_due` 12.00 |
| **C6** | NORTH, every earlier acceptance case, out of NORTH's own catalogue file. Steps 1–5 are the stage-2 pipeline over an untouched `promotions.py` and an unchanged per-file catalogue, so every promotion figure is identical to the cent; step 6 adds the one VAT entry the market has always owed. See the table below. | every reported figure **unchanged in name, meaning and value** — `subtotal`, `total`, the discounts, every line's `gross` and `net`; `tax` and `amount_due` are new fields beside them ✔ |

### C6 in full — the earlier cases, with what changed and what did not

| # | Cart | Stage-2 figures — same names, same numbers (`total`, and the line `net`s) | VAT 17% half-up = `tax` | `amount_due` |
|---|---|---|---|---|
| **A1** | WIDGET 12.50×2, no codes | line 25.00, 25.00 | 4.25 | 29.25 |
| **A2 / B1** | + SAVE10 | line 22.50, 22.50 | 3.825 → 3.83 | **26.33** (= C1) |
| **A3** | TENOFF (stackable) on 25.00 | line 15.00, 15.00 | 2.55 | 17.55 |
| **A4** | COFFEE 4.00×4, COFFEE3 | line 12.00, 12.00 | 2.04 | 14.04 |
| **A5 / B2** | COFFEE3 + SAVE10 | lines 10.80 / 11.25, 22.05 | 3.7485 → 3.75 | 25.80 |
| **A6** | WIDGET 12.50×1, "NOPE" | line 12.50, 12.50; NOPE **unknown**, no entry | 2.125 → 2.13 | 14.63 |
| **A7** | 1.00 cart, TENOFF | line 0.00, 0.00 — clamped, never negative | 0.00 | 0.00 |
| **B3** | 50.00, SAVE10 + TENOFF both non-stackable | 40.00, TENOFF applied, SAVE10 superseded (forgone 5.00) | 6.80 | 46.80 |
| **B4** | 150.00, same two | 135.00, SAVE10 wins | 22.95 | 157.95 |
| **B5** | 100.00, same two, exact tie | 90.00, SAVE10 (entered first) | 15.30 | 105.30 |
| **B3′** | COFFEE3 + SAVE10, both non-stackable | 24.50, the BOGO wins across scopes | 4.165 → 4.17 | 28.67 |

Every discount, every allocation, every contest outcome and every code outcome in that table is
produced by code this stage does not touch, and every figure stage-2 reported is still reported under
its own name with its own value. The only new numbers in each row are the last two.

### Two traces the acceptance cases do not cover, worked because they are where this design could go wrong

- **A cart-level discount in SOUTH, with a leftover cent.** SOUTH, three lines at 3.33, 3.33, 3.34
  (list 10.00), SAVE10. The cart stage takes 10% of 10.00 = 1.00 and allocates it over the three
  remainings: 0.33, 0.33, 0.34 (largest-remainder, exact). Line amounts 3.00, 3.00, 3.00. The tax
  stage then assesses **each final amount**: 300×20/120 = 50 → 0.50 each; cart `tax` 1.50; `total`
  and `amount_due` both 9.00.
  The allocation rounds once and the tax rounds once per line, and neither rounding is ever re-done —
  which is why no residue can appear between them.
- **NORTH's discount folds with a positive tax delta.** C1's cart explanation contains −2.50 and
  +3.83. `cart_discount_total` folds `kind == PROMOTION` only and reports **2.50**; `tax` folds
  `kind == TAX` and reports **3.83**; `net_delta` folds everything and reports **+1.33**, which is
  exactly 26.33 − 25.00 (I8). A fold that filtered only on scope would have reported the cart's
  discount as 1.33 — the single concrete bug this stage's change to `deltas_for` prevents.

---

## 14. Invariants, and the single place each is enforced

| | Invariant | Enforced at |
|---|---|---|
| **I1** | No line amount and no cart total is ever negative | `Money` is non-negative by construction; `propose_*` clamps before anything is recorded; `Money.after` raises as a tripwire. Tax only ever adds or moves nothing |
| **I2** | A discount never takes more than remains at the point it is applied | the clamp inside `CartLedger.propose_cart` / `propose_line`, always against `remaining` = Σ line remaining, which no tax entry has ever touched (I14) |
| **I3** | Every submitted code gets a truthful outcome of its own | one `CodeOutcome` per submitted code, in submission order; four statuses. Unchanged |
| **I4** | Money is one currency, 2dp, never finer than a cent | `Money` holds integer minor units; `Money.portion` is the only rounding point and rounds once per figure; formatting lives on `Money`/`MoneyDelta` |
| **I5** | The same cart and codes price to the same **amounts** whatever order the codes were typed — and in an exact tie the first-entered code is the one named applied | `canonical_order`; `choose_non_stackable`'s tie-break. Unchanged; tax is order-free by construction (one assessment, last) |
| **I6** | The per-line costs sum exactly to the cart `total`; a line's cost is what the customer pays for that line — **exactly as stage-2 stated it**, in both markets | definitional: `CartLedger.remaining` **is** Σ line remaining, and `total` is the cart's amount when every promotion has applied (`Explanation.after_promotions`). The only entry that is neither allocated to the lines nor an aggregate of line entries is a `CartTaxRule`'s single assessment, and it lands past `total`, on `amount_due` — which is why keeping stage-2's names (Q20) keeps stage-2's invariant word for word |
| **I7** | A catalogue mistake is contained to the code it was written on — and now also to the market whose file it is | `load_catalog`, unchanged, per file; `load_catalogs` loads each market's file independently, so a broken NORTH entry disables one NORTH code and an unreadable NORTH file cannot stop a SOUTH cart pricing. A market with **no** catalogue is not priceable (§11) |
| **I8** | Every explanation's deltas sum exactly to the difference between its list price and its final amount — no residue, no rounding entry | definitional: `Explanation.final` is computed from the entries, tax delta included |
| **I9** | An explanation describes what actually happened, in the order it happened | the one operation that moves a balance is the one that appends the entry — `LineLedger.free/reduce/assess_tax`, `CartLedger.assess_tax` |
| **I10** | Each cart-level **promotion**'s per-line shares sum exactly to its cart-level delta | `Money.allocate`, called once per cart-level promotion at the moment it is committed |
| **I11** | At most one non-stackable code applies per cart, whatever kinds contend, and each of the others is reported naming the winner and its forgone amount | `choose_non_stackable`, called once per cart; `CartLedger.record_superseded`. Unchanged |
| **I12** | *(new)* Tax is assessed **exactly once per amount**, at the level the market's law names, and a tax figure reported above that level is the **sum** of the assessments below it — never a fresh assessment of the aggregate. The customer pays `total` plus whatever tax was assessed on the cart as a whole (zero where the law assesses per line) | `CartLedger.assess_tax`: a `LineTaxRule` is asked once per line by that line's own ledger and the cart's entry is built by summing those entries; a `CartTaxRule` is asked once by the cart and no line is touched. There is no code path that computes tax from a cart amount under a per-line rule (C3, C4) |
| **I13** | *(new)* Every amount's explanation accounts for its tax: the tax figure is an entry in the same record the amount is computed from, and no tax figure is produced anywhere else | the `TAX` adjustment; `Explanation.tax` and every quote tax figure are folds over it (`decisions/0016`) |
| **I14** | *(new)* The tax assessment is the last thing that happens to an amount: no promotion is proposed or committed after it | the tax stage is step 6, and `CartLedger.assess_tax` **seals** the ledger — every later `propose_*`, `record_superseded` or second `assess_tax` raises |

`goals.md` carries I1–I14 as product rules; this table is where each one is enforced.

---

## 15. The subtractive pass

Every type, guard and abstraction added in this stage was put to one question: *if I deleted it, would
the ownership of a rule the product needs today actually be damaged?* The pass also re-ran over
stage-2's machinery, because a new requirement is the moment old structure stops paying for itself.

**Cut, and why:**
- **A `Market` value type** (an id paired with the law and the offers it resolves to). A market now
  resolves to *two* things — its tax rule and its catalogue — which is exactly when such a type starts
  to look necessary, and it still is not: each resolution has an owner (`market.py` and `catalog.py`),
  each raises its own truthful failure naming the market, and a type that merely held one of each
  would add a third place for them to disagree. Re-introduce it the day something is true of a market
  that is true of neither — its own currency, say (a stated non-goal).
- **A `TaxScope` / `treatment` flag on one `TaxRule`.** Two markets, two laws, two classes; a
  (level × inclusive/exclusive × rounding) matrix has eight cells, six of which no country we sell in
  occupies, and the engine would have to read the flags to know what to do — the rule leaking back out
  of its owner.
- **A `rounding` parameter on each tax rule.** The mode is not a knob on a law, it *is* the law: "per
  line, half-even" is one legal rule. A different combination is a different small class.
- **Allocating NORTH's cart VAT across the lines** so that every line could carry a tax share. It
  would give `Σ line.tax == cart.tax` in both markets and a tidier invariant table — and it would
  invent a per-line tax figure the market does not assess, does not round per line, and does not put
  on an invoice. Tidiness is not a product force; a fabricated number on an invoice is a liability.
- **A separate `TaxSummary` / tax record beside the explanation.** It is the second producer of a
  money fact that `decisions/0011` exists to prevent (§16, rejected alternative 1).
- **A `Rounding` parameter on `Money.percentage`.** The promotion rounding rule did not change; the
  call sites that would have to pass `HALF_UP` are in `promotions.py`, which this stage keeps untouched.
- **A `TaxRate` type wrapping `Percent`.** `Percent` already is "a percentage, exact to the written
  digits"; a subtype that adds no rule is a rename.
- **A `market` field on `CodeOutcome` or on each `Adjustment`.** The market is a property of the whole
  quote, stated once.
- **An `UnknownMarketError`.** Its only handling is the CLI's exit 3 with a message — the same
  handling as a malformed cart. One error type per handling response (`design-principles.md` §7): a
  market with no tax law is reported as `InvalidCartError` naming it, and a market with no catalogue as
  `CatalogError` naming it, because *that* one is handled differently (exit 2: the offers could not be
  read, which is the catalogue's existing failure, not the cart's).
- **Per-line `amount_excluding_tax` and a cart `total_excluding_tax`.** The owner's answer to Q24 is
  that an invoice needs the line's amount and the line's tax; a figure nobody named is a subtraction
  away from two that are reported.
- **A market column in one shared catalogue file**, and a `market` field on `CatalogEntry`. One file
  per market (Q21) makes the containment structural instead of a filter the resolve step has to
  remember to apply, and keeps a structural rule out of the file non-engineers edit daily.
- **Effective-dated tax rates** (a rate with a start date, so a change can be staged). The owner:
  *"not now — build for today"*. When a rate changes it is an edit to `market.py` and a deploy, which
  is what "keep that with the engineers" means.

**Kept, with the force that keeps them:**
- **`TaxAssessment`** — an assessment has to say two things (how much tax, and whether paying it moves
  the amount), and they must arrive together or a caller can record one against the wrong amount. It is
  also what lets one entry kind serve both laws.
- **`LineTaxRule` / `CartTaxRule` as two protocols** — a line rule and a cart rule act on different
  things; the engine's dispatch is typed rather than flag-driven; each market implements exactly one.
  A second genuinely different implementation of each is named in §8 (per-line sales tax; a reduced
  rate by SKU).
- **`Money.portion`** — extracting tax from a tax-inclusive amount is not a percentage of it, and the
  rounding mode now varies. One exact rational multiply with the mode named, in the one module that
  rounds.
- **The `TAX` adjustment kind and its `tax` field** — a fourth row in the story because it is a fourth
  kind of thing (a starting point, a saving, a code that was beaten, the tax); and the field because
  in an inclusive market the delta is zero and the tax figure would otherwise have nowhere to live,
  exactly as `forgone` lives on a zero-delta `NOT_APPLIED`.
- **The seal on `CartLedger`** — one flag and one raise, protecting a rule worth real money (§7, I14).
- **`PromotionCatalogs`** — it owns one rule: *a market we hold no offers for is not priceable, and we
  say which market*. A bare `Mapping[MarketId, PromotionCatalog]` at the public seam would leave that
  rule to whichever caller remembered a `KeyError`, and would have nowhere to tag a problem with the
  file it came from.
- **`Explanation.after_promotions`** — `total` is a real moment in the story (every promotion applied,
  no tax assessed), and it is the figure this product has always reported. Deriving it as
  `final − tax` instead would be arithmetic over two folds where a fold already exists, and would stop
  being correct the moment a market assessed tax per line *and* on top.

**Carried forward, still unpaid:** `LinePromotion` still has one implementation, and stage-2's
line-scoped contest is still unexercised. Stage-3 adds nothing to that argument either way.
Re-measure at the first implementation review.

**Watched, not yet a problem:** `Adjustment` is now one type with four kinds and two kind-specific
money fields (`forgone`, `tax`), policed by a shape rule per kind. That is still one type a reader can
hold in their head, and every consumer branches on `kind` anyway. If a fifth kind or a third
kind-specific field arrives, the honest move is to segregate it into a small frozen class per kind
behind a shared protocol (`design-principles.md` §2) — noted here so the next session does not mistake
the growth for something that was never noticed.

---

## 16. Alternatives rejected (structural)

1. **Compute tax beside the amounts and report it as its own figure.** Rejected: it makes two
   producers of one money fact, which is precisely what `decisions/0011` exists to prevent, and the
   product owner's requirement that "an explanation that cannot account for the tax is not an
   explanation" says the same thing from the customer's side. A tax figure the explanation does not
   contain is a number support cannot show working for.
2. **A `taxable_amount` concept threaded through the ledgers, with every line tracking a net and a
   gross balance in parallel.** Rejected: two balances per line is two producers again, and it forces
   every promotion, clamp and allocation to state which balance it means. The design keeps **one**
   balance per line — the amount in the market's own prices — and derives the excluding-tax figure at
   the end by subtracting the recorded tax.
3. **Branch on the market inside the engine** (`if market is SOUTH: … else: …`). Rejected: it makes
   "how many countries do we sell in" a reason for the pipeline module to change, scatters the rate and
   the rounding mode across the sequencing code, and puts the one thing each new country brings — its
   law — in the module least able to own it.
4. **Make the market a parameter of `price_cart` rather than a property of the cart.** Rejected: a
   caller could then price a NORTH cart under SOUTH's law, and the request would not say what it asked
   for. The cart names its market; the engine binds it to the law, exactly as it binds a code to a
   promotion.
5. **Put the VAT rates in a business-edited file.** Rejected for the reason `0004` and `0005` rejected
   structural rules in such a file: a mistyped tax rate misreports money to a tax authority rather than
   merely mispricing a cart. Confirmed by the owner (Q19): *"keep that with the engineers — I don't
   want anyone editing a tax rate by hand."*
6. **One `TaxRule` with `assess(amount)` plus a scope flag.** Rejected: the engine would read the flag
   to decide which amounts to pass, so the rule about where a market assesses tax would live outside
   the rule. Two protocols with different method names keep it inside and make the dispatch typed.
7. **A new `TAX_INCLUDED` kind distinct from `TAX_ADDED`.** Rejected: a reader and an invoice treat
   both as the same row — "VAT 20%: 1.80" — and the difference between them is already carried, exactly
   and machine-readably, by the entry's delta. Two kinds would make every consumer handle two cases to
   ask one question.
8. **Rename the reported figures so that `total` means the payable** (this stage's own first draft).
   Rejected by the product owner, and rightly: *"the numbers you had stay the numbers you had, and the
   tax and the amount they pay sit beside them — just make the number the customer pays the obvious
   one."* Every existing figure keeps its name, meaning and value, and `amount_due` is the new field
   whose name can only mean one thing. It also turned out to keep I6 word for word (§14).
9. **Round SOUTH's cart tax at cart level and allocate it back to the lines.** Rejected by C4 outright
   — it gives 0.08 where the invoice says 0.06 — and structurally: the invoice figure is the line
   figure, so the line is where the rounding has to happen and the cart figure has to be a sum.
10. **Assess tax during the cart stage (or make it a promotion of its own kind).** Rejected: tax is not
    a promotion — it is not a code, it is not in the catalogue, it cannot be superseded, it does not
    compete, and it must not be clamped to what remains. Modelling it as one would put a legal
    obligation inside the machinery whose whole job is discretionary discounts.
11. **One catalogue file with a market column, or a `market` field on each entry.** Rejected: the owner
    runs different offers per market and asked for one file each, and a market column is a structural
    rule in the file non-engineers edit daily — the same objection `0004` and `0005` made to ordering
    priorities, with the added risk that one market's typo re-prices another's.
12. **Let the caller pass the one catalogue it thinks applies** (`price_cart(cart, catalog)`
    unchanged). Rejected for the reason alternative 4 was: a SOUTH cart could be priced against NORTH's
    offers and nothing in the system would notice. The cart names its market, and the market selects
    both its law and its offers, in one step.
13. **Price a cart whose market has no catalogue, reporting every code as `unknown`.** Rejected: it
    tells support the opposite of the truth (`decisions/0009` drew exactly this line between "unknown"
    and "temporarily unavailable"), and we cannot tell a code that does not exist from one we failed to
    load.

---

## 17. Product decisions — answered by the product owner

Nothing below is assumed. One answer changed the design, one replaced a choice this stage had made,
and the rest confirmed the draft. `decisions/0019` files them.

| Q | Question | The owner's answer | Where it lives | Effect on the draft |
|---|---|---|---|---|
| **Q19** | Where do VAT rates live, and who changes one? | *"Keep that with the engineers. I don't want anyone editing a tax rate by hand. And a rate changing: not now — build for today."* | the table in `market.py` | **Confirmed**, and it closes a door as well: no effective-dated rates, no rate history, no staging mechanism. A rate change is an edit and a deploy |
| **Q20** | The reported figure names, now that a cart has a tax and a payable | *"Nothing is live yet, nobody is reading those names. The numbers you had stay the numbers you had, and the tax and the amount they pay sit beside them. Just make the number the customer pays the obvious one."* | `quote.py` + `cli.py` | **Changed, and better.** The draft's rename is dropped: `subtotal`, `total`, `gross`, `net` and the discount figures keep their names, meanings and values, and `tax` and `amount_due` are added beside them. I6 survives word for word as a result (§10, §14) |
| **Q21** | Is the catalogue shared across markets, and what does a fixed amount mean in SOUTH? | *"One file per market. They run different offers. And ten off is ten off the price on the shelf, in both places. That's what the customer sees."* | `catalog.py` (`PromotionCatalogs`, `load_catalogs`) + the engine's resolve step | **Changed.** One catalogue per market, selected by the cart; `price_cart` takes the catalogues rather than one catalogue (§11). The AMT kind is untouched — a fixed amount was always "off the price on the shelf" |
| **Q22** | Must a cart state its market? | *"A cart is for one market, and it tells you which. Nothing is live yet, so there are no callers sending nothing."* | `cart.py` + the resolve step | **Confirmed.** Required, no default, no compatibility path for a missing market |
| **Q23** | Does NORTH need VAT per line? | *"No. Only SOUTH invoices have to show it."* | `market.py` | **Confirmed.** A NORTH line's `tax` is 0.00 and no per-line split is invented |
| **Q24** | What must SOUTH's invoice show per line? | *"What's on the card is what we need."* | `quote.py` / `cli.py` | **Confirmed, and it removed a field:** the card asks for the line's amount and the line's tax — `net` and `tax`. The per-line amount-excluding-tax figure is cut (§15) |

**What the two changed answers moved, in one line each.** Q21 made a market resolve to *two* things
instead of one — its law and its offers — which is the stage's only public-signature change and which
put the containment of a catalogue mistake on a per-market boundary as well as a per-code one (I7).
Q20 removed a rename this stage had proposed, and with it the one place where a caller's existing
field would have changed meaning.

**Nothing remains open.** No rule in this design now rests on a guess.

---

## 18. What the first sprint builds, and what it must prove

Build order follows dependency order, test-first, one decision at a time. Items marked **new** did not
exist in stage-2; modules not listed are not touched by this stage.

1. `money.py` — everything stage-2 required, plus **new:** `portion` exact and rounding **once** under
   both modes (half-up: 382.5 → 383, 374.85 → 375; half-even: 2.5 → 2, 7.5 → 8, 3.5 → 4, 250 → 250);
   `portion` with a denominator that does not divide; `Percent.as_fraction` exact for whole and
   fractional rates ("17" → (17,100), "7.5" → (75,1000)); `percentage` unchanged in behaviour and
   defined through `portion`; `MoneyDelta.addition` and `is_addition`.
2. **new:** `market.py` — each rule's arithmetic in isolation: `VatAddedToCart` on 22.50 → 3.83 with a
   +3.83 delta; on 0.00 → 0.00 with a zero delta; `VatIncludedInLine` on 10.80 → 1.80, on 0.15 → 0.02,
   on 0.45 → 0.08, on 0.00 → 0.00, each with a **zero** delta; `tax_rule_for` on both markets and on an
   unknown one; the normalisation of a market id ("south" is SOUTH).
3. `explanation.py` — stage-2's suite, plus **new:** a `TAX` entry with a +tax delta moves `final` by
   exactly the tax; one with a zero delta does not move `final` at all; the shape rule refuses a `TAX`
   entry with no `tax`, with a reducing delta, or with a delta that is neither zero nor exactly +tax;
   `tax` folds only `TAX` entries; the discount folds ignore a `TAX` entry (the C1 fold, §13); after any
   sequence including a tax entry, `net_delta == between(list_price, final)` exactly, property-style.
4. `cart.py` — stage-2's validation unchanged, plus **new:** a market id is required and normalised
   ("south" is SOUTH); `CartLine.gross()` keeps its name and its behaviour.
5. `promotions.py` — **unchanged**; its stage-2 suite must pass untouched. That it does is the evidence
   that the promotion seam absorbed a second country without moving.
6. `catalog.py` — every stage-2 test must pass unchanged against a single file, plus **new:**
   `load_catalogs` loads one file per market; a broken entry in one market's file disables that one
   code and leaves the other market untouched; an unreadable file for one market does not stop a cart
   in another pricing; `for_market` on a market we hold no catalogue for raises, naming it; `problems`
   tags each problem with its market.
7. `engine.py` — C1–C6 exactly, A1–A7 and B1–B5 with their stage-2 figures plus the VAT row of §13,
   codes resolved in the cart's own market's catalogue, and the break cases below.
8. `quote.py` / `cli.py` — every stage-2 field with its stage-2 name and number, plus `tax` and
   `amount_due`; `market` echoed; the `tax` entry serialized with its delta, its tax and its running
   amount; repeatable `--catalog MARKET=PATH`; a missing or unknown market exits 3 naming it, a
   missing catalogue for the cart's market exits 2 naming it; every other exit code unchanged.

**Break cases the engine must answer** — the exit criteria of the implementation objective. Stage-1's
and stage-2's lists stand in full (they are all NORTH cases now, and every one of them must still
produce its stage-2 figures), and this stage adds:

- **C3 and C4 as the rounding-locus test:** three 0.15 lines give 0.06, and there must be no code path
  that can produce 0.08 — the cart's entry under a per-line rule is built only by summing line entries;
- **half-even in both directions:** a line at 0.15 (2.5 → 0.02, down to even) and one at 0.21
  (3.5 → 0.04, up to even) in the same cart, so a "round half down" implementation fails;
- **half-up where half-even would differ:** NORTH on 22.50 → 3.83 (C1), and a cart whose VAT lands
  exactly on a half-cent boundary the other way;
- **the same cart, with the same codes, priced in both markets** (each from its own catalogue) —
  identical promotion deltas and identical code outcomes, different `amount_due`, and in NORTH every
  line `tax` 0.00 while in SOUTH every line `tax` is positive;
- **a code that exists in one market's file and not the other** — applied in the first, reported
  `unknown` in the second, with no cross-talk between the files;
- **a cart naming a market we have no catalogue for** — not priced, exit 2, naming the market, and
  *not* priced with every code reported `unknown`;
- **a cart-level discount in SOUTH with a leftover cent** (§13) — the shares sum exactly, each line's
  tax is assessed on its own final amount, the cart tax is their sum, and no rounding entry exists;
- **tax on 0.00** — an empty cart in each market, and a cart clamped to 0.00 by an AMT code (A7 in
  SOUTH too): the assessment is recorded, the tax is 0.00, and the story still ends with it;
- **the seal (I14)** — a ledger refuses a proposal, a commit, a supersession record and a second
  assessment after `assess_tax`; and the pipeline never attempts one;
- **the clamp is never computed against tax (I2)** — in NORTH, an AMT code larger than the cart is
  clamped to the pre-VAT remaining, not to the VAT-inclusive total;
- **reconciliation, every case:** `Σ line.net == total` (I6, unchanged from stage-2, in both markets);
  `amount_due == total + cart-level tax`; and in SOUTH `Σ line.tax == quote.tax` exactly;
- **the names and numbers this product already had** — for every stage-2 case, `subtotal`, `total`,
  `line_discount_total`, `cart_discount_total` and each line's `gross`, `net`, `line_discount`,
  `cart_discount_share` are identical to their stage-2 values, and the only new fields are `tax` and
  `amount_due` (Q20);
- **the discount folds exclude tax** — NORTH C1 reports `cart_discount_total` 2.50, not 1.33;
- **agreement** — every reported figure equals the corresponding fold over an explanation, tax
  included; no figure is produced any other way;
- **a non-stackable contest in SOUTH** — contenders are compared on the tax-inclusive amounts they
  actually take off the basket, the winner commits before any assessment, and the loser's `forgone` is
  the number it was compared on;
- **a BOGO in SOUTH** (C5) — the freed unit is worth its listed, tax-inclusive price, and the line's
  tax is assessed on what is left;
- **an unknown market, a missing market, and a market differing only in case** — the first two are not
  priced (exit 3, naming the market), the third prices normally;
- **catalogue continuity** — the stage-2 catalogue file, unedited, loaded as NORTH's, prices every
  stage-2 case to its stage-2 figures under its stage-2 field names; and the same file's codes, copied
  into a SOUTH file, price a SOUTH cart with no change to the file's contents.
