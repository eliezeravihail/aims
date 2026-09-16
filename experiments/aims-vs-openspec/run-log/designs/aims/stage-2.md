# Cart pricing — architecture (stage 2)

**Status:** the complete architecture of the product as it now stands — cart pricing *with its
explanation*, and promotions that can exclude one another. It supersedes `design/stage-1.md` as the
shape the first sprint builds against; stage-1 is kept unedited as the record of the earlier round.
No implementation code exists yet.

**Substrate (given, not chosen):** Python 3.11+, standard library only, single process, single
currency, no UI/network/database/persistence. `decimal.Decimal` permitted but confined.
`decisions/0001`.

**What changed and why, in one line:** the product owner asked for every price to arrive with the
ordered list of adjustments that produced it, and for some codes to exclude one another. The first
of those cannot be bolted on — an explanation computed *beside* the amounts is a second producer of
the same fact, and two producers drift. So the pricing record itself becomes the primary artifact:
an amount is now **defined as** its list price plus the adjustments committed against it, and the
quote is read off that record. `decisions/0011`, `0012`, `0013`.

---

## 1. The idea in one paragraph

Pricing is a sequence of **adjustments** to money, and the product's new requirement is that the
sequence — not just its arithmetic result — is the deliverable. So there is one kind of thing at the
centre of this design: an **explanation**, opened at a list price and extended by one entry per
thing that happened, whose final amount is *computed from* its entries rather than stored beside
them. Each cart line owns one; the cart owns one. A promotion never touches money directly: it is
asked what it wants, the **ledger** turns that into a **proposal** — a fully computed, not yet
applied change, already clamped to what remains and already split across the lines it lands on — and
committing that proposal is the single act that both moves the balance and appends the entry. An
amount and its explanation therefore cannot disagree, because there is no second place either could
come from. The proposal seam is also what makes **non-stackable** codes expressible: every code that
may not be combined with another is proposed against one and the same basket — the one that exists
between the two stages, after the codes nobody contests have done their work — compared on what it
would actually take off that basket whatever kind it is, and the largest is committed there and then.
Each of the others is recorded, with the number it would have saved, as *not applied, superseded by*
the winner. There is exactly one such contest per cart, it is a step of the pipeline rather than an
interruption inside one, and no promotion learns that another exists.

```
catalogue file (TOML, business-edited; a code may be marked non-stackable)
        │  catalog.load_catalog()          ← the only module that knows the file format
        ▼
  PromotionCatalog ── lookup(code) → CatalogEntry{promotion, stackable}
                                     │
cart (customer id, lines, codes) ────┤
        │                            ▼
        │                    engine.price_cart()
        │   ┌────────────────────────────────────────────────────────────────┐
        │   │ 1 resolve codes      unknown / disabled / duplicate: reported, never fatal
        │   │ 2 canonical order    the result does not depend on typing order
        │   │ 3 LINE stage         uncontested line codes: propose → commit (units become free)
        │   │ 4 THE CONTEST        every non-stackable code, any scope, against this one basket:
        │   │                      largest wins and commits here; the rest recorded superseded
        │   │ 5 CART stage         uncontested cart codes: propose → commit (money comes off)
        │   │ 6 read the answer    every figure is read off an explanation
        │   └────────────────────────────────────────────────────────────────┘
        ▼
   CartLedger ──────────────► Quote
     ├─ cart Explanation  ───────► quote.explanation   (list → … → total)
     └─ LineLedger per line ─────► line.explanation    (list → … → net)
                                          │
                                          ▼
                                   cli.py serializes to JSON
```

Every promotion **kind** in the system — the percentage, the fixed amount, the one-free-in-every-N —
is untouched by this stage. That they did not have to change is the evidence that the stage-1
promotion seam was drawn in the right place; what changed is the machinery that *records*, which is
where the new requirement actually lives.

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
| `pricing/catalog.py` | where promotion definitions come from, or how they are written, changes |
| `pricing/quote.py` | what we report back changes |
| `pricing/engine.py` | how promotions interact — order, exclusion, clamping, spreading, reporting — changes |
| `pricing/cli.py` | the wire format or the command surface changes |
| `promotions.toml` | the business adds, retires, or re-marks a **code** (no engineer, no deploy) |

`explanation.py` is new, and it is deliberately **not** part of `quote.py`. An explanation is built
during pricing (by the ledgers, engine-side) and read after pricing (by the quote, report-side); it
is the shared vocabulary between the two, so it belongs to neither. Putting it in `quote.py` would
make the ledgers import the answer type they are supposed to be upstream of.

Dependency rules, unchanged: nothing imports `cli.py`; only `catalog.py` imports `tomllib`; only
`money.py` and `catalog.py` import `decimal`; `promotions.py` imports `money.py` and `cart.py` and
nothing else — in particular it does not import `explanation.py`, because no promotion writes an
explanation.

---

## 3. Money, and the change in money

Stage-1's `Money` is unchanged: a **non-negative** amount in integer minor units, the only place
that rounds, the only place that formats to 2dp, the only place that splits an amount into parts
that still sum to it (`decisions/0003`).

The new requirement adds a second concept. "The exact money delta this adjustment contributed" is
not an amount — it is a **change** to one, it is signed, and the whole feature turns on such changes
being addable: *the deltas sum exactly to the difference between the list price and the final
price*. A subtraction whose result may be negative is not expressible in `Money` at all — by design,
since `Money.__sub__` raises on underflow. So a signed sibling is introduced, exactly as
`decisions/0003` anticipated one would have to be, and `decisions/0012` records it.

```python
# pricing/money.py

class Money:
    """A non-negative amount of the single currency, held as an integer number of cents."""
    # stage-1, unchanged:
    @classmethod
    def parse(cls, text: str) -> "Money": ...        # "12.50" -> 1250; exact, via Decimal
    @classmethod
    def zero(cls) -> "Money": ...
    def __add__(self, other: "Money") -> "Money": ...
    def __sub__(self, other: "Money") -> "Money": ...        # raises ArithmeticError on underflow
    def times(self, whole_units: int) -> "Money": ...        # exact; no rounding possible
    def percentage(self, percent: "Percent") -> "Money": ... # THE ONLY ROUNDING POINT (ROUND_HALF_UP)
    def allocate(self, weights: "Sequence[Money]") -> "list[Money]": ...
        # splits self into parts proportional to weights, summing EXACTLY to self; largest-remainder,
        # ties by index. Zero weights sum -> all-zero result (self must then be zero; asserted).
    def is_zero(self) -> bool: ...
    def format(self) -> str: ...                     # always 2dp: "12.50", "0.00"

    # new in stage 2:
    def after(self, delta: "MoneyDelta") -> "Money": ...
        # self + delta. Raises ArithmeticError if the result would be negative — the tripwire, not
        # the policy: a proposal is clamped before it can ever be committed (§7).


class MoneyDelta:
    """A signed change in money, in integer minor units.

    Money answers "how much is this?"; MoneyDelta answers "how much did this move it?". They are not
    the same concept and are not interchangeable: every amount in the product is non-negative, and
    every discount is a negative change to one.
    """
    __slots__ = ("_minor",)

    @classmethod
    def opening(cls, amount: Money) -> "MoneyDelta": ...     # +amount — a list price entering a ledger
    @classmethod
    def reduction(cls, amount: Money) -> "MoneyDelta": ...   # -amount — a discount
    @classmethod
    def nothing(cls) -> "MoneyDelta": ...                    # exactly zero
    @classmethod
    def between(cls, basis: Money, final: Money) -> "MoneyDelta": ...   # final - basis, signed
    @classmethod
    def total(cls, deltas: "Iterable[MoneyDelta]") -> "MoneyDelta": ... # THE sum — one implementation

    def __add__(self, other: "MoneyDelta") -> "MoneyDelta": ...
    def __neg__(self) -> "MoneyDelta": ...
    def magnitude(self) -> Money: ...                # the unsigned size: what a contest compares (§8)
    def is_reduction(self) -> bool: ...
    def is_zero(self) -> bool: ...
    def format(self) -> str: ...                     # "-2.50", "+25.00", "0.00"
    # __eq__, __lt__ (signed), __hash__, __repr__


class Percent:
    """A percentage in (0, 100], exact to the written digits."""   # stage-1, unchanged
    @classmethod
    def parse(cls, text: str) -> "Percent": ...
    def format(self) -> str: ...
```

Why a second type rather than letting `Money` go negative: `Money`'s non-negativity is what invariants
I1 and I2 stand on, in every line of the system — making it signed to serve the report would take the
guarantee away from the product to give a field to a document. And why not a `Money` plus a direction
flag: because then "do these sum exactly to the difference" is a rule every reader re-implements with
an `if`, which is precisely the kind of rule this design gives an owner. `MoneyDelta.total` is that
owner, and it is used by the explanation, by the contest, and by the tests, so there is one summation
in the system.

---

## 4. The request domain — unchanged

```python
# pricing/cart.py

class Sku:
    """A stock identifier, normalised once here (Q7), so promotion targeting is a comparison."""
    @classmethod
    def of(cls, raw: str) -> "Sku": ...

@dataclass(frozen=True)
class CartLine:
    sku: Sku
    unit_price: Money
    quantity: int                                    # >= 1, validated here
    def gross(self) -> Money: ...                    # unit_price.times(quantity) — the line's list price

@dataclass(frozen=True)
class Cart:
    customer_id: str                                 # carried, echoed, read by nothing (goals.md)
    lines: tuple[CartLine, ...]
    codes: tuple[str, ...]                           # exactly as the customer typed them, in order
    # Construction raises InvalidCartError with every problem found, not the first.
```

An empty cart is valid and prices to 0.00 with an explanation consisting of nothing but its list
price of 0.00. The cart still knows nothing about promotions, and now nothing about explanations
either: it supplies the list prices an explanation is opened at, and that is all.

The submission **order** of `codes` has acquired a second job in this stage — it is the tie-break
when two mutually exclusive codes are worth the same (B5, §8). It was already the order outcomes are
reported in.

---

## 5. Promotions — two scopes, and a flag that is not theirs

The promotion seam is **unchanged by this stage**, which is the point worth noticing about it:

```python
# pricing/promotions.py

class PromotionCode:
    @classmethod
    def of(cls, raw: str) -> "PromotionCode": ...    # normalised once (Q7): trim + case-fold

class Promotion(Protocol):
    @property
    def code(self) -> PromotionCode: ...
    def describe(self) -> str: ...                   # "10% off the cart", "1 free for every 3 COFFEE"

class LinePromotion(Promotion, Protocol):
    @property
    def target(self) -> Sku: ...
    def free_units(self, paid_units: int) -> int: ...

class CartPromotion(Promotion, Protocol):
    def requested_discount(self, remaining: Money) -> Money: ...
```

```python
@dataclass(frozen=True)
class PercentOffCart:                # kind = "PCT"
    code: PromotionCode
    percent: Percent
    def requested_discount(self, remaining: Money) -> Money:
        return remaining.percentage(self.percent)

@dataclass(frozen=True)
class AmountOffCart:                 # kind = "AMT"
    code: PromotionCode
    amount: Money
    def requested_discount(self, remaining: Money) -> Money:
        return self.amount           # deliberately ignores `remaining`: clamping is not my job

@dataclass(frozen=True)
class OneFreeInEveryN:               # kind = "BOGO"
    code: PromotionCode
    target: Sku
    every: int                       # N >= 2, validated by the loader
    def free_units(self, paid_units: int) -> int:
        return paid_units // self.every
```

`every = 3` means three cost two (`decisions/0007`). `describe()` is the promotion's own phrase and
is what an explanation entry shows — the engine must never assemble that sentence from a kind tag
and a number, because only the promotion knows its parameters.

**Where "non-stackable" is *not*.** It is tempting to put `stackable: bool` on the promotion. It does
not belong there: stackability is a property of the **definition the business wrote**, not of the
arithmetic rule the kind implements. Ten percent off is ten percent off whether or not the business
lets it combine, and `PercentOffCart` should not grow a field it never reads. So the flag rides with
the catalogue entry (§10) and reaches the engine on the resolved code (§8), and the promotion kinds
stay exactly as they were. The operational consequence is that marking an existing code
non-stackable is a **data edit** — which is the same axis on which codes are added and retired, and
therefore the axis the catalogue was built for.

---

## 6. The explanation — the account of one amount

This is the new centre of the design.

```python
# pricing/explanation.py

class Scope(Enum):
    LINE = "line"                    # the adjustment came from a promotion that frees units
    CART = "cart"                    # the adjustment came from a promotion that takes money off the cart

class AdjustmentKind(Enum):
    LIST_PRICE  = "list_price"       # the opening entry: where the amount started
    PROMOTION   = "promotion"        # a code that actually moved money
    NOT_APPLIED = "not_applied"      # a code that qualified but was superseded by another (§8)

@dataclass(frozen=True)
class Adjustment:
    kind: AdjustmentKind
    delta: MoneyDelta                       # the exact money this contributed
    code: PromotionCode | None              # None only for LIST_PRICE
    scope: Scope | None                     # None only for LIST_PRICE
    detail: str                             # the promotion's own phrase, or the supersession reason
    superseded_by: PromotionCode | None     # NOT_APPLIED only
    forgone: Money | None                   # NOT_APPLIED only: what it would have saved

    # __post_init__ enforces the shape of each kind, in particular:
    #   NOT_APPLIED  =>  delta.is_zero()  and superseded_by is not None and forgone is not None
    #   LIST_PRICE   =>  code is None and scope is None and not delta.is_reduction()
    #   PROMOTION    =>  code is not None and scope is not None and delta.is_reduction()

class Explanation:
    """The ordered story of one amount: opened at a list price, then one entry per thing that happened.

    The final amount is COMPUTED from the entries. There is no stored total to disagree with them.
    """
    @classmethod
    def opened_at(cls, list_price: Money) -> "Explanation": ...
        # creates the single LIST_PRICE entry, delta = MoneyDelta.opening(list_price)

    def record(self, adjustment: Adjustment) -> "Explanation": ...   # returns a new Explanation

    @property
    def list_price(self) -> Money: ...               # the opening entry's amount
    @property
    def final(self) -> Money: ...                    # Money.zero().after(total of ALL deltas)
    @property
    def net_delta(self) -> MoneyDelta: ...           # total of the deltas AFTER the opening entry
    def entries(self) -> tuple[Adjustment, ...]: ...             # opening entry first, then in order
    def steps(self) -> "Iterator[tuple[Adjustment, Money]]": ... # each entry with the running amount after it
    def deltas_for(self, scope: Scope) -> MoneyDelta: ...        # the fold the report uses (§9)
```

Three properties hold **by construction**, not by assertion, and they are the whole feature:

1. `final == list_price.after(net_delta)` and `net_delta == MoneyDelta.between(list_price, final)` —
   the deltas sum exactly to the difference between the list price and the final price, to the cent.
   There is no residue, because `final` is not an independent number: it *is* the sum.
2. The order of `entries()` is the order things were committed (§7), so the story is the history.
3. A `NOT_APPLIED` entry contributes exactly zero, so recording what did *not* happen cannot disturb
   the arithmetic of what did.

**There is no rounding entry and there cannot be one.** Every delta is exact at the moment it is
made: a percentage rounds once, inside `Money.percentage`, and the rounded result *is* the delta;
splitting a cart-level delta across lines uses `Money.allocate`, which is exact by construction. A
"rounding" line only becomes necessary when a total is computed independently of the parts, which
this design has no way to do.

`steps()` exists because the reader's question is "25.00 → 22.50", not "delta −2.50": the running
amount after each entry is what a support agent reads out. It is derived on demand and deliberately
not stored on the entry — a stored running amount is a second copy of the arithmetic, which is the
exact failure mode this stage exists to remove.

---

## 7. The ledgers — the only things that can change an amount

A ledger owns a balance **and** its explanation, and the single operation that moves the balance is
the same operation that appends the entry. That is the enforcement point for "the explanation
describes what actually happened": there is no path to a number that does not go through a recorded
adjustment.

Applying a promotion is split into two moments, because the non-stackable rule needs to compare two
possible futures before either happens:

- **propose** — compute the whole change: clamp it to what remains, decide which lines it lands on,
  and price it. Nothing moves.
- **commit** — apply the proposal and record it. Nothing is recomputed.

A proposal is a **prepared transaction**: made against the current state and either committed
immediately or discarded. It is never held across another commit. That rule is what makes the
comparison honest — every contender is proposed against the same state, and the winner commits at
that same state, so *the number it won with is the number it took*, and the loser's reported "would
have saved" is the number it was compared on rather than a later re-derivation.

```python
# pricing/engine.py  (internal collaborators; none of this is public)

class Proposal(Protocol):
    """A fully computed change, not yet applied."""
    @property
    def code(self) -> PromotionCode: ...
    @property
    def scope(self) -> Scope: ...
    @property
    def detail(self) -> str: ...                     # the promotion's describe()
    def total(self) -> MoneyDelta: ...               # what the customer gets — what a contest compares
    def line_deltas(self) -> tuple[MoneyDelta, ...]: ...   # one per cart line; zero where untouched
    def commit(self) -> None: ...                    # apply to the ledgers that produced me, and record

class LineProposal(Proposal, Protocol):
    def freed_units(self) -> tuple[int, ...]: ...    # one per cart line; only a line promotion has these
```

`LineProposal` is a *specialization*, not a flag on a shared record: a cart promotion has no units to
free, and giving it a `freed_units` field full of zeros would force the unit concept onto a producer
and consumers that have no notion of it (`design-principles.md` §2, the same argument that gave the
promotions two scopes in stage-1). The contest, which is the one consumer that unifies them, needs
only `total()` and identity — the common part — so it depends only on `Proposal`.

```python
class LineLedger:
    """One cart line's running balance and its story. commit is the only thing that changes either."""
    def __init__(self, line: CartLine): ...          # explanation opened at line.gross()
    @property
    def paid_units(self) -> int: ...                 # quantity minus units freed so far
    @property
    def unit_price(self) -> Money: ...
    @property
    def remaining(self) -> Money: ...                # == self.explanation.final, always
    @property
    def explanation(self) -> Explanation: ...
    def free(self, units: int, adjustment: Adjustment) -> None: ...   # units come off the paid count
    def reduce(self, adjustment: Adjustment) -> None: ...             # money only
    # and nothing else: every entry in a line's explanation moved that line (Q13b), so a line has no
    # record-only operation. Both of these move the balance and append the entry in one step (I9).

class CartLedger:
    """The cart's balance, its story, and every rule about how an adjustment is spread across lines."""
    def __init__(self, cart: Cart): ...
        # one LineLedger per line; the cart explanation opened at the sum of the lines' list prices
    @property
    def remaining(self) -> Money: ...                # Σ line.remaining — the cart has no balance of its own
    @property
    def explanation(self) -> Explanation: ...
    def paid_units(self, sku: Sku) -> int: ...       # across every line of that SKU

    def propose_line(self, promotion: LinePromotion) -> LineProposal: ...
        # asks free_units(paid_units(target)), clamps to what is still paid for, chooses WHICH units
        # cheapest-unit-price-first across every line of that SKU (Q8), and prices them.
    def propose_cart(self, promotion: CartPromotion) -> Proposal: ...
        # asks requested_discount(remaining), clamps to `remaining`, and splits the clamped amount
        # across the lines by Money.allocate on their current remainings.

    def record_superseded(self, loser: Proposal, winner: PromotionCode) -> None: ...
        # writes the NOT_APPLIED entry into the CART explanation only: a code that was not applied
        # did not change any line's price, and a line's story carries only what moved it (Q13b).
        # One place, so "what the customer is told about a superseded code" has one implementation.

    def priced_lines(self) -> tuple[PricedLine, ...]: ...
```

**The cart has no balance of its own.** `CartLedger.remaining` is the sum of the line balances, so
invariant I6 (the line figures sum exactly to the total) is not maintained — it is *definitional*.
This is the structural change stage-2 makes to stage-1, and the new requirement forces it: a line's
explanation must name each cart-level promotion and its share of it, which means a cart-level
discount has to be split across the lines **at the moment it is taken**, not accumulated and split
once at the end. Once it is split at that moment, there is nothing left for the cart to hold.

**Clamping, and why a line can never go negative.** Two clamps, both in `propose`, both before
anything is recorded: a line proposal may not free more units than are still paid for, and a cart
proposal may not take more money than `remaining`. The allocation that follows cannot break the
second one either: `Money.allocate` gives line *i* either `floor(taken × wᵢ / Σw)` or one cent more,
and with `taken ≤ Σw` a line's share can exceed its own weight `wᵢ` only if its floor term already
equals `wᵢ`, which requires `taken = Σw` — and in that case every remainder is zero, so no leftover
cent is handed out at all. A line's share is therefore always ≤ its remaining, and `Money.after`
never has to raise. The raise stays as the tripwire that says the clamp was bypassed.

---

## 8. The engine — order, exclusion, and the report

```python
# pricing/engine.py  (the public seam of the library)

def price_cart(cart: Cart, catalog: PromotionCatalog) -> Quote: ...
```

```python
@dataclass(frozen=True)
class ResolvedCode:
    """A code the customer submitted, bound to what it resolved to and where it was typed."""
    as_typed: str                    # exactly as typed, for the report
    index: int                       # submission position — the report order, and the tie-break (B5)
    code: PromotionCode              # normalised
    promotion: Promotion
    stackable: bool                  # from the catalogue entry; not a property of the kind (§5)

def canonical_order(resolved: "Iterable[ResolvedCode]") -> list[ResolvedCode]: ...
    # THE ordering rule (I5): sort by (stage, kind rank, code). Never by submission order.

@dataclass(frozen=True)
class Choice:
    winner: ResolvedCode | None
    superseded: tuple[tuple[ResolvedCode, Proposal], ...]

def choose_non_stackable(
    contenders: "Sequence[tuple[ResolvedCode, Proposal]]",
) -> Choice: ...
    # THE exclusion rule: the largest discount wins; an exact tie goes to the lowest submission
    # index. Contenders are only codes whose proposal actually gives something.
```

### The pipeline, step by step, with the owner of each rule

| # | Step | Owner | Rule |
|---|---|---|---|
| 1 | **Resolve codes** | engine | Each submitted code is normalised (Q7) and looked up. Found → a `ResolvedCode` carrying the promotion and its `stackable` flag. Defined but misconfigured → `no_effect`, "temporarily unavailable" (Q6, I7). Not found → `unknown`. Already resolved this cart → counted once, the repeat reported as entered twice (Q4). Nothing raises: I3. |
| 2 | **Canonical order** | `canonical_order` | Line stage before cart stage; within the cart stage PCT before AMT; ties by code, which is unique. The customer's typing order never reaches this (I5, `decisions/0008`). |
| 3 | **Line stage** | `CartLedger` | Walk the **stackable** line-scoped codes in canonical order, proposing and committing each. Freed units are taken cheapest-unit-price first across the lines of that SKU (Q8). |
| 4 | **The contest** | `choose_non_stackable` | One contest per cart, here — at the boundary between the stages, which is the single moment at which *every* non-stackable code can be honestly priced: a line-scoped one against the units still paid for, a cart-scoped one against the subtotal cart promotions act on. All of them are proposed against this one basket, the largest wins and is committed immediately, and each of the others is recorded superseded (Q12, Q14). |
| 5 | **Cart stage** | `CartLedger` | Walk the **stackable** cart-scoped codes in canonical order. Each proposal is computed against `remaining` — what the previous ones, including a contest winner, left — so two 10% codes take 19%, not 20% (Q3, `decisions/0008`), and a fixed amount larger than the cart is clamped to it (I2). Committing splits the amount across the lines, so every line's explanation names the promotion and its share. |
| 6 | **Read the answer** | `quote.py` | Every figure in the `Quote` is read off an explanation (§9). Nothing is recomputed, so nothing can disagree. |
| 7 | **Report** | engine | One `CodeOutcome` per submitted code, in submission order: `applied` with what it took, `superseded` with what it would have taken and which code beat it, `no_effect` with a reason, or `unknown`. |

### The contest, precisely

A **contender** is a non-stackable resolved code — of *either* scope — whose proposal, made at the
contest moment, is a non-zero reduction. That is what "both qualify on one cart" means operationally:
a code that would give nothing (a BOGO below its threshold, a fixed amount on a basket already at
0.00) is not in the contest, does not supersede anything, and is not superseded by anything. It keeps
its ordinary `no_effect` reason, which is the truthful one. A **stackable** code never contends and
can never be superseded (Q11): non-stackable means only that it may not sit beside another
non-stackable one.

With fewer than two contenders there is no contest and nothing is superseded — a lone non-stackable
code simply applies. With two or more:

- the winner is the contender whose `total().magnitude()` is largest — *the one that gives the
  customer the larger discount* — compared on what it actually takes off the basket in front of it,
  clamped, whatever kind it is (Q12, Q14). A BOGO's magnitude is the value of the units it would
  free; a percentage's is the money it would take. They are the same quantity, so they compare;
- an exact tie is broken by the lowest `index` — *the one the customer entered first*;
- the winner is committed **right there**, at the contest moment, so the amount compared and the
  amount taken are the same amount;
- every loser is recorded by `record_superseded` as a `NOT_APPLIED` adjustment in the **cart's**
  explanation, with `forgone` set to its own proposal's magnitude and `superseded_by` set to the
  winner's code, and is reported as `CodeStatus.SUPERSEDED`. It is not written into any line's
  explanation, because it changed no line's price (Q13b).

The losers' entries are written immediately after the winner's, in submission order, so the cart's
story reads: *"TENOFF −10.00 → 40.00; SAVE10 not applied — would have saved 5.00, superseded by
TENOFF."*

**Why the stage boundary is the only honest moment.** The contest must compare codes of both scopes
on one basket, and it must commit the winner at the state it was compared on, or the explanation
would carry a number that never happened. Before the line stage, a cart-scoped code cannot be priced
against the subtotal it will actually act on. After the cart stage, there is nothing left for a
winner to do. Between them, both are exact: the units still paid for are settled, and `remaining` is
precisely the subtotal cart promotions work from. The one visible consequence is an ordering one: a
contest winner runs after every uncontested line code and before every uncontested cart code, which
for a cart-scoped winner can mean applying ahead of its canonical kind position (a non-stackable AMT
before a stackable PCT). That is deterministic, it is one sentence, and the order within the cart
stage was ours to fix (`decisions/0008`, Q2).

**What this does to order-independence (I5).** The amounts are still independent of the order the
customer typed the codes in: the canonical order decides everything, and in an exact tie the two
contenders take the same amount by definition, so every figure in the quote is identical either way.
What is *not* order-independent is which of two tied codes is named as applied — B5 says SAVE10
because it was entered first, and typing them the other way would name TENOFF. That is the product
owner's explicit rule, and it is the only place submission order reaches a result.
`decisions/0013` records the narrowing and `decisions/0014` confirms it in the owner's words:
**the amounts are order-independent; the identity of the applied code, in an exact tie, follows
submission order — and it is fine that it shows.**

---

## 9. The answer

```python
# pricing/quote.py

class CodeStatus(Enum):
    APPLIED    = "applied"
    SUPERSEDED = "superseded"        # valid, qualified, beaten by another code it cannot combine with
    NO_EFFECT  = "no_effect"
    UNKNOWN    = "unknown"

@dataclass(frozen=True)
class CodeOutcome:
    code: str                        # exactly as typed, so the customer recognises it
    status: CodeStatus
    amount: Money | None             # APPLIED: what it actually took
    forgone: Money | None            # SUPERSEDED: what it would have saved
    superseded_by: PromotionCode | None   # SUPERSEDED: the code that beat it
    detail: str                      # the promotion's phrase, or the reason

@dataclass(frozen=True)
class PricedLine:
    sku: Sku
    unit_price: Money
    quantity: int
    free_units: int
    explanation: Explanation         # THE line's price, as a story: list → … → net

    @property
    def gross(self) -> Money: ...                  # explanation.list_price
    @property
    def net(self) -> Money: ...                    # explanation.final — the invoice figure (Q1)
    @property
    def line_discount(self) -> Money: ...          # |Σ deltas of LINE scope|
    @property
    def cart_discount_share(self) -> Money: ...    # |Σ deltas of CART scope|

@dataclass(frozen=True)
class Quote:
    customer_id: str
    lines: tuple[PricedLine, ...]
    explanation: Explanation         # THE cart's price, as a story: list → … → total
    codes: tuple[CodeOutcome, ...]   # one per submitted code, in submission order

    @property
    def subtotal(self) -> Money: ...               # explanation.list_price (Σ line gross)
    @property
    def total(self) -> Money: ...                  # explanation.final
    @property
    def line_discount_total(self) -> Money: ...
    @property
    def cart_discount_total(self) -> Money: ...
```

Every figure stage-1 reported is still reported, with the same meaning and the same name — but each
is now a **fold over the explanation** rather than a stored field. That is the subtractive
consequence of the new requirement: once the explanation exists, a stored `net` is a second copy of a
number the explanation already determines, and two copies of one fact is exactly what the product
owner is paying us to eliminate. `decisions/0011`.

`free_units` stays a stored count because it is not money and not part of the arithmetic; the line
ledger owns it.

**The cart's explanation and the lines' explanations agree by construction.** A line-scoped
adjustment appears in the cart explanation as the *aggregate* of the line deltas it caused; a
cart-scoped adjustment appears in each line's explanation as that line's *share* — what that line's
price actually went down by (Q17). The one entry that appears at cart level only is `NOT_APPLIED`:
a superseded code moved no line, so no line's story mentions it (Q13b). Since its delta is zero, the
two levels still reconcile exactly. Both directions are
the same numbers summed the same way — `Money.allocate` guarantees the shares sum exactly to the
aggregate — so `Σ line.net == total` and, per promotion, `Σ line share == cart delta`. Neither is
checked afterwards; both are the way the numbers are produced.

---

## 10. The catalogue

```toml
# promotions.toml — edited by the business. Amounts and percentages are QUOTED; an unquoted
# 10.00 would be a binary float, and money is never a float.

[SAVE10]
kind    = "PCT"
percent = "10"

[TENOFF]
kind      = "AMT"
amount    = "10.00"
stackable = false        # may not be combined with another non-stackable code

[COFFEE3]
kind  = "BOGO"
sku   = "COFFEE"
every = 3                # one free for every 3 in the cart: 3 cost 2, 6 cost 4
```

`stackable` is a new optional boolean on any entry, **defaulting to `true`** — the file the business
already has keeps its exact meaning, and marking a code non-stackable is one word on one line, no
engineer and no deploy. A non-boolean value is a malformed entry like any other: the code is
disabled, the problem names the code and the field, and every other code still prices (I7,
`decisions/0009`).

```python
# pricing/catalog.py

@dataclass(frozen=True)
class CatalogEntry:
    """What the business wrote about one code: the rule, and how it may be combined."""
    promotion: Promotion
    stackable: bool

@dataclass(frozen=True)
class CatalogProblem:
    code: str | None                 # the code whose entry is broken; None for a whole-file problem
    detail: str                      # names the field and what is wrong with it

class PromotionCatalog:
    def lookup(self, code: PromotionCode) -> CatalogEntry | None: ...
    def is_disabled(self, code: PromotionCode) -> bool: ...   # defined in the file, but unusable
    @property
    def problems(self) -> tuple[CatalogProblem, ...]: ...
    def __len__(self) -> int: ...

def load_catalog(source: "str | os.PathLike | IO[bytes]") -> PromotionCatalog: ...
    # A broken ENTRY is skipped, recorded, and its code marked disabled (Q6, I7). Raises CatalogError
    # only when the file is unreadable or is not valid TOML, so nothing can be trusted.

class CatalogError(Exception):
    problems: tuple[CatalogProblem, ...]

_PARSERS: "dict[str, Callable[[PromotionCode, Mapping[str, Any]], Promotion]]"
    # kind -> parser. THE registration point for a new kind: one class in promotions.py + one entry
    # here. `stackable` is read by the loader itself, outside the table, because it applies to every
    # kind and is not part of any kind's rule.
```

`lookup` returns the **entry**, not the promotion, so that the rule and the combination policy arrive
together and a caller cannot get one and forget the other. The loader validates what a promotion
cannot validate about itself: that the kind exists, that required fields are present and well-formed,
that `every >= 2`, that a percentage is in range, that an amount is non-negative, that `stackable` is
a boolean, and that no code is defined twice.

---

## 11. The CLI (a serialization boundary, nothing more)

```
$ python -m pricing quote --catalog promotions.toml < cart.json > quote.json
$ python -m pricing validate-catalog --catalog promotions.toml
```

```jsonc
// cart.json (in) — unchanged
{ "customer_id": "c-123",
  "lines": [ { "sku": "WIDGET", "unit_price": "50.00", "quantity": 1 } ],
  "codes": ["SAVE10", "TENOFF"] }

// quote.json (out) — every amount a 2dp string, every delta a signed 2dp string  [case B3]
{ "customer_id": "c-123",
  "lines": [
    { "sku": "WIDGET", "unit_price": "50.00", "quantity": 1, "free_units": 0,
      "gross": "50.00", "line_discount": "0.00", "cart_discount_share": "10.00", "net": "40.00",
      "explanation": [
        { "kind": "list_price", "delta": "+50.00", "amount": "50.00", "detail": "list price" },
        { "kind": "promotion",  "code": "TENOFF", "scope": "cart", "delta": "-10.00",
          "amount": "40.00", "detail": "10.00 off the cart" }
      ] } ],
  "subtotal": "50.00", "line_discount_total": "0.00", "cart_discount_total": "10.00",
  "total": "40.00",
  "explanation": [
    { "kind": "list_price", "delta": "+50.00", "amount": "50.00", "detail": "list price" },
    { "kind": "promotion",  "code": "TENOFF", "scope": "cart", "delta": "-10.00",
      "amount": "40.00", "detail": "10.00 off the cart" },
    { "kind": "not_applied", "code": "SAVE10", "scope": "cart", "delta": "0.00",
      "amount": "40.00", "forgone": "5.00", "superseded_by": "TENOFF",
      "detail": "SAVE10 would have saved 5.00; TENOFF saved more" } ],
  "codes": [
    { "code": "SAVE10", "status": "superseded", "forgone": "5.00", "superseded_by": "TENOFF",
      "detail": "SAVE10 would have saved 5.00; TENOFF saved more" },
    { "code": "TENOFF", "status": "applied", "amount": "10.00", "detail": "10.00 off the cart" } ] }
```

`amount` on an explanation entry is the **running amount after that entry** — `Explanation.steps()`
serialized — because that is what a support agent reads out ("50.00, then TENOFF takes 10.00, so
40.00"). It is derived at serialization time, never stored (§6).

Exit codes are unchanged: `0` priced — including carts with unknown codes, superseded codes, and a
catalogue with broken entries, whose problems go to **stderr**; `2` the catalogue file is unreadable
or not valid TOML; `3` the cart input is malformed. `validate-catalog` stays strict and exits
non-zero on any problem at all, including a non-boolean `stackable`.

---

## 12. The required cases, traced through the design

### The new cases

| # | Trace | Result |
|---|---|---|
| **B1** | WIDGET 12.50×2, SAVE10. Line explanation opened at 25.00; cart explanation at 25.00. No line stage. Cart stage: `propose_cart` asks 10% of remaining 25.00 → 2.50, clamped to 2.50, allocated over weights (25.00) → 2.50 on L1. Commit: L1 remaining 22.50, both explanations get `SAVE10 −2.50`. | cart: **list 25.00 → SAVE10 −2.50 → 22.50**; line the same; deltas after the opening entry sum to **−2.50** = 22.50 − 25.00 ✔ |
| **B2** | COFFEE 4.00×4 + WIDGET 12.50×1; COFFEE3, SAVE10, both stackable. Cart explanation opened at 28.50. Line stage: COFFEE3 → `free_units(4) = 1`, cheapest unit 4.00 → L1 delta −4.00, L1 remaining 12.00; cart entry `COFFEE3 −4.00` (the aggregate). Cart stage: remaining 12.00 + 12.50 = 24.50 → 10% = 2.45, allocated over (12.00, 12.50) → 1.20 and 1.25, exact, no leftover cent. | **total 22.05** ✔; cart story **28.50 → COFFEE3 −4.00 → 24.50 → SAVE10 −2.45 → 22.05**, in the order applied, deltas summing to −6.45 ✔; L1 12.00→10.80, L2 12.50→11.25, Σ = 22.05 ✔ |
| **B3** | WIDGET 50.00×1; SAVE10 and TENOFF, both non-stackable. No uncontested line codes, so the contest moment is the untouched basket: both are proposed against remaining 50.00 — SAVE10 −5.00, TENOFF −10.00. TENOFF is larger, wins, and commits there. SAVE10 recorded `NOT_APPLIED` in the cart's explanation, forgone 5.00, superseded_by TENOFF, delta 0.00. | **total 40.00** ✔; SAVE10 present in the explanation, **not applied, superseded by TENOFF** ✔; deltas sum −10.00 ✔ |
| **B4** | WIDGET 150.00×1, same two codes. Contest against remaining 150.00: SAVE10 −15.00, TENOFF −10.00 → **SAVE10 wins** and commits; TENOFF recorded `NOT_APPLIED`, forgone 10.00, superseded_by SAVE10. | **total 135.00** ✔, TENOFF marked superseded ✔ |
| **B5** | WIDGET 100.00×1, same two codes. Contest: SAVE10 −10.00, TENOFF −10.00 — an exact tie on `magnitude()`. Tie-break is the lowest submission index: SAVE10 was typed first (index 0). SAVE10 commits; TENOFF recorded `NOT_APPLIED`, forgone 10.00. | **total 90.00** ✔, SAVE10 applied **because it was entered first** ✔, TENOFF superseded ✔ |
| **B3′** | *(not an acceptance case; the shape Q12 opened.)* COFFEE 4.00×4 + WIDGET 12.50×1 with COFFEE3 and SAVE10 **both non-stackable**. No uncontested line code runs, so the contest is on the submitted basket, 28.50: COFFEE3 would free one 4.00 unit (−4.00), SAVE10 would take 10% of 28.50 (−2.85). The BOGO is larger and wins across scopes — it commits, freeing the unit. SAVE10 is recorded superseded, forgone 2.85. | **total 24.50**, and the story is **28.50 → COFFEE3 −4.00 → 24.50**, with SAVE10 not applied ✔ |

### B6 — every earlier acceptance case, unchanged

| # | Trace | Result |
|---|---|---|
| **A1** | WIDGET 12.50×2, no codes. Explanation is the opening entry alone. | line **25.00**, total **25.00** ✔ |
| **A2** | = B1. | **22.50** ✔ |
| **A3** | TENOFF (stackable) on 25.00: requested 10.00 ≤ remaining, allocated over one line. | **15.00** ✔ |
| **A4** | COFFEE 4.00×4, COFFEE3: `4 // 3 = 1` free at 4.00, no cart stage. | **12.00** ✔ |
| **A5** | = B2. | **22.05** ✔ |
| **A6** | "NOPE" resolves to nothing → `CodeOutcome(UNKNOWN)`; it is **not** an adjustment and so has no entry in either explanation. Pricing untouched. | total **12.50**, NOPE **unknown** ✔ |
| **A7** | Subtotal 1.00, TENOFF asks 10.00. `propose_cart` clamps to `remaining` = 1.00 *before* anything is recorded, so the committed delta is −1.00 and the outcome is `applied 1.00`. | total **0.00**, never negative ✔ — structurally, and the explanation says exactly that: **1.00 → TENOFF −1.00 → 0.00** |

**Where stage-2 could have changed an old number, and does not.** Stage-1 allocated the *aggregate*
cart discount to the lines once, at the end; stage-2 allocates **each** cart-level discount as it is
taken. The two differ only in the pennies, only when a cart carries two or more cart-level
promotions, and only on the per-line figures — the total is computed from the balances either way.
No acceptance case, old or new, has two cart-level promotions, so every stated amount is identical;
the change is forced by the requirement that a line's story name each promotion separately.

A second place stage-2 could have moved an old number is the contest's position in the order: a
winner commits between the stages rather than at its kind's canonical slot. That can only bite a cart
that carries a non-stackable code *and* an uncontested cart code — B1–B6 carry no non-stackable codes
at all except B3–B5, which carry nothing else. Every stated amount is again identical.

---

## 13. Invariants, and the single place each is enforced

| | Invariant | Enforced at |
|---|---|---|
| **I1** | No line cost and no cart total is ever negative | `Money` is non-negative by construction; `propose_*` clamps before anything is recorded; `Money.after` raises as a tripwire if a clamp was ever bypassed |
| **I2** | A discount never takes more than remains at the point it is applied | the clamp inside `CartLedger.propose_cart` / `propose_line` — a promotion states what it *wants*, the ledger decides what is taken |
| **I3** | Every submitted code gets a truthful outcome of its own | the engine emits one `CodeOutcome` per submitted code, in submission order, with four statuses because there are four different conversations: applied, superseded, no effect (with a reason), unknown |
| **I4** | Money is one currency, 2dp, never finer than a cent | `Money` holds integer minor units; `Money.percentage` is the only rounding point; formatting lives on `Money`/`MoneyDelta` |
| **I5** | The same cart and codes always price to the same **amounts**, whatever order the codes were typed in — and in an exact tie between two mutually exclusive codes, the first-entered one is the one named applied | `canonical_order` for the amounts; `choose_non_stackable`'s tie-break for the naming (`decisions/0013`) |
| **I6** | The per-line costs sum exactly to the total | definitional: `CartLedger.remaining` **is** Σ line remaining; the cart keeps no balance of its own |
| **I7** | A catalogue mistake is contained to the code it was written on | `load_catalog`; a disabled code is reported "temporarily unavailable", never "unknown" |
| **I8** | *(new)* Every explanation's deltas sum exactly to the difference between its list price and its final price — no residue, no rounding entry | definitional: `Explanation.final` is computed from the entries; there is no stored total to disagree with them |
| **I9** | *(new)* An explanation describes what actually happened, in the order it happened | `LineLedger.free/reduce` — the one operation that moves a balance is the one that appends the entry; there is no other path to an amount |
| **I10** | *(new)* Each cart-level adjustment's per-line shares sum exactly to its cart-level delta | `Money.allocate`, called once per cart-level promotion at the moment it is committed |
| **I11** | *(new)* At most one non-stackable code applies to a cart, whatever kinds the contenders are, and each of the others is reported naming the code that beat it and what it would have saved | `choose_non_stackable`, called once per cart at step 4, is the only place a proposal is discarded; `CartLedger.record_superseded` is the only place the loser's entry is written |

---

## 14. The subtractive pass

Every type, guard and abstraction added in this stage was put to one question: *if I deleted it,
would the ownership of a rule the product needs today actually be damaged?* The pass also re-ran over
stage-1's machinery, because a new requirement is the moment old structure stops paying for itself.

**Cut, and why:**
- **The stored `net`, `gross`, `line_discount`, `cart_discount_share`, `subtotal`, `total`,
  `line_discount_total`, `cart_discount_total` fields.** Once the explanation exists, each of these
  is a second copy of a number the explanation already determines — and "the explanation and the
  amount disagree" is the exact failure the product owner says would make the feature worthless. They
  are now folds over the explanation, reported under the same names.
- **A stored running amount on each adjustment.** Derivable by `steps()`, and a stored one is the
  same second copy in miniature.
- **The separate cart money balance (`MoneyLedger`).** The cart's remaining is the sum of the lines'.
  Deleting it turned I6 from a maintained property into a definition.
- **`UnitLedger` as a thing of its own.** A line's paid-unit count and its money balance change
  together, always, and the new requirement makes the line's *story* a third thing that changes with
  them — three facts, one owner: `LineLedger`.
- **A `Rounding` adjustment kind.** There is nothing for it to absorb: one rounding point, and an
  exact allocator. The product owner forbade it, and the design has no way to need it.
- **A `stackable` field on the promotion kinds.** Stackability is a property of the definition, not
  of the arithmetic; the kinds are untouched by this whole stage (§5).
- **A `Supersession` value type.** Its two facts (which code won, what was forgone) live on the
  `NOT_APPLIED` adjustment and on the outcome, both of which must carry them anyway.
- **Per-line `NOT_APPLIED` entries, and with them `LineLedger.note`.** The product owner's answer to
  Q13b — *"if it didn't change that line's price, it doesn't need to be on that line"* — removed
  them: a superseded code is recorded once, in the cart's explanation, where the choice was actually
  made. A line's story now contains nothing but what moved that line, so a line ledger has no
  record-only operation at all and every entry it holds came from a balance moving.
- **A contest inside each stage.** Q12 made contention cross-scope, and a cross-scope comparison has
  exactly one honest moment (§8), so two stage-local contests collapsed into one pipeline step. The
  rule got smaller as it got more general — one contest, one winner, one address.
- **A "would-be quote" / dry-run pricing pass to compare candidates.** The proposal already *is* the
  computed change; re-running pricing to compare two codes would be a second implementation of
  pricing, and the two would drift.

**Kept, with the force that keeps them:**
- **`MoneyDelta`** — the deltas must *sum*, and the sum must equal a difference that is negative.
  Without it that rule has no owner and every caller re-implements it with a sign convention and an
  `if`. It is also what keeps `Money` non-negative, which I1/I2 stand on.
- **`Explanation`** — it *is* invariants I8 and I9. Delete it and the amounts have no history, which
  is the feature.
- **`Adjustment` + `AdjustmentKind` + `Scope`** — three kinds because a reader and a UI treat them as
  three different rows (a starting point, a saving, a code that was beaten); `Scope` because the
  line-level and cart-level discount figures the product owner asked for in Q1 are exactly the two
  folds it separates.
- **`Proposal` / `LineProposal`** — the present force is the contest: two changes must be fully
  computed and compared *before* either is applied, and the loser's number must be reported. Without
  the seam, comparison means either applying-and-undoing or a parallel evaluation that can disagree
  with the real one.
- **`CatalogEntry`** — `lookup` must hand back the rule and the combination policy together; the
  alternative is a second lookup a caller can forget.
- **`ResolvedCode`** — the tie-break needs the submission index *bound to* the promotion; a parallel
  list keyed by position is the same data with a way to get it wrong.
- **`choose_non_stackable` as a named function** — it is invariant I11, and the exclusion policy is
  the interaction rule most likely to be revised next (weight by kind, exclude stackable codes too,
  compare on a different basket), so it is worth exactly one address. Q11–Q14 each landed inside it
  or inside its single call site, which is the evidence that the address is the right one.

**Carried forward, still unpaid:** `LinePromotion` has one implementation today (stage-1 §5 argued
it on rule-ownership grounds: it is the seam that keeps "one free in every three" out of the engine).
This stage does not change that, and adds a second use for it — a line-scoped contest — that is also
unexercised today. Re-measure at the first implementation review, not now.

---

## 15. Alternatives rejected (structural)

1. **Compute the explanation after pricing, from the figures.** Rejected: it makes two producers of
   one fact, and the product owner's single hard requirement is that they cannot disagree. It is also
   not possible in general — once a cart-level discount has been rounded and allocated, which
   promotion contributed which cent to which line is not recoverable from the totals.
2. **Keep stage-1's single end-of-pricing allocation and split the aggregate share per promotion
   afterwards.** Rejected: re-deriving a per-promotion share from an aggregate rounds a second time,
   and the second rounding does not have to agree with the first — which is precisely the "residue"
   the owner says must never appear.
3. **A `rounding` adjustment to make the sums close.** Rejected by the owner, and unnecessary: the
   only rounding is inside `Money.percentage`, and its result *is* a delta, not an error to absorb.
4. **Make `Money` signed instead of adding `MoneyDelta`.** Rejected: non-negativity is the property
   I1 and I2 are enforced by, everywhere. Removing it from the type to serve a report would move the
   guarantee back into every call site. `decisions/0003` anticipated a *signed sibling*; this is it.
5. **Let promotions decide stacking (each knowing the others, or sorting themselves).** Rejected:
   not knowing about other promotions is the one thing the promotion seam exists to guarantee. The
   exclusion rule is an interaction rule, and interaction is the engine's single responsibility.
6. **A fourth `CodeStatus`? No — report a superseded code as `no_effect` with a sentence.** Rejected:
   support's response is different in kind ("your code was valid, the other one saved you more"), the
   superseding code must be machine-readable to be shown next to it, and I3 says we report what
   actually happened. Four statuses, four genuinely different conversations — no more.
7. **Decide the contest before the line stage, against the basket as submitted.** Rejected: an
   uncontested line code committed afterwards changes the base, so a cart-scoped winner would take
   less than it won with — a number in the explanation that never happened, which is the one thing
   the owner says makes the feature worthless. The contest sits at the stage boundary instead (§8).
8. **Let the contest winner keep its own canonical kind position instead of committing where it was
   compared.** Rejected for the same reason: anything committed between the comparison and the
   winner's slot makes the compared number a fiction. The cost of rejecting it is an ordering
   wrinkle (a non-stackable AMT can precede a stackable PCT), which is deterministic and stated.
9. **Two contests, one per stage, so a BOGO and a percentage never contend.** Rejected by the owner
   (Q12: *"if two of them can't be combined, the bigger one wins — it doesn't matter what kind they
   are"*), and it was the more complicated design: two comparison moments, two states, and a code
   that is non-stackable in name but combinable in fact whenever the other one happened to be of the
   other kind.
10. **`stackable` as a per-code numeric priority in the catalogue.** Rejected for the reason stage-1
   rejected ordering priorities in the data file: a structural rule in a file non-engineers edit
   daily means a typo silently re-prices the shop. `false` is a fact about the code; a priority is a
   rule about the system.

---

## 16. Product decisions — answered by the product owner

Nothing below is assumed. Each answer lives in exactly one named place, which is what kept this
revision small: one answer changed the design, one simplified it, two were handed back to us, and the
rest confirmed the draft. `decisions/0014` files them.

| Q | Question | The owner's answer | Where it lives | Effect on the draft |
|---|---|---|---|---|
| **Q11** | Does a non-stackable code exclude *every* other promotion, or only other non-stackable ones? | *"Non-stackable only means it can't sit next to another non-stackable one."* | the contender test in step 4 | **Confirmed.** A stackable code never contends and can never be superseded |
| **Q12** | Can a line-scoped code and a cart-scoped code contend? | *"If two of them can't be combined, the bigger one wins. It doesn't matter what kind they are."* | step 4 — one contest per cart | **Changed.** Contention is cross-scope, so the two stage-local contests became a single pipeline step at the stage boundary — the one moment both scopes can be honestly priced (§8). The rule got smaller as it got more general |
| **Q13a** | Do codes that resolved but did nothing appear in the explanation? | *"Wherever support will see it. Your call."* | step 7 (the outcome report) | **Ours, and decided:** they stay out of the explanation and in the per-code outcomes, which sit beside it in the same response. The explanation answers *why is this price what it is*; "COFFEE3 found only 2 coffees" explains a code, not the price |
| **Q13b** | Does a superseded cart-wide code appear on each line? | *"If it didn't change that line's price, it doesn't need to be on that line."* | `record_superseded` | **Changed, and simpler.** A `NOT_APPLIED` entry is written once, into the cart's explanation. A line's story now contains nothing but what moved that line |
| **Q14** | The comparison basis | *"Compare what each one actually takes off the basket in front of you."* | `choose_non_stackable` + step 4 | **Confirmed**, and now exact: every contender is proposed against the same basket — the one between the stages — clamped to what can actually be taken, and the winner commits there, so what it won with is what it took |
| **Q15** | The narrowing of order-independence | *"Same amounts every time. The first one they typed wins the tie, and it's fine that it shows."* | I5, `decisions/0013` | **Confirmed.** The narrowing is intended, not tolerated |
| **Q16** | Unknown and unavailable codes in the explanation | *"Wherever support will see it. Your call."* | step 1 + the outcome report | **Ours, and decided:** the same call as Q13a — reported in full as outcomes, never as adjustments. A code we do not run moved no money and has no place in an account of money that moved |
| **Q17** | A cart-wide promotion on a line | *"What that line's price actually went down by."* | `propose_cart` + `Money.allocate` | **Confirmed.** The share, which is what forces per-promotion allocation (§7) |
| **Q18** | The leftover cent | *"As long as it adds up, a cent here or there on a line is fine."* | `Money.allocate` | **Confirmed.** Largest-remainder, no rounding entry, sums exact |

**Q13a and Q16 were handed back to us** ("your call"), so they are recorded here as *our* decision
with its reason, not as an owner statement — the same treatment `decisions/0002` gave the entry-point
choice. The reason, in one line: an explanation is the account of the money that moved, in the order
it moved; every code the customer typed is accounted for regardless, one row each, in the outcomes
that travel with it. The single exception is a superseded code, which is in the explanation because a
choice between two possible prices *is* part of why this price is this price — and because the owner
asked for it by name.

**Nothing remains open.** No rule in this design now rests on a guess.

---

## 17. What the first sprint builds, and what it must prove

Build order follows dependency order, test-first, one decision at a time. Items marked **new** did
not exist in stage-1.

1. `money.py` — parse/format round-trip; half-up at the cent (12.55 × 10% → 1.26, 12.51 × 10% →
   1.25); underflow raises; `allocate` sums exactly, including the leftover-cent case and the
   all-zero-weights case. **new:** `MoneyDelta` sign handling, `total` over an empty sequence,
   `between` in both directions, `magnitude`, `format` ("-2.50", "+25.00", "0.00"), and
   `Money.after` raising when a delta would go below zero.
2. **new:** `explanation.py` — `opened_at` produces exactly one `LIST_PRICE` entry; `final` equals
   the list price when nothing was recorded; after any sequence of records,
   `net_delta == MoneyDelta.between(list_price, final)` **exactly** (property-style, over generated
   sequences, not only the worked examples); a `NOT_APPLIED` entry never moves `final`; each kind's
   shape rule is refused when violated; `steps()` yields the running amounts in order.
3. `cart.py` — validation rejects quantity 0 and negative, reports all problems, accepts an empty
   cart.
4. `promotions.py` — each kind's rule in isolation, including `free_units` at 0, below threshold, at
   threshold, and at two full groups.
5. `catalog.py` — every kind parses; each malformed shape is reported by code and field and disables
   only that code while the rest of the file loads (I7); `every = 1`/`0` rejected; duplicate
   definitions caught; unquoted float amounts rejected; a non-TOML file is the one fatal case.
   **new:** `stackable` defaults to true when absent, parses `false`, and a non-boolean value
   disables that one code and names the field.
6. `engine.py` — A1–A7 and B1–B5 exactly, plus the break cases below.
7. `cli.py` — exit codes (0 priced, 2 unsalvageable catalogue, 3 malformed cart), catalogue problems
   on stderr while `quote` still succeeds, `validate-catalog` non-zero on any problem, a JSON
   round-trip with every amount a string. **new:** the explanation arrays on the quote and on each
   line, signed delta strings, and `superseded_by` / `forgone` on an outcome.

**Break cases the engine must answer** — the exit criteria of the implementation objective, not a
wish list. Stage-1's list stands in full (empty cart with a code; empty code list; AMT larger than
the subtotal; AMT on a cart already at 0.00; two AMT codes exceeding the subtotal; PCT on a 0.00
subtotal; two 10% codes taking 19% not 20%; PCT and AMT giving the same total whichever order they
were typed; BOGO with its SKU absent; BOGO below, at, and two groups past its threshold; 6 units of a
1-in-3 → 2 free; two BOGOs on one SKU; one SKU on two lines at different prices → the cheapest units
are the free ones; a code entered twice; a lower-case code matching an upper-case entry; one broken
catalogue entry; a non-TOML file; an unknown code mixed with a good one; reversed code order giving
an identical quote), and this stage adds:

- **the sum, everywhere:** on every case above and below, each line's explanation and the cart's
  explanation satisfy `net_delta == between(list_price, final)` to the cent, and `Σ line.net ==
  total`;
- **agreement:** for every case, each reported figure equals the corresponding fold over the
  explanation — no figure is produced any other way;
- **order:** the cart explanation lists a line-stage adjustment before a cart-stage one (B2), and two
  cart-stage adjustments in canonical order;
- **two cart promotions on a multi-line cart:** each one's per-line shares sum exactly to its own
  cart-level delta (I10), and the line nets still sum to the total — the case where stage-1's single
  allocation and stage-2's per-promotion allocation would differ;
- **a leftover cent:** a cart-level discount over three lines whose proportional shares do not divide
  evenly — the extra cent lands on exactly one line, the shares still sum exactly, and there is no
  rounding entry;
- **B3, B4, B5 exactly**, and additionally: **three** non-stackable codes contending (one winner, two
  superseded, both naming the winner); a **three-way tie** (the first-entered wins, the other two are
  superseded by it);
- **cross-scope contention (Q12)** — a non-stackable BOGO against a non-stackable percentage, in both
  directions: the BOGO wins when the units it frees are worth more (B3′ in §12) and loses when they
  are not, and in each case the loser's `forgone` is the amount it was compared on;
- **the contest moment** — an *uncontested* line code applies before the contest, so a non-stackable
  BOGO on the same SKU sees fewer paid units, and a non-stackable percentage is compared against the
  subtotal that BOGO left, not against the submitted basket;
- **the ordering wrinkle** — a non-stackable AMT and an uncontested stackable PCT on one cart: the
  AMT commits at the contest, the PCT then takes its percentage of what remains, and the explanation
  lists them in exactly that order;
- **a non-stackable code that does not qualify** — e.g. TENOFF alongside a non-stackable SAVE10 on a
  cart already reduced to 0.00: neither supersedes the other, both report `no_effect`, and no
  `NOT_APPLIED` entry is written;
- **a lone non-stackable code** — applies normally, nothing is superseded;
- **a stackable code is never superseded** (Q11) — a non-stackable TENOFF beside a stackable SAVE10:
  both apply, in order, and neither is marked not-applied;
- **a non-stackable code entered twice** — counted once (Q4), so it enters the contest once and the
  repeat is reported as entered twice, not as superseded by itself;
- **a non-stackable code beaten by one that is clamped** — contenders are compared on the clamped,
  actually-takeable amount, so a 10.00 fixed discount on a 4.00 basket contends with −4.00, not
  −10.00;
- **a superseded code is recorded once** (Q13b) — the `NOT_APPLIED` entry is in the cart's
  explanation and in **no** line's explanation, every line's deltas still sum to that line's own
  difference, and the totals are untouched;
- **only movement is explained** (Q13a, Q16) — an unknown code, a temporarily-unavailable code and a
  code that found nothing to do each produce a full `CodeOutcome` and **no** explanation entry, at
  either level;
- **catalogue continuity** — a catalogue with no `stackable` anywhere prices every stage-1 case to
  the identical amount (B6).
