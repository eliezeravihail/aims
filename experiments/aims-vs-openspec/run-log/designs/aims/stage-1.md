# Cart pricing — architecture (stage 1)

**Status:** design deliverable of the first design objective, revised after the product owner answered
the ten open questions (§13). No implementation code exists yet; this is the shape the first sprint
builds against. No product decision is now assumed: every rule below is either stated by the product
owner or is a structural choice recorded in `decisions/`.

**Substrate (given, not chosen):** Python 3.11+, standard library only, single process, single
currency, no UI/network/database/persistence. `decimal.Decimal` permitted. Entry-point shape was left
to us — see §12 and `decisions/0002`.

---

## 1. The idea in one paragraph

A cart is priced in **two stages, because promotions act on two different things.** BOGO makes whole
*units* free, which changes what a *line* costs. PCT and AMT take money off the *cart*. Case A5
(COFFEE 4.00×4 + WIDGET 12.50×1, COFFEE3 + SAVE10 → 22.05) is only reachable if the units settle
first (16.00 → 12.00, subtotal 24.50) and the percentage then works on what is left (−2.45). So the
engine runs every line promotion, sums the lines into a subtotal, runs every cart promotion against
that subtotal, and finally allocates the cart discount back across the lines so the lines still sum to
the total. Each stage runs against a **ledger** that owns the clamp — "you may not take more than
remains" — so no promotion can produce a negative line or a negative cart, whatever its author does.
Promotions themselves are dumb about all of this: each one answers exactly one question about its own
rule and knows nothing about ordering, clamping, other promotions, or where its definition came from.

```
catalogue file (TOML, business-edited)
        │  catalog.load_catalog()          ← the only module that knows the file format
        ▼
  PromotionCatalog ── lookup(code) ──┐
                                     │
cart (customer id, lines, codes) ────┤
        │                            ▼
        │                    engine.price_cart()
        │                            │
        │   ┌────────────────────────┼─────────────────────────────┐
        │   │ 1 resolve codes        │ unknown / disabled / duplicate reported, never fatal
        │   │ 2 canonical order      │ result independent of typing order
        │   │ 3 LINE stage           │ UnitLedger per line  → free units
        │   │ 4 subtotal             │ Σ line nets
        │   │ 5 CART stage           │ MoneyLedger          → clamped discounts
        │   │ 6 allocate             │ Money.allocate       → lines sum to total
        │   │ 7 report               │ one outcome per submitted code
        │   └────────────────────────┼─────────────────────────────┘
        ▼                            ▼
                                   Quote  ──► cli.py serializes to JSON (the only module that knows JSON)
```

---

## 2. Module map

One sentence per module, stating **the single reason it would change**. If two reasons fit in one
sentence with an "and", the module is wrong.

| Module | Changes when… |
|---|---|
| `pricing/money.py` | the currency's arithmetic, rounding, or presentation rules change |
| `pricing/cart.py` | what a caller may ask us to price changes |
| `pricing/promotions.py` | a promotion **kind**'s own rule is added or changed |
| `pricing/catalog.py` | where promotion definitions come from, or how they are written, changes |
| `pricing/quote.py` | what we report back changes |
| `pricing/engine.py` | how promotions interact — order, clamping, allocation, reporting — changes |
| `pricing/cli.py` | the wire format or the command surface changes |
| `promotions.toml` | the business adds or retires a **code** (no engineer, no deploy) |

Nothing above imports downward into `cli.py`, and nothing except `catalog.py` imports `tomllib`,
and nothing except `money.py`/`catalog.py` imports `decimal`.

---

## 3. Money — the one place that rounds

Every amount in this product is non-negative (`goals.md` non-goals: no refunds, no credits). That is
not a coincidence to be re-checked at every call site; it is a property of the type.

```python
# pricing/money.py

class Money:
    """A non-negative amount of the single currency, held as an integer number of cents."""

    __slots__ = ("_minor",)

    @classmethod
    def parse(cls, text: str) -> "Money": ...       # "12.50" -> 1250; exact, via Decimal; rejects "-1.00", "1.005"
    @classmethod
    def zero(cls) -> "Money": ...

    def __add__(self, other: "Money") -> "Money": ...
    def __sub__(self, other: "Money") -> "Money": ...
        # raises ArithmeticError on underflow. Pricing never calls this unguarded: it subtracts
        # through a ledger that clamps first (§6). The raise is the tripwire, not the policy.
    def times(self, whole_units: int) -> "Money": ...   # exact; no rounding possible

    def percentage(self, percent: "Percent") -> "Money": ...
        # THE ONLY ROUNDING POINT IN THE SYSTEM. Exact rational × percent, ROUND_HALF_UP to the cent.

    def allocate(self, weights: "Sequence[Money]") -> "list[Money]": ...
        # Splits self into len(weights) parts, proportional to weights, summing EXACTLY to self.
        # Largest-remainder: floor each share, hand the leftover cents to the largest fractional
        # remainders, ties broken by index. Weights summing to zero -> all-zero result (self must
        # then be zero; asserted).

    def is_zero(self) -> bool: ...
    def format(self) -> str: ...                     # always 2 decimal places: "12.50", "0.00"
    # __eq__, __lt__, __hash__, __repr__


class Percent:
    """A percentage between 0 (exclusive) and 100 (inclusive), exact to the written digits."""
    @classmethod
    def parse(cls, text: str) -> "Percent": ...      # "10", "7.5"; rejects "0", "-5", "120", "abc"
    def format(self) -> str: ...
```

Why these and not `Decimal` everywhere or a bare `int` of cents: `decisions/0003`. The short version —
with `Decimal` everywhere, sub-cent values stay representable and every operation has to remember to
quantize, so "who rounded, and when" is asked at every call site; with a bare `int`, the rounding rule,
the non-negativity rule, the 2dp formatting rule and the exact-split rule have no owner and get
re-implemented per caller.

`allocate` is small and easy to overlook, and it is the entire reason invariant **I6** (line costs sum
to the cart total) is achievable rather than aspirational. Worked: a 1.50 cart discount over lines of
10.00 and 5.01 → shares 1.00 and 0.50 (floors 0.99 and 0.50, one leftover cent to the larger
remainder), lines 9.00 and 4.51, sum 13.51 = 15.01 − 1.50. ✔

---

## 4. The request domain

```python
# pricing/cart.py

class Sku:
    """A stock identifier. Normalised once, here, so promotion targeting is a comparison, not a rule."""
    @classmethod
    def of(cls, raw: str) -> "Sku": ...              # strips, rejects empty; case rule per Q7

@dataclass(frozen=True)
class CartLine:
    sku: Sku
    unit_price: Money
    quantity: int                                    # >= 1, validated here (see §11, subtractive pass)

    def gross(self) -> Money:                        # unit_price.times(quantity)
        ...

@dataclass(frozen=True)
class Cart:
    customer_id: str                                 # carried, echoed, read by nothing (goals.md non-goals)
    lines: tuple[CartLine, ...]
    codes: tuple[str, ...]                           # exactly as the customer typed them

    # Construction raises InvalidCartError with every problem found, not the first.
```

An empty cart is **valid** and prices to 0.00 with its codes reported as having no effect; that is a
customer emptying their basket with a code still in the box, not an error.

The cart knows nothing about promotions. It is asked only for its lines and their gross.

---

## 5. Promotions — two scopes, because there are genuinely two concepts

```python
# pricing/promotions.py

class PromotionCode:
    """A code as it identifies a promotion — normalised once (Q7), so lookup is a dict hit."""
    @classmethod
    def of(cls, raw: str) -> "PromotionCode": ...

class Promotion(Protocol):
    """What every promotion has in common: an identity, and a phrase for the outcome report."""
    @property
    def code(self) -> PromotionCode: ...
    def describe(self) -> str: ...                   # "10% off the cart", "buy 3 get 1 free on COFFEE"

class LinePromotion(Promotion, Protocol):
    """A promotion that makes whole units of one SKU free."""
    @property
    def target(self) -> Sku: ...
    def free_units(self, paid_units: int) -> int: ...
        # Given how many units of my SKU are still being paid for, how many become free?
        # Returns 0 when the promotion does not bite. Must never exceed paid_units.

class CartPromotion(Promotion, Protocol):
    """A promotion that takes money off the cart."""
    def requested_discount(self, remaining: Money) -> Money: ...
        # How much I WANT to take, given what is left. What is actually taken is the ledger's
        # decision, never mine (§6).
```

Today's three kinds — each a small frozen dataclass owning one rule and nothing else:

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
    every: int                       # N >= 2, validated by the catalogue loader
    def free_units(self, paid_units: int) -> int:
        return paid_units // self.every
```

**The BOGO rule, as the product owner stated it (Q5): "with three of them in the cart, one is free."**
So `every = 3` means three COFFEE cost two — 3 units → 1 free, 4 → 1, 6 → 2. Both the type and the
catalogue field are named for that reading (`every`, not `buy`), because the draft's other reading —
groups of N+1, the 4th one free — fits cases A4 and A5 equally well and diverges only at 6 units. A
field called `buy` would have left the shop one plausible misreading away from giving away an extra
coffee, and nothing in the file would have said which was meant. `every = 2` is the classic
buy-one-get-one-free; `every = 1` would make everything free and is rejected by the loader.

Each kind also implements `describe()` — the phrase the outcome report shows the customer ("10% off the
cart", "1 free for every 3 COFFEE"). It belongs on the promotion because only the promotion knows its
own parameters; the engine must never assemble that sentence from a kind tag and a number.

**Why two interfaces rather than one `Promotion.apply(cart)`.** The generality of a type crossing an
interface is pinned from both ends (design-principles §2): it must carry everything the consumer needs
(floor) and commit to nothing a producer cannot honestly supply (ceiling). Here no single signature
meets both. A cart promotion has no line to speak about — forcing it to return line-level adjustments
makes it fabricate an attribution it does not have. A line promotion must not see the cart — handing it
the whole cart lets it reach past its own SKU, and then "which promotion changed this line?" stops
having an answer. When the two bounds cannot both be met, that is evidence of **two concepts**, and the
resolution is two types with a shared supertype for the common part (identity and description) — not
one lossy compromise. Cart scope already has two real implementations today (PCT, AMT), so it is not a
decorative interface.

Line scope has exactly one implementation today, which is a fair challenge (§2's `ICat` trap, and the
subtractive pass in §11). It earns its place anyway, and not on the grounds that more kinds may come:
**it is the seam that keeps "buy 3 get 1 free" out of the engine.** Delete it and the engine has to
know what N means, and the rule that defines the product's most intricate promotion loses its owner. A
second implementation is also easy to describe concretely rather than speculatively — "every 3rd unit
of SKU X is half price" needs the same routing and the same unit ledger and a different rule — which is
§2's own test for whether an abstraction is real.

**`target` as a routing key, and Tell-Don't-Ask.** The engine reads `promotion.target` to pick which
line ledger to consult. That is the engine learning *which* ledger, never *how much* — the amount is
only ever obtained by telling the promotion "here is what is still paid for; what becomes free?". The
alternative considered was `promotion.apply(all_ledgers)`, which is purer Tell-Don't-Ask but widens
what any promotion can touch, for no gain today.

---

## 6. The engine — sequencing, clamping, allocation, reporting

```python
# pricing/engine.py  (public seam of the library)

def price_cart(cart: Cart, catalog: PromotionCatalog) -> Quote: ...
```

Internal collaborators (not public):

```python
class UnitLedger:
    """Units of one cart line that are still being paid for."""
    def __init__(self, line: CartLine): ...
    @property
    def paid_units(self) -> int: ...
    def free(self, units: int) -> int: ...           # clamps to what remains; returns what was freed

class MoneyLedger:
    """Money still takeable from the cart."""
    def __init__(self, subtotal: Money): ...
    @property
    def remaining(self) -> Money: ...
    def take(self, requested: Money) -> Money: ...   # clamps to `remaining`; returns what was taken

def canonical_order(promotions: Iterable[Promotion]) -> list[Promotion]: ...
    # The single home of the ordering rule (I5, Q2, Q3): sort by (stage, kind rank, code).
```

### The pipeline, step by step, with the owner of each rule

| # | Step | Owner | Rule |
|---|---|---|---|
| 1 | **Resolve codes** | engine | Each submitted code is normalised (case-insensitive, trimmed — Q7) and looked up. Found → promotion. Defined but misconfigured → `no_effect`, "temporarily unavailable" (Q6). Not found → `unknown`. Already resolved this cart → counted once, and the repeat is reported as entered twice (Q4). Nothing raises: I3. |
| 2 | **Canonical order** | `canonical_order` | Line stage before cart stage; within the cart stage PCT before AMT; ties by code, which is unique — a total order, so I5 holds. The product owner's requirement (Q2) is not *which* order but that the same cart always prices the same, so the order is ours and is pinned here, in one function, rather than emerging from the customer's typing. |
| 3 | **Line stage** | engine + `UnitLedger` | For each line promotion in order: total the still-paid units of its target SKU across all lines of that SKU, ask `free_units`, then free that many units from those lines **cheapest unit price first** (Q8 — the same SKU does appear on two lines at two prices, and the cheap ones are the free ones). A second BOGO on the same SKU therefore sees only what is still paid for, and can never free more units than exist. |
| 4 | **Subtotal** | engine | `subtotal = Σ (gross − line_discount)`. This, not the gross, is what cart promotions apply to — that is the whole of A5. |
| 5 | **Cart stage** | engine + `MoneyLedger` | Ledger starts at the subtotal. For each cart promotion in order: `taken = ledger.take(promo.requested_discount(ledger.remaining))`. Clamping here is the single enforcement point for I1 and I2. Passing `remaining` — not the original subtotal — is what makes two 10% codes take **19%, not 20%** (Q3): the second sees what the first left. |
| 6 | **Total** | engine | `total = ledger.remaining`. Non-negative by construction, not by a final `max(0, …)` — A7 cannot be got wrong. |
| 7 | **Allocate** | `Money.allocate` | The cart discount is split across lines in proportion to each line's post-line-promotion net, exactly. This is what makes `PricedLine.net` the invoice figure the product owner asked for (Q1) and the lines add up to the total. I6 holds by construction. |
| 8 | **Report** | engine | One `CodeOutcome` per submitted code, in submission order: `applied` with the amount actually taken (or the value of the freed units), `no_effect` with a reason, or `unknown`. |

**Zero-effect reporting.** A promotion that resolves and evaluates to nothing is reported
`no_effect` with a reason a support agent can read out: "COFFEE3 gives 1 free for every 3 COFFEE;
there are 2 in the cart", "TENOFF — nothing left to discount", "SAVE10 was entered twice and counted
once" (Q4), "SUMMER15 is temporarily unavailable" (a code whose catalogue entry is broken — Q6). A promotion that took *some* of what it wanted is `applied`
with what it actually took (A7: TENOFF on a 1.00 cart is `applied 1.00`, and the total is 0.00). Three
statuses, because the caller has exactly three responses: show the saving, tell the customer the code
did nothing here, tell the customer the code is not one of ours.

---

## 7. The answer

```python
# pricing/quote.py

class CodeStatus(Enum):
    APPLIED = "applied"
    NO_EFFECT = "no_effect"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class CodeOutcome:
    code: str                    # exactly as typed, so the customer recognises it
    status: CodeStatus
    amount: Money | None         # what it actually saved, when APPLIED
    detail: str                  # description when applied; the reason otherwise; "" for UNKNOWN

@dataclass(frozen=True)
class PricedLine:
    sku: Sku
    unit_price: Money
    quantity: int
    free_units: int
    gross: Money                 # unit_price × quantity
    line_discount: Money         # unit_price × free_units
    cart_discount_share: Money   # this line's allocated share of cart-level discounts
    net: Money                   # gross − line_discount − cart_discount_share
                                 # ← THE line price: what the customer pays for this line, the number
                                 #   on the invoice (Q1). Σ net == total, exactly (I6).

@dataclass(frozen=True)
class Quote:
    customer_id: str
    lines: tuple[PricedLine, ...]
    subtotal: Money              # Σ gross
    line_discount_total: Money
    cart_discount_total: Money
    total: Money                 # subtotal − line_discount_total − cart_discount_total, ≥ 0
    codes: tuple[CodeOutcome, ...]
```

`PricedLine` carries four figures rather than one because the product owner's answer names `net` as
the line price (Q1) while an invoice, a partial refund and a support conversation each need to see
where it came from — the gross, what the line's own promotion took, and what share of the cart-level
discount landed here. Recomputing any of those from the others is not possible once rounding and
allocation have happened, which is exactly why they are reported rather than derived
(`decisions/0006`, `decisions/0007`).

---

## 8. The catalogue

```toml
# promotions.toml — edited by the business. Amounts and percentages are QUOTED; an unquoted
# 10.00 would be a binary float, and money is never a float.

[SAVE10]
kind    = "PCT"
percent = "10"

[TENOFF]
kind   = "AMT"
amount = "10.00"

[COFFEE3]
kind  = "BOGO"
sku   = "COFFEE"
every = 3         # one free for every 3 in the cart: 3 cost 2, 6 cost 4
```

```python
# pricing/catalog.py

@dataclass(frozen=True)
class CatalogProblem:
    code: str | None                 # the code whose entry is broken; None for a whole-file problem
    detail: str                      # names the field and what is wrong with it

class PromotionCatalog:
    def lookup(self, code: PromotionCode) -> Promotion | None: ...
    def is_disabled(self, code: PromotionCode) -> bool: ...   # defined in the file, but unusable
    @property
    def problems(self) -> tuple[CatalogProblem, ...]: ...
    def __len__(self) -> int: ...

def load_catalog(source: str | os.PathLike | IO[bytes]) -> PromotionCatalog: ...
    # A broken ENTRY is skipped, recorded in `problems`, and its code is marked disabled — the
    # shop keeps selling on every other code (Q6).
    # Raises CatalogError only when there is nothing to salvage: the file is unreadable or is not
    # valid TOML, so no entry can be trusted.

class CatalogError(Exception):
    problems: tuple[CatalogProblem, ...]

_PARSERS: dict[str, Callable[[PromotionCode, Mapping[str, Any]], Promotion]]
    # kind -> parser. THE registration point for a new kind. Adding a kind = one class in
    # promotions.py + one entry here. Nothing else in the system changes.
```

The loader is the only module that knows about TOML, files, or the `kind` column. It validates what a
promotion cannot validate about itself: that the kind exists, that required fields are present and
well-formed, that `every >= 2`, that a percentage is in range, that an amount is non-negative, and
that no code is defined twice. `decisions/0005`, `decisions/0009`.

**One typo must not stop the shop selling (Q6 — invariant I7).** So a bad entry is contained to its own code rather
than failing the load: the catalogue is still usable, it carries the list of problems for the
business, and the broken code is *disabled* rather than *absent*. The distinction is deliberate and is
the reason `is_disabled` exists — a customer typing a code we genuinely do not run and a customer
typing a real code that our own file has broken are two different conversations for support, and I3
says we report what actually happened. The problems list is printed for the business (§9); it is never
part of the customer-facing quote.

---

## 9. The CLI (a serialization boundary, nothing more)

```
$ python -m pricing quote --catalog promotions.toml < cart.json > quote.json
$ python -m pricing validate-catalog --catalog promotions.toml
```

```jsonc
// cart.json (in)
{ "customer_id": "c-123",
  "lines": [ { "sku": "WIDGET", "unit_price": "12.50", "quantity": 2 } ],
  "codes": ["SAVE10"] }

// quote.json (out) — every amount a 2dp string, never a JSON number
{ "customer_id": "c-123",
  "lines": [ { "sku": "WIDGET", "unit_price": "12.50", "quantity": 2, "free_units": 0,
               "gross": "25.00", "line_discount": "0.00",
               "cart_discount_share": "2.50", "net": "22.50" } ],
  "subtotal": "25.00", "line_discount_total": "0.00", "cart_discount_total": "2.50",
  "total": "22.50",
  "codes": [ { "code": "SAVE10", "status": "applied", "amount": "2.50", "detail": "10% off the cart" } ] }
```

Exit codes for `quote`: `0` priced — including carts with unknown codes, and including a catalogue
with broken entries, whose problems go to **stderr** so the business sees them while the shop keeps
selling (Q6, I3, I7); `2` the catalogue file is unreadable or not valid TOML, so nothing could be
salvaged; `3` the cart input is malformed. `validate-catalog` is the inverse: it exists to be strict,
and exits non-zero if the file has any problem at all, so an edit is checked before it ships.

Two error types exist (`CatalogError`, `InvalidCartError`) because there are exactly two distinct
responses: fix the data file, or fix the request. A broken *entry* is not an exception at all — it is
data in `PromotionCatalog.problems`, because the caller's response to it is to carry on. No further
error hierarchy is invented for errors nobody catches separately (design-principles §7).

`validate-catalog` exists because the people editing the catalogue are not engineers and must not
learn about a typo from a customer's failed checkout (`decisions/0002`).

---

## 10. The required cases, traced through the design

All amounts in cents internally; shown here as written.

| # | Trace | Result |
|---|---|---|
| **A1** | no codes. Line gross 25.00, no line discount, subtotal 25.00, no cart stage, allocation 0.00. | line **25.00**, total **25.00** ✔ |
| **A2** | SAVE10 resolves to `PercentOffCart(10)`. Subtotal 25.00 → requested 2.50 → ledger takes 2.50. Allocation: one line, share 2.50. | line net **22.50**, total **22.50** ✔ |
| **A3** | TENOFF → `AmountOffCart(10.00)`. Requested 10.00 ≤ remaining 25.00 → taken 10.00. | total **15.00** ✔ |
| **A4** | COFFEE3 → `OneFreeInEveryN(COFFEE, every=3)`. Paid units 4 → `free_units = 4 // 3 = 1` → UnitLedger frees 1 → line discount 4.00, line net 12.00, subtotal 12.00, no cart stage. | total **12.00** ✔ |
| **A5** | Line stage: COFFEE 4 units → 1 free → COFFEE net 12.00. Subtotal 12.00 + 12.50 = **24.50**. Cart stage: SAVE10 → 10% of 24.50 = 2.45, taken 2.45. Total 22.05. Allocation of 2.45 by weights (12.00, 12.50): shares 1.20 and 1.25 (exact, no remainder). Lines 10.80 and 11.25, sum 22.05. | total **22.05** ✔, and I6 holds |
| **A6** | "NOPE" normalises, lookup misses → `CodeOutcome(code="NOPE", status=UNKNOWN)`. Pricing continues untouched. | total **12.50**, NOPE reported **unknown** ✔ |
| **A7** | Subtotal 1.00. TENOFF requests 10.00; `MoneyLedger.take` clamps to remaining 1.00 → taken 1.00, remaining 0.00. Outcome `applied 1.00`. Allocation: 1.00 over weight (1.00) → 1.00. Line net 0.00. | total **0.00**, not negative ✔ — structurally, not by a final clamp |

---

## 11. The subtractive pass

Every type, guard and abstraction above was put to one question: *if I deleted it, would the ownership
of a rule the product needs today actually be damaged?*

**Kept, with the force that keeps them:**
- `Money` — owns rounding, non-negativity, 2dp presentation, exact splitting. Four rules, one home.
- `Percent` — owns range validity; without it "is 120% legal?" is re-answered per caller.
- `Sku`, `PromotionCode` — both are *matched*, so normalisation is a rule (Q7) that must have one home,
  or "save10" and "SAVE10" silently diverge between the catalogue and the cart.
- The two scope interfaces — see §5.
- `UnitLedger`, `MoneyLedger` — they *are* invariants I1/I2. Delete them and clamping becomes every
  promotion author's responsibility, which is how A7 becomes a bug.
- `canonical_order` — it *is* invariant I5, and the product owner asked for exactly that (Q2).
- `CatalogProblem` / `is_disabled` — the product owner's answer to Q6 ("tell us which code is broken
  and carry on") *is* their present force: without them a broken entry is indistinguishable from a
  code we never ran, and the business is told nothing.

**Cut, and why:**
- `Quantity` as a value type — one rule (≥ 1) used at one construction site. `CartLine` validates it;
  a wrapper class would be a label on an int.
- `CustomerId` as a value type — carried, echoed, read by nothing (`goals.md`). A type with no rule
  and no behaviour is rent paid to nobody. It earns a type the day something is decided from it.
- `Currency` / a money amount tagged with a currency — one currency, stated. Adding the tag now buys a
  future nobody has asked for and makes every amount noisier today.
- A `PromotionKind` enum in the domain — the kind is a catalogue-file column, and it already has a home
  in the parser table. An enum in the domain would mean the engine switching on kind, which is exactly
  what the two interfaces exist to prevent.
- A `Discount` object threaded through the stages — the ledgers already hold what was taken, and the
  outcome report already carries it. A third representation of the same fact is drift waiting to happen.
- A promotion-`priority` field in the catalogue file — ordering is a structural rule (I5); putting it
  in a file that non-engineers edit daily means a typo silently re-prices the shop.
- An error hierarchy beyond the two types — nothing catches a third one distinctly.

---

## 12. Alternatives rejected (structural)

1. **One flat `Promotion.apply(cart) -> cart` pipeline.** Rejected: hands every promotion the entire
   cart, makes non-negativity everyone's job, and turns the A5 ordering into an accident of list
   position rather than a stated rule. `decisions/0004`.
2. **`Decimal` end to end.** Rejected: sub-cent values stay representable, so rounding becomes a
   question asked at every call site. `decisions/0003`.
3. **A local HTTP endpoint as the entry point.** Rejected: adds a transport, a lifecycle, and a
   catalogue-freshness rule to a product that asked for none of the three; the library can be wrapped
   in whatever the storefront already runs. `decisions/0002`.
4. **Promotion definitions as a Python module.** Rejected: makes every promotion edit a code deploy —
   the one thing the product owner explicitly refuses. `decisions/0005`.
5. **Clamping the total once at the end (`max(0, total)`).** Rejected: it makes A7 pass while leaving
   each *intermediate* step free to go negative, so the per-code "what did this code actually save"
   report becomes fiction. Clamping per application is what makes the report true.

---

## 13. Product decisions — answered by the product owner

Nothing below is assumed any longer. Each answer lives in exactly one named place, which is what kept
the revision small: three answers changed the design, the rest confirmed it.

| Q | Question | The owner's answer | Where it lives | Effect on the draft |
|---|---|---|---|---|
| **Q1** | Does a line price include its share of cart-level discounts? | "What the customer actually pays for that line — the number on the invoice. The line prices have to add up to the total." | step 7 + `Money.allocate`; `PricedLine.net` | **Confirmed.** `net` is now named as the invoice figure; I6 was already the design's invariant |
| **Q2** | With a PCT and an AMT on one cart, which applies first? | "Whatever order you pick, the answer has to be the same every time for the same cart." | `canonical_order` | **Confirmed, and re-read:** the requirement is determinism (I5), not a particular order. We keep percentages first and pin it in one function |
| **Q3** | Two 10% codes — 19% or 20%? | "19%, not 20%." | step 5 passing `ledger.remaining` | **Confirmed.** Each cart promotion sees what the previous one left |
| **Q4** | The same code entered twice? | "Count it once, and tell the customer it was entered twice." | step 1 + the outcome report | **Confirmed**, with the message duty made explicit: the repeat is reported as entered-twice, not silently dropped |
| **Q5** | Is the 4th free, or one free for every 3? | "With three of them in the cart, one is free." | `OneFreeInEveryN.free_units` | **Changed.** `free = paid // every`, not `paid // (buy + 1)`; type and catalogue field renamed so the file cannot be misread. A4/A5 still hold; 6 coffees now cost 4, not 5 |
| **Q6** | A typo in the promotions file? | "One typo shouldn't stop the shop selling. Tell us which code is broken and carry on with the rest." | `load_catalog`, `CatalogProblem`, `is_disabled` | **Changed.** Entry-level problems are contained and reported instead of fatal; only an unparseable file still fails. A broken code is reported *disabled*, not *unknown* |
| **Q7** | Case sensitivity? | "Customers type them however they like — SAVE10 and save10 are the same code." | `PromotionCode.of`, `Sku.of` | **Confirmed** |
| **Q8** | Same SKU on two lines at different prices? | "Yes, that happens. The cheapest ones are the free ones." | step 3 | **Confirmed**, and now a stated requirement rather than a guess |
| **Q9** | Validity windows, usage limits? | "Not now — build for today." | `goals.md` non-goals | **Confirmed as a non-goal** — no dormant date field, no disabled machinery |
| **Q10** | Anything depending on the customer id? | "Not now — build for today." | `goals.md` non-goals | **Confirmed as a non-goal** — the id is carried and echoed; `CustomerId` stays cut (§11) |

Q9 and Q10 are recorded as **owner-stated non-goals**, not as assumptions: the design does not build a
seam for either. When one arrives, Q9 is a field on a catalogue entry plus a filter in the resolve
step, and Q10 is a predicate at the same step — both inside boundaries that already exist, which is
the argument for not pre-building them.

Two consequences of Q2 + Q3 worth stating plainly, because they are now *our* choice rather than an
open question: SAVE10 + TENOFF on a 25.00 cart is 12.50 (percentage first), and SAVE10 + SAVE10 is
20.25 on the same cart. Both are pinned by one function and one argument respectively, and both are
recorded in `decisions/0008`.

---

## 14. What the first sprint builds, and what it must prove

The build order follows the dependency order, test-first, one decision at a time:

1. `money.py` — parse/format round-trip; half-up at the cent (12.55 × 10% → 1.26, 12.51 × 10% → 1.25);
   underflow raises; `allocate` sums exactly, including the leftover-cent case and the all-zero-weights
   case.
2. `cart.py` — validation rejects quantity 0 and negative, reports all problems, accepts an empty cart.
3. `promotions.py` — each kind's rule in isolation, including `free_units` at 0, below threshold, at
   threshold, and at two full groups.
4. `catalog.py` — every kind parses; each malformed shape is reported by code and field and disables
   only that code while the rest of the file loads (I7); `every = 1` and `every = 0` are rejected;
   duplicate code definitions are caught; an unquoted float amount is rejected rather than silently
   accepted; a non-TOML file is the one fatal case.
5. `engine.py` — A1–A7 exactly, plus the break cases below.
6. `cli.py` — the exit codes (0 priced, 2 unsalvageable catalogue, 3 malformed cart), catalogue
   problems on stderr while `quote` still succeeds, `validate-catalog` non-zero on any problem, and a
   JSON round-trip with every amount a string.

**Break cases the engine must answer** (these are the exit criteria of the implementation objective,
not a wish list): empty cart with a code; a code list that is empty; AMT larger than the subtotal
(A7); AMT on a cart already reduced to 0.00 → `no_effect`, never negative; two AMT codes together
exceeding the subtotal; PCT on a 0.00 subtotal; **two 10% codes taking 19%, not 20% (Q3)**; **PCT and
AMT together giving the same total whichever order they were typed in (Q2, I5)**; BOGO whose SKU is
absent → `no_effect` with a reason; BOGO below threshold (2 units of a 1-in-3 → 0 free); BOGO at
exactly the threshold (**3 units → 1 free: three cost two**); **6 units of a 1-in-3 → 2 free, which is
the case that tells Q5's two readings apart**; two BOGOs on the same SKU (free units never exceed
quantity); **the same SKU on two lines at different prices → the cheapest units are the free ones
(Q8)**; the same code twice → counted once and reported as entered twice (Q4); a code typed in lower
case matching an upper-case catalogue entry (Q7); **a catalogue with one broken entry → every other
code still prices, the broken one is reported disabled, and the problem names the code and field
(Q6)**; a catalogue that is not valid TOML → the only fatal case; an unknown code mixed with a good one
(A6); codes submitted in reversed order producing an identical quote (I5); and, on every one of the
above, `Σ line.net == total` (I6) and `total ≥ 0` (I1).
