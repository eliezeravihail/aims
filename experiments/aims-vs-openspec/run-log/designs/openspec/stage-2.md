# Cart Pricing Service — Architecture

A service that answers one question, and shows its working: what does this cart cost, and why? It takes a
customer id, a list of lines (SKU, list unit price, quantity) and the promotion codes the customer typed,
and returns what every line costs and what the cart costs — each amount accompanied by the ordered chain of
adjustments that produced it, and each submitted code accounted for, so nothing is silently swallowed.

Promotion definitions live in a data file the commercial team edits directly. Codes are added and retired
constantly and must not require an engineer. The file also says which promotions refuse to be combined with
one another.

## 1. Context and constraints

Fixed substrate:

- Python 3.11+, standard library only. A new runtime dependency would have to earn its place; none does.
- `decimal.Decimal` is available. Nothing mandates it, but see Decision 1.
- Single process, single currency, no UI, no network, no database, no persistence.
- Entry point may be a library with a CLI or a local HTTP endpoint. See Decision 8.

Three forcing constraints, none of them in the substrate.

**One — PCT and AMT are declared against the whole cart, but the caller wants a number for every line.** A
cart-level amount has to come back down onto the lines, and the moment it does, rounding can make the lines
stop summing to the total.

**Two — every amount must arrive with the ordered list of adjustments that produced it, and the two must
never disagree.** Finance and support cannot defend a number they cannot decompose; a refund has already
been given away because nobody could show the working. The naive shape — compute the money, then write a
commentary describing it — is exactly the shape that drifts, because there are then two representations of
one fact and only one of them is load-bearing. So the explanation here is not a report produced beside the
arithmetic: it is the structure the arithmetic runs on (Decision 9).

**Three — some promotions refuse to be combined.** When two non-stackable codes both qualify, one must win
on the money it actually saves the customer, and the loser must be visible, named, and attributed to the
code that beat it (Decision 10).

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
That worked trace is also, almost verbatim, the explanation the service now returns for the same cart.

## 2. Goals and non-goals

**Goals**

- One pure function is the product: `price(request, catalogue) -> PricedCart`. Everything else is an
  adapter or a helper.
- `sum(line amounts) == cart total` holds by construction for every input, not because the test cases
  happen to divide evenly.
- Every reported amount is the end of an explanation, not a number kept beside one. The explanation and the
  amount cannot disagree because there is only one of them.
- The deltas in any explanation sum exactly to the difference between its list amount and its final amount,
  with no residue and no balancing entry — and no residue exists to confess.
- An explanation lists price changes and nothing else. What happened to a code that changed no price is
  answered in the outcome list returned beside it, so neither artifact is padded with the other's job.
- Exactly one place in the system rounds, and exactly one place can violate the sum invariant. Both are
  small enough to reason about completely.
- When two promotions cannot be combined, the customer gets the one worth more to them, judged on the money
  it actually takes off this cart; the one they did not get is reported by name with the code that beat it.
- Adding a fourth promotion kind is a new rule class plus a catalogue schema entry. The engine does not
  learn about it, and it inherits stackability and explanation for free.
- A promotion-file typo costs exactly one promotion code, never the shop. It is reported completely and
  actionably, and it is loud in the one place that can act on it before customers do: a check the
  commercial team runs on the file themselves.

**Non-goals**

- No product catalogue. Unit prices arrive in the request and are trusted; the service never looks up or
  second-guesses a price. A real trust boundary, and deliberate — it keeps `price()` pure and testable
  against any price the caller invents.
- No promotion state: no budgets, no usage counts, no per-customer redemption history. Those need
  persistence, which the substrate excludes; they would also make `price()` impure.
- No concurrency design. Everything is immutable and there is no shared mutable state, so there is nothing
  to guard; that is the whole story.
- No i18n or currency handling. One currency, two decimal places, no symbol in the data model.
- No presentation policy. The service returns the full explanation, including the step for a promotion that
  was superseded; whether a customer-facing screen shows it is the caller's choice.
- No retention. The explanation travels with the result and is never stored. A caller that may have to
  answer for a price later keeps the result it was given; the service holds no history and never needs to
  re-price a past cart in order to explain it.

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
                   |      - arbitrate non-stackables      |
                   |      - cap, apportion, post steps    |
                   |    verify the chains                 |
                   |    render PricedCart                 |
                   +--------------------------------------+
                      |          |          |            |
                      v          v          v            v
                 +---------+  +--------+  +-----------+  +--------------+
                 |  rules  |  | money  |  |  ledger   |  |  allocation  |
                 | Pct Amt |  |quantize|  | Step      |  |  apportion   |
                 |  Bogo   |  | clamp  |  | Ledger    |  | (largest     |
                 +---------+  +--------+  | post()    |  |  remainder)  |
                      |           ^       | current   |  +--------------+
                      +-----------+       +-----------+         |
                                  |             |               |
                                  +-------------+---------------+
                        +---------+
                        | models  |  frozen dataclasses + cart validation
                        +---------+
                             ^
        (everything depends on models; models depends on money and ledger only)

   cli  ->  catalogue, engine, models        (adapter; no pricing logic)
```

Arrows point the way dependencies run. What each component owns:

| Component | Owns | Never does |
|---|---|---|
| `money` | The single rounding rule; exact parsing; the non-negative clamp primitive | Know what a cart or a promotion is |
| `allocation` | Splitting one exact amount across weights so the parts sum to the whole | Know what a cart or a promotion is |
| `ledger` | The explanation: steps, the linked chain, `current` as a projection of it, the chain invariants, and the rule that a step exists only where a price changed | Know what a promotion means, or decide which ones apply |
| `models` | Request and result shapes; cart validity; `CartState` over the ledgers | Know how any promotion behaves |
| `rules` | What each promotion kind *means*, given a cart state | Round, clamp, order itself, see another rule, or read its own stackability |
| `catalogue` | The file format, the entry schema and modifiers, validation, quarantining bad entries, building rule objects | Price anything, or decide what to do about a rejected entry |
| `engine` | Order, arbitration between non-stackables, the floor, apportionment, posting steps, the boundary guard, rendering | Know that PCT, AMT or BOGO exist by name |
| `cli` | JSON in and out, exit statuses | Contain a pricing rule, or compute, merge or reorder an explanation step |

`money`, `allocation` and `ledger` are leaves that know nothing about promotions — which is precisely what
makes the three invariant-critical pieces testable in isolation against pure arithmetic properties.
`allocation` owns *the parts sum to the whole*. `ledger` owns *the chain links, and the deltas sum to the
difference*. `money` owns *there is exactly one rounding rule*. Every money guarantee this service makes is
one of those three, composed by the engine.

## 4. Decisions

### Decision 1 — Money is `Decimal`, and exactly one module is allowed to round

**Choice.** All money is `decimal.Decimal` at two decimal places. A `money` module owns three operations —
quantize to two places with `ROUND_HALF_UP`, parse an exact money value from a string, and clamp to
non-negative — and nothing else in the codebase calls `.quantize()` or constructs a `Decimal` from a float.

**Why.** Binary floating point cannot represent `0.10` or `12.50`, so a float pipeline accumulates error
that shows up as a stray cent under exactly the conditions nobody tests. The alternative that avoids
`Decimal` is integer cents everywhere, which is also exact and genuinely faster. It loses on readability at
the boundary: percentages become integer arithmetic with explicit scaling, the catalogue has to be written
in cents (`amount = 1000` for ten pounds, an invitation to a factor-of-100 mistake by the very people we
said would edit it), and every error message has to re-divide. `Decimal` keeps the domain language and is
exact; cents would be the right call only if profiling demanded it, and nothing here is hot.

The single-rounding-site rule matters more than the type choice. Rounding scattered across a codebase is how
`sum(lines) != total` gets in: two places round the same quantity differently and neither is wrong on its
own. Concretely, `quantize` is reached from exactly two kinds of site — where a *rate* becomes an *amount*,
and where a *proportional share* becomes *cents*. Everywhere else money is added and subtracted, which
`Decimal` does exactly at two places with no rounding at all. That is also why an explanation needs no
rounding line: after the single quantization, nothing is ever re-rounded.

`ROUND_HALF_UP`, not `ROUND_HALF_EVEN`: retail money rounds half up, and the statistical-bias argument for
banker's rounding applies to summing many independently rounded values — which this design specifically does
not do, because it apportions one exact amount instead.

**Also.** The library never mutates the global decimal context. Setting precision at import would silently
change the arithmetic of any application that embeds us. Where extra precision is needed for an intermediate
product, it is taken inside a `localcontext()`.

### Decision 2 — Cart-scoped discounts are apportioned by largest remainder

**Choice.** A cart-scoped promotion produces one cart-level amount, quantized once. That exact amount is
then split across the lines: each line takes its exact proportional share **truncated down** to whole cents,
and the residual cents are handed out one each to the lines with the largest truncated fractions, ties going
to the earlier line. This lives in an `allocation` module as a single function over an amount and a list of
weights, with no knowledge of carts or promotions.

**Why this shape.** The obvious alternative — apply the percentage to each line and let the total be the sum
— is wrong twice over. It rounds N times instead of once, so the total drifts from the percentage the
customer was promised; and it cannot express AMT at all, because "ten pounds off" is not a per-line quantity
until you decide how to split it. The other alternative — keep full precision per line and round only for
display — fails the moment anything downstream (tax, a refund, a ledger) adds the displayed lines back up
and gets a different number. It would also make the per-line explanation a lie, since the deltas shown would
not be the deltas used.

Largest remainder is chosen over "give the whole residual to the largest line" or "to the last line" because
it distributes the error where it is least visible and is stable under reordering in the way that matters:
the tie-break on line position makes it fully deterministic.

**Why truncate rather than round each share.** This is the load-bearing detail. Rounding each share half-up
can *over*-allocate — three shares of `0.335` round to `0.34` each, `1.02` against an amount of `1.00` — and
there is no way to claw back an overdraft without picking a victim line. Truncation can only ever
under-allocate, and by at most (number of lines − 1) cents, which is exactly the residual the
largest-remainder pass gives back. The algorithm is correct because of that asymmetry, not by luck.

**Worked.** Amount `1.00` over lines standing at `3.33`, `3.33`, `3.34`:

```
  exact shares    0.333    0.333    0.334
  truncated       0.33     0.33     0.33     = 0.99   (residual 0.01)
  fractions       0.3      0.3      0.4
  residual cent            ->  to line 3 (largest fraction)
  result          0.33     0.33     0.34     = 1.00   exactly
```

The function's contract is `sum(parts) == amount`, unconditionally. Zero-weight lines take nothing. A total
weight of zero with a non-zero amount is an internal invariant violation and raises, rather than returning
something plausible — but the engine makes it unreachable (see Decision 4). This contract is what lets the
cart explanation and the line explanations agree to the cent: a cart-level delta is exactly the sum of the
line deltas it was split into.

### Decision 3 — Each promotion kind is a rule object behind one interface

**Choice.** A rule declares its code, its scope and whether it stacks, and answers one question:

```python
class Scope(IntEnum):
    LINE          = 0    # BOGO: knows which lines it touches
    CART_PERCENT  = 1    # PCT
    CART_AMOUNT   = 2    # AMT

class PromotionRule(Protocol):
    code: str            # canonical, upper-cased
    scope: Scope
    stackable: bool      # catalogue data; the rule itself never reads it
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
knows exactly which lines its free units came from and must *not* be apportioned — the free coffee comes off
the coffee line, not proportionally off the widget. PCT and AMT genuinely are cart-wide and have no opinion
about lines. One return type covers both: a rule that knows, says; a rule that does not, defers, and the
engine apportions. A future tiered discount, a category-wide percentage, or a spend-threshold gift picks
whichever arm fits without a new concept.

**Why not `if kind == "PCT": ... elif ...` in the engine.** Because promotions change constantly. Today that
means new *codes*, which the catalogue already absorbs. Kinds follow codes — they always do — and the branch
version makes every new kind an edit to the one function that must never break. Here the engine's loop never
mentions PCT, AMT or BOGO.

**Rules are pure and blind.** A rule reads the state, returns an outcome, and never mutates anything, never
rounds by itself (it asks `money`), never learns about other rules, never applies the non-negative floor,
and never inspects its own `stackable` flag. Every one of those is the engine's job, because each is a place
the invariants could break and they should break in one file or not at all.

**Purity is what makes non-stackable selection cheap.** Choosing between two non-stackable promotions means
asking each what it *would* take off without letting it take it. Because `evaluate` returns an outcome
instead of mutating state, that question is just a call: no speculative state, no undo, no transaction. The
arbitration in Decision 10 evaluates each candidate exactly once and applies the winner's already-computed
outcome, so the value a promotion was chosen for is, by construction, the value it takes.

**What each rule means:**

- **PCT** — the rate applied to the cart's *current* amount, quantized once, apportioned by the engine.
  Because each rule acts on what the previous one left, two 10% codes take 19% off, not 20%.
- **AMT** — its full declared amount, returned without clamping; the engine caps it.
- **BOGO** — the named SKU's quantity summed **across all lines**, then one unit free for every N units:
  `free = quantity // N`. Three in the cart makes one free, four or five still one, six makes two. Free
  units are drawn from the lowest-priced units first and attributed to the lines they came from — the same
  SKU really does appear at two prices in this catalogue, so the cheapest-first rule is load-bearing rather
  than decorative.

### Decision 4 — The engine is a fold, and it owns order, arbitration, the floor, and attribution

**Choice.**

```
  state = one LineLedger per submitted line, opened at its list amount
          (a ledger's current amount IS the end of its chain - Decision 9)

  queue = sorted(resolved, key=(rule.scope, rule.code))

  while queue:
      rule = queue.pop_front()

      if rule.stackable:
          apply_step(rule, rule.evaluate(state))            # ordinary path
          continue

      # first non-stackable reached: arbitrate here, once, for all of them
      candidates = [rule] + [r for r in queue if not r.stackable]
      queue = [r for r in queue if r.stackable]             # none of the others runs

      trials = [(r, effective(r.evaluate(state), state.remaining)) for r in candidates]
      winners = [t for t in trials if t.outcome is Applied]

      if winners:
          winner = max(winners, key=(value, -submitted_position))   # larger wins; tie -> entered first
          apply_step(winner.rule, winner.outcome)                   # the outcome it was chosen on
          for other in winners if other is not winner:
              record not_applied(other.code, superseded_by=winner.code)   # delta 0.00, cart chain only
      for t in trials where t.outcome is NotApplicable:
          record the rejection                              # never superseded, never superseding

  where apply_step(rule, outcome):
      value  = min(outcome.value, state.remaining)          # the floor, applied once, here
      capped = value < outcome.value
      parts  = outcome.per_line  or  apportion(value, [ledger.current ...])
      if value != 0:
          state = state.post(parts, code=rule.code, capped=capped)   # steps only where a price changed
      record applied(value, capped, no_effect = value == 0)          # the outcome records it either way
```

**Why the floor lives here, not in AMT.** "A cart total is never negative" reads like a property of
fixed-amount discounts, and it would be easy to clamp inside `AmtRule`. Putting it in the fold instead makes
it structurally impossible for *any* rule — including the fourth kind nobody has written yet — to drive the
cart below zero, however wrong that rule is. A rule may honestly return its full declared value and let the
engine tell it what was actually available. That is why case A7 reports `TENOFF` as applied taking `1.00`
and *capped*, rather than as applied taking `10.00` or as rejected: the customer used the code, it just ran
out of cart. The explanation carries the same `-1.00`, marked capped, so the story and the money match.

**Why sort by scope, then code.** Ordering is a business rule, so it should be data. The `Scope` ordinal *is*
the ordering policy, stated once. The secondary sort on code makes multiple promotions of one kind
independent of the order the customer typed them — two customers with the same basket and the same two codes
must not get different prices because one typed them the other way round. Submitted order is preserved for
*reporting*, and used for exactly one pricing purpose: the tie-break in Decision 10.

**Why PCT before AMT.** The requirement is that the answer be the same every time for the same cart; the
order itself was delegated to us. We keep percentage before fixed amount because it preserves the face value
of a voucher: a customer holding "10.00 off" gets 10.00 off (or whatever remains), instead of having their
voucher quietly shaved by a percentage applied after it. That is the version that can be explained at a
support desk, and it is the more generous of the two orderings.

**Why arbitration lives in the fold and not before it.** A promotion's value depends on the cart state when
its turn comes — that is the whole point of the running discounted base. So "which of these is worth more?"
is not answerable before the fold starts; it is only answerable at a specific moment, and the fold is where
moments exist. A pre-pass would have to price the cart to decide, which is the fold again, in a second copy.

**Attribution comes free.** `post` appends a step to each affected line's chain and one step to the cart's
chain, and the amounts move *because* those steps exist. That is the whole explainability requirement, and
it falls out of the fold rather than being a second pass that can disagree with the first.

**Line-level floor.** `apportion` cannot produce a part larger than a line's own amount, because the value is
already capped at the cart remaining and shares are proportional to line amounts — so no line can go
negative either. A line already at `0.00` has weight zero and takes nothing, and gets no step.

### Decision 5 — The catalogue is TOML, with money and rates written as quoted strings

**Choice.**

```toml
[[promotion]]
code = "SAVE10"
kind = "PCT"
rate = "10"          # quoted: parsed as an exact Decimal

[[promotion]]
code = "TENOFF"
kind = "AMT"
amount = "10.00"     # quoted
stackable = false    # bare boolean: TOML booleans are exact

[[promotion]]
code = "COFFEE3"
kind = "BOGO"
sku  = "COFFEE"
n    = 3             # unquoted: TOML integers are exact, so this one is safe bare
```

**Why TOML.** It is in the 3.11 standard library (`tomllib`), so it costs no dependency; it supports
comments, so an entry can say why it exists and when it retires; and it has no trailing-comma or quoting
traps for a non-engineer editing in a hurry. JSON is the serious alternative and also dependency-free, and
`json.load(parse_float=Decimal)` even defuses the float problem — but it has no comments, and a missing
comma produces a parse error at a character offset rather than at an entry. CSV cannot carry parameters that
differ by kind without a column zoo. YAML would need a dependency and is ruled out by the substrate.

**Why the money fields are quoted.** TOML floats are IEEE-754 binary: `amount = 10.10` parses to
`10.0999999999999996...`, and the catalogue's formatting would leak into prices. Writing money and rates as
strings and parsing them with `Decimal(str)` keeps them exact. Integers and booleans are exempt because TOML
represents them exactly, which is why `n = 3` and `stackable = false` are bare — the inconsistency is
deliberate and worth one line of explanation in the file header, because forcing `n = "3"` would suggest
quoting is cosmetic. The loader **rejects** a bare float in a money field rather than coercing it, with a
message that says to quote it; silently coercing would hide the one mistake this rule exists to catch.

### Decision 6 — A malformed catalogue entry is quarantined; only an unreadable file is fatal

**Choice.** Loading validates every entry, keeps the valid ones, and skips the invalid ones. It returns the
catalogue **together with a report** of everything it rejected, each identified by entry and field:

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

**Why this, and what it costs.** The instruction is explicit: one typo must not stop the shop selling. That
is the right call for a file edited daily by people who are not engineers, and it is the opposite of what a
"fail loudly at load" instinct would produce. The cost is real and worth naming: the failure moves from
deploy time to checkout time. A broken code is one the marketing email has already promised, and the
customer who types it is told we have never heard of it. Nobody finds out from the service itself.

So the design compensates in two places rather than accepting that silently:

1. **The rejects are returned, not logged.** Making them part of the load result means ignoring them is a
   deliberate act by the caller, not an oversight. The CLI writes them to stderr on every run.
2. **`check-catalogue` becomes the loud gate.** Since loading no longer refuses anything, the checker is the
   *only* place a broken entry stops something — so it reports failure whenever any entry was rejected, and
   the publishing process should refuse to ship a file that fails it. That restores the deploy-time alarm
   without ever blocking a checkout.

Together these give both properties the situation actually needs: lenient at runtime, loud at publish time.

**Why a duplicate code is quarantined rather than resolved.** Two definitions of `SAVE10` is not a typo in
one entry; it is a question we cannot answer. Taking the first, or the last, would price carts on a coin
toss — the one failure mode worse than an unknown code, because it is invisible. So that code alone is
withdrawn and reported, and the rest of the file loads. That costs one code, not the shop.

### Decision 7 — Codes are resolved before anything is applied, and every one gets an outcome

**Choice.** A resolver pass normalises each submitted code (`strip().upper()`), looks it up, and classifies
it: resolved to a rule, unknown, or a duplicate of one already seen. Only resolved rules enter the fold. The
result reports an outcome for every submitted code, in submitted order, from a closed set: applied (with the
value taken, whether it was capped, and whether it had no effect), or not applied with `UNKNOWN_CODE`,
`NOT_APPLICABLE`, `DUPLICATE`, or `SUPERSEDED` — which additionally carries the code that beat it.

**The outcome list is the complete record of every code; the explanation is the record of the money.** Every
submitted code appears in the outcomes, in submitted order, whatever became of it. Only price changes — and
the supersession decisions that chose between them — appear in an explanation. So a code that was unknown,
duplicate, not applicable, or applied but worth nothing is answered for in one predictable place, returned
beside the explanation in the same result. Support has two artifacts for the two questions it actually asks:
"why is this amount what it is?" and "what happened to the code I typed?".

**Why a closed enum and not a message.** A caller has to branch on this — "unknown code" is a typo the
customer can fix, "not applicable" is a basket they can fix, "superseded" is neither and needs a different
sentence entirely. Free-text reasons get parsed by desperate callers.

**Why `SUPERSEDED` is its own reason and carries a code.** "Your code was valid but the other one saved you
more" is a different sentence from "we have never heard of that code" and from "that code does not apply to
what is in your basket", and support has to be able to say it. Folding supersession into `NOT_APPLICABLE`
would lose the only fact that makes the sentence sayable — which code won — and would tell a customer their
working code was broken. It is the one reason that names another code, and it is the same code the
`NOT_APPLIED` step in the explanation names, taken from the same arbitration result rather than recomputed.

**Why "applied, took `0.00`" is not a rejection.** The code was real and it was used; the cart just had
nothing left. Reporting it as a rejection would tell the customer their valid code was bad. It is flagged
`no_effect` so the customer can be told that it was accepted and saved them nothing.

**Why four reasons are enough.** Retirement is done by deleting the entry from the catalogue, so there are
no validity dates and no expired state to report — a retired code is simply unknown. A quarantined entry
lands in the same place for the same reason: the customer-facing answer is "unknown code", while the
operator-facing detail lives in the load report where it can be acted on. Two audiences, two channels, one
closed enum.

**Cart errors and code errors are deliberately different.** A malformed *cart* (quantity `0`, negative price)
rejects the whole request: that is a caller bug, and pricing it would invent an answer. A bad *code* never
does — the rest of the cart still prices.

### Decision 8 — Library with a thin CLI, not an HTTP endpoint

**Choice.** `price(request, catalogue) -> PricedCart` is the contract. The CLI is one adapter: a `price`
subcommand reading a cart as JSON on stdin and writing the result as JSON on stdout, and a `check-catalogue`
subcommand. Exit status distinguishes success, bad cart, and bad catalogue; codes that were not applied do
not affect it, because a cart with an unknown or superseded code priced successfully.

**Why not HTTP.** The substrate forbids network, persistence and multi-process anyway, so an HTTP endpoint
would buy nothing and cost a server lifecycle, request parsing, status-code mapping and a concurrency story.
A CLI over JSON is scriptable, diffable, and makes the acceptance tables an exact fixture comparison. If the
product later needs HTTP, it is a second adapter over the same function — the engine does not change, which
is the point of putting the contract at the function rather than at the transport.

**The JSON boundary re-introduces floats, so it is a named rule.** Money is written as strings on output
(`"12.50"`, `"-2.45"`, not `12.50`) and parsed from strings or with `parse_float=Decimal` on input. This is
exactly the leak Decision 1 exists to prevent, and the easiest one in the system to reintroduce by accident
at the last mile — and it would now corrupt the explanation as well as the total.

**The adapter writes the explanation; it never derives one.** Rendering is the last place a second,
disagreeing computation could appear — a total summed from the lines "for convenience", steps merged for
tidiness. The CLI's contract forbids computing, merging, reordering or summarising steps. It serialises what
`price()` returned, in order.

### Decision 9 — The explanation is the ledger; the amounts are read off it

**Choice.** A line's money is not a `Decimal` that steps happen to describe. It is a chain:

```python
class StepKind(Enum):
    LIST_PRICE  = "list_price"    # the basis: what we started from
    ADJUSTMENT  = "adjustment"    # a promotion moved money
    NOT_APPLIED = "not_applied"   # a promotion qualified but was superseded

@dataclass(frozen=True)
class Step:
    kind: StepKind
    code: str | None              # None only for LIST_PRICE
    delta: Decimal                # exactly 0.00 for LIST_PRICE and NOT_APPLIED
    amount_before: Decimal
    amount_after: Decimal         # == amount_before + delta, always
    capped: bool = False
    superseded_by: str | None = None   # set only for NOT_APPLIED

@dataclass(frozen=True)
class Ledger:                     # one per line, plus one for the cart
    steps: tuple[Step, ...]       # opens with a LIST_PRICE step
    @property
    def current(self) -> Decimal: return self.steps[-1].amount_after
```

`current` is a projection, not a field. There is no second copy of the amount to drift, so "the explanation
and the amount disagree" is not a bug to test for — it is a state the type cannot hold. `post` is the only
way to extend a ledger, and it builds each new step from the previous `amount_after`, so the chain is linked
by construction too.

**Why a basis step with a zero delta.** The rule we were given is that the deltas sum to *the difference*
between list and final. If the list price were itself a delta of `+25.00`, the deltas would sum to the final
price instead, and every consumer would have to special-case the first entry. Making the basis a step with
`delta = 0.00` keeps one uniform shape — every step names what it was and what it contributed — and makes
the sum rule true over the whole sequence with no exceptions. On that step `amount_before == amount_after ==
list amount`, so the chain still links.

**Why no rounding line, ever.** A residue line is the classic way to make an explanation add up, and it is
exactly what was refused. This design has nothing to confess: `apportion` splits an exact amount into parts
that sum to it exactly (Decision 2), and every delta is money that was quantized once and thereafter only
added and subtracted (Decision 1). The invariant is not "we corrected the residue" but "there is no
residue". The absence of a residual step is stated as a requirement, so a future implementation cannot
quietly buy itself slack.

**The cart ledger and the line ledgers are two views of one event.** `post` writes them together: the
promotion's cart-level step carries the cart delta, each affected line gets a step carrying its own part,
and the parts sum to the cart delta because `apportion` guarantees it (a line-scoped rule hands back parts
that already are the whole). A line that receives `0.00` gets no step at all — noise, not information.

**One placement rule: a step appears where the price changed.** Stated in one sentence — if it did not
change that line's price, it does not need to be on that line — and applied literally, everywhere:

- a line that receives `0.00` of an apportioned discount gets no step;
- a promotion that takes `0.00` overall gets no step on any line *and none on the cart chain either*; its
  outcome still reports it as applied, having saved nothing;
- a code that was unknown, duplicate or not applicable never reaches an explanation at all; the outcome list
  is where it is answered for;
- the single exception is a superseded promotion, recorded on the cart chain only. It changed no price, but
  it decided which promotion did, and it has to be visible so support can say "your code was valid, the
  other one saved you more". It never appears on a line, where a `0.00` step per line would be noise
  proportional to the size of the cart.

An explanation is therefore a list of price changes with no filler, and every code — including the ones that
changed nothing — is still accounted for, one row each, in the outcomes returned beside it.

**What this costs.** Result size grows with (lines x promotions), which for a cart is nothing. Building
frozen steps allocates more than mutating a running total, which for a cart is also nothing. Both are worth
naming because the trade is deliberate: we pay allocation to make a class of bug unrepresentable.

**The guard at the boundary.** `price()` re-derives the stated relations before returning: chains link,
chains end at the reported amounts, each cart delta equals the sum of its line deltas, each applied code that
moved money reports exactly its cart step's delta while an applied code with no step reports `0.00`, and the
line finals sum to the total. That is cheap, and it is
the difference between believing an invariant and knowing it. A failure raises: a result whose explanation
contradicts its amounts is worse than no result, because it is the artifact someone would show a customer.

**What a result looks like** for `COFFEE 4.00 x4` + `WIDGET 12.50 x1` with `COFFEE3` and `SAVE10`:

```
  cart      list 28.50 -> COFFEE3 -4.00 -> 24.50 -> SAVE10 -2.45 -> 22.05
  line 0    list 16.00 -> COFFEE3 -4.00 -> 12.00 -> SAVE10 -1.20 -> 10.80
  line 1    list 12.50 ->                           SAVE10 -1.25 -> 11.25

  cart deltas   -4.00 + -2.45 = -6.45 = 22.05 - 28.50            exact
  COFFEE3       -4.00 = -4.00 + 0.00   (line 0 + line 1)         exact
  SAVE10        -2.45 = -1.20 + -1.25                            exact
  lines         10.80 + 11.25 = 22.05                            exact
```

Line 1 carries no `COFFEE3` step because no coffee money moved on it. That is the difference between an
explanation and a log.

### Decision 10 — Non-stackable promotions are arbitrated once, on one basis, at the point of application

**Choice.** At most one non-stackable promotion is applied. The choice is made at a single instant — where
the first non-stackable promotion falls in the `(scope, code)` order — by evaluating every non-stackable
candidate against *that same state*, comparing the money each would actually take off after the
non-negative cap, and applying the winner's already-computed outcome right there. Ties go to the code
submitted first. Losers become `NOT_APPLIED` steps on the cart chain naming the winner, and `SUPERSEDED`
code outcomes carrying the winner's code.

**Why one basis.** The instruction is to compare what each one actually takes off the basket in front of
you: the cart as it stands at that moment, after whatever has already been applied to it, never the list
subtotal. "The one that gives the customer the larger discount" only means something if both numbers are
measured against the same cart. Evaluating `SAVE10` at its scope position and `TENOFF` at its
own would compare a percentage of one amount against a fixed amount measured on another, and the winner
would silently depend on the ordering policy rather than on the money. One state, one moment, one
comparison.

**Why the winner is applied where it was compared.** If the winner were compared at the arbitration point
but applied later at its own scope position, an intervening stackable promotion could change what it
actually takes — and the explanation would then say "TENOFF beat SAVE10 by 10.00" while the line showed
`-8.50`. That is precisely the disagreement that makes the feature worthless. Comparing and applying at the
same instant makes the promise and the payment the same number by construction, not by test.

**Why after the cap.** A `10.00` voucher on a `5.00` cart gives the customer `5.00`, not `10.00`. Comparing
declared values would hand the customer the smaller real discount while the explanation claimed the larger
one. "Larger discount" means money, so the comparison is on the capped value.

**Ties.** Equal money is the only case where the customer's typing order matters, and it was chosen
explicitly: first entered wins. This is the single, deliberate exception to "input order never changes the
price", and it is stated in the spec as such rather than hidden in a sort key — with a scenario that
reverses a tied pair and expects the other winner, so nobody later "fixes" it as a bug. It is stable: the
submitted position is a total order, so there is never a second tie to break.

**What does not compete.** A non-stackable promotion that does not qualify (a BOGO whose SKU is absent) is
`NOT_APPLICABLE` and takes no part: it supersedes nothing and is superseded by nothing. A duplicate
occurrence never reaches arbitration, so a code cannot beat itself. A cart with exactly one non-stackable
code prices exactly as it would have if that code were stackable — which is what keeps every earlier
acceptance case untouched.

**Alternatives rejected.**

- *Filter before the fold, by declared value.* Simple, and wrong: a percentage has no value until you know
  the base, so the filter would have to price the cart to decide — which is the fold.
- *Apply both and keep the better result.* Doubles the computation, needs two ledgers, and leaves no honest
  place to record the loser.
- *Exclusivity groups now (codes conflict only within a named group).* Explicitly declined: one rule, two
  of them cannot sit together, nothing more elaborate, build for today. If it is ever wanted the seam is the
  same — arbitration partitions candidates by group instead of taking them as one set — and nothing else in
  the design moves. Building it now would invent semantics (what does a code in two groups mean?) that
  nobody has asked for.

### Decision 11 — Stackability is a catalogue modifier, not a kind and not a rule

**Choice.** `stackable` is an optional boolean on any catalogue entry, defaulting to `true` when absent.

**Why in the file.** Whether two offers may be combined is a commercial decision, made by the same people who
decide the rate and the amount, and changed on the same cadence. Putting it in code would put a release
between them and a decision they own — the exact failure the catalogue exists to prevent.

**Why a modifier rather than a kind parameter.** It applies to every kind and means the same thing in each,
so it belongs to none of them. The entry validator therefore has two vocabularies: parameters, which are
per-kind and strictly checked (an AMT entry carrying a SKU is a mistake), and modifiers, which are permitted
on any entry. A fourth kind gets stackability for free.

**Why bare rather than quoted.** Decision 5 quotes money and rates because TOML floats are binary. Booleans
and integers are exact in TOML, so `stackable = false` is safe bare and consistent with `n = 3`.

**Why an unreadable value is rejected rather than defaulted.** `stackable = "false"` is a string, and a
string is not false. Treating an unreadable value as stackable would combine a promotion the commercial team
declared exclusive, which is a money error nobody would see. Rejecting the entry costs one code and reports
it — the same trade the rest of the catalogue makes (Decision 6).

**Why absence means stackable.** Every entry written before this modifier existed must keep its meaning, and
the earlier acceptance cases must price unchanged. Defaulting to non-stackable would silently switch today's
stacking behaviour off.

## 5. The acceptance tables against this design

| # | Path through the design | Result |
|---|---|---|
| A1 | No codes; lines render at list | line `25.00`, total `25.00` |
| A2 | PCT on `25.00` -> `2.50`, apportioned to the one line | total `22.50` |
| A3 | AMT returns `10.00`; engine caps at `25.00` remaining, no cap needed | total `15.00` |
| A4 | BOGO N=3, 4 units -> `4 // 3` = 1 free @ `4.00` | total `12.00` |
| A5 | Scope order: BOGO (`-4.00`) then PCT on `24.50` (`-2.45`); apportioned `1.20` / `1.25` | lines `10.80` + `11.25`, total `22.05` |
| A6 | `NOPE` fails resolution -> `UNKNOWN_CODE`; fold sees no rules | total `12.50`, code reported |
| A7 | AMT returns `10.00`; engine caps at remaining `1.00`, marks capped | total `0.00`, never negative |

| # | Path through the design | Result |
|---|---|---|
| B1 | One PCT step posted to the cart and the single line | explanation `25.00` -> `SAVE10 -2.50` -> `22.50`; deltas sum `-2.50` |
| B2 | Two steps posted in scope order; `SAVE10` apportioned `1.20` / `1.25` | total `22.05`; cart, coffee and widget chains each reconcile exactly |
| B3 | Arbitration at `50.00`: `TENOFF` `10.00` beats `SAVE10` `5.00` | total `40.00`; `SAVE10` a `NOT_APPLIED` step and a `SUPERSEDED` outcome naming `TENOFF` |
| B4 | Arbitration at `150.00`: `SAVE10` `15.00` beats `TENOFF` `10.00` | total `135.00`; `TENOFF` superseded by `SAVE10` |
| B5 | Arbitration at `100.00`: both `10.00`; tie -> earlier submitted position | `SAVE10` applied, total `90.00`; `TENOFF` superseded |
| B6 | No non-stackable codes in A1-A7, and the explanation is additive | every earlier amount unchanged |

A5/B2 is the case that validates the money structure: it needs the ordering (Decision 4), cross-scope
composition (Decision 3), and apportionment back onto two lines (Decision 2) to be right at once, and it is
also the case where the cart explanation and the two line explanations have to reconcile to the cent.
B3-B5 validate the decision structure: the same two codes, the same catalogue, three different winners,
each chosen on money measured at one moment and applied at that same moment.

## 6. Risks and trade-offs

- **A rounding or apportionment bug is invisible until it is expensive** → the sum invariant is the stated
  contract of one small function with no domain knowledge, checkable exhaustively over random amounts and
  weights. Three-way splits of an odd cent are the cases worth generating rather than hand-picking.
- **An explanation that drifts from the amount is the failure that makes the feature worthless** → the
  amount is a projection of the chain (Decision 9), so drift requires bypassing the type rather than merely
  making a mistake; the boundary guard re-derives every stated relation before a result leaves `price()`,
  and raises instead of returning. The residual risk is a rendering adapter recomputing a total on the way
  out, which is why the CLI is forbidden from computing, merging or reordering steps.
- **The arbitration point is a subtle ordering rule** → the winner is applied where the *first*
  non-stackable promotion falls in `(scope, code)` order, which is not necessarily where that winner's own
  kind would sit; a non-stackable AMT can land ahead of a stackable AMT that sorts before it. The
  alternative costs the property that matters more (compared value == taken value), so the rule is stated
  normatively in the spec and pinned by acceptance cases in both orderings.
- **The tie-break re-introduces submitted order into pricing** → a single, explicitly chosen exception to
  "input order never changes the price", bounded to a tie between non-stackable candidates, stated in the
  spec with a scenario that reverses a tied pair and expects the other winner.
- **One global non-stackable class is what was asked for** → every non-stackable code competes with every
  other one, and groups have been declined for now. The cost is that a catalogue wanting "one shipping offer
  and one basket offer" cannot express it without all four competing. The seam is named in Decision 10 —
  arbitration partitions candidates instead of taking them as one set — so adding groups later is a
  partition key, not a rework.
- **An explanation exists only in the response** → the service keeps nothing, by substrate and by decision,
  so the artifact that settles a dispute a month later is the one the caller stored. Retention is therefore
  someone else's explicit obligation rather than an implicit one: it belongs in the contract governing the
  caller, and it is why the result is complete and self-describing rather than a summary that assumes a
  later re-price.
- **Quarantining a broken entry moves the failure from deploy time to checkout time** → the right call for
  availability, but a code the marketing email promised can fail silently in front of a customer. Mitigated
  by returning the rejects in the load result rather than logging them, by writing them to stderr on every
  run, and above all by `check-catalogue` reporting failure so publishing can be gated.
- **`check-catalogue` is the only loud alarm** → if nobody wires it into the publishing process, broken
  entries reach production unnoticed. That makes it an operational requirement rather than a convenience,
  which is why it appears in the deployment note.
- **The application order encodes a business rule in a `Scope` enum** → one ordinal per kind in one place,
  read by the fold as data. With the order delegated to us and only stability required, the risk is not the
  choice but that a later reader mistakes it for an implementation detail; the enum carries the reasoning
  and the spec states the order normatively.
- **BOGO's threshold reads two ways in English** → "for every 3, one free" can mean one free at three, or a
  group of four with one free at four. Case A4 cannot tell them apart. The settled rule is the first:
  `free = quantity // N`, stated explicitly at three, four and six.
- **The service trusts the prices it is given** → no product catalogue means a caller passing a wrong unit
  price gets a confidently wrong total, now with a confidently wrong explanation attached. A deliberate
  boundary, but it belongs in whatever contract governs the caller.
- **Stacking limits are still coming and still not built** → exclusivity has arrived as non-stackability; a
  cap on how many promotions may stack has not. The seam is unchanged — a limit is a filter over the
  resolved rules before the fold — but it raises a policy question arbitration has already answered once
  (which ones to keep), and it should reuse the same "most money to the customer" principle rather than
  invent a second one.
- **The customer id still does nothing** → carried through untouched so the result is self-describing, and
  the natural hook for a future eligibility rule, which is deferred. Carrying an unused field is a small
  smell; inventing eligibility semantics nobody asked for would be a larger one.

## 7. Deployment note

Nothing exists yet, so there is no migration, no rollback path and no compatibility surface.

The operational note is the catalogue. It is a production input owned outside engineering, and because a
malformed entry is quarantined rather than fatal, the service itself will never refuse a bad file. The
publishing process should run `check-catalogue` against the candidate file and refuse to ship on failure.
That gate is the entire safety story for a file that can otherwise take a promised promotion offline without
anyone being told — and, now, for a `stackable` flag that a typo would otherwise turn into a quarantined
code.

One obligation sits outside this service and has to be written down somewhere a caller will read it: the
explanation is returned and never stored, so a caller who may have to answer for a price later — a
checkout, an order service, anything that can be asked "why was this 22.05?" a month afterwards — keeps the
priced result it was given. The service holds no history and cannot reconstruct one, and it does not need
to: every result is complete on its own.

Two audiences need a written page, because both now read this service's output directly:

- the commercial team, for the file: the kinds and their parameters, the quoting rule, `stackable = false`
  and what it means for a customer holding two exclusive codes, retirement by deletion, and the check;
- finance and support, for the explanation: how to read a chain, what each step kind means, that the deltas
  reconcile list to final with no rounding line, that a code which changed no price is answered for in the
  outcome list rather than in the chain, and what to tell a customer whose code was superseded.

## 8. Settled business rules

These are confirmed, not assumptions:

| Rule | Settled as |
|---|---|
| BOGO threshold | One free for every N in the cart — three in the basket means one is free (`quantity // N`) |
| Two percentage codes | Compound: two 10% codes take 19% off, not 20% |
| Order of application | Ours to choose provided it is stable per cart; PCT before AMT |
| Rounding | Must come out to the cent and be reproducible; half-up is our tie-break within that |
| Explanation content | Per line and per cart: an ordered chain from list price to final, each entry naming a code or the list price itself and its exact delta |
| Explanation arithmetic | Deltas sum exactly to final minus list, to the cent, with no residue and no rounding line |
| Explanation fidelity | It describes what actually happened, in the order it happened; explanation and amount may never disagree |
| Where a step belongs | Where the price changed: nothing that moved no money on a line is listed on that line, and nothing that moved no money at all is listed anywhere |
| Codes that changed no price | Answered for in the code outcomes — the complete, submitted-order record returned beside the explanation — not as an empty step |
| Non-stackable promotions | Marked in the catalogue; at most one applies; the larger discount wins |
| Superseded promotions | Appear in the explanation marked not applied, naming the code that superseded them |
| Ties between non-stackables | The code the customer entered first is applied, and the explanation shows it |
| What exclusives are compared on | What each actually takes off the basket as it stands at that moment, after the cap — not face value, not the list subtotal |
| Exclusivity groups | Declined for now: one rule, two non-stackable promotions cannot sit together |
| Retaining explanations | The caller keeps the result; the service stores nothing |
| Malformed catalogue entry | Quarantined and reported, never fatal |
| A code that takes `0.00` | Accepted, saved nothing — not a rejection, and not a step either |
| Same SKU at two prices | Happens in practice; the cheapest units are the free ones |
| Stacking limits, customer-id rules | Expected later, deliberately not built now |
| Retiring a code | Delete the entry; a retired code is reported as unknown |

Four of these moved the design rather than confirming it. **BOGO** was originally specified as groups of N+1
(one free at four). The **catalogue** originally refused to load at all if any entry was malformed. The
**explanation** turned the result inside out: rather than computing amounts and describing them, the design
now computes the description and reads the amounts off it (Decision 9). And **non-stackability** forced the
one deliberate exception to input-order independence, together with a new decision point inside the fold
(Decision 10).

## 9. Genuinely open, and safely deferrable

None of these changes the components, the seams, or the work:

- Where the catalogue file lives and how a deployment points at it. The loader takes a path either way.
- Whether an explanation step should also carry the apportionment mechanics of a cart-scoped discount (the
  weights, the remainder-cent assignment) beyond the per-line deltas it already carries. Additive: extra
  fields on an existing step, with the sum rules unaffected.
- Whether a customer-facing rendering should suppress the not-applied step that a support-facing one keeps.
  A presentation choice over one flag; the service returns the same result either way, and the placement
  rule in Decision 9 already keeps every other non-event out of the chain.
- Whether `check-catalogue` should eventually be its own entry point, for a publishing pipeline with no
  reason to install the pricing library — more attractive now that it is the gate the catalogue's safety
  depends on.
- Whether the quarantine report should also reach an operator through a channel of its own, rather than only
  through the load result and stderr. A deployment concern; it does not change the loader.
