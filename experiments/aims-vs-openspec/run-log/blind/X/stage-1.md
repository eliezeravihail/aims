# Cart Pricing Service — Architecture

A service that answers one question: what does this cart cost? It takes a customer id, a list of lines
(SKU, list unit price, quantity) and the promotion codes the customer typed, and returns what every line
costs and what the cart costs — with an outcome for every code, so nothing is silently swallowed.

Promotion definitions live in a data file the commercial team edits directly. Codes are added and retired
constantly and must not require an engineer.

## 1. Context and constraints

Fixed substrate:

- Python 3.11+, standard library only. A new runtime dependency would have to earn its place; none does.
- `decimal.Decimal` is available. Nothing mandates it, but see Decision 1.
- Single process, single currency, no UI, no network, no database, no persistence.
- Entry point may be a library with a CLI or a local HTTP endpoint. See Decision 8.

The forcing constraint is not in the substrate — it is in the request. **PCT and AMT are declared against
the whole cart, but the caller wants a number for every line.** A cart-level amount therefore has to come
back down onto the lines, and the moment it does, rounding can make the lines stop summing to the total.
Everything structural below follows from taking that seriously.

The acceptance table pins down more than it appears to. Case A5 — `COFFEE 4.00 x4` and `WIDGET 12.50 x1`
with `COFFEE3` and `SAVE10`, expecting `22.05` — reconciles exactly one way:

```
  list subtotal            28.50
  COFFEE3  (1 free @4.00)  -4.00   ->  24.50
  SAVE10   (10% of 24.50)  -2.45   ->  22.05
```

Ten percent of the *list* subtotal would be `2.85` and give `25.65`. So the order is not a preference we
are free to choose: BOGO resolves first, and PCT is taken against the amount left behind. The design
encodes that as data — a scope ordinal — not as a sequence of statements someone can reorder by accident.

## 2. Goals and non-goals

**Goals**

- One pure function is the product: `price(request, catalogue) -> PricedCart`. Everything else is an
  adapter or a helper.
- `sum(line amounts) == cart total` holds by construction for every input, not because the test cases
  happen to divide evenly.
- Exactly one place in the system rounds, and exactly one place can violate the sum invariant. Both are
  small enough to reason about completely.
- Adding a fourth promotion kind is a new rule class plus a catalogue schema entry. The engine does not
  learn about it.
- The result explains itself: every line lists the adjustments that produced it, every code reports what
  it actually took off. A support agent can answer "why is this 22.05?" from the response alone.
- A promotion-file typo costs exactly one promotion code, never the shop. It is reported completely and
  actionably, and it is loud in the one place that can act on it before customers do: a check the
  commercial team runs on the file themselves.

**Non-goals**

- No product catalogue. Unit prices arrive in the request and are trusted; the service never looks up or
  second-guesses a price. A real trust boundary, and deliberate — it keeps `price()` pure and testable
  against any price the caller invents.
- No promotion state: no budgets, no usage counts, no per-customer redemption history. Those need
  persistence, which the substrate excludes, and they would make `price()` impure.
- No tax, shipping, currency conversion or eligibility. The customer id is carried through untouched and
  drives no rule today.
- No concurrency design. Everything is immutable and there is no shared mutable state, so there is nothing
  to guard; that is the whole story.

## 3. Components and the seams between them

```
                  catalogue.toml            (edited by the commercial team)
                        |
                        v
             +---------------------+
             |  catalogue          |  parse, validate, build rules
             +---------------------+
                        |  Catalogue: code -> PromotionRule
                        v
  CartRequest -->  +--------------------------------------+
                   |  engine.price()                      |
                   |    validate cart                     |
                   |    resolve codes  -> rules, rejects   |
                   |    sort by (scope, code)             |
                   |    fold rules over CartState         |
                   |    render PricedCart                 |
                   +--------------------------------------+
                      |             |               |
                      v             v               v
                 +---------+   +---------+   +--------------+
                 |  rules  |   |  money  |   |  allocation  |
                 | Pct Amt |   | quantize|   |  apportion   |
                 |  Bogo   |   | clamp   |   | (largest     |
                 +---------+   +---------+   |  remainder)  |
                      |             ^        +--------------+
                      +-------------+                |
                                    +----------------+
                        +---------+
                        | models  |  frozen dataclasses + cart validation
                        +---------+
                             ^
                   (everything depends on models; models depends on money only)

   cli  ->  catalogue, engine, models        (adapter; no pricing logic)
```

Arrows point the way dependencies run. What each component owns:

| Component | Owns | Never does |
|---|---|---|
| `money` | The single rounding rule; exact parsing; the non-negative clamp primitive | Know what a cart or a promotion is |
| `allocation` | Splitting one exact amount across weights so the parts sum to the whole | Know what a cart or a promotion is |
| `models` | Request and result shapes; cart validity; `CartState` and its transition | Know how any promotion behaves |
| `rules` | What each promotion kind *means*, given a cart state | Round, clamp, order itself, or see another rule |
| `catalogue` | The file format, the entry schema, validation, quarantining bad entries, building rule objects | Price anything, or decide what to do about a rejected entry |
| `engine` | Order, the floor, apportionment, attribution, rendering | Know that PCT, AMT or BOGO exist by name |
| `cli` | JSON in and out, exit statuses | Contain a pricing rule |

`money` and `allocation` are leaves that know nothing about promotions — which is precisely what makes the
two invariant-critical pieces testable in isolation against pure arithmetic properties.

## 4. Decisions

### Decision 1 — Money is `Decimal`, and exactly one module is allowed to round

**Choice.** All money is `decimal.Decimal` at two decimal places. A `money` module owns three operations —
quantize to two places with `ROUND_HALF_UP`, parse an exact money value from a string, and clamp to
non-negative — and nothing else in the codebase calls `.quantize()` or constructs a `Decimal` from a float.

**Why.** Binary floating point cannot represent `0.10` or `12.50`, so a float pipeline accumulates error
that surfaces as a stray cent under exactly the conditions nobody tests. The alternative that avoids
`Decimal` is integer cents everywhere, which is also exact and genuinely faster. It loses on readability at
the boundary: percentages become integer arithmetic with explicit scaling, the catalogue has to be written
in cents (`amount = 1000` for ten pounds — an invitation to a factor-of-100 mistake by the very people we
said would edit it), and every error message has to re-divide. `Decimal` keeps the domain language and is
exact. Cents would be right only if profiling demanded it, and nothing here is hot.

The single-rounding-site rule matters more than the type choice. Rounding scattered across a codebase is
how `sum(lines) != total` gets in: two places round the same quantity differently and neither is wrong on
its own. Concretely, `quantize` is reached from exactly two kinds of site — where a *rate* becomes an
*amount*, and where a *proportional share* becomes *cents*. Everywhere else money is added and subtracted,
which `Decimal` does exactly at two places with no rounding at all.

`ROUND_HALF_UP`, not `ROUND_HALF_EVEN`: retail money rounds half up, and the statistical-bias argument for
banker's rounding applies to summing many independently rounded values — which this design specifically
does not do, because it apportions one exact amount instead.

The library never mutates the global decimal context. Setting precision at import would silently change
the arithmetic of any application embedding us; extra precision for an intermediate product is taken
inside a `localcontext()`.

### Decision 2 — Cart-scoped discounts are apportioned by largest remainder

**Choice.** A cart-scoped promotion produces one cart-level amount, quantized once. That exact amount is
then split across lines: each line takes its exact proportional share **truncated down** to whole cents,
and the residual cents are handed out one each to the lines with the largest truncated fractions, ties
going to the earlier line. This lives in `allocation` as a single function over an amount and a list of
weights, with no knowledge of carts or promotions.

**Why this shape.** The obvious alternative — apply the percentage to each line and let the total be the
sum — is wrong twice over. It rounds N times instead of once, so the total drifts from the percentage the
customer was promised; and it cannot express AMT at all, because "ten pounds off" is not a per-line
quantity until you decide how to split it. The other alternative — keep full precision per line and round
only for display — fails the moment anything downstream (tax, a refund, a ledger) adds the displayed lines
back up and gets a different number.

Largest remainder is chosen over "give the whole residual to the largest line" or "to the last line"
because it distributes the error where it is least visible, and the tie-break on line position makes it
fully deterministic.

**Why truncate rather than round each share.** This is the load-bearing detail. Rounding each share
half-up can *over*-allocate — three shares of `0.335` round to `0.34` each, `1.02` against an amount of
`1.00` — and there is no way to claw back an overdraft without picking a victim line. Truncation can only
ever under-allocate, and by at most (number of lines − 1) cents, which is exactly the residual the
largest-remainder pass gives back. The algorithm is correct because of that asymmetry, not by luck.

**Worked.** Amount `1.00` over lines standing at `3.33`, `3.33`, `3.34`:

```
  exact shares    0.333    0.333    0.334
  truncated       0.33     0.33     0.33     = 0.99   (residual 0.01)
  fractions       0.3      0.3      0.4
  residual cent            ->  to line 3 (largest fraction)
  result          0.33     0.33     0.34     = 1.00   exactly
```

The function's contract is `sum(parts) == amount`, unconditionally. Zero-weight lines take nothing. A
total weight of zero with a non-zero amount is an internal invariant violation and raises rather than
returning something plausible — but the engine makes it unreachable (Decision 4).

### Decision 3 — Each promotion kind is a rule object behind one interface

**Choice.** A rule declares its code and its scope, and answers one question:

```python
class Scope(IntEnum):
    LINE          = 0    # BOGO: knows which lines it touches
    CART_PERCENT  = 1    # PCT
    CART_AMOUNT   = 2    # AMT

class PromotionRule(Protocol):
    code: str            # canonical, upper-cased
    scope: Scope
    def evaluate(self, state: CartState) -> RuleOutcome: ...

@dataclass(frozen=True)
class Applied:
    value: Decimal                              # what it would take, quantized
    per_line: Mapping[int, Decimal] | None      # None => the engine apportions it

@dataclass(frozen=True)
class NotApplicable:
    reason: RejectionReason
    message: str

RuleOutcome = Applied | NotApplicable
```

**Why the `per_line | None` split.** This is the seam that makes the three kinds one thing. BOGO already
knows exactly which lines its free units came from and must *not* be apportioned — the free coffee comes
off the coffee line, not proportionally off the widget. PCT and AMT genuinely are cart-wide and have no
opinion about lines. One return type covers both: a rule that knows, says; a rule that does not, defers,
and the engine apportions. A future tiered discount, category-wide percentage, or spend-threshold gift
picks whichever arm fits, without a new concept.

**Why not `if kind == "PCT": ... elif ...` in the engine.** Because the stated pressure from the product
owner is that promotions change constantly. Today that means new *codes*, which the catalogue already
absorbs. Kinds follow codes — they always do — and the branch version makes every new kind an edit to the
one function that must never break. Here the engine's loop never mentions PCT, AMT or BOGO.

**Rules are pure and blind.** A rule reads the state, returns an outcome, and never mutates anything, never
rounds by itself (it asks `money`), never learns about other rules, and never applies the non-negative
floor. Every one of those is the engine's job, because each is a place the invariants could break and they
should break in one file or not at all.

What each rule means:

- **PCT** — the rate applied to the cart's *current* amount, quantized once, apportioned by the engine.
  Because each rule acts on what the previous one left, two 10% codes take 19% off, not 20%.
- **AMT** — its full declared amount, returned without clamping; the engine caps it.
- **BOGO** — the named SKU's quantity summed **across all lines** (the promotion says "in the cart", not
  "on this line"), then one unit free for every N units: `free = quantity // N`. Three in the cart makes
  one free, four or five still one, six makes two. Free units are drawn from the lowest-priced units first
  and attributed to the lines they came from — the same SKU really does appear at two prices in this
  catalogue, so the cheapest-first rule is load-bearing rather than decorative.

### Decision 4 — The engine is a fold, and it owns order, the floor, and attribution

**Choice.**

```
  state = one LineState per submitted line, current_amount = list amount

  for rule in sorted(resolved, key=(rule.scope, rule.code)):
      outcome = rule.evaluate(state)

      NotApplicable -> record the rejection; state unchanged; carry on

      Applied ->
          value  = min(outcome.value, state.remaining)          # the floor, applied once, here
          capped = value < outcome.value
          parts  = outcome.per_line  or  apportion(value, [line.current_amount ...])
          state  = state.reduced_by(parts, attributed_to=rule.code)
          record applied(value, capped, no_effect = value == 0)
```

**Why the floor lives here, not in AMT.** "A cart total is never negative" reads like a property of
fixed-amount discounts, and it would be easy to clamp inside the AMT rule. Putting it in the fold instead
makes it structurally impossible for *any* rule — including the fourth kind nobody has written yet — to
drive the cart below zero, however wrong that rule is. A rule may honestly return its full declared value
and let the engine tell it what was actually available. That is why case A7 reports `TENOFF` as applied
taking `1.00` and *capped*, rather than as applied taking `10.00` or as rejected: the customer used the
code, it just ran out of cart.

**Why sort by scope, then code.** Ordering is a business rule, so it should be data. The `Scope` ordinal
*is* the ordering policy, stated once. The secondary sort on code makes multiple promotions of one kind
independent of the order the customer typed them — two customers with the same basket and the same two
codes must not get different prices because one typed them the other way round. Submitted order is still
preserved for *reporting*, which is a separate concern.

**Why PCT before AMT.** The requirement placed on us is that the answer be the same every time for the
same cart; the order itself is ours to pick, and fixing it in the `Scope` ordinal satisfies both. We keep
percentage before fixed amount because it preserves the face value of a voucher: a customer holding
"10.00 off" gets 10.00 off, or whatever remains, instead of having their voucher quietly shaved by a
percentage applied after it. That is the version that can be explained at a support desk, and it is the
more generous of the two orderings — the right default for a discount the customer was already promised.

**Attribution comes free.** `reduced_by` records, per line, which code took what. That is the whole
explainability requirement, and it falls out of the fold rather than being a second pass that can disagree
with the first.

**Line-level floor.** `apportion` cannot produce a part larger than a line's own amount, because the value
is already capped at the cart remaining and shares are proportional to line amounts — so no line goes
negative either. A line already at `0.00` has weight zero and takes nothing.

### Decision 5 — The catalogue is TOML, with money and rates written as quoted strings

**Choice.**

```toml
[[promotion]]
code = "SAVE10"
kind = "PCT"
rate = "10"        # quoted: parsed as an exact Decimal

[[promotion]]
code = "TENOFF"
kind = "AMT"
amount = "10.00"   # quoted

[[promotion]]
code = "COFFEE3"
kind = "BOGO"
sku  = "COFFEE"
n    = 3           # unquoted: TOML integers are exact, so this one is safe bare
```

**Why TOML.** It is in the 3.11 standard library (`tomllib`), so it costs no dependency; it supports
comments, so an entry can say why it exists and when it retires; and it has no trailing-comma or quoting
traps for a non-engineer editing in a hurry. JSON is the serious alternative and also dependency-free, and
`json.load(parse_float=Decimal)` even defuses the float problem — but it has no comments, and a missing
comma produces a parse error at a character offset rather than at an entry. CSV cannot carry parameters
that differ by kind without a column zoo. YAML would need a dependency and is ruled out by the substrate.

**Why the money fields are quoted.** TOML floats are IEEE-754 binary: `amount = 10.10` parses to
`10.0999999999999996...`, and the catalogue's formatting would leak into prices. Writing money and rates
as strings and parsing them with `Decimal(str)` keeps them exact. Integers are exempt because TOML
integers are exact, which is why `n = 3` is bare — the inconsistency is deliberate and worth one line of
explanation in the file header, because forcing `n = "3"` would suggest quoting is cosmetic. The loader
**rejects** a bare float in a money field rather than coercing it, with a message that says to quote it;
silently coercing would hide the one mistake this rule exists to catch.

### Decision 6 — A malformed catalogue entry is quarantined; only an unreadable file is fatal

**Choice.** Loading validates every entry, keeps the valid ones, and skips the invalid ones. It returns
the catalogue **together with a report** of everything it rejected, each identified by entry and field:

```python
@dataclass(frozen=True)
class LoadResult:
    catalogue: Catalogue              # built from the entries that were valid
    rejected: tuple[EntryError, ...]  # one per skipped entry, with entry and field
```

A quarantined code behaves exactly as if it were absent: a cart submitting it is told the code is unknown,
and every other promotion still applies. A file that cannot be parsed *as a whole*, or is missing, is a
different matter and still fails hard — there are no entries to salvage, and producing an empty catalogue
would silently switch every promotion off while appearing to work.

**Why this, and what it costs.** The instruction is explicit: one typo must not stop the shop selling.
That is the right call for a file edited daily by people who are not engineers, and it is the opposite of
what a "fail loudly at load" instinct would produce. The cost is real and worth naming: the failure moves
from deploy time to checkout time. A broken code is one the marketing email has already promised, and the
customer who types it is told we have never heard of it. Nobody finds out from the service itself.

So the design compensates in two places rather than accepting that silently:

1. **The rejects are returned, not logged.** Making them part of the load result means ignoring them is a
   deliberate act by the caller, not an oversight. The CLI writes them to stderr on every run.
2. **`check-catalogue` becomes the loud gate.** Since loading no longer refuses anything, the checker is
   now the *only* place a broken entry stops something — so it reports failure whenever any entry was
   rejected, and the publishing process should refuse to ship a file that fails it. That restores the
   deploy-time alarm without ever blocking a checkout.

Together these give both properties the situation actually needs: lenient at runtime, loud at publish
time.

**Why a duplicate code is quarantined rather than resolved.** Two definitions of `SAVE10` is not a typo in
one entry; it is a question we cannot answer. Taking the first, or the last, would price carts on a coin
toss — the one failure mode worse than an unknown code, because it is invisible. So that code alone is
withdrawn and reported, and the rest of the file loads. That costs one code, not the shop.

### Decision 7 — Codes are resolved before anything is applied, and every one gets an outcome

**Choice.** A resolver pass normalises each submitted code (`strip().upper()`), looks it up, and classifies
it: resolved to a rule, unknown, or a duplicate of one already seen. Only resolved rules enter the fold.
The result reports an outcome for every submitted code, in submitted order, from a closed set: applied
(with the value taken, whether it was capped, and whether it had no effect), or rejected with
`UNKNOWN_CODE`, `NOT_APPLICABLE` or `DUPLICATE`.

**Why a closed enum and not a message.** A caller has to branch on this — "unknown code" is a typo the
customer can fix, "not applicable" is a basket they can fix, and the two deserve different words in the UI.
Free-text reasons get parsed by desperate callers.

**Why "applied, took `0.00`" is not a rejection.** The code was real and it was used; the cart just had
nothing left. Reporting it as a rejection would tell the customer their valid code was bad. It is flagged
`no_effect` so the customer can be told that it was accepted and saved them nothing.

**Why three reasons are enough.** Retirement is done by deleting the entry from the catalogue, so there
are no validity dates and no expired state to report — a retired code is simply unknown, which is the
right thing to tell a customer. A quarantined entry lands in the same place for the same reason: the
customer-facing answer is "unknown code", while the operator-facing detail lives in the load report where
it can actually be acted on. Two audiences, two channels, one closed enum.

**Cart errors and code errors are deliberately different.** A malformed *cart* (quantity `0`, negative
price) rejects the whole request: that is a caller bug, and pricing it would invent an answer. A bad *code*
never does, because the product owner's rule is explicit — the rest of the cart still prices.

### Decision 8 — Library with a thin CLI, not an HTTP endpoint

**Choice.** `price(request, catalogue) -> PricedCart` is the contract. The CLI is one adapter: a `price`
subcommand reading a cart as JSON on stdin and writing the result as JSON on stdout, and a
`check-catalogue` subcommand. Exit status distinguishes success, bad cart, and bad catalogue; rejected
codes do not affect it, because a cart with an unknown code priced successfully.

**Why not HTTP.** The substrate forbids network, persistence and multi-process anyway, so an HTTP endpoint
would buy nothing and cost a server lifecycle, request parsing, status-code mapping and a concurrency
story. A CLI over JSON is scriptable, diffable, and makes the acceptance table an exact fixture comparison.
If the product later needs HTTP, it is a second adapter over the same function — the engine does not
change, which is the point of putting the contract at the function rather than at the transport.

**The JSON boundary re-introduces floats, so it is a named rule.** Money is written as strings on output
(`"12.50"`, not `12.50`) and parsed from strings or with `parse_float=Decimal` on input. This is exactly
the leak Decision 1 exists to prevent, and the easiest one in the system to reintroduce by accident at the
last mile.

## 5. The acceptance table against this design

| # | Path through the design | Result |
|---|---|---|
| A1 | No codes; lines render at list | line `25.00`, total `25.00` |
| A2 | PCT on `25.00` -> `2.50`, apportioned to the one line | total `22.50` |
| A3 | AMT returns `10.00`; engine caps at `25.00` remaining, no cap needed | total `15.00` |
| A4 | BOGO N=3, 4 units -> `4 // 3` = 1 free @ `4.00` | total `12.00` |
| A5 | Scope order: BOGO (`-4.00`) then PCT on `24.50` (`-2.45`); apportioned `1.20` / `1.25` | lines `10.80` + `11.25`, total `22.05` |
| A6 | `NOPE` fails resolution -> `UNKNOWN_CODE`; fold sees no rules | total `12.50`, code reported |
| A7 | AMT returns `10.00`; engine caps at remaining `1.00`, marks capped | total `0.00`, never negative |

A5 is the case that validates the whole structure: it needs the ordering (Decision 4), cross-scope
composition (Decision 3), and apportionment back onto two lines (Decision 2) to all be right at once.

## 6. Risks and trade-offs

- **A rounding or apportionment bug is invisible until it is expensive** → the sum invariant is the stated
  contract of one small function with no domain knowledge, checkable exhaustively over random amounts and
  weights. Three-way splits of an odd cent are the cases worth generating rather than hand-picking.
- **Quarantining a broken entry moves the failure from deploy time to checkout time** → the right call for
  availability, but it means a code the marketing email promised can fail silently in front of a customer.
  Mitigated by returning the rejects in the load result rather than logging them, by writing them to
  stderr on every run, and above all by `check-catalogue` reporting failure so publishing can be gated.
- **`check-catalogue` is now the only loud alarm** → if nobody wires it into the publishing process, broken
  entries reach production unnoticed. That makes it an operational requirement rather than a convenience,
  which is why it appears in the deployment note rather than as a nice-to-have.
- **The application order encodes a business rule in a `Scope` enum** → one ordinal per kind in one place,
  read by the fold as data. With the order delegated to us and only stability required, the risk is not
  the choice but that a later reader mistakes it for an implementation detail; the enum carries the
  reasoning and the spec states the order normatively.
- **BOGO's threshold reads two ways in English** → "for every 3, one free" can mean one free at three, or
  a group of four with one free at four. Case A4 cannot tell them apart. The settled rule is the first:
  `free = quantity // N`. This is the one place where the spec's wording and a casual reading of the code
  name can diverge, so the rule states the quantities explicitly at three, four and six.
- **The service trusts the prices it is given** → no product catalogue means a caller passing a wrong unit
  price gets a confidently wrong total. A deliberate boundary, but it belongs in whatever contract governs
  the caller.
- **Stacking limits and exclusivity are coming but not built** → both are expected; today's behaviour is
  unlimited stacking with no exclusivity. Building them speculatively would be worse, but the seam is
  named so it is an addition later, not a rework: a limit is a filter over the resolved rules before the
  fold, and exclusivity is a catalogue field plus the same filter. Neither touches `money`, `allocation`,
  or the rules themselves.
- **The customer id currently does nothing** → carried through untouched so the result is self-describing,
  and the natural hook for a future eligibility rule, which is also deferred. Carrying an unused field is
  a small smell; inventing eligibility semantics nobody asked for would be a larger one.

## 7. Deployment note

Nothing exists yet, so there is no migration, no rollback path and no compatibility surface.

The operational note is the catalogue. It is a production input owned outside engineering, and because a
malformed entry is quarantined rather than fatal, the service itself will never refuse a bad file. The
publishing process should therefore run `check-catalogue` against the candidate file and refuse to ship on
failure. That gate is the entire safety story for a file that can otherwise take a promised promotion
offline without anyone being told.

## 8. Settled business rules

These are confirmed, not assumptions:

| Rule | Settled as |
|---|---|
| BOGO threshold | One free for every N in the cart — three in the basket means one is free (`quantity // N`) |
| Two percentage codes | Compound: two 10% codes take 19% off, not 20% |
| Order of application | Ours to choose provided it is stable per cart; PCT before AMT |
| Rounding | Must come out to the cent and be reproducible; half-up is our tie-break within that |
| Malformed catalogue entry | Quarantined and reported, never fatal |
| A code that takes `0.00` | Accepted, saved nothing — not a rejection |
| Same SKU at two prices | Happens in practice; the cheapest units are the free ones |
| Stacking limits, exclusivity, customer-id rules | Expected later, deliberately not built now |
| Retiring a code | Delete the entry; a retired code is reported as unknown |

Two of these moved the design rather than confirming it: **BOGO** was originally specified as groups of
N+1 (one free at four), and the **catalogue** originally refused to load at all if any entry was
malformed. Both were revised — the first in the rule and its scenarios, the second in Decision 6, the
catalogue and CLI behaviour, and the deployment note.

## 9. Genuinely open, and safely deferrable

None of these changes the components, the seams, or the work:

- Where the catalogue file lives and how a deployment points at it. The loader takes a path either way.
- Whether the result should also carry a machine-readable trace of how each cart-scoped discount was
  apportioned, beyond the per-line attribution it already has. Purely additive.
- Whether `check-catalogue` should eventually be its own entry point, for a publishing pipeline with no
  reason to install the pricing library — more attractive now that it is the gate the catalogue's safety
  depends on.
- Whether the quarantine report should also reach an operator through a channel of its own, rather than
  only through the load result and stderr. A deployment concern; it does not change the loader.
