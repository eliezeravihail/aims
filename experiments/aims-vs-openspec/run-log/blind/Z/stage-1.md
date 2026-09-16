# Cart Pricing Service — Architecture (Stage 1)

Status: **stage 1 closed.** All fifteen open questions answered by the product owner and folded in (§13);
no product decision in this document is a guess. No implementation.
Substrate: Python 3.11+, standard library only, single process, single currency, no persistence.

---

## 1. What this service is

One question, answered purely: **given a cart and some codes, what does each line cost and what does the
cart cost?**

It is a *calculator*, not a workflow. It holds no state between calls, talks to nothing, and has exactly
two inputs — the **cart** (from the caller, per request) and the **promotion catalog** (a file the product
owner edits). That shape is the single most important structural fact about the system, and everything
below follows from it:

- A pure function `price(cart, catalog) -> Quote` is the whole product. Everything else is an adapter.
- Because it is pure, it is exhaustively testable without fixtures, clocks, servers or mocks.
- Because the catalog is data, adding a code is an edit, not a deploy — which is what the PO asked for.

### 1.1 Entry point: library first, thin CLI adapter

**Decision.** Ship a library (`pricing.price`) with a thin CLI wrapper. Not an HTTP endpoint.

The substrate forbids the network, so a "local HTTP endpoint" would only be a loopback socket wrapping the
same function while adding a server lifecycle, port config, request framing and a second error channel to
get right. The caller is an online store that will eventually call this over its own transport; handing it
a library keeps that choice open and keeps this codebase free of transport concerns. The CLI exists so the
PO can price a cart and lint the catalog without an engineer:

```
python -m pricing price    --catalog promos.toml --cart cart.json   # JSON quote on stdout
python -m pricing validate --catalog promos.toml [--strict]         # lint the promo file
python -m pricing explain  --catalog promos.toml --cart cart.json   # human-readable trace
```

If HTTP is later required, it is a new adapter module over the same `price()` call, with no change to the
core. That is the intended seam, not a hypothetical one.

---

## 2. The contract (the part that gets judged first)

Everything crossing a boundary is an immutable, `frozen=True` dataclass. Money is `decimal.Decimal`,
never `float`, and never at the boundary as a float — see §5.

### 2.1 Input

```python
@dataclass(frozen=True)
class CartLine:
    sku: str                 # non-empty, case-sensitive
    unit_price: Decimal      # >= 0, exactly 2 dp (list price, per unit)
    quantity: int            # >= 1

@dataclass(frozen=True)
class Cart:
    customer_id: str
    lines: tuple[CartLine, ...]
    codes: tuple[str, ...]   # as typed by the customer, in entry order
```

Lines are **not** keyed by SKU: the same SKU may legitimately appear twice (different price tiers, gift
wrap, split shipments). Promotions that care about SKU aggregate across lines themselves (§6.3).

### 2.2 Output

```python
@dataclass(frozen=True)
class LineQuote:
    sku: str
    quantity: int
    unit_price: Decimal
    gross: Decimal                       # unit_price * quantity
    line_discount: Decimal               # from line-targeted promos (BOGO)
    allocated_cart_discount: Decimal     # this line's share of cart-wide promos
    net: Decimal                         # gross - line_discount - allocated_cart_discount, >= 0
    attribution: tuple[Attribution, ...] # (code, amount) pairs making up the two discount figures

@dataclass(frozen=True)
class Quote:
    currency: str
    lines: tuple[LineQuote, ...]         # same order and arity as cart.lines
    gross_subtotal: Decimal
    total_discount: Decimal
    total: Decimal                       # >= 0
    code_results: tuple[CodeResult, ...] # one per submitted code, in submission order
```

**`net` is the line price** — settled by the PO: it is what the customer actually pays for that line, the
number on the invoice, and the line prices add up to the total (invariant I3). Every cart-wide discount is
therefore *allocated* down to the lines (§5.3); no other output shape can satisfy "they have to add up".

The other three money fields are the audit trail behind that one number, not alternative answers to it.
They are published because the moment anyone refunds a line, prints a receipt, or asks "why is this
12.00 and not 12.50", the breakdown is needed and a schema change is the expensive way to get it.
`line_discount` and `allocated_cart_discount` stay separate rather than summed for the same reason: on a
return of a single line, the line-level part travels with the line while the cart-level part has to be
recomputed against what remains in the order.

### 2.3 Per-code verdicts

```python
class CodeStatus(StrEnum):
    APPLIED         # changed the price; amount says by how much
    CAPPED          # applied, but limited by the zero floor (requested > amount)
    NO_EFFECT       # recognised and eligible, but worth 0.00 on this cart
    NOT_APPLICABLE  # recognised, but its conditions are not met (e.g. SKU not in cart)
    UNKNOWN         # no such code in the catalog (includes retired codes, §7.4)
    UNAVAILABLE     # in the catalog but quarantined as malformed (§7.3) - an internal fault
    DUPLICATE       # same code entered more than once; counted once (§6.4)

@dataclass(frozen=True)
class CodeResult:
    code: str                # echoed exactly as the customer typed it (§6.4)
    status: CodeStatus       # the machine-readable verdict - the field to branch on
    amount: Decimal          # what it actually took off; 0.00 unless APPLIED/CAPPED
    requested_amount: Decimal | None   # what it would have taken off, when CAPPED
    label: str | None        # the catalog's own description, when the code resolved (§7.1)
    detail: str              # internal explanation - diagnostics only, never displayed
```

**Rule: one code in, exactly one verdict out, in the order submitted.** This is the direct answer to
"reported back as such, not silently ignored". It is stronger than an error list, because there is no way
to forget a code: the arity of `code_results` is checked against the arity of `cart.codes`. A code that is
unknown, inapplicable or worthless is *data in the response*, never an exception, never a log line only.

`UNKNOWN` and `UNAVAILABLE` may well read identically to the customer ("we don't recognise that code").
They are distinct in the payload because they are opposite operationally: `UNKNOWN` is a customer typo and
needs no one's attention, while `UNAVAILABLE` means a live promotion is broken and someone should be
paged. Collapsing them would make that alert impossible to raise.

**The front end writes what the customer sees; this service does not** (PO's answer). That divides the
three text-ish fields cleanly and permanently:

- `status` is the contract. It is a closed enum, and it is what the front end branches on to choose its
  wording. Adding a member is a breaking change to be made deliberately; changing what one *means* is
  worse, and neither is to be done to dodge a copy change.
- `label` is the catalog's own line, written by whoever writes the promotions — the one customer-ready
  string in the payload, and the reason a front end can say "Buy 3 coffees, get one free" without
  duplicating the promotion list. It is `None` exactly when no promotion resolved (`UNKNOWN`).
- `detail` is for engineers and support tooling: "COFFEE not in cart", "requested 10.00, 1.00 available",
  "quarantined: percent out of range". It is deliberately **not** a stable interface — no front end should
  parse it or print it, and it may be reworded in any release. Anything a customer must be told has to be
  reachable from `status`, `label` and the amounts; if it ever is not, the fix is a new `status` member,
  not a richer sentence.

This split is worth stating because the failure mode is well known: prose written for logs quietly becomes
the customer's error message, and then the wording cannot be changed without a regression.

---

## 3. Invariants — the acceptance surface

These are the properties the design exists to guarantee. They are stated here because they are what
reviewers and tests should check; the component boundaries in §4 are chosen so that each invariant has
exactly one owner who can violate it.

| # | Invariant | Owned by |
|---|---|---|
| I1 | Every money value in a `Quote` is a `Decimal` with exactly 2 decimal places | `money` |
| I2 | `line.net == line.gross - line.line_discount - line.allocated_cart_discount`, and `line.net >= 0` | `ledger` |
| I3 | `sum(line.net for line in lines) == quote.total` — exactly, no drift | `ledger` (allocation) |
| I4 | `quote.total >= 0` | `engine` (clamp) |
| I5 | `quote.total_discount == quote.gross_subtotal - quote.total` | `ledger` |
| I6 | `len(code_results) == len(cart.codes)`, same order, same spelling | `engine` |
| I7 | Sum of `amount` over APPLIED/CAPPED results `== total_discount` | `ledger` |
| I8 | Same (cart, catalog) ⇒ byte-identical quote. No dict/set iteration order, no clock, no RNG | `engine` |
| I9 | No promotion input — however malformed — raises out of `price()`; malformed *carts* always do | `engine` |

I3 and I7 are the two that a naive implementation gets wrong, and I3 is now a stated product requirement
("the line prices have to add up to the total"), not merely an internal tidiness rule. Together they are
why cart-wide discounts are *allocated* down to lines rather than merely subtracted from a total (§5.3).

I8 is also a stated product requirement, twice over ("the answer has to be the same every time for the
same cart"). It is the reason ordering is a fixed table rather than submission order (§6.1), why allocation
ties break on line index rather than on whatever order a dict yields (§5.3), and why no clock or random
source may enter the core (§9). Determinism here is a design constraint with teeth, not a platitude: every
"pick one" in this document is resolved to a rule, none is left to runtime happenstance.

---

## 4. Components and seams

Dependencies point one way only. Nothing to the left imports anything to its right.

```
        money ──────────────────────────────────────────────┐
          │    quantisation, allocation, the zero floor      │
          ▼                                                  │
        model ── Cart / Quote / CodeResult (frozen data)     │ used by
          │                                                  │ all
          ├──────────────► catalog ── file → PromotionDef    │
          │                  │         + diagnostics         │
          │                  ▼                               │
          │                rules ── one evaluator per kind   │
          │                  │      pure: snapshot→Proposal  │
          │                  ▼                               │
          └──────────────► engine ── phases, dedupe, cap,     │
                             │        clamp, verdicts        │
                             ▼                               │
                          ledger ── the only mutable thing ──┘
                             │
                             ▼
                       api / cli  (I/O lives here and nowhere else)
```

### 4.1 `money` — the arithmetic authority

Owns: the rounding mode and quantum, the multiplication and percentage helpers, and the
largest-remainder allocator. Owns nothing about promotions.

Why it is its own component: rounding is the classic leak. If `quantize` calls are sprinkled through
rule code, every new rule is a fresh chance to round in a new place and break I3. Here there is one
`ROUND_HALF_UP`, one `Decimal('0.01')`, and code review can grep for stray `quantize` outside this module.

### 4.2 `model` — the vocabulary

Owns the frozen dataclasses of §2 and cart-shape validation only (non-empty SKU, `quantity >= 1`,
`unit_price >= 0` and 2dp). It knows nothing about promotions, so the request shape can be validated by
a caller before any catalog is loaded.

**A quantity of 0 is rejected as a malformed cart** rather than priced at `0.00` or dropped. Dropping it
would break the promise that `quote.lines` matches `cart.lines` one-for-one, which the caller relies on to
render its own basket; pricing it keeps a line the customer is not buying on the invoice and lets it soak
up an allocated share of a cart discount (§5.3). Rejecting keeps a single rule — a line is something being
bought — and pushes the empty-line question back to the basket code, where "the customer removed it"
actually means something. Negative quantities are rejected for the same reason: a return is not a cart
line with a minus sign in front of it, and treating it as one would put the zero floor in the wrong place.

### 4.3 `catalog` — file to definitions, with diagnostics

Owns the on-disk format, its parsing, its validation, and the quarantine policy. Produces an immutable
`PromotionCatalog` plus a list of `CatalogDiagnostic`. Owns no arithmetic.

The critical seam: **the catalog never hands the engine a definition it has not validated.** A `PCT` that
reached the engine is guaranteed to have a percent in range and a usable identity; the percent rule
therefore contains no defensive checks, and "is this file sane" is answerable offline by
`validate` without a cart (§7.3).

### 4.4 `rules` — one pure evaluator per promotion kind

Each kind implements:

```python
class Rule(Protocol):
    kind: ClassVar[str]           # "PCT" | "AMT" | "BOGO"
    phase: ClassVar[Phase]        # when it gets to act (§6.1)
    def evaluate(self, defn: PromotionDef, view: CartView) -> Proposal | NotApplicable: ...
```

`CartView` is a **read-only snapshot** of the ledger: per-line gross, per-line current net, SKU→line
index, per-SKU quantity still being paid for (§6.3), and the current running subtotal. `Proposal` is one of:

```python
CartProposal(amount: Decimal)                       # PCT, AMT — engine allocates it (§5.3)
LineProposal(items: tuple[tuple[int, Decimal], ...])  # BOGO — (line index, amount)
NotApplicable(detail: str)                          # explains itself, in the customer's terms
```

This is the design's spine: **a rule proposes, it never mutates, and it never decides whether it is
allowed.** Capping at the zero floor, ordering, deduplication and verdict recording all live in the
engine. The consequence is that adding a kind cannot break the cart total — the worst a bad new rule can
do is propose a wrong number, and the engine still caps, allocates and clamps it. That is what makes a
data-driven, frequently-edited promotion system safe to extend.

A rule may return a `Proposal` of `0.00`; the engine turns that into `NO_EFFECT`, distinct from
`NOT_APPLICABLE` (which means the conditions were not met at all). Customer service needs that difference.

### 4.5 `engine` — the orchestrator, and the only place policy lives

Owns, in order: resolve each submitted code against the catalog; dedupe (§6.4); group by phase; order
within phase; call evaluators; cap and apply each proposal through the ledger; assemble the `Quote` and
the verdict list. Owns every rule in §6 — none of them is distributed into the rule classes.

### 4.6 `ledger` — the single mutable object

A per-request accumulator: per-line gross, per-line applied discounts with attribution, and the running
subtotal. It is the **only** mutable state in the system and it never escapes the call. It exposes
`apply_line(index, code, amount)` and `apply_cart(code, amount)`; both cap internally against available
money and return the amount actually taken. I2, I3, I5 and I7 are enforced here, in two methods, rather
than in every rule.

### 4.7 `api` / `cli` — adapters

JSON in, JSON out; string→`Decimal` at the edge; exit codes; file reading. The only module permitted to
touch the filesystem or `sys`. `price()` itself takes an already-parsed cart and catalog.

---

## 5. Money

### 5.1 Representation

`decimal.Decimal` throughout, constructed **only from strings or integers**. Floats are rejected at the
boundary with an input fault rather than silently accepted, because `0.1 + 0.2` is how pricing services
end up a cent short and nobody finds out for a quarter. JSON input therefore carries prices as strings
(`"12.50"`), and the CLI documents that. Internal arithmetic runs in a `localcontext()` with ample
precision and `InvalidOperation` / `DivisionByZero` trapped — an arithmetic surprise should be a loud
crash in development, never a wrong price in production.

### 5.2 Where rounding happens — exactly three places

1. **Catalog load**: parameters are normalised once (percent to a 4dp `Decimal`, amounts to 2dp).
2. **Proposal**: each proposed discount is quantised to 2dp, `ROUND_HALF_UP`, before the engine sees it.
3. **Allocation**: an already-2dp cart discount is split into 2dp per-line parts that sum exactly.

Nowhere else. Line gross is `unit_price * quantity` — a 2dp value times an integer, which is exact in
`Decimal` and needs no rounding at all. So there is no accumulated drift anywhere in the pipeline; the
only representable error is the deliberate half-up at step 2, which is the customer-visible discount
figure and must be a real money amount.

The PO's requirement is that it "comes out to the cent" and that the same cart gives the same answer
twice. Both are structural here rather than a matter of care: exactness comes from `Decimal` plus the
allocation rule (§5.3), which is what makes the parts sum to the whole; repeatability comes from there
being no float, no clock and no iteration-order dependency anywhere in the core (I8).

Within that, `ROUND_HALF_UP` (not banker's rounding) is the chosen mode, because a 10%-off figure of
`2.445` shown as `2.44` reads as short-changing, and because half-up is what a person computes by hand
when checking their receipt. Banker's rounding is the better choice for summing many signed figures, which
is not what this does. The mode lives in one constant in `money`, so it is auditable in one place.

### 5.3 Allocating a cart-wide discount back to lines

A cart-wide discount (`PCT`, `AMT`) is one number, but I3 demands the lines sum to the total. The
**largest-remainder (Hamilton) method** over current line nets:

1. For each line, `exact_i = discount * net_i / subtotal`.
2. Take `floor_i = exact_i` truncated to 2dp; give each line that much.
3. Rank lines by the discarded fraction, descending; ties broken by **ascending line index** (determinism,
   I8). Hand out the leftover cents, one each, down that ranking.
4. Cap each line's share at that line's net; any cent that cannot land moves to the next line in ranking.

Properties: the parts sum to the whole exactly (I3), no line goes negative (I2), each line's share is
within one cent of its proportional fair share, and the outcome is independent of dict ordering (I8).

Worked example — `5.00` off lines of `3.33 / 3.33 / 3.34`: exact shares `1.665 / 1.665 / 1.670`; floors
`1.66 / 1.66 / 1.67` = `4.99`; one cent left; remainders tie at `.5`, `.5`, `0`, so the lowest index wins
and line 1 gets `1.67`. Nets `1.66 / 1.67 / 1.67`, total `5.00`. A naive per-line `round(pct * net)` gives
`4.99` and violates I3 — which is precisely the bug this component exists to prevent.

Step 4 also makes the zero floor work per line, which matters for A7-shaped carts with more than one line.

### 5.4 The zero floor

Capping happens at the moment of application, in the ledger: a proposal is reduced to the money actually
available, and the reduction is recorded. It is **not** a `max(0, total)` at the end, for two reasons:
a late clamp would leave `code_results` claiming a discount that was never given (breaking I7), and it
would leave line nets that do not sum to the total (breaking I3). Clamping where the money runs out keeps
the ledger honest, and gives the `CAPPED` verdict its `requested_amount`: for A7, TENOFF reports
`amount=1.00, requested_amount=10.00`, and the total is `0.00`. "The cart total is never negative" is
thereby a consequence of the structure rather than a patch on the last line of the function.

A total of `0.00` is a **valid, returnable result, not an error** (PO: "it happens"). The floor is a floor
and nothing more: pricing never refuses a cart for being worth nothing and never substitutes a minimum
charge. It returns an ordinary `Quote` whose line nets are `0.00` and whose codes report honestly what
they took. Anything downstream that cannot take a zero-value order — a payment step, say — then makes that
call with full information, which is where it belongs; a pricing service that refuses to answer would be
withholding the very number needed to decide.

---

## 6. Promotion semantics

### 6.1 Ordering: phases, declared by kind

Order is not a property of a code and not of the order the customer typed things. It is a property of the
**kind**, in a table owned by the engine:

| Phase | Kind | Acts on |
|---|---|---|
| 10 — `LINE_ITEM` | BOGO | individual lines |
| 20 — `CART_PERCENT` | PCT | running subtotal after phase 10 |
| 30 — `CART_AMOUNT` | AMT | running subtotal after phase 20 |

Case A5 forces 10 before 20: `COFFEE3` then `SAVE10` gives `24.50 − 2.45 = 22.05` ✔. Running phase 20
first is not merely a different order, it is ill-defined — the free coffee would have to be valued either
at list (`25.65 − 4.00 = 21.65`, wrong) or at its already-discounted price (`25.65 − 3.60 = 22.05`, right
only because one multiplication happens to commute here, and not once rounding bites). Line-level offers
change *what the cart contains*; cart-level offers price *what it contains*. That is the reason for the
order, and it generalises to every future kind, which is why phase is declared by kind rather than argued
case by case.

20 before 30 (percentage first, then fixed amount) is not forced by any case, and the PO's answer was that
they do not mind which — only that **the same cart always gives the same answer**. That is a constraint on
the *mechanism*, not on the order, and this design already meets it: order is a property of the kind, held
in one table, so two customers who type `SAVE10` and `TENOFF` in opposite orders are charged the same
price. Submission order cannot reach the arithmetic.

Percentage-first is the chosen entry in that table (on `25.00`: `12.50` rather than `13.50`), because a
fixed amount behaves like a voucher redeemed against what is finally owed, which is naturally last, and
because it is the customer-favourable reading. Since the PO is indifferent, this is recorded as an
engineering choice and is a one-line edit to the table if merchandising ever wants the other one.

Within a phase, codes are processed in **submission order** — the only ordering input the customer has,
and a total order, so it is deterministic. It matters in exactly two places: which AMT code gets `CAPPED`
when the floor bites, and which BOGO consumes units first (§6.3).

Multiple PCT codes therefore **compound**: 10% then 10% off `100.00` takes `19.00`, not `20.00`, since the
second applies to the `90.00` that is then owed. The PO confirmed this reading.

### 6.2 PCT and AMT

- **PCT(percent)** — `amount = quantise(running_subtotal × percent / 100)`. Applies to the whole cart
  including shipping-free lines (there are none today). Zero subtotal ⇒ `NO_EFFECT`, not an error.
- **AMT(amount)** — proposes the fixed amount; the ledger caps it at the remaining subtotal.

Both are `CartProposal`s and are allocated across lines by §5.3, so a customer looking at a line sees the
cart discount reflected in it.

### 6.3 BOGO

Parameters: `sku` and `n` (the "buy" count).

**Free units = `floor(paid_qty_of_sku / n)`** — confirmed by the PO: three coffees in the cart with
`COFFEE3` means one of them is free. So quantity 3 gives 1 free, 4 gives 1, 6 gives 2. (The alternative
industry reading, a group of four — `floor(qty / (n+1))` — would have given 0, 1 and 1. Case A4 could not
distinguish the two; the PO's answer does. The boundary table in §11 is now the specification.)

Each free unit is valued at the **lowest** unit price among that SKU's still-paid units, and the discount
is attributed to the lines holding them, lowest line index first. Aggregation is **across lines by SKU**,
so splitting a SKU over two lines can neither farm extra free units nor lose earned ones.

Free units are removed by *value*, never by quantity: the line keeps quantity 4 and gains a `4.00`
discount. The customer still receives four coffees, so the quantity must not be edited — an invoice that
says "3 coffees" for a cart containing four is a support ticket and a fulfilment bug.

If the SKU is absent, or the paid quantity is `< n`, the code reports `NOT_APPLICABLE` with a detail
naming the SKU and what was needed.

**Two BOGO codes on the same SKU both apply** (PO's answer). That makes their interaction a real rule, and
the naive one is dangerous — evaluated independently against the original quantity, two "every 2nd free"
codes on a quantity of 4 award 4 free units and give the line away:

| qty | codes | independent | sequential (chosen) |
|---|---|---|---|
| 6 | n=3, n=5 | 3 free | 2 free |
| 4 | n=2, n=2 | **4 free — entire line** | 3 free |
| 12 | n=3, n=4 | 7 free | 6 free |

**Rule: BOGO codes in phase 10 are evaluated sequentially in submission order, and each sees only the
units still being paid for.** `COFFEE3` on six coffees takes two; a following `COFFEE5` then looks at the
four remaining paid units and finds no group of five. The PO confirmed both the number (two) and the
principle behind it: *a coffee we already gave away shouldn't earn another one.* That sentence is the
rule — a free unit is not consideration, so it cannot count towards the next offer's threshold — and it is
worth keeping verbatim in the code, because it generalises to every line-level offer added later and is
the thing a future reader needs in order not to "fix" the sequencing. A unit can only be given away once, so total free
units can never exceed the quantity, and each code's attribution is a number of units that genuinely
existed when it ran. The ledger's cap (§5.4) remains as a backstop, but under this rule it is unreachable
from BOGO — which is the point: correctness should not depend on the backstop.

This is why `CartView` exposes *current* paid quantity per SKU rather than the cart's original quantity.
Evaluators stay pure; the sequencing is the engine's, as with every other ordering decision.

### 6.4 Duplicate codes

A code entered twice **counts once, and the customer is told** (PO's answer). The first occurrence is
evaluated normally; each later occurrence reports `DUPLICATE` with a detail saying it was already entered.

Deduplication happens in the engine, before phases, comparing the resolved catalog code — so the same
promotion entered under two spellings that both resolve to it is still caught, and neither the rules nor
the ledger need to know duplicates exist. Note that this is `DUPLICATE`, not an error: the cart prices
normally and the extra entry is simply reported, which is the same principle as §8.

Code matching is **case-insensitive and whitespace-trimmed** on lookup — `save10`, ` SAVE10 ` and `SAVE10`
are one code, confirmed by the PO: customers type them however they like. (Copy-paste carries spaces, and
phone keyboards capitalise the first letter unbidden; neither should cost a customer their discount.) The `code_results`
entry echoes the customer's spelling verbatim so the front end can show it next to what they typed, while
`DUPLICATE` detection compares resolved codes. Catalog keys are canonical and uppercase; `validate`
rejects two keys that differ only by case, since that would make the file's meaning depend on a lookup
rule rather than on what it says.

---

## 7. The promotion catalog

### 7.1 Format: TOML, read with `tomllib`

**Decision.** TOML, parsed by the 3.11 standard-library `tomllib`. No new dependency.

The requirement is explicit that non-engineers edit this file constantly. Against JSON, TOML gives:
comments (so a retired code can be left in place with a note and a date), no trailing-comma or
missing-brace traps, no quoting of keys, and diffs that stay readable in a pull request. Against YAML it
gives a stdlib parser and no Norway problem. The cost is one more format in the repo; the benefit is that
the PO's stated workflow — edit, eyeball, ship — actually works.

```toml
# promos.toml — settings, then one table per code. Edit freely; run `validate` before shipping.

[settings]
currency = "GBP"        # one currency for the whole service (§7.4)

[promotions.SAVE10]
kind    = "PCT"
percent = "10"          # quoted: money and rates are never TOML floats
label   = "10% off everything"

[promotions.TENOFF]
kind   = "AMT"
amount = "10.00"
label  = "10.00 off your order"

[promotions.COFFEE3]
kind  = "BOGO"
sku   = "COFFEE"
n     = 3
label = "Buy 3 coffees, get one free"

# Retiring a code = delete it (or comment it out, which is the same thing to the loader).
# A customer who types it afterwards is told we don't know that code.
# [promotions.SUMMER20]   <- retired <date>
# kind = "PCT"
# percent = "20"
```

Promotions live under a `[promotions.…]` table rather than at the top level so that settings and codes
cannot collide: without it, a promotion legitimately named `SETTINGS` would silently become configuration.
One nesting level is a small price for making the file's two kinds of content impossible to confuse.

### 7.2 Numbers are strings, and the loader enforces it

`percent = 10.5` is a TOML float, i.e. an IEEE double, i.e. the beginning of a rounding bug. The loader
**rejects floats for any money or rate field** with a diagnostic that names the fix ("write
`percent = \"10.5\"`"). Counts (`n`) are integers, as they should be. This is a small rule that removes an
entire failure mode from a file edited by people who are not thinking about binary floating point.

### 7.3 Validation and quarantine

Per code, the loader checks: the table name is a well-formed code; `kind` is known; the parameters for
that kind are present, correctly typed, and in range (`0 <= percent <= 100`, `amount > 0`, `n >= 1`);
there are no unknown keys (a typo'd `precent` must not silently become a 0%-off code); and `label` is
present and non-empty.

`label` is **mandatory**, not decoration. Since the front end composes customer wording from `status` and
`label` (§2.3), a promotion without one leaves the storefront with nothing to display but a bare code. The
person adding a promotion is the only person who knows what it should be called, and they are already in
the file — requiring it there costs them a few seconds and is the only point at which it can be caught.

Two behaviours from one pass:

- **`validate` (CLI)** reports *every* diagnostic with its code and field, and `--strict` makes warnings
  fatal. This is the PO's pre-ship check and the CI gate.
- **`price` (runtime)** *quarantines* a bad entry: it is excluded from the catalog, and any cart using it
  gets `UNAVAILABLE` with a detail, while the rest of the cart prices normally. A typo in one promotion
  must never take down pricing for every customer — that is the same principle as "an unknown code does
  not stop the rest of the cart", applied one level up. Because a quarantined code is a live promotion
  that is failing, `UNAVAILABLE` is the signal ops should alert on (§2.3); the customer-facing wording can
  still be the same as for an unknown code.

`[settings]` is not quarantinable: a missing or invalid `currency` is a deployment fault, not one bad
promotion, and it fails like an unreadable file.

An unreadable or unparseable *file* is different: that is a deployment fault, and `price()` raises rather
than pricing every cart at list price while looking healthy.

### 7.4 Retiring a code, and the currency

**Retirement is deletion** (PO's answer): remove the table from the file — or comment it out, which the
loader cannot tell apart and which preserves the history for whoever reads the file next. A customer who
then enters it gets `UNKNOWN`, which the PO confirmed is the right thing to tell them.

This is the reason there is **no `enabled = false` flag**. It would be a second way to express the same
intent, and two mechanisms for "this code is over" means every future question ("does a disabled code
report unknown or unavailable?", "does `validate` check disabled entries?") has to be answered twice. A
commented-out block is already the low-tech version of the flag, with no code behind it.

**Currency is configured once**, in `[settings].currency`, and is copied into every `Quote`. It is not a
field on the cart and not a CLI flag: the catalog is the file the PO already owns, one currency is the
stated scope, and a per-request currency would immediately raise "what if it disagrees with the catalog?"
— a whole validation path bought for a capability nobody asked for. The service does not convert, compare
or interpret it; it is a label carried through so that a downstream consumer never has to guess. The one
rule the loader enforces is that it is a plausible currency code (three uppercase letters), which catches
the empty string and the typo without pretending to a currency registry.

If multi-currency ever arrives it is a real design change — prices, promotion amounts and rounding rules
all become currency-dependent, and minor units stop being 2 everywhere. Carrying a per-request currency
field today would not make that day cheaper; it would only make today's code look as though it had.

### 7.5 What the catalog deliberately does not have

No date ranges, no enable/disable flag, no per-customer eligibility, no usage limits, no
stacking-exclusion groups. All are
plausible next requests (and `customer_id` is carried through the model as the hook for the second), but
none was asked for, and each would add a clock, a store, or a constraint solver to a system that currently
needs none. §9 shows what each would cost.

---

## 8. Failure model

Two categories, deliberately different, because conflating them is what makes pricing services either
brittle or silently wrong.

**Input faults — raise.** A malformed cart (negative quantity, non-2dp price, float money, missing SKU),
or an unreadable catalog file. These are caller bugs; the service must not invent a price for a cart it
does not understand. A single `CartValidationError` carrying a list of field-level problems, so the caller
learns everything wrong at once.

**Promotion outcomes — report.** Unknown, quarantined, inapplicable, duplicated, zero-valued, capped. These are *normal business results of a normal request*, not errors: the customer
mistyped a code, or the offer does not fit their basket. They travel in `code_results` (§2.3), the cart
still prices, and the caller can render them next to the promo box. A6 is exactly this path.

There is no third "silently ignore" category, and no logging-only path. Anything the service decides about
a code is in the response.

### 8.1 Scale and limits

No cart-size or code-count limit is imposed. Pricing is a single in-memory pass: `O(L × C)` for `L` lines
and `C` codes, with one `O(L log L)` sort per cart-wide code for the allocation ranking, and no allocation,
parsing or I/O inside the loops. A 500-line cart with 20 codes is microseconds of `Decimal` arithmetic;
there is no point at which this design needs attention before the store's own basket limits bite, and an
arbitrary cap invented here would only be a new way to reject a legitimate cart.

Two things are worth stating rather than assuming. The catalog is parsed **once per process** and the
resulting `PromotionCatalog` is immutable and shared across calls, so catalog size does not appear in the
per-cart cost at all — this is the reason `price()` takes an already-loaded catalog instead of a path.
And because a pathological cart costs time but not memory beyond its own size, a size limit belongs at the
caller's request boundary, where a rejection can be explained to a customer, not in the pricing core.

---

## 9. Extension scenarios — what changes when the PO asks for…

The point of §4's seams is that these have bounded, predictable answers.

| Request | Change |
|---|---|
| A new code of an existing kind | Edit `promos.toml`. No code, no deploy. |
| "Buy X get Y free" (cross-SKU) | New rule class + catalog schema fragment + a phase-10 entry. Engine untouched. |
| "PCT on one category only" | New rule; needs product metadata the cart does not carry — that is the real cost, not the rule. |
| Reverse PCT/AMT ordering | One entry in the engine's phase table. |
| Codes with start/end dates | `as_of: datetime` parameter on `price()`, injected by the caller (never `now()` inside the core, or I8 dies), plus two catalog fields and an eligibility check in the engine. |
| Per-customer eligibility | Engine gains a `customer_id` check against catalog criteria; the field is already in the model. |
| "Best of" instead of stacking | Engine-level: evaluate candidate subsets, keep the cheapest total. Rules stay pure and unchanged — this is why they return proposals instead of mutating. |
| Tax / shipping | New phases after 30; allocation (§5.3) is already the mechanism for apportioning them to lines. |
| HTTP front end | New adapter beside `cli`. Core untouched. |
| A second currency | Genuinely a redesign, not a field: prices, promotion amounts, minor units and rounding all become currency-dependent (§7.4). Flagged so it is never mistaken for a small change. |

---

## 10. The acceptance cases, traced

| # | Trace | Result |
|---|---|---|
| A1 | gross `12.50 × 2 = 25.00`; no codes | line `25.00`, total `25.00` ✔ |
| A2 | subtotal `25.00`; SAVE10 → `2.50`; allocated to the single line | total `22.50`, SAVE10 `APPLIED 2.50` ✔ |
| A3 | subtotal `25.00`; TENOFF `10.00` ≤ subtotal | total `15.00`, TENOFF `APPLIED 10.00` ✔ |
| A4 | COFFEE qty 4, `4 // 3 = 1` free at `4.00` (phase 10) | line `12.00`, total `12.00` ✔ |
| A5 | phase 10: COFFEE `16.00 − 4.00 = 12.00`; subtotal `24.50`. phase 20: `2.45`, allocated `1.20` / `1.25` (both exact, no remainder) | lines `10.80` / `11.25`, total `22.05` ✔ |
| A6 | NOPE not in catalog; no phases run | total `12.50`, NOPE `UNKNOWN` ✔ |
| A7 | subtotal `1.00`; TENOFF proposes `10.00`, ledger caps at `1.00` | total `0.00`, TENOFF `CAPPED amount 1.00, requested 10.00` ✔ |

Note A5: the invariant sum holds exactly (`10.80 + 11.25 = 22.05`) — I3 is satisfied without a fudge
factor, which is the whole reason for §5.3.

### 10.1 Cases the answers now pin down

None of these is in the PO's table, but each is decided by an answer given above, so each is a number the
PO can check now rather than discover in production. They belong in the acceptance suite next to A1–A7.

| # | Cart | Codes | Result | From |
|---|---|---|---|---|
| D1 | WIDGET 12.50 ×2 | SAVE10, SAVE10 | total `22.50`; second entry `DUPLICATE` | Q6 |
| D2 | anything totalling 100.00 | two different 10% codes | total `81.00` (19% off, not 20%) | Q3 |
| D3 | COFFEE 4.00 ×6 | COFFEE3, COFFEE5 | 2 free, total `16.00`; COFFEE5 `NOT_APPLICABLE` (only 4 paid units remain) | Q4, Q12 |
| D4 | WIDGET 12.50 ×2 | SAVE10, TENOFF | total `12.50` — percentage first, and the same if entered in the other order | Q2 |
| D5 | WIDGET 1.00 ×1, GIZMO 1.00 ×1 | TENOFF | total `0.00`; allocated `1.00` / `1.00`; TENOFF `CAPPED amount 2.00, requested 10.00` | Q5 + floor |

D5 is the one worth dwelling on: it is A7 with a second line, and it is where "lines must add up to the
total" and "never negative" meet. The cap has to happen before allocation, or the two lines are handed
`5.00` each and go negative; and it has to be recorded as `2.00`, or the verdict claims a `10.00` discount
the customer never received. A design that clamps at the end fails this case while passing A7.

---

## 11. How this should be tested (for the build stage, not built here)

- **The seven cases**, as a table-driven suite — necessary, nowhere near sufficient.
- **Invariant properties** over generated carts and code sets: I2–I8 must hold for *every* input, including
  carts of 40 lines at `0.01`, quantities of 1, codes repeated five times, and every ordering of the same
  code set. These catch allocation and rounding bugs the seven cases never will.
- **Catalog fuzzing**: every field missing, mistyped, floated, out of range, duplicated — assert the
  service always prices and always quarantines.
- **The BOGO boundary table** — quantities `n−1`, `n`, `n+1`, `2n`, `2n+1` against `floor(qty / n)`; for
  `COFFEE3` that is 2→0, 3→1, 4→1, 6→2, 7→2 free. This table *is* the specification of the PO's answer to
  Q1 and belongs in the repo as one. Add a second table for two stacked BOGOs on one SKU (§6.3), since
  sequential consumption is the rule most likely to be "fixed" by a later reader who has not read §6.3.
- **Determinism**: price the same input twice in one process and once in a fresh one; bytes must match.

---

## 12. Decisions at a glance

| Decision | Alternative rejected | Because |
|---|---|---|
| Pure `price(cart, catalog)` library + thin CLI | Local HTTP endpoint | No network in substrate; transport is the caller's choice; purity is testability |
| `Decimal` from strings only, floats rejected at the edge | Integer cents | `Decimal` keeps the 2dp contract visible at every boundary and reads like the money it represents; cents push the formatting bug outward to every caller |
| Rules propose, engine disposes | Rules mutate a running total | A bad rule then cannot break the total, the floor, or I3 — the property that makes a frequently-edited promo system safe |
| Cart discounts allocated to lines (largest remainder) | Subtract from the total only | Lines must sum to the total; anything else drifts by cents and is unauditable |
| Cap at application, in the ledger | `max(0, total)` at the end | A late clamp makes the verdicts lie about what was given |
| Phase table keyed by kind | Order = submission order | Two customers typing the same codes in different orders must be charged the same |
| One verdict per submitted code | Error list | Impossible to silently drop a code; arity is checkable |
| Quarantine bad catalog entries at runtime, fail loudly in `validate` | Refuse to start | One typo must not stop the shop; the PO still gets a hard gate before ship |
| TOML via stdlib `tomllib` | JSON | The file's stated audience is non-engineers editing constantly; comments and forgiving syntax are the feature |
| Stacked BOGOs consume units sequentially | Each evaluated against original quantity | Independent evaluation can award more free units than the cart holds and give a line away (§6.3) |
| Retirement = delete the entry; no `enabled` flag | A disable flag | Two mechanisms for "this code is over" means every downstream question is answered twice |
| Currency in `[settings]`, once | Per-request currency field | Nothing to disagree with, no reconciliation path bought for an unasked capability |
| Zero/negative quantity rejects the cart | Price it at 0.00, or drop the line | Keeps line-for-line correspondence with the caller's basket; a line is something being bought |
| No cart-size limit | A defensive cap | One linear in-memory pass; an invented cap only rejects legitimate carts |
| `status` + `label` are the interface; `detail` is unstable internal prose | One human-readable message per code | The front end owns customer wording (§2.3); log prose that leaks into the storefront can never be reworded again |
| `label` mandatory in the catalog | Optional, with the code as fallback | The storefront depends on it, and the person adding the promotion is the only one who can write it |
| A `0.00` total is a normal result | Refuse, or impose a minimum charge | Confirmed real; pricing must return the number downstream needs in order to decide |

---

## 13. Product answers — all closed

### 13.1 The answers, and where each one lives

| Q | Answer | Where it lives |
|---|---|---|
| Q1 BOGO at quantity 3 | One is free — `floor(qty / n)` | §6.3, boundary table §11 |
| Q2 PCT vs AMT order | PO indifferent; must be repeatable | §6.1 — repeatability is the phase table; percentage-first chosen |
| Q3 Two 10% codes | 19%, compounded | §6.1 |
| Q4 Two BOGOs on one SKU | Both apply | §6.3 — sequential unit consumption |
| Q5 Line price | What the customer pays; lines add up to the total | §2.2, I3, §5.3 |
| Q6 Duplicate code | Count once, tell the customer | §6.4 |
| Q7 Rounding | To the cent, same answer twice | §5.2, I1, I8 |
| Q8 Retiring a code | Delete it; `UNKNOWN` is the right message | §7.4 |
| Q9 Zero-quantity line | Engineering's call | §4.2 — reject as malformed |
| Q10 Currency | One currency, 2dp; configuration our call | §7.4 — `[settings].currency` |
| Q11 Cart size | Engineering's call | §8.1 — no limit, linear pass |
| Q12 Stacked BOGO magnitude | Two — a coffee already given away doesn't earn another | §6.3 |
| Q13 Zero-value orders | Fine, it happens | §5.4 |
| Q14 Code matching | Customers type them however they like | §6.4 |
| Q15 Wording | Ours is internal; the front end writes the customer's | §2.3, §7.3 |

Three of these changed the design rather than confirming it. **Q4** replaced a conflict rule with an
interaction rule and removed the `SUPERSEDED` status entirely — a status nothing can now produce should
not exist, or someone will eventually invent a use for it. **Q5** turned "publish both readings of a line
price and let the invoice decide" into a single answer, `net`, with the rest demoted to an explicit audit
trail. **Q8** removed the `enabled` flag that had been provisionally sketched.

The last four confirmed choices the design had already made, which is the useful outcome: it means the
reasoning recorded against each one was the product's reasoning, not a coincidence. Q15 was the exception
in one respect — confirming that wording is the front end's job turned a loose `detail` string into a
deliberate three-way split (`status` as the contract, `label` as the one customer-ready string, `detail`
as explicitly unstable internal prose) and made `label` mandatory in the catalog, since the storefront now
depends on it.

### 13.2 Nothing is open

Every product decision in this document traces to an answer in the table above or to an explicitly
delegated engineering call (Q9, Q10, Q11), each of which is recorded with its reasoning in §12 rather than
left as an assumption.

What that does **not** mean is that nothing will change. The questions most likely to arrive next are
visible from here — dated or customer-limited codes, "best of" instead of stacking, a second currency,
tax — and §9 states what each would cost before anyone has to estimate it under pressure. Two are cheap
because of where the seams were put; one (a second currency) is not, and is flagged as a redesign
precisely so it is never quoted as a field.

The build can start from this document. §3's invariants and §10's traced cases, taken together, are the
acceptance criteria; §11 says what the test suite has to cover beyond them.
