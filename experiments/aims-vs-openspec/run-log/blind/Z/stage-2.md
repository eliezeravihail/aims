# Cart Pricing Service — Architecture (Stage 2)

Status: **stage 2 closed.** All ten stage-2 questions answered by the product owner and folded in
(§13.2); three were delegated back to engineering and are recorded with their reasoning rather than left
as assumptions. Complete and self-contained: this document supersedes stage 1 as the description of the
product and needs no other document to be read alongside it. Every stage-1 product answer is still in
force and restated here (§13.1). No implementation.

Substrate: Python 3.11+, standard library only, single process, single currency, no persistence,
no network, no UI, no database. `decimal.Decimal` available.

---

## 1. What this service is

One question, answered purely: **given a cart and some codes, what does each line cost, what does the
cart cost, and — as of this stage — why?**

It is a *calculator*, not a workflow. It holds no state between calls, talks to nothing, and has exactly
two inputs — the **cart** (from the caller, per request) and the **promotion catalog** (a file the product
owner edits). That shape is the single most important structural fact about the system:

- A pure function `price(cart, catalog) -> Quote` is the whole product. Everything else is an adapter.
- Because it is pure, it is exhaustively testable without fixtures, clocks, servers or mocks.
- Because the catalog is data, adding a code is an edit, not a deploy.

### 1.1 The stage-2 requirement, stated as a structural property

Finance and support cannot answer "why is this 22.05?", and a refund was issued because nobody could show
the working. The requirement is therefore not "add a field" but: **the price and the story of the price
must be incapable of disagreeing.**

That distinction decides the architecture of this stage. A design that computes the amounts and then also
builds a narrative alongside them has two code paths producing two answers, and every future promotion
kind is a fresh opportunity for them to drift — exactly the failure the PO says would make the feature
worthless. So:

> **The explanation is not derived from the amounts. The amounts are derived from the explanation.**

Pricing writes one append-only record of what it did — the **journal** (§4.6). Every money figure the
service publishes (line net, cart total, discount per code, discount in total) is a *fold of that record*,
computed nowhere else. The published explanation is a *projection of the same record*, in the order the
entries were appended. There is no second source for either. "The explanation matches the amount" is then
not a test that could fail; it is the only representable state.

The two things the PO said would be checked hard map onto this directly:

- *deltas sum exactly, with no residue and no rounding line* — because the deltas **are** the money, and
  the one place where a number is split (allocating a cart-wide discount to lines, §5.3) splits it by
  largest remainder so the parts sum to the whole by construction. There is no reconciliation step because
  there is nothing left over to reconcile, and `AdjustmentKind` (§2.4) has no member that could express one.
- *the explanation describes what actually happened, in the order it happened* — because the journal is
  append-only, written only at the moment the engine acts, and the projector never sorts it.

### 1.2 Entry point: library first, thin CLI adapter

**Decision (kept from stage 1).** Ship a library (`pricing.price`) with a thin CLI wrapper. Not an HTTP
endpoint. The substrate forbids the network, so a "local HTTP endpoint" would only be a loopback socket
wrapping the same function while adding a server lifecycle, port config, request framing and a second
error channel to get right. The caller is an online store that will eventually call this over its own
transport; handing it a library keeps that choice open.

```
python -m pricing price    --catalog promos.toml --cart cart.json   # JSON quote on stdout
python -m pricing validate --catalog promos.toml [--strict]         # lint the promo file
python -m pricing explain  --catalog promos.toml --cart cart.json   # the explanation, rendered
```

`explain` existed in stage 1 as a debug trace. It is now a renderer over a first-class structure that is
also in the JSON payload — the support tool and the CLI read the same thing, so a support agent and an
auditor cannot be shown different stories. What it must render is specified, not left to the adapter: see
**the support view** (§4.8), which is where the PO's "wherever support will see it" is discharged.

If HTTP is later required, it is a new adapter module over the same `price()` call, with no change to the
core. That is the intended seam, not a hypothetical one.

### 1.3 A note on retention

There is no persistence in the substrate, and none is added. The explanation travels **inside the quote**,
as data, so a caller that stores the quote has stored the working — it stays valid and legible a year
later without re-running pricing against a catalog that has since changed. That is what an audit needs,
and it is why the explanation is a value in the response rather than a log line or a second endpoint.

The quote carries **no version stamp** — no catalog revision, no quote id, no timestamp (PO: *not now,
build for today*). Two of the three would require something the substrate does not have (a clock, a store),
and the third would be a field this service could only copy from its caller. If an auditor one day needs to
know which rules produced a year-old quote, §9 records what that costs: a field on `Quote`, filled by the
caller that already knows. Adding it speculatively today would mean inventing a versioning scheme for a
file whose only version control is the repository it lives in.

---

## 2. The contract

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

Entry order of `codes` is load-bearing in two ways now: it breaks ties in the exclusion contest (§6.5,
case B5) and it fixes the order of per-code verdicts (I6).

### 2.2 The explanation — the new centre of the output

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
    delta: Decimal              # signed, exactly 2dp. Negative = money off.
    running: Decimal            # the amount after this adjustment
    superseded_by: str | None   # set if and only if kind is NOT_APPLIED
    forgone_delta: Decimal | None  # NOT_APPLIED: the (negative) delta it would have contributed

@dataclass(frozen=True)
class Explanation:
    basis: Decimal                        # the list price this explanation starts from
    final: Decimal                        # the price it ends at
    adjustments: tuple[Adjustment, ...]   # ordered; adjustments[0].kind is always LIST_PRICE
```

Read as the PO stated it, for case B1:

| kind | code | delta | running |
|---|---|---|---|
| LIST_PRICE | — | `0.00` | `25.00` |
| PROMOTION | SAVE10 | `-2.50` | `22.50` |

`sum(delta) = -2.50 = final - basis`. ✔

**Why the opening entry carries a delta of `0.00`.** Confirmed by the PO (Q21): *the deltas add up to what
came off, and it has to be clear what we started from.* Those are two requirements, and they are only
simultaneously satisfiable if the opening entry is an opening *balance* rather than a movement — the first
line of a ledger, which states where the account stood before anything happened. So the deltas sum to
`-2.50` (what came off) while the starting point is stated on the opening row's `running`.

"Clear what we started from" is then met **twice over, from one fold**: `Explanation.basis` is the figure
as a field, and `adjustments[0].running` is the same figure as the first thing anyone reads. They cannot
disagree (I10), and the support view is required to lead with it (§4.8). The alternative shape — opening
delta `+25.00`, deltas summing to the final price — is internally consistent but makes the deltas add up
to what is *owed* rather than to what *came off*, so it is rejected.

**Why `running` is published even though it is derivable.** Because it is emitted *by the same fold that
produces the deltas*, not recomputed afterwards, it cannot disagree with them — and it makes the structure
directly renderable by a support tool with no arithmetic of its own, which is a large part of why the
feature exists. It also gives the invariant checker a second, redundant statement of the same truth: I12
asserts the chain and I11 asserts the sum, and a bug that satisfies one rarely satisfies the other.

**There is deliberately no `RESIDUAL` / `ROUNDING` kind.** The enum has three members and none of them can
express "…and a bit extra to make it add up". A future engineer who finds themselves needing one has found
a bug in the allocator (§5.3), not a missing enum member. This is the type-level form of the PO's "no
rounding line that exists to make the arithmetic close".

A `PROMOTION` adjustment may carry a delta of `0.00` only when a promotion genuinely applied and was worth
nothing on this cart (§4.4); it is never used as padding.

**What an adjustment carries is exactly what the PO asked for and no more**: the code, the promotion's name
(`label`, from the catalog) and the money. Confirmed at Q25 — *code, name and amount is enough* — so there
is no catalog-authored "why this one didn't apply" sentence and no free-text field anywhere in the
explanation. A superseded row states the same three things plus the code that beat it and the amount it
would have given, which is that same vocabulary reused rather than a new one invented.

### 2.3 Output

```python
@dataclass(frozen=True)
class LineQuote:
    sku: str
    quantity: int
    unit_price: Decimal
    gross: Decimal                       # unit_price * quantity (the line's list price)
    line_discount: Decimal               # positive magnitude, from line-targeted promos (BOGO)
    allocated_cart_discount: Decimal     # positive magnitude, this line's share of cart-wide promos
    net: Decimal                         # gross - line_discount - allocated_cart_discount, >= 0
    explanation: Explanation             # basis == gross, final == net

@dataclass(frozen=True)
class Quote:
    currency: str
    lines: tuple[LineQuote, ...]         # same order and arity as cart.lines
    gross_subtotal: Decimal
    total_discount: Decimal              # positive magnitude
    total: Decimal                       # >= 0
    explanation: Explanation             # basis == gross_subtotal, final == total
    code_results: tuple[CodeResult, ...] # one per submitted code, in submission order
```

**`net` is the line price**: what the customer actually pays for that line, the number on the invoice, and
the line prices add up to the total (I3). Every cart-wide discount is therefore *allocated* down to the
lines (§5.3); no other output shape can satisfy "they have to add up".

`line_discount` and `allocated_cart_discount` are retained from stage 1 and are now **folds of the
journal**, not separately accumulated figures — the engine has no way to write one directly. They stay
separate rather than summed because on a return of a single line, the line-level part travels with the
line while the cart-level part has to be recomputed against what remains in the order.

**`LineQuote.attribution` is removed**, replaced by `explanation`. Stage 1 published an unordered
`(code, amount)` list as the audit trail behind a line. That list is now strictly weaker than the
explanation (no order, no basis, no running balance, no not-applied entries) and describes the same facts —
two representations of one truth is precisely the drift risk this stage exists to eliminate. The PO
confirms nothing reads it yet (Q22), so it is removed outright rather than kept as a deprecated alias:
a field with no consumer and a better replacement is pure future confusion. Should one ever be wanted back
it returns as a *projection* of the journal, never as a second accumulation.

### 2.4 Per-code verdicts

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

**Rule: one code in, exactly one verdict out, in the order submitted.** There is no way to forget a code:
the arity of `code_results` is checked against the arity of `cart.codes` (I6). A code that is unknown,
inapplicable, superseded or worthless is *data in the response*, never an exception, never a log line only.

`SUPERSEDED` returns to the status set, having been deliberately removed at the end of stage 1 on the
grounds that nothing could produce it. Something can now: it is the direct answer to "support needs to tell
the customer *your code was valid but the other one saved you more*". Its two a file note fields carry the
rest of that sentence — `superseded_by` names the winning code, and `requested_amount` is what the losing
code would have taken off.

**`requested_amount` is reused rather than duplicated**, and its meaning is stated once for both users:
*the amount this code proposed and did not receive*. For `CAPPED` the money ran out; for `SUPERSEDED` a
rival won. A separate `forgone_amount` field would be the same number under a second name, and support's
question ("how much was my code worth?") is the same question in both cases.

`superseded_by` echoes **the winning code in the customer's own spelling** — the exact string that appears
as `code` on the winner's own `CodeResult` — so a front end can match it to what is on the customer's
screen. The canonical form is always recoverable by the same trim-and-uppercase rule used for lookup (§6.4).

`UNKNOWN` and `UNAVAILABLE` may well read identically to the customer. They are distinct in the payload
because they are opposite operationally: `UNKNOWN` is a customer typo and needs no one's attention, while
`UNAVAILABLE` means a live promotion is broken and someone should be paged.

**The front end writes what the customer sees; this service does not.** That divides the text-ish fields
cleanly and permanently:

- `status` is the contract — a closed enum, the thing to branch on. Adding a member is a breaking change
  to be made deliberately (this stage makes one); changing what one *means* is worse.
- `label` is the catalog's own line, written by whoever writes the promotions — the one customer-ready
  string in the payload. It is `None` exactly when no promotion resolved (`UNKNOWN`). It appears in
  `Adjustment` too, for the same reason: so that an explanation can be rendered as
  "10% off everything − £2.45" without the renderer holding a copy of the promotion list.
- `detail` is for engineers and support tooling and is deliberately **not** a stable interface. No front
  end should parse or print it.

This split matters more at this stage, not less. The explanation will be read aloud to customers and shown
to auditors, and the temptation to put a hand-written sentence in it is strong. It carries structured
fields and the catalog's own `label` and nothing else; anything a customer must be told has to be reachable
from `status`, `label`, `kind` and the amounts.

---

## 3. Invariants — the acceptance surface

These are the properties the design exists to guarantee. Each has exactly one owner who is capable of
violating it; the component boundaries in §4 are chosen so that this is true.

| # | Invariant | Owned by |
|---|---|---|
| I1 | Every money value in a `Quote` is a `Decimal` with exactly 2 decimal places | `money` |
| I2 | `line.net == line.gross - line.line_discount - line.allocated_cart_discount`, and `line.net >= 0` | `journal` |
| I3 | `sum(line.net for line in lines) == quote.total` — exactly, no drift | `journal` (allocation) |
| I4 | `quote.total >= 0` | `journal` (cap at application) |
| I5 | `quote.total_discount == quote.gross_subtotal - quote.total` | `journal` |
| I6 | `len(code_results) == len(cart.codes)`, same order, same spelling | `journal` (resolutions) |
| I7 | Sum of `amount` over APPLIED/CAPPED results `== total_discount` | `explain` |
| I8 | Same (cart, catalog) ⇒ byte-identical quote. No dict/set iteration order, no clock, no RNG | `engine` |
| I9 | No promotion input — however malformed — raises out of `price()`; malformed *carts* always do | `engine` |
| **I10** | Every `Explanation` starts with a `LIST_PRICE` adjustment whose `delta == 0.00` and `running == basis`, and it is the only one | `explain` |
| **I11** | `sum(a.delta for a in adjustments) == final - basis`, exactly, for every line explanation and the cart explanation | `explain` |
| **I12** | `adjustments[i].running == adjustments[i-1].running + adjustments[i].delta` for all `i > 0`, and `adjustments[-1].running == final` | `explain` |
| **I13** | For every journal entry, its cart-level delta `== sum` of its per-line deltas | `journal` |
| **I14** | Every money figure in the `Quote` is a fold of the journal; no figure is computed by a second path | boundary (§4.7) |
| **I15** | Adjustment order == journal append order == the order the engine acted. The projector never sorts | `explain` |
| **I16** | No adjustment exists whose purpose is to reconcile: `AdjustmentKind` has three members, none of them residual | `model` |
| **I17** | At most one promotion marked non-stackable is `APPLIED` or `CAPPED` in a quote | `engine` |
| **I18** | Every `SUPERSEDED` result names a code that is `APPLIED`/`CAPPED` in the same quote, whose `amount` is `>=` the superseded code's `requested_amount`; if equal, the winner's submission index is lower | `engine` |
| **I19** | `result.amount == -adjustment.delta` for the entry that realised it; `result.requested_amount == -adjustment.forgone_delta` where both exist | `explain` |
| **I20** | Every submitted code appears exactly once in the support view, in one of its two code sections | `api` / `cli` |

I3 and I7 are the two a naive implementation gets wrong. I13 is why they now come free: the journal is a
matrix whose rows are adjustments and whose columns are lines (§4.6), and I13 says every row's margin
agrees. Given I13, I3 is a theorem rather than a rule to enforce —
`sum(nets) = sum(grosses) + sum(all deltas) = gross_subtotal - total_discount = total` — and I7 likewise,
because `code_results` is a projection of the same rows.

I14 is the stage-2 invariant and the only one owned by a *boundary* rather than a module: it is enforced
by the fact that `Adjustment`, `LineQuote` and `Quote` are constructed in exactly one place (`explain`),
from exactly one input (the journal). It cannot be unit-tested into existence; it is kept by not adding a
second constructor. That is the single most important thing for a reviewer to check in this design.

I18 turns cases B3, B4 and B5 from three examples into one property that holds for every cart.

I20 is the only invariant about a *rendering*, and it is here rather than in a style guide because the PO
asked for non-events to be reported "wherever support will see it" (§4.8). It is checkable precisely
because I6 already fixes the arity of `code_results`: a view that drops a code drops it from a list whose
length is known.

I8 remains a stated product requirement. It is why ordering is a fixed table rather than submission order
(§6.1), why allocation ties break on line index (§5.3), why the contest's tie-break is a total order
(§6.5), and why no clock or random source may enter the core.

---

## 4. Components and seams

Dependencies point one way only. Nothing to the left imports anything to its right.

```
        money ────────────────────────────────────────────────────┐
          │    quantisation, allocation, the zero floor            │
          ▼                                                        │
        model ── Cart / Quote / Explanation / CodeResult (frozen)  │ used by
          │                                                        │ all
          ├──────────────► catalog ── file → PromotionDef          │
          │                  │         + diagnostics               │
          │                  ▼                                     │
          │                rules ── one evaluator per kind         │
          │                  │      pure: snapshot → Proposal      │
          │                  ▼                                     │
          └──────────────► engine ── pipeline, dedupe, contest,    │
                             │        cap, verdicts                │
                             ▼                                     │
                          journal ── the only mutable thing;       │
                             │        append-only record ──────────┘
                             ▼
                          explain ── journal → Quote + Explanations (pure)
                             │
                             ▼
                          api / cli  (I/O lives here and nowhere else)
```

Two changes from stage 1: the `ledger` is reframed as the `journal` (§4.6), and `explain` is a new
component (§4.7). Everything else is unchanged, which is the point of having had seams.

### 4.1 `money` — the arithmetic authority

Owns: the rounding mode and quantum, the multiplication and percentage helpers, and the largest-remainder
allocator. Owns nothing about promotions.

Why it is its own component: rounding is the classic leak. If `quantize` calls are sprinkled through rule
code, every new rule is a fresh chance to round in a new place and break I3. Here there is one
`ROUND_HALF_UP`, one `Decimal('0.01')`, and code review can grep for stray `quantize` outside this module.

This component is why "no rounding line" is achievable at all: the allocator is the only place a money
figure is divided, and it is defined to produce parts that sum exactly to the whole (§5.3).

### 4.2 `model` — the vocabulary

Owns the frozen dataclasses of §2 and cart-shape validation only (non-empty SKU, `quantity >= 1`,
`unit_price >= 0` and 2dp). It knows nothing about promotions, so the request shape can be validated by a
caller before any catalog is loaded. It also owns I16, in the sense that the shape of `AdjustmentKind` is
what makes a reconciliation line unrepresentable.

**A quantity of 0 is rejected as a malformed cart** rather than priced at `0.00` or dropped. Dropping it
would break the one-for-one correspondence between `quote.lines` and `cart.lines` that the caller relies
on to render its own basket; pricing it keeps a line the customer is not buying on the invoice and lets it
soak up an allocated share of a cart discount (§5.3). Rejecting keeps a single rule — a line is something
being bought. Negative quantities are rejected for the same reason: a return is not a cart line with a
minus sign in front of it, and treating it as one would put the zero floor in the wrong place.

### 4.3 `catalog` — file to definitions, with diagnostics

Owns the on-disk format, its parsing, its validation, and the quarantine policy. Produces an immutable
`PromotionCatalog` plus a list of `CatalogDiagnostic`. Owns no arithmetic.

The critical seam: **the catalog never hands the engine a definition it has not validated.** A `PCT` that
reached the engine is guaranteed to have a percent in range and a usable identity; the percent rule
therefore contains no defensive checks, and "is this file sane" is answerable offline by `validate`
without a cart (§7.4). Stage 2 adds one field, `stackable` (§7.3), and no new validation shape.

### 4.4 `rules` — one pure evaluator per promotion kind

Each kind implements:

```python
class Rule(Protocol):
    kind: ClassVar[str]           # "PCT" | "AMT" | "BOGO"
    phase: ClassVar[Phase]        # when it gets to act (§6.1)
    def evaluate(self, defn: PromotionDef, view: CartView) -> Proposal | NotApplicable: ...
```

`CartView` is a **read-only snapshot** of the journal's current fold: per-line gross, per-line current net,
SKU→line index, per-SKU quantity still being paid for (§6.3), and the current running subtotal. `Proposal`
is one of:

```python
CartProposal(amount: Decimal)                         # PCT, AMT — engine allocates it (§5.3)
LineProposal(items: tuple[tuple[int, Decimal], ...])  # BOGO — (line index, amount)
NotApplicable(detail: str)                            # explains itself
```

**A rule proposes, it never mutates, and it never decides whether it is allowed.** Capping at the zero
floor, ordering, deduplication, exclusion and verdict recording all live in the engine. The consequence is
that adding a kind cannot break the cart total — the worst a bad new rule can do is propose a wrong number,
and the engine still caps, allocates and clamps it.

**This component required no change at all in stage 2, and that is the largest single piece of evidence
that the stage-1 seams were placed correctly.** The exclusion contest (§6.5) must ask "what would this
promotion be worth right now?" without applying it. Because `evaluate` is pure and returns a value, asking
is free and provably side-effect-free; there is no "dry run" mode to add, no rollback, no second code path.
Had rules mutated a running total, the contest would have required transactional state and the design would
have been substantially worse. It is also why the contest belongs in the engine: deciding that a promotion
is not allowed is exactly the decision a rule is forbidden to make about itself.

A rule may return a `Proposal` of `0.00`; the engine turns that into `NO_EFFECT`, distinct from
`NOT_APPLICABLE` (conditions not met at all). Customer service needs that difference, and §6.5 now needs
it too, to decide who enters a contest.

### 4.5 `engine` — the orchestrator, and the only place policy lives

Owns, in order (§6.6 states the walk precisely): resolve each submitted code against the catalog; dedupe
(§6.4); order the survivors into the pipeline (§6.1); walk it, holding the exclusion contest at the first
contender (§6.5); cap and append each proposal through the journal; record one resolution per submitted
code. Owns every rule in §6 — none of them is distributed into the rule classes.

The engine **never constructs an `Explanation`, a `LineQuote` or a `Quote`.** It writes journal entries.
That restriction is I14.

### 4.6 `journal` — the single mutable object, and the record of truth

Stage 1 called this the `ledger` and described it as an accumulator with attribution attached. Stage 2
inverts the emphasis: it is a **record** from which the accumulation is derived. The rename is not
cosmetic — it is the difference between "a total, plus some notes about it" and "a history, whose fold is
the total".

```python
@dataclass(frozen=True)
class Entry:                        # one row of the matrix; one act of the engine
    seq: int                        # append order — the "when"
    source: Source                  # PROMOTION | NOT_APPLIED
    scope: Scope                    # LINE | CART  (which discount bucket it folds into)
    code: str | None                # customer's spelling
    canonical: str | None
    label: str | None
    parts: tuple[Decimal, ...]      # one signed delta per cart line, 2dp, aligned to cart.lines
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

The journal holds `opening: tuple[Decimal, ...]` (the line list prices), an append-only `entries` list,
and an append-only `resolutions` list. It is the **only** mutable state in the system and it never escapes
the call.

**The matrix.** `opening` is the header row; each entry is a row of per-line deltas. Case B2 in full:

| row | COFFEE line | WIDGET line | row total |
|---|---|---|---|
| opening (list) | `16.00` | `12.50` | `28.50` |
| COFFEE3 | `-4.00` | `0.00` | `-4.00` |
| SAVE10 | `-1.20` | `-1.25` | `-2.45` |
| **column total (net)** | **`10.80`** | **`11.25`** | **`22.05`** |

Read down a column and you have that line's explanation; read across a row and you have that promotion's
cart-level delta; read the margins and they agree because I13 says every row sums. The cart explanation is
the right-hand column of row totals; the line explanations are the vertical readings. **This is the whole
of stage 2 in one table**, and it is why "the explanation and the amount disagree" has no representation:
they are the same numbers read in two directions.

Interface, all of it:

```python
def would_take(self, proposal: Proposal) -> tuple[Decimal, ...]   # pure: capped per-line parts
def append(self, entry: Entry) -> None                            # the only mutator of entries
def resolve(self, resolution: Resolution) -> None                 # the only mutator of resolutions
def view(self) -> CartView                                        # the fold, for rules
```

**`append` does not cap and `would_take` does not mutate**, and application is defined as
`append(entry_from(would_take(p)))`. There is exactly one capping function, used both to measure a
contender (§6.5) and to apply a winner, so the number that wins a contest and the number that lands in the
journal are produced by the same code. Two capping paths would be the classic way to reintroduce the
disagreement this stage exists to remove.

The fold (running subtotal, per-line net, per-SKU paid quantity) may be cached for O(1) access by `view`,
but the cache is written **only** by `append`. A cached fold that can be written from anywhere else is a
second source of truth wearing a performance costume.

I2, I3, I4, I5, I6 and I13 are enforced here, in two mutators, rather than in every rule.

### 4.7 `explain` — the projector

A pure function `project(journal, cart, catalog_currency) -> Quote`. It reads the journal and constructs
everything the caller sees: both kinds of `Explanation`, every `LineQuote`, the `Quote`, and every
`CodeResult`. It has no other input and performs no pricing decision.

Three projections of one record:

| Output | Projection |
|---|---|
| line `i`'s explanation | `opening[i]`, then every entry with `parts[i] != 0.00`, in `seq` order |
| the cart explanation | `sum(opening)`, then every entry, in `seq` order, delta = `sum(parts)` |
| `code_results` | `resolutions` in submission order, amounts read from the linked entry |

Rules the projector owns:

- **It never sorts** (I15). Entry order is append order is the order things happened.
- **It never computes a money figure that is not a sum of `parts`** (I14). `net`, `total`,
  `line_discount`, `allocated_cart_discount`, `total_discount` and every `CodeResult.amount` are folds.
- **Sign conversion happens here and only here**, under the naming rule of §5.5: journal deltas are
  signed, the summary fields are positive magnitudes. The conversion is one negation in one module and
  the relation is asserted as I19.
- **A line omits entries whose part is `0.00`** — the COFFEE3 row does not appear on the WIDGET line's
  explanation, because it did not move that line's price. This is the PO's rule verbatim (Q19): *if it
  didn't change that line's price, it doesn't need to be on that line.* The cart explanation keeps
  everything, so nothing is lost — the promotion is still named, at the level where it acted.
  Not-applied entries have all-zero parts and so appear only in the cart explanation, which is also where
  the supersession actually happened — the decision was about the cart, not about a line.

Putting the projector behind its own boundary is what makes I14 checkable by reading imports rather than
by testing outputs: if `Quote(` appears anywhere outside this module, the invariant is gone.

### 4.8 `api` / `cli` — adapters

JSON in, JSON out; string→`Decimal` at the edge; exit codes; file reading. The only module permitted to
touch the filesystem or `sys`. `price()` itself takes an already-parsed cart and catalog.

In JSON, every money value is a **string** (`"-2.50"`, `"22.05"`), including deltas, for the reason in
§5.1. An explanation serialises as an ordered array, and array order is part of the contract.

#### The support view

The PO's answer to "where do unknown, duplicate and inapplicable codes get reported?" was *wherever support
will see it* (Q20). Support will not read JSON; they will read a rendered page. So the obligation lands on
the renderer, not on the payload, and the rendering is specified here rather than left to whoever writes
the adapter. `python -m pricing explain` and any support tool built on this service render **four parts, in
this order**:

1. **What we started from** — the basis, alone on its own line ("List price 28.50"). Required by Q21.
2. **What came off** — the explanation, in order, one row per adjustment: code, name, delta, running
   balance. A superseded row also names the code that beat it and what it would have given.
3. **Codes that did not change the price** — every submitted code with no adjustment of its own:
   `NO_EFFECT`, `NOT_APPLICABLE`, `UNKNOWN`, `UNAVAILABLE`, `DUPLICATE`. Each with its status and, where
   it resolved, its name.
4. **What is owed** — the final total.

Support therefore sees every code on one screen, which is what was asked for, while the arithmetic in
part 2 stays exactly the set of rows that sum (I11). Part 3 is the right home for non-events precisely
because it is *not* in the sum: "we don't recognise WINTER25" is not a step in the calculation of 22.05,
and a cart with six mistyped codes must not push the two adjustments that actually set the price off the
bottom of the page.

The two parts cannot between them drop a code: part 2 is a projection of the journal, part 3 is every
`CodeResult` with no linked entry, and I6 fixes the arity of `code_results` at exactly the number of codes
submitted. That is I20, and it is the reason this is a four-part contract rather than a styling note.

---

## 5. Money

### 5.1 Representation

`decimal.Decimal` throughout, constructed **only from strings or integers**. Floats are rejected at the
boundary with an input fault rather than silently accepted, because `0.1 + 0.2` is how pricing services end
up a cent short and nobody finds out for a quarter. JSON input therefore carries prices as strings
(`"12.50"`). Internal arithmetic runs in a `localcontext()` with ample precision and `InvalidOperation` /
`DivisionByZero` trapped — an arithmetic surprise should be a loud crash in development, never a wrong
price in production.

### 5.2 Where rounding happens — exactly three places

1. **Catalog load**: parameters are normalised once (percent to a 4dp `Decimal`, amounts to 2dp).
2. **Proposal**: each proposed discount is quantised to 2dp, `ROUND_HALF_UP`, before the engine sees it.
3. **Allocation**: an already-2dp cart discount is split into 2dp per-line parts that sum exactly.

Nowhere else. Line gross is `unit_price * quantity` — a 2dp value times an integer, exact in `Decimal`,
needing no rounding. There is no accumulated drift anywhere in the pipeline; the only representable error
is the deliberate half-up at step 2, which is the customer-visible discount figure and must be a real money
amount.

This list is now also the **proof obligation for "no residue"**. A residue could only arise where a 2dp
number is derived from another and the difference is dropped. Step 2 produces a figure from scratch, so
there is nothing to drop. Step 3 is the only division, and the allocator is defined to re-distribute its
own remainder (§5.3). Step 1 happens before any cart exists. Hence no reconciliation line is needed
anywhere, which is what lets §2.2's enum omit one.

`ROUND_HALF_UP` (not banker's rounding) is the chosen mode, because a 10%-off figure of `2.445` shown as
`2.44` reads as short-changing, and because half-up is what a person computes by hand when checking their
receipt — which is now literally what support will do, against the explanation. The mode lives in one
constant in `money`.

### 5.3 Allocating a cart-wide discount back to lines

A cart-wide discount (`PCT`, `AMT`) is one number, but I3 and I13 demand the parts sum to it. The
**largest-remainder (Hamilton) method** over current line nets:

1. For each line, `exact_i = discount * net_i / subtotal`.
2. Take `floor_i = exact_i` truncated to 2dp; give each line that much.
3. Rank lines by the discarded fraction, descending; ties broken by **ascending line index** (I8). Hand out
   the leftover cents, one each, down that ranking.
4. Cap each line's share at that line's net; any cent that cannot land moves to the next line in ranking.

Properties: the parts sum to the whole exactly (I13 ⇒ I3), no line goes negative (I2), each line's share is
within one cent of its proportional fair share, and the outcome is independent of dict ordering (I8).

Worked example — `5.00` off lines of `3.33 / 3.33 / 3.34`: exact shares `1.665 / 1.665 / 1.670`; floors
`1.66 / 1.66 / 1.67` = `4.99`; one cent left; remainders tie at `.5`, `.5`, `0`, so the lowest index wins
and line 1 gets `1.67`. Nets `1.66 / 1.67 / 1.67`, total `5.00`. A naive per-line `round(pct * net)` gives
`4.99` and violates I3 — and would now *also* produce an explanation whose deltas do not sum, which is the
PO's stated deal-breaker. The allocator is the component that makes both promises simultaneously, and it
is the reason the extra cent is attached to a real line rather than parked in a rounding row.

### 5.4 The zero floor

Capping happens at the moment of application, in the journal: a proposal is reduced to the money actually
available, and **only the reduced figure is ever journalled**. It is not a `max(0, total)` at the end: a
late clamp would leave `code_results` claiming a discount that was never given (breaking I7) and line nets
that do not sum to the total (breaking I3) — and now also an explanation whose deltas overshoot the final
price (breaking I11).

This is the second reason no reconciliation line is needed: **the journal records what was given, never
what was asked for.** The asked-for figure lives on the `Resolution` as `requested_amount`, outside the
money column entirely, so it can never contaminate a sum. For A7, TENOFF reports `amount=1.00,
requested_amount=10.00`, the explanation shows a single `-1.00` delta, and the total is `0.00`.

A total of `0.00` is a **valid, returnable result, not an error**. Pricing never refuses a cart for being
worth nothing and never substitutes a minimum charge; anything downstream that cannot take a zero-value
order makes that call with full information.

### 5.5 Signs: one lexical rule

The explanation needs signed movements (the PO writes `-2.50`); the summary fields are named for
quantities that are naturally positive (a *discount* of `2.50`, an *amount* of `10.00`). Rather than force
one convention onto both and end up with a `total_discount` of `-2.45` that reads like a credit, the
convention is carried by the **name of the field**, which is the simplest rule a reviewer can apply
without consulting this document:

> **Anything named `delta` is a signed movement — negative means money came off.
> Anything named `amount` or `discount` is a positive magnitude.**

That is the whole rule, it covers every money field in the contract, and it is mechanically checkable.
`Adjustment.delta` and `Adjustment.forgone_delta` are signed; `CodeResult.amount`,
`CodeResult.requested_amount`, `line_discount`, `allocated_cart_discount` and `total_discount` are
magnitudes. `gross`, `net`, `total`, `basis` and `running` are prices, and prices are never negative
(I2, I4).

The conversion between the two happens at exactly one point — the projector (§4.7) — and is asserted by
I19, so the two conventions cannot drift apart. Choosing this over an all-signed payload also keeps every
stage-1 field's meaning identical, which is the payload half of B6. (Engineering's call, delegated at Q23.)

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

Case A5/B2 forces 10 before 20: `COFFEE3` then `SAVE10` gives `24.50 − 2.45 = 22.05` ✔. Running phase 20
first is not merely a different order, it is ill-defined — the free coffee would have to be valued either
at list or at its already-discounted price. Line-level offers change *what the cart contains*; cart-level
offers price *what it contains*. That is the reason for the order, and it generalises to every future kind,
which is why phase is declared by kind rather than argued case by case.

20 before 30 is not forced by any case; the PO is indifferent as long as the same cart always gives the
same answer. Percentage-first is the chosen entry (on `25.00`: `12.50` rather than `13.50`), because a
fixed amount behaves like a voucher redeemed against what is finally owed, and it is the customer-favourable
reading. It is a one-line edit to the table.

Within a phase, codes are processed in **submission order** — the only ordering input the customer has, and
a total order, so it is deterministic. The pair `(phase, submission_index)` is therefore a total order over
the codes on a cart; call it the **pipeline order**. It is the order the engine walks, the order entries are
appended, and hence the order of the explanation (I15). Submission order still cannot reach the
*arithmetic* — two customers typing `SAVE10` and `TENOFF` in opposite orders are charged the same price —
except through the one place the PO has now explicitly asked for it: the tie-break in §6.5.

Multiple PCT codes **compound**: 10% then 10% off `100.00` takes `19.00`, not `20.00`. The explanation
shows this honestly as two entries of `-10.00` and `-9.00`, which is the answer to the support question it
will generate.

### 6.2 PCT and AMT

- **PCT(percent)** — `amount = quantise(running_subtotal × percent / 100)`. Zero subtotal ⇒ `NO_EFFECT`.
- **AMT(amount)** — proposes the fixed amount; the journal caps it at the remaining subtotal.

Both are `CartProposal`s and are allocated across lines by §5.3, so a customer looking at a line sees the
cart discount reflected in it — and, now, sees it named in that line's explanation.

### 6.3 BOGO

Parameters: `sku` and `n` (the "buy" count).

**Free units = `floor(paid_qty_of_sku / n)`**: three coffees with `COFFEE3` means one is free; 4 gives 1,
6 gives 2. Each free unit is valued at the **lowest** unit price among that SKU's still-paid units, and the
discount is attributed to the lines holding them, lowest line index first — which is also what determines
the shape of that entry's `parts` row. Aggregation is **across lines by SKU**, so splitting a SKU over two
lines can neither farm extra free units nor lose earned ones.

Free units are removed by *value*, never by quantity: the line keeps quantity 4 and gains a `4.00` discount.
The customer still receives four coffees, so the quantity must not be edited.

If the SKU is absent, or the paid quantity is `< n`, the code reports `NOT_APPLICABLE` with a detail naming
the SKU and what was needed.

**Two BOGO codes on the same SKU both apply**, and the naive interaction is dangerous — evaluated
independently against the original quantity, two "every 2nd free" codes on a quantity of 4 award 4 free
units and give the line away:

| qty | codes | independent | sequential (chosen) |
|---|---|---|---|
| 6 | n=3, n=5 | 3 free | 2 free |
| 4 | n=2, n=2 | **4 free — entire line** | 3 free |
| 12 | n=3, n=4 | 7 free | 6 free |

**Rule: BOGO codes in phase 10 are evaluated sequentially in submission order, and each sees only the units
still being paid for.** *A coffee we already gave away shouldn't earn another one.* That sentence is the
rule — a free unit is not consideration, so it cannot count towards the next offer's threshold — and it is
worth keeping verbatim in the code, because it generalises to every line-level offer added later and is the
thing a future reader needs in order not to "fix" the sequencing. A unit can only be given away once, so
the journal's cap is a backstop that BOGO cannot reach.

This is why `CartView` exposes *current* paid quantity per SKU rather than the cart's original quantity.
Evaluators stay pure; the sequencing is the engine's.

### 6.4 Duplicate codes

A code entered twice **counts once, and the customer is told**. The first occurrence is evaluated normally;
each later occurrence gets a `DUPLICATE` resolution and **no journal entry** — nothing happened to the
money, so nothing appears in the explanation (§6.7).

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

**Definitions.**

- A **contender** is a submitted code that resolved to a non-stackable definition and survived dedupe and
  quarantine.
- The **contest point** is the pipeline slot (§6.1) of the *first* contender in pipeline order. Everything
  earlier in the pipeline has already been applied when the contest is held, so contenders are measured
  against a realistic cart, not against list price.

**The contest, at the contest point:**

1. Evaluate every contender — including those whose own slot is later — against the **same** `CartView`.
   This is speculative and provably free of side effects, because `evaluate` is pure (§4.4).
2. Pass each resulting proposal through `journal.would_take` (§4.6) to get the parts that *would* land.
   A contender's **value** is the magnitude of their sum: what the customer would actually receive,
   not what the promotion notionally claims.
   - `NotApplicable` ⇒ resolution `NOT_APPLICABLE`; the contender leaves the contest.
   - value `0.00` ⇒ resolution `NO_EFFECT`, with `superseded_by` left `None`; the contender leaves the
     contest. The PO's words are the specification here: *it wasn't beaten by anything — it just saved
     them nothing. Say that.* `NO_EFFECT` with an amount of `0.00` and no `superseded_by` says exactly
     that and nothing else; marking it `SUPERSEDED` would tell the customer they lost a contest they were
     never in, and would make `superseded_by` unreliable as the answer to "which code beat mine?".
3. Rank the survivors by `(value descending, submission_index ascending)`. This is a total order, so the
   outcome is deterministic (I8), and its second key is exactly the PO's tie rule: *if they tie, apply the
   one the customer entered first* (case B5).
4. **Zero survivors** — nothing applies and nobody is superseded.
5. **One survivor** — it applies at the contest point, with the proposal that was measured. Nobody is
   marked superseded: a code that did not qualify did not lose a contest, it simply did not apply. This
   matches the PO's wording, which scopes supersession to promotions that *both qualify*.
6. **Two or more survivors** — the first in the ranking wins and applies at the contest point with the very
   proposal that was measured; every other survivor gets a `NOT_APPLIED` journal entry (all-zero parts,
   `superseded_by` = the winner's code as the customer typed it, `forgone_delta` = the negative of its own
   measured value) and a `SUPERSEDED` resolution.
7. The group's entries are appended in **submission order**, so the narrative reads in the order the
   customer entered their codes. Only the winner's entry has non-zero parts, so the order among them cannot
   affect any arithmetic.
8. Every contender's own later pipeline slot is **skipped** — it has already been resolved. The walk
   continues with the remaining stackable codes.

**Measure and apply are one act.** The winner is applied with the proposal that won, at the moment it won;
it is never re-evaluated. This is what makes the explanation truthful: the sentence "TENOFF beat SAVE10
because it was worth 10.00 rather than 5.00" is backed by `-10.00` being literally the delta in the
journal, not by a second calculation that happens to agree. It also means the winner's amount cannot be
changed by anything that happens between the contest and its own phase.

**Which slot the winner applies at — engineering's call (Q18), and this is the reasoning.** The PO has no
view, so the choice is made on simplicity. Because the winner applies at the *earliest contender's* slot,
a group behaves as a single promotion occupying the earliest slot any of its members would have occupied.
If a non-stackable AMT beats a non-stackable PCT, the AMT acts in the PCT's phase rather than its own.
With only the group present (B3–B5) this is invisible; it is visible only when stackable codes sit between
the two phases, and then the effect is customer-favourable and exact.

This is the simpler of the two candidates by a clear margin. It keeps the engine a **single forward walk**
with no deferred work: nothing is remembered between slots, nothing is revisited, and the contest is one
bounded excursion at one point. The alternative — measure at the contest point but apply the winner in its
own, later phase — needs the engine to carry a pending decision across slots, and then to answer a question
that has no good answer: by the time the winner's own slot arrives the cart may have shrunk, so either the
frozen figure is applied and may exceed the money available, or it is re-evaluated and the number that won
the contest is no longer the number that lands. The second is exactly the disagreement this stage exists
to eliminate; the first breaks the zero floor. A rule that needs neither is the one to take.

**Scope of exclusion — settled by the PO, both halves.** *Non-stackable only means it can't sit next to
another non-stackable one* (Q16), and *one rule: two of them can't sit together — nothing more elaborate*
(Q17). So:

- A non-stackable promotion **still combines freely with stackable ones**. A cart carrying non-stackable
  `SAVE10` and stackable `COFFEE3` gets both; `SAVE10` simply has no rival to contest. The contest is
  entered only by non-stackable codes, and it never suppresses anything outside itself.
- All non-stackable promotions on a cart form **one group** — there are no named groups, no per-promotion
  exclusion lists, and no priority field (§7.6). `stackable` is one boolean with one meaning, and at most
  one non-stackable promotion applies to a cart (I17).

Both answers are worth recording as answers rather than as defaults, because each one closes off an
elaboration that a later reader will be tempted to add. Named groups and priorities are the two standard
next features of any exclusion system, and the PO has explicitly declined both; adding either without being
asked would put a second, silently-overriding answer next to the tie-break rule the PO did specify (largest
discount, then entry order).

### 6.6 The engine walk, end to end

The whole of the engine's policy, in order. Every step is deterministic.

1. **Resolve.** For each submitted code, in submission order: trim and uppercase, look up. Not found ⇒
   `UNKNOWN`. Quarantined ⇒ `UNAVAILABLE`. Write the resolution; no entry.
2. **Dedupe.** Second and later occurrences of the same canonical code ⇒ `DUPLICATE`; no entry.
3. **Order.** Sort the survivors by `(phase(kind), submission_index)` — the pipeline.
4. **Walk.** For each slot in pipeline order:
   - If the code was already resolved by a contest, skip it.
   - If the code is a contender and the contest has not yet been held, hold it (§6.5) and continue.
   - Otherwise evaluate the rule against `journal.view()`; `NotApplicable` ⇒ `NOT_APPLICABLE` resolution,
     no entry; a `0.00` proposal ⇒ `NO_EFFECT` resolution, no entry; otherwise
     `append(entry_from(would_take(proposal)))` and resolve `APPLIED`, or `CAPPED` if `would_take` reduced
     it.
5. **Project.** Hand the journal to `explain` (§4.7). The engine returns whatever comes back and touches
   no money figure itself.

Step 4's "no entry" cases are the subject of §6.7.

### 6.7 What appears in the explanation, and what does not

**An entry is written when the engine acts on the money at a slot** — either it moved money, or it decided
not to move money that a rival moved instead. That is the whole rule, and it gives:

| Outcome | In the explanation | In `code_results` |
|---|---|---|
| APPLIED / CAPPED | yes, with its delta | yes |
| SUPERSEDED | yes, `NOT_APPLIED`, delta `0.00`, naming the winner | yes |
| NO_EFFECT | no | yes |
| NOT_APPLICABLE | no | yes |
| UNKNOWN / UNAVAILABLE / DUPLICATE | no | yes |

The dividing line: **the explanation answers "why is this 22.05?"; `code_results` answers "what became of
each code I entered?"** Those are different questions, and conflating them in the payload makes the
explanation worse at its job — the rows of an explanation are the rows that sum, and padding them with
non-events buries the two adjustments that actually set the price. Supersession is in the explanation
because the PO put it there, and because it is genuinely a *pricing* decision made at a point in the
pipeline: the price is what it is partly because SAVE10 was set aside.

**Where the PO's answer lands.** Asked whether unknown, duplicate and inapplicable codes should also be in
the explanation, the PO said *wherever support will see it — your call* (Q20). Taken literally, that is a
requirement about the **screen**, not about the data structure, and it is discharged there: the support
view (§4.8) renders the explanation and then a "codes that did not change the price" section, so support
sees every code in one place without the sum-checked narrative being diluted. The payload keeps the two
structures apart because they answer different questions and because only one of them has to add up.

Every outcome is reported somewhere, in the response, always, and now also somewhere on the rendered page
(I20). There is no silently-ignored category and no logging-only path (§8).

---

## 7. The promotion catalog

### 7.1 Format: TOML, read with `tomllib`

**Decision.** TOML, parsed by the 3.11 standard-library `tomllib`. No new dependency.

Non-engineers edit this file constantly. Against JSON, TOML gives comments (so a retired code can be left
in place with a note and a date), no trailing-comma or missing-brace traps, no quoting of keys, and diffs
that stay readable in a pull request. Against YAML it gives a stdlib parser and no Norway problem.

```toml
# promos.toml — settings, then one table per code. Edit freely; run `validate` before shipping.

[settings]
currency = "GBP"        # one currency for the whole service (§7.5)

[promotions.SAVE10]
kind      = "PCT"
percent   = "10"          # quoted: money and rates are never TOML floats
label     = "10% off everything"
stackable = false         # cannot be combined with another non-stackable promotion (§6.5)

[promotions.TENOFF]
kind      = "AMT"
amount    = "10.00"
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
**rejects floats for any money or rate field** with a diagnostic naming the fix. Counts (`n`) are integers.

### 7.3 `stackable` — the new field

- Type: TOML **boolean**, not a string. It is a flag, not a quantity, so the float hazard of §7.2 does not
  apply and a bare `false` is the most readable thing in the file.
- Optional, **defaulting to `true`**. Every promotion written before this stage keeps its exact meaning and
  no existing catalog needs editing — which is the file-level half of B6.
- Named for the property, not its absence. `stackable = false` reads better than `non_stackable = true`,
  and the engine never has to write `if not defn.non_stackable`.
- The existing unknown-key rule catches `stackble` rather than silently making a promotion stackable, which
  is exactly the typo that would be most expensive: a code that quietly combines when it must not.

No new validation *shape* is introduced — a wrong type is a diagnostic like any other, and the entry is
quarantined at runtime. There is deliberately no check that a catalog contains at least two non-stackable
promotions: one is a perfectly ordinary state (it simply never contests), and inventing a warning for it
would train people to ignore warnings.

### 7.4 Validation and quarantine

Per code, the loader checks: the table name is a well-formed code; `kind` is known; the parameters for that
kind are present, correctly typed and in range (`0 <= percent <= 100`, `amount > 0`, `n >= 1`);
`stackable`, if present, is a boolean; there are no unknown keys; and `label` is present and non-empty.

`label` is **mandatory**, not decoration. The front end composes customer wording from `status` and
`label`, and the explanation carries `label` as its only human-readable field — a promotion without one
leaves both the storefront and the support tool showing a bare code. The person adding the promotion is the
only person who knows what it should be called, and they are already in the file.

Two behaviours from one pass:

- **`validate` (CLI)** reports *every* diagnostic with its code and field; `--strict` makes warnings fatal.
  This is the pre-ship check and the CI gate.
- **`price` (runtime)** *quarantines* a bad entry: it is excluded from the catalog, any cart using it gets
  `UNAVAILABLE`, and the rest of the cart prices normally. A typo in one promotion must never take down
  pricing for every customer. Because a quarantined code is a live promotion that is failing, `UNAVAILABLE`
  is the signal ops should alert on.

A quarantined non-stackable promotion is not a contender and supersedes nobody — it never reaches the
pipeline. That is the correct and conservative behaviour: a broken promotion must not silently suppress a
working one.

`[settings]` is not quarantinable: a missing or invalid `currency` is a deployment fault. An unreadable or
unparseable *file* is likewise a deployment fault, and `price()` raises rather than pricing every cart at
list price while looking healthy.

### 7.5 Retiring a code, and the currency

**Retirement is deletion**: remove the table from the file — or comment it out, which the loader cannot
tell apart and which preserves the history for whoever reads the file next. A customer who then enters it
gets `UNKNOWN`. This is the reason there is **no `enabled = false` flag**: two mechanisms for "this code is
over" means every future question has to be answered twice.

**Currency is configured once**, in `[settings].currency`, and copied into every `Quote`. Not a field on
the cart and not a CLI flag: one currency is the stated scope, and a per-request currency would immediately
raise "what if it disagrees with the catalog?". The loader checks only that it is three uppercase letters.

If multi-currency ever arrives it is a real design change — prices, promotion amounts, minor units and
rounding all become currency-dependent. Carrying a per-request currency field today would not make that day
cheaper.

### 7.6 What the catalog deliberately does not have

No date ranges, no enable/disable flag, no per-customer eligibility, no usage limits, no named
stacking-exclusion groups, no priority field. All are plausible next requests (`customer_id` is carried
through the model as the hook for the third), but none was asked for, and each would add a clock, a store,
or a constraint solver. §9 states what each would cost.

Two of these were put to the PO at this stage and declined, so they are absent by decision rather than by
omission:

- **Named exclusion groups** (Q17) — *one rule: two of them can't sit together, nothing more elaborate.*
- **A catalog-authored "why this didn't apply" line** (Q25) — *code, name and amount is enough.* The
  explanation therefore carries no free text at all, which also keeps §2.4's rule intact: the catalog's
  `label` stays the single customer-ready string, and nothing in the payload competes with it.

A **priority** field deserves a specific mention now that exclusion exists, because it is the obvious thing
to reach for: it is not added, because the PO has specified the tie-break already (largest discount, then
entry order) and a priority field would be a second, silently-overriding answer to the same question.

---

## 8. Failure model

Two categories, deliberately different, because conflating them is what makes pricing services either
brittle or silently wrong.

**Input faults — raise.** A malformed cart (negative quantity, non-2dp price, float money, missing SKU), or
an unreadable catalog file. These are caller bugs; the service must not invent a price for a cart it does
not understand. A single `CartValidationError` carrying a list of field-level problems, so the caller
learns everything wrong at once.

**Promotion outcomes — report.** Unknown, quarantined, inapplicable, duplicated, zero-valued, capped,
superseded. These are *normal business results of a normal request*. They travel in `code_results`, the
cart still prices, and the caller can render them next to the promo box.

There is no third "silently ignore" category and no logging-only path. Anything the service decides about a
code is in the response — and as of this stage, anything the service decides about the *price* is in the
explanation.

**Invariant violations.** I10–I19 are cheap to check and are checked in `explain` before the `Quote` is
returned, raising an internal error rather than shipping a quote whose explanation does not add up. This is
the one place the design prefers a crash to an answer: a wrong price that is correctly explained is a
pricing bug, but a right price with a broken explanation is the bug the PO refunded a customer over, and it
must never leave the process. The check is O(lines × entries) over data already in hand.

I20 is the exception: it is a property of a rendering, so it cannot be checked in `explain` and is instead
a test obligation on the adapter (§11). That asymmetry is honest — the core can guarantee that every code
is *in* the response, and only the adapter can guarantee it reaches the screen.

### 8.1 Scale and limits

No cart-size or code-count limit is imposed. Pricing is a single in-memory pass: `O(L × C)` for `L` lines
and `C` codes, with one `O(L log L)` sort per cart-wide code for the allocation ranking. The journal adds
one `L`-wide row per applied code — the same order of storage the allocation already needed — and the
contest adds one extra evaluation per contender, once. The invariant check is one more pass over the same
matrix. A 500-line cart with 20 codes remains microseconds of `Decimal` arithmetic.

The catalog is parsed **once per process** and the resulting `PromotionCatalog` is immutable and shared
across calls, so catalog size does not appear in the per-cart cost — which is why `price()` takes an
already-loaded catalog instead of a path. A size limit belongs at the caller's request boundary, where a
rejection can be explained to a customer.

---

## 9. Extension scenarios — what changes when the PO asks for…

| Request | Change |
|---|---|
| A new code of an existing kind | Edit `promos.toml`. No code, no deploy. |
| Mark an existing code non-stackable | Edit `promos.toml`. No code, no deploy. |
| Named exclusion groups instead of one | Catalog field + group key in the contest's step 1. Engine shape unchanged. |
| "Buy X get Y free" (cross-SKU) | New rule class + catalog schema fragment + a phase-10 entry. Engine untouched; it journals and explains itself for free. |
| "PCT on one category only" | New rule; needs product metadata the cart does not carry — that is the real cost. |
| Reverse PCT/AMT ordering | One entry in the engine's phase table. |
| Codes with start/end dates | `as_of: datetime` parameter on `price()`, injected by the caller (never `now()` inside the core, or I8 dies), plus two catalog fields and an eligibility check. |
| Per-customer eligibility | Engine gains a `customer_id` check against catalog criteria; the field is already in the model. |
| "Best of" across *all* promotions, not just non-stackables | The contest already is a best-of over a set. Widening the set is a change to how contenders are selected (step 1), not to the mechanism. |
| A "what if" / counterfactual API | Cheap: run `price()` on variant carts and compare. Purity is the feature. |
| Tax / shipping | New phases after 30; allocation is already the mechanism for apportioning them to lines, and each becomes an ordinary row in the explanation. |
| Show the explanation to customers, not just support | No core change: it is already a value in the payload with `label` as its human-readable field (§2.4). |
| A version stamp for auditors (declined for now, Q24) | A field on `Quote`, filled by the caller that knows its own catalog revision. No clock and no store enters the core; `price()` would take it as a parameter, exactly as a date-limited promotion would take `as_of`. |
| Named exclusion groups (declined, Q17) | Catalog field + a group key in the contest's step 1. The contest already ranks a set; it would rank several. |
| HTTP front end | New adapter beside `cli`. Core untouched. |
| A second currency | Genuinely a redesign, not a field: prices, promotion amounts, minor units and rounding all become currency-dependent (§7.5). Flagged so it is never mistaken for a small change. |

The first three rows are the measure of this stage: the two things the PO asked for land as *data* plus one
engine step, and the next likely request after them ("best of everything") is a change to a set, not to a
structure.

---

## 10. The acceptance cases, traced

### 10.1 Stage-2 cases

| # | Trace | Result |
|---|---|---|
| B1 | opening `(25.00)`. SAVE10 PCT 10% of `25.00` = `2.50`; parts `(-2.50)` | total `22.50`; explanation `LIST 0.00→25.00`, `SAVE10 -2.50→22.50`; deltas sum `-2.50` ✔ |
| B2 | opening `(16.00, 12.50)` = `28.50`. Phase 10 COFFEE3: `4//3=1` free at `4.00`, parts `(-4.00, 0.00)` → `24.50`. Phase 20 SAVE10: `2.45`, allocated `1.20`/`1.25` (both exact, no remainder), parts `(-1.20, -1.25)` | total `22.05` ✔; cart explanation `LIST 28.50`, `COFFEE3 -4.00→24.50`, `SAVE10 -2.45→22.05`, sum `-6.45` ✔ |
| B3 | both non-stackable. Contest at SAVE10's phase-20 slot on subtotal `50.00`: SAVE10 `5.00`, TENOFF `10.00`. TENOFF wins | total `40.00`; explanation `LIST 50.00`, `SAVE10 not applied (0.00, superseded by TENOFF, would have been -5.00) →50.00`, `TENOFF -10.00→40.00` ✔ |
| B4 | subtotal `150.00`: SAVE10 `15.00`, TENOFF `10.00`. SAVE10 wins | total `135.00`; `SAVE10 -15.00→135.00`, then `TENOFF not applied, superseded by SAVE10, would have been -10.00` ✔ |
| B5 | subtotal `100.00`: both `10.00` — tie. Rank key `(value desc, submission asc)` ⇒ SAVE10 (index 0) | total `90.00`; `SAVE10 -10.00→90.00`, `TENOFF not applied, superseded by SAVE10` ✔ |
| B6 | no `stackable = false` in the stage-1 catalog ⇒ zero contenders ⇒ step 4 of §6.6 never branches ⇒ the walk is byte-for-byte the stage-1 walk. Explanations are additive output | A1–A7 and D1–D5 unchanged ✔ |

B2 is worth dwelling on: the cart explanation's two deltas (`-4.00`, `-2.45`) are the row totals of the
matrix in §4.6, and the two line explanations are its columns. Neither is computed from the other; both are
read off the same rows. That is the mechanical content of "the explanation and the amount cannot disagree".

B3 shows why the loser's entry carries `forgone_delta`: support's sentence is "your code was worth £5.00,
the other was worth £10.00", and both numbers are in the explanation, with only one of them in the money
column.

### 10.2 Stage-1 cases, still binding (B6)

| # | Trace | Result |
|---|---|---|
| A1 | gross `12.50 × 2 = 25.00`; no codes | line `25.00`, total `25.00`; explanation is `LIST` alone, deltas sum `0.00` ✔ |
| A2 | subtotal `25.00`; SAVE10 → `2.50` | total `22.50`, SAVE10 `APPLIED 2.50` ✔ |
| A3 | subtotal `25.00`; TENOFF `10.00` ≤ subtotal | total `15.00`, TENOFF `APPLIED 10.00` ✔ |
| A4 | COFFEE qty 4, `4 // 3 = 1` free at `4.00` (phase 10) | line `12.00`, total `12.00` ✔ |
| A5 | identical to B2 | total `22.05` ✔ |
| A6 | NOPE not in catalog; no entry, one resolution | total `12.50`, NOPE `UNKNOWN`; explanation is `LIST` alone ✔ |
| A7 | subtotal `1.00`; TENOFF proposes `10.00`, `would_take` returns `(-1.00)` | total `0.00`, TENOFF `CAPPED amount 1.00, requested 10.00`; explanation shows `-1.00`, never `-10.00` ✔ |
| D1 | SAVE10 twice | total `22.50`; second entry `DUPLICATE`, one adjustment in the explanation ✔ |
| D2 | two different 10% codes on `100.00` | total `81.00`; explanation `-10.00` then `-9.00` — the compounding is visible, not inferred ✔ |
| D3 | COFFEE `4.00 ×6`, COFFEE3 + COFFEE5 | 2 free, total `16.00`; COFFEE5 `NOT_APPLICABLE` (only 4 paid units remain) ✔ |
| D4 | WIDGET `12.50 ×2`, SAVE10 + TENOFF (both stackable) | total `12.50`, and the same if entered in the other order ✔ |
| D5 | WIDGET `1.00`, GIZMO `1.00`, TENOFF | total `0.00`; parts `(-1.00, -1.00)`; TENOFF `CAPPED amount 2.00, requested 10.00` ✔ |

A1 and A6 pin the degenerate explanation: a single `LIST_PRICE` adjustment, `sum(deltas) == 0.00 ==
final - basis`. I11 holds trivially, which is the right answer — an empty narrative is still a narrative.

D5 remains the case that breaks naive designs: the cap must happen *before* allocation, or the two lines
are handed `5.00` each and go negative; and it must be recorded as `2.00`, or the verdict and now also the
explanation claim a `10.00` discount the customer never received.

### 10.3 Cases the stage-2 rules newly pin down

These follow from decisions above and belong in the suite beside B1–B6.

| # | Cart | Codes | Result | From |
|---|---|---|---|---|
| E1 | WIDGET `50.00` | TENOFF (NS), SAVE10 (NS), entered in that order | TENOFF wins on value regardless of entry order; SAVE10 `SUPERSEDED` | §6.5 step 3 |
| E2 | WIDGET `50.00` | SAVE10 (NS), COFFEE3 (NS, no coffee in cart) | SAVE10 applies; COFFEE3 is `NOT_APPLICABLE`, **not** `SUPERSEDED`; nobody is marked superseded | §6.5 step 5 |
| E3 | WIDGET `3.00` | SAVE10 (NS, `0.30`), TENOFF (NS, capped to `3.00`) | TENOFF wins on the **capped** value; total `0.00`; TENOFF `CAPPED`, SAVE10 `SUPERSEDED` requested `0.30` | §6.5 step 2 |
| E4 | WIDGET `50.00` | SAVE10 (NS), TENOFF (NS), THIRD (NS, `2.00`) | TENOFF wins; SAVE10 **and** THIRD both `SUPERSEDED`, both naming TENOFF | §6.5 step 6, I17 |
| E5 | COFFEE `4.00 ×4` | COFFEE3 (NS), SAVE10 (NS) | contest is held at phase 10 (COFFEE3's slot, the earliest contender); both measured on the list cart | §6.5 contest point |
| E6 | WIDGET `50.00` | SAVE10 (NS), SAVE10 (NS) | second is `DUPLICATE` before the contest; the first applies alone; no supersession | §6.4 ordering |
| E7 | any cart | one NS code only | applies exactly as if stackable; no contest, no supersession | §6.5 step 5 |

E2 and E7 are the two that keep `SUPERSEDED` honest: it means *you lost a contest*, never *you did not
apply*. E3 is the one that keeps it truthful about money: the contest compares what the customer would
receive, not what the promotion claims.

---

## 11. How this should be tested (for the build stage, not built here)

- **The cases** of §10, table-driven — necessary, nowhere near sufficient.
- **Invariant properties** over generated carts and code sets: I2–I19 must hold for *every* input,
  including carts of 40 lines at `0.01`, quantities of 1, codes repeated five times, and every ordering of
  the same code set.
- **The agreement property, stated as a fuzz oracle**: for every generated quote, recompute every money
  figure independently from the explanation alone — `final = basis + sum(deltas)` per line, `total =
  sum(line finals)`, `code amount = -delta` — and assert equality with the published fields. This is the
  test that would have caught the bug that caused the refund, and it is expressible only because the
  explanation is complete.
- **The residue property**: assert that for every entry, `sum(parts) == the proposal's capped amount`, and
  that no `Adjustment` in any quote has a `code` that is not in `cart.codes`. A reconciliation line would
  have to appear as either a mismatched row sum or a nameless adjustment; both are checkable.
- **The contest property** (I18): over random non-stackable sets, the applied contender's amount is `>=`
  every superseded contender's `requested_amount`, and on equality its submission index is lower.
- **Contest × cap**, specifically E3: the winner must be chosen on capped value. A property that generates
  tiny subtotals with large `AMT` codes catches a comparison done on notional amounts.
- **Order fidelity** (I15): shuffle the input codes and assert that the *explanation order* tracks pipeline
  order, and that the amounts do not change except through the §6.5 tie-break.
- **Catalog fuzzing**: every field missing, mistyped, floated, out of range, duplicated, plus `stackable`
  as a string / number / null — assert the service always prices and always quarantines.
- **The BOGO boundary table** — quantities `n−1`, `n`, `n+1`, `2n`, `2n+1` against `floor(qty / n)`; for
  `COFFEE3` that is 2→0, 3→1, 4→1, 6→2, 7→2 free. This table *is* the specification. Add a second table
  for two stacked BOGOs on one SKU (§6.3).
- **The support view** (I20): over generated carts, assert that every submitted code appears exactly once
  across the view's two code sections, and that part 2 contains exactly the codes with a journal entry.
  A golden-file render of B3 is also worth keeping, because the sentence support reads aloud — "your code
  was valid, but the other one saved you more" — is assembled from four fields and nothing else.
- **Determinism**: price the same input twice in one process and once in a fresh one; bytes must match,
  explanations included.

---

## 12. Decisions at a glance

| Decision | Alternative rejected | Because |
|---|---|---|
| **The amounts are a fold of the explanation, not vice versa** | Compute amounts, then build a narrative beside them | Two paths drift; the PO's stated deal-breaker is exactly that drift. One record, three projections |
| **`explain` is a separate module and the only constructor of `Quote`** | Let the engine assemble the output | Makes "no second computation path" (I14) checkable by reading imports, not by testing outputs |
| **The journal is append-only, written only where the engine acts** | A mutable running total with notes attached | "In the order it happened" is then free, not maintained |
| **Opening adjustment has delta `0.00`; `basis` also published as a field** | Opening delta `= +basis`, deltas summing to the final price | PO: deltas add up to *what came off*, and *it has to be clear what we started from*. Only an opening balance satisfies both, and the basis is then stated twice from one fold |
| **No `RESIDUAL`/`ROUNDING` adjustment kind** | A reconciliation line when parts don't sum | The allocator makes parts sum exactly; an unrepresentable plug line is stronger than a rule against writing one |
| **Line explanations omit zero-share entries** | Every applied code on every line | PO: *if it didn't change that line's price, it doesn't need to be on that line*. The cart explanation still names it |
| **Contest measures with the same `would_take` that applies** | A separate "estimate" path | One capping function; the number that wins is the number that lands |
| **Contest held at the first contender's slot; winner applies there** (engineering's call, Q18) | Measure early, apply in the winner's own phase | Keeps the engine a single forward walk with nothing deferred. Applying later means either a stale figure that may need capping, or a re-evaluation — and then the number that won is not the number that lands |
| **Contest compares capped value** | Compare notional promotion value | "Larger discount" means what the customer receives (case E3) |
| **Contenders worth `0.00` leave the contest as `NO_EFFECT`, `superseded_by` left `None`** | Let them contest and be superseded | PO: *it wasn't beaten by anything — it just saved them nothing. Say that.* It also keeps `superseded_by` reliable as the answer to "which code beat mine?" |
| **`SUPERSEDED` reinstated as a status; `superseded_by` a first-class field** | Encode it in `detail` | `detail` is explicitly unstable internal prose; the front end must be able to branch on this |
| **`requested_amount` reused for supersession** | A second `forgone_amount` field | Same number, same question ("what was my code worth?"), stated once |
| **`stackable` defaults to `true`** | `non_stackable` defaulting to false | Every existing catalog keeps its meaning unedited; the field names a property, not its absence |
| **One global exclusion group** | Named groups, or a priority field | PO: *one rule: two of them can't sit together. Nothing more elaborate.* Priority would also be a second, silent answer to the tie-break already specified |
| **Non-stackable excludes only other non-stackables** | Excludes every promotion | PO: *non-stackable only means it can't sit next to another non-stackable one.* A cart with one non-stackable and one stackable code gets both |
| **`LineQuote.attribution` removed outright** | Keep both, or keep a deprecated alias | Two representations of one truth is the drift this stage removes; the explanation strictly dominates, and the PO confirms nothing reads the old field |
| **Non-events reported in the support view, not in the explanation** (our call, Q20) | Zero-delta entries in the explanation for unknown / duplicate / inapplicable codes | PO: *wherever support will see it.* That is a requirement about the screen; the explanation's rows stay exactly the rows that sum |
| **Signed `delta`, positive `amount`/`discount`, by a naming rule** (engineering's call, Q23) | One signed convention throughout | A `total_discount` of `-2.45` reads like a credit; the field name carries the convention and one negation in one module bridges them (§5.5) |
| **No version stamp on the quote** | A catalog revision or quote id | PO: *not now — build for today.* Two of the three need a clock or a store; the third is the caller's to supply |
| **No catalog "why not" text** | A per-promotion explanation string | PO: *code, name and amount is enough* — and it keeps `label` the only customer-ready string |
| **Invariant check before returning** | Trust the construction | A right price with a broken explanation is the bug that caused a refund; it must not leave the process |
| Pure `price(cart, catalog)` library + thin CLI | Local HTTP endpoint | No network in substrate; purity is testability — and is what makes the contest's speculative evaluation free |
| `Decimal` from strings only, floats rejected at the edge | Integer cents | Keeps the 2dp contract visible at every boundary; cents push the formatting bug to every caller |
| Rules propose, engine disposes | Rules mutate a running total | A bad rule cannot break the total; and it is why stage 2 needed no change to `rules` at all |
| Cart discounts allocated to lines (largest remainder) | Subtract from the total only | Lines must sum to the total, and now deltas must sum with no residue |
| Cap at application, in the journal | `max(0, total)` at the end | A late clamp makes both the verdicts and the explanation lie |
| Phase table keyed by kind | Order = submission order | Two customers typing the same codes in different orders must be charged the same |
| One verdict per submitted code | Error list | Impossible to silently drop a code; arity is checkable |
| Quarantine bad catalog entries at runtime, fail loudly in `validate` | Refuse to start | One typo must not stop the shop |
| TOML via stdlib `tomllib` | JSON | The file's audience is non-engineers editing constantly |
| Stacked BOGOs consume units sequentially | Each evaluated against original quantity | Independent evaluation can give a line away |
| Retirement = delete the entry; no `enabled` flag | A disable flag | Two mechanisms for "this code is over" |
| Currency in `[settings]`, once | Per-request currency field | Nothing to disagree with |
| Zero/negative quantity rejects the cart | Price it at 0.00, or drop the line | Keeps line-for-line correspondence with the caller's basket |
| No cart-size limit | A defensive cap | One linear in-memory pass |
| `status` + `label` are the interface; `detail` is unstable internal prose | One human-readable message per code | The front end owns customer wording; the explanation carries structure and `label`, never a sentence |
| `label` mandatory in the catalog | Optional, with the code as fallback | The storefront *and now the explanation* depend on it |
| A `0.00` total is a normal result | Refuse, or impose a minimum charge | Pricing must return the number downstream needs in order to decide |

---

## 13. Product answers and open questions

### 13.1 Stage-1 answers — closed, and still in force

| Q | Answer | Where it lives |
|---|---|---|
| Q1 BOGO at quantity 3 | One is free — `floor(qty / n)` | §6.3, boundary table §11 |
| Q2 PCT vs AMT order | PO indifferent; must be repeatable | §6.1 |
| Q3 Two 10% codes | 19%, compounded | §6.1, case D2 |
| Q4 Two BOGOs on one SKU | Both apply | §6.3 |
| Q5 Line price | What the customer pays; lines add up to the total | §2.3, I3, §5.3 |
| Q6 Duplicate code | Count once, tell the customer | §6.4 |
| Q7 Rounding | To the cent, same answer twice | §5.2, I1, I8 |
| Q8 Retiring a code | Delete it; `UNKNOWN` is the right message | §7.5 |
| Q9 Zero-quantity line | Engineering's call ⇒ reject as malformed | §4.2 |
| Q10 Currency | One currency, 2dp; configuration our call | §7.5 |
| Q11 Cart size | Engineering's call ⇒ no limit, linear pass | §8.1 |
| Q12 Stacked BOGO magnitude | Two — a coffee already given away doesn't earn another | §6.3 |
| Q13 Zero-value orders | Fine, it happens | §5.4 |
| Q14 Code matching | Customers type them however they like | §6.4 |
| Q15 Wording | Ours is internal; the front end writes the customer's | §2.4, §7.4 |

Q4's answer is the one stage 2 partially reverses: it removed `SUPERSEDED` on the grounds that nothing
could produce it. The non-stackable flag now can, and the status returns with a narrower and better-defined
meaning (E2, E7) than the one it had before it was deleted.

### 13.2 Stage-2 answers — all closed

| Q | Answer | Where it lives |
|---|---|---|
| Q16 What "non-stackable" excludes | Only another non-stackable; it still sits beside stackable codes | §6.5 "Scope of exclusion" |
| Q17 One group or named groups | One rule: two of them can't sit together. Nothing more elaborate | §6.5, §7.6 |
| Q18 Which slot the winner applies at | Engineering's call ⇒ the earliest contender's slot | §6.5 "Which slot the winner applies at" |
| Q19 A promotion worth `0.00` on a line | If it didn't change that line's price, it isn't on that line | §4.7 |
| Q20 Where non-events are reported | Ours to place ⇒ `code_results` in the payload, part 3 of the support view on screen | §4.8, §6.7, I20 |
| Q21 The shape of the opening entry | Deltas add up to what came off; what we started from must be clear | §2.2, I10–I12 |
| Q22 `LineQuote.attribution` | Nothing reads it ⇒ removed outright | §2.3 |
| Q23 Sign convention | Engineering's call ⇒ `delta` is signed, `amount`/`discount` are magnitudes | §5.5, §4.7, I19 |
| Q24 A stamp for auditors | Not now — build for today | §1.3, §9 |
| Q25 A catalog-authored "why not" line | Code, name and amount is enough | §2.2, §7.6 |

Three of these changed the design rather than confirming it. **Q20** moved a requirement off the data
structure and onto the renderer, which turned a vague "the front end will show something" into a
four-part support view with an invariant (I20) — the explanation stays exactly the rows that sum, and
support still sees every code on one screen. **Q24** and **Q25** each removed something the design had
been prepared to carry: no version stamp, and no free text anywhere in the explanation. Both subtractions
are worth having, because a field added speculatively is a field someone must later be talked out of
depending on.

**Q16 and Q17 confirmed the narrow reading**, which is the more valuable outcome than it looks: they close
off named groups, per-promotion exclusion lists and priority fields, all of which a later reader will be
tempted to add the first time a merchandiser asks a slightly harder question. When that day comes it is a
new product decision, not a gap in this one — and §9 prices it.

**Three questions were delegated back to engineering** (Q18, Q20, Q23). Each is recorded above with its
reasoning in the body rather than left as an assumption, which is the same treatment stage 1 gave Q9, Q10
and Q11. The test for whether that was done honestly is whether a reader who disagrees can find the
argument and the one place to change it; for these three that is §6.5, §4.8 and §5.5 respectively.

### 13.3 Nothing is open

Every product decision in this document traces to an answer in §13.1 or §13.2, or to an explicitly
delegated engineering call recorded with its reasoning in §12.

The mechanism is the part worth defending in review, and it is not open: **one append-only journal, three
projections, no second computation path**, and a contest that measures with the same function it applies
with. Every question answered above changed *what goes into the journal* or *what is shown from it*. None
of them touched the property the PO actually asked for — that the explanation and the amount are the same
numbers read two ways, and so cannot disagree.

What that does not mean is that nothing will change. The requests most likely to arrive next are visible
from here — named exclusion groups, "best of" across all promotions, dated codes, a version stamp, tax —
and §9 states what each costs before anyone has to estimate it under pressure. The first three are cheap
because of where the seams were put: the contest already ranks a set of candidates, so widening the set or
splitting it into groups is a change to *which* candidates compete, not to how competition works. A second
currency is not cheap, and is flagged as a redesign precisely so it is never quoted as a field.

The build can start from this document. §3's invariants and §10's traced cases, taken together, are the
acceptance criteria; §11 says what the test suite has to cover beyond them.
