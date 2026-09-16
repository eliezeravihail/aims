# Cart Pricing Service — Architecture

A service that answers one question, and shows its working: what does this cart cost, and why? It takes a
customer id, the **market** the cart is being priced for, a list of lines (SKU, listed unit price, quantity)
and the promotion codes the customer typed. It returns what every line costs and what the cart costs — each
amount accompanied by the ordered chain of adjustments that produced it, each submitted code accounted for,
and the tax stated and derived beside them, so nothing is silently swallowed and nothing on an invoice is a
number somebody has to trust.

Promotion definitions live in data files the commercial team edits directly — one per market, because the
two countries run different offers. Codes are added and retired constantly and must not require an engineer.
A file also says which of its promotions refuse to be combined with one another. Tax law does not live
there: a market declares four facts about its tax, those four facts are the entire difference between the
two countries, and they are kept with engineering so that nobody edits a tax rate by hand.

## 1. Context and constraints

Fixed substrate:

- Python 3.11+, standard library only. A new runtime dependency would have to earn its place; none does.
- `decimal.Decimal` is available. Nothing mandates it, but see Decision 1.
- Single process, single currency, no UI, no network, no database, no persistence.
- Entry point may be a library with a CLI or a local HTTP endpoint. See Decision 8.

Four forcing constraints, none of them in the substrate.

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

**Four — the same cart is now priced under two tax laws that disagree about what a listed price means.** In
`NORTH`, listed prices exclude the tax; 17% is added to the discounted cart once, at the end, rounded
half-up, and the line amounts are untouched. In `SOUTH`, listed prices already contain 20% tax; promotions
come off the gross shelf price the customer can see; every line must report how much of its final amount is
tax, rounded half-even **per line**; and the cart's tax is the sum of those line figures.

Two of those differences are arithmetic. The third is structural, and the acceptance table makes it
unmissable:

```
  SOUTH, three lines at 0.15 (no promotions)

  per line   0.15 * 20/120 = 0.025  -> half-even -> 0.02   x3  =  0.06   <- the law
  per cart   0.45 * 20/120 = 0.075  -> half-even -> 0.08         =  0.08   <- not the law
```

Both are defensible arithmetic; only one is what the invoice must say. So in a per-line market the cart's
tax is not a figure at all — it is a sum — and the design has to *make* it one rather than merely compute it
that way this time (Decision 14).

The promotion acceptance table pins down more than it appears to, as it always did. Case A5 — `COFFEE 4.00
x4` and `WIDGET 12.50 x1` with `COFFEE3` and `SAVE10`, expecting `22.05` — reconciles exactly one way:

```
  list subtotal            28.50
  COFFEE3  (1 free @4.00)  -4.00   ->  24.50
  SAVE10   (10% of 24.50)  -2.45   ->  22.05
```

Ten percent of the *list* subtotal would be `2.85` and give `25.65`. So the order is not a preference we are
free to choose: BOGO resolves first, and PCT is taken against the amount left behind. The design encodes
that as data — a scope ordinal — not as a sequence of statements someone can reorder by accident. That
worked trace is also, almost verbatim, the explanation the service returns for the same cart.

## 2. Goals and non-goals

**Goals**

- One pure function is the product: `price(request, catalogue, markets) -> PricedCart`. Everything else is
  an adapter or a helper.
- `sum(line amounts) == cart total` holds by construction for every input, not because the test cases happen
  to divide evenly.
- Every reported amount is the end of an explanation, not a number kept beside one. The explanation and the
  amount cannot disagree because there is only one of them.
- The deltas in any explanation sum exactly to the difference between its list amount and its final amount,
  with no residue and no balancing entry — and no residue exists to confess.
- An explanation lists price changes and nothing else. What happened to a code that changed no price is
  answered in the outcome list returned beside it, so neither artifact is padded with the other's job.
- Exactly one module rounds, and exactly one place can violate the sum invariant. Both are small enough to
  reason about completely.
- When two promotions cannot be combined, the customer gets the one worth more to them, judged on the money
  it actually takes off this cart; the one they did not get is reported by name with the code that beat it.
- **The promotion pipeline is market-blind.** Rules, ordering, arbitration, capping, apportionment and every
  explanation are the same code in every country. That is what makes "every earlier case prices exactly as
  it does today" a structural property rather than a claim the acceptance table has to keep re-establishing.
- **A tax law is four declared facts** — rate, whether listed prices include the tax, per line or per cart,
  and the rounding mode. A third country that fits those four is a table entry, not a release of the engine.
- **The tax is explained to the same standard as the price.** Every figure states what it was taken from, at
  what rate, added or extracted, rounded how and at what level; and the figures reconcile exactly, in all
  three columns, with the amounts the promotions produced.
- Adding a fourth promotion kind is a new rule class plus a catalogue schema entry. The engine does not
  learn about it, and it inherits stackability, explanation and tax for free.
- A promotion-file typo costs exactly one promotion code, never the shop. It is reported completely and
  actionably, and it is loud in the one place that can act on it before customers do: a check the commercial
  team runs on the file themselves.

**Non-goals**

- No product catalogue. Unit prices arrive in the request and are trusted; the service never looks up or
  second-guesses a price. A real trust boundary, and deliberate — it keeps `price()` pure and testable
  against any price the caller invents.
- No promotion state: no budgets, no usage counts, no per-customer redemption history. Those need
  persistence, which the substrate excludes, and they would make `price()` impure.
- No concurrency design. Everything is immutable and there is no shared mutable state, so there is nothing
  to guard; that is the whole story.
- No currency handling. A market declares a tax law, not a currency; both markets are priced in the same
  money, at two decimal places, with no symbol in the data model.
- No tax history and no dated rates. A market carries one rate. Rates with validity dates would need a clock
  and a rule about which date governs, and neither exists here.
- No tax on list amounts. An invoice states the tax within what is being charged; tax on a price nobody is
  paying is a number with no claim on anyone.
- No market-scoping feature for promotions, because none is needed: each market has its own catalogue file,
  so a code is offered in a market by being in that market's file (Decision 5).
- No re-pricing of a past cart at the rate it was priced under, and no dated rates. Build for today; the
  caller keeps the result it was given.
- No retention. The explanation and the tax account travel with the result and are never stored; a caller
  who may have to answer for a price later keeps the result it was given.

## 3. Components and the seams between them

```
   <market>-catalogue.toml                         market declarations
  (one per market, each naming it;                (four facts per market;
   edited by the commercial team)                  kept with engineering)
              |                                                |
              v                                                v
    +---------------------+                        +-------------------------+
    |  catalogue          |  parse, validate,      |  markets                |
    |                     |  build rules           |  name -> TaxPolicy      |
    +---------------------+                        +-------------------------+
              |  Catalogue: market + (code -> rule)            |  TaxPolicy
              v                                                v
  CartRequest  -->  +------------------------------------------------------+
  (incl. market)    |  engine.price()                                      |
                    |    validate cart   +  resolve market -> policy       |
                    |    refuse a catalogue belonging to another market    |
                    |    resolve codes   -> rules, rejects                 |
                    |    sort by (scope, code)                             |
                    |    fold rules over CartState     <-- market-blind    |
                    |      - arbitrate non-stackables                      |
                    |      - cap, apportion, post steps                    |
                    |    assess tax from the amounts the fold left behind  |
                    |    verify the chains and the tax accounts            |
                    |    render PricedCart                                 |
                    +------------------------------------------------------+
                   |         |          |           |            |
                   v         v          v           v            v
              +---------+ +--------+ +---------+ +----------+ +----------+
              |  rules  | | money  | | ledger  | |allocation| |   tax    |
              | Pct Amt | |quantize| | Step    | | apportion| | assess() |
              |  Bogo   | | (mode) | | Ledger  | | (largest | | TaxFigure|
              +---------+ | clamp  | | post()  | | remainder| +----------+
                   |      +--------+ | current | +----------+      |
                   |          ^      +---------+       |           |
                   +----------+----------+-------------+-----------+
                              |
                        +---------+
                        | models  |  frozen dataclasses + cart validation
                        +---------+
                             ^
        (everything depends on models; models depends on money and ledger only)

   cli  ->  catalogue, markets, engine, models     (adapter; no pricing logic)
```

Arrows point the way dependencies run. What each component owns:

| Component | Owns | Never does |
|---|---|---|
| `money` | The rounding primitive under a named mode; exact parsing; the non-negative clamp | Know what a cart, a promotion or a market is; choose a mode of its own |
| `allocation` | Splitting one exact amount across weights so the parts sum to the whole | Know what a cart or a promotion is |
| `ledger` | The explanation: steps, the linked chain, `current` as a projection of it, the chain invariants, and the rule that a step exists only where a price changed | Know what a promotion means, or decide which ones apply |
| `tax` | What a rate does to an amount: added or extracted, rounded once, and `net + tax == payable` | Know what a promotion, a code or a cart line is — it takes an amount |
| `markets` | The policy table and name resolution | Price anything, or decide what a caller does about an unknown market |
| `models` | Request and result shapes; cart validity; `CartState` over the ledgers | Know how any promotion behaves, or how tax is figured |
| `rules` | What each promotion kind *means*, given a cart state | Round, clamp, order itself, see another rule, read its own stackability, or know a market exists |
| `catalogue` | The file format, the market a file declares, the entry schema and modifiers, validation, quarantining bad entries, building rule objects | Price anything, carry tax, or decide what to do about a rejected entry |
| `engine` | Order, arbitration, the floor, apportionment, posting steps, market resolution, refusing a catalogue of another market, tax assembly, the boundary guard, rendering | Know that PCT, AMT or BOGO exist by name, or figure a tax itself |
| `cli` | JSON in and out, exit statuses | Contain a pricing rule, or compute, merge, reorder, re-round or sum anything it was handed |

`money`, `allocation`, `ledger` and `tax` are leaves that know nothing about promotions — which is precisely
what makes the four invariant-critical pieces testable in isolation against pure arithmetic properties.
`allocation` owns *the parts sum to the whole*. `ledger` owns *the chain links, and the deltas sum to the
difference*. `money` owns *there is exactly one rounding site*. `tax` owns *net plus tax is payable*. Every
money guarantee this service makes is one of those four, composed by the engine.

The engine is the only component that knows a promotion and a market exist in the same system, and even
there they never meet: the fold runs to completion before the policy is touched.

## 4. Decisions

### Decision 1 — Money is `Decimal`, exactly one module rounds, and the mode is data

**Choice.** All money is `decimal.Decimal` at two decimal places. A `money` module owns three operations —
quantize to two places **under a named rounding mode**, parse an exact money value from a string, and clamp
to non-negative — and nothing else in the codebase calls `.quantize()` or constructs a `Decimal` from a
float.

**Why.** Binary floating point cannot represent `0.10` or `12.50`, so a float pipeline accumulates error
that shows up as a stray cent under exactly the conditions nobody tests. The alternative that avoids
`Decimal` is integer cents everywhere, which is also exact and genuinely faster. It loses on readability at
the boundary: percentages become integer arithmetic with explicit scaling, the catalogue has to be written
in cents (`amount = 1000` for ten pounds, an invitation to a factor-of-100 mistake by the very people we
said would edit it), and every error message has to re-divide. `Decimal` keeps the domain language and is
exact; cents would be the right call only if profiling demanded it, and nothing here is hot.

The single-rounding-site rule matters more than the type choice. Rounding scattered across a codebase is how
`sum(lines) != total` gets in: two places round the same quantity differently and neither is wrong on its
own. Concretely, `quantize` is reached from exactly three kinds of site — where a *rate* becomes an
*amount*, where a *proportional share* becomes *cents*, and where a *tax portion* becomes an amount.
Everywhere else money is added and subtracted, which `Decimal` does exactly at two places with no rounding.

**Half-up is the promotion pipeline's mode, unconditionally.** Retail money rounds half up, and the
statistical-bias argument for banker's rounding applies to summing many independently rounded values — which
the promotion pipeline specifically does not do, because it apportions one exact amount instead.

That carve-out is exactly where the second market lands. Per-line tax *is* many independently rounded values
summed into a cart figure, and `SOUTH` law says half-even — the situation banker's rounding was invented
for. So `quantize` takes the mode as an argument, and **the mode is a property of the rule being applied**,
never a choice made at the arithmetic site: promotion sites pass half-up (the default), the tax site passes
whatever the market declared. Two modes, still exactly one module that rounds, still exactly one rounding
event per amount.

The alternatives were a second quantize function for tax (spreads one rule over two names and invites a
third) and a global mode (makes the result depend on ambient state, which is the one thing `price()` must
never do).

**Also.** The library never mutates the global decimal context. Setting precision at import would silently
change the arithmetic of any application that embeds us. Where extra precision is needed for an intermediate
product or quotient, it is taken inside a `localcontext()`.

### Decision 2 — Cart-scoped discounts are apportioned by largest remainder

**Choice.** A cart-scoped promotion produces one cart-level amount, quantized once. That exact amount is
then split across the lines: each line takes its exact proportional share **truncated down** to whole cents,
and the residual cents are handed out one each to the lines with the largest truncated fractions, ties going
to the earlier line. This lives in an `allocation` module as a single function over an amount and a list of
weights, with no knowledge of carts, promotions or markets.

**Why this shape.** The obvious alternative — apply the percentage to each line and let the total be the sum
— is wrong twice over. It rounds N times instead of once, so the total drifts from the percentage the
customer was promised; and it cannot express AMT at all, because "ten pounds off" is not a per-line quantity
until you decide how to split it. The other alternative — keep full precision per line and round only for
display — fails the moment anything downstream (an invoice, a refund, a ledger) adds the displayed lines
back up and gets a different number.

Largest remainder is chosen over "give the whole residual to the largest line" because it distributes the
error where it is least visible, and the tie-break on line position makes it fully deterministic.

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
something plausible — but the engine makes it unreachable (Decision 4).

Note what this function is *not* used for: tax is never apportioned (Decision 14). It is available if a
cart-level market is ever asked to show per-line tax, and that is the only future use it has.

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
    stackable: bool
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
engine apportions. A future tiered discount, category percentage or spend-threshold gift picks whichever arm
fits without a new concept.

**Why not `if kind == "PCT": ... elif ...` in the engine.** Because promotions change constantly. Today that
means new *codes*, which the catalogue already absorbs. Kinds follow codes — they always do — and the branch
version makes every new kind an edit to the one function that must never break. Here the engine's loop never
mentions PCT, AMT or BOGO.

**Rules are pure and blind.** A rule reads the state, returns an outcome, and never mutates anything, never
rounds by itself (it asks `money`), never learns about other rules, never applies the non-negative floor,
and **never learns which market it is in**. Every one of those is the engine's job, because each is a place
the invariants could break and they should break in one file or not at all.

**Purity is what makes non-stackable selection cheap.** Choosing between two non-stackable promotions means
asking each what it would take off *without* letting it take it. Because `evaluate` returns an outcome
instead of mutating state, that question is just a call: no speculative state, no undo, no transaction.

**Stackability is a flag on the rule, not a kind.** Each rule carries `stackable: bool` alongside its code
and scope. It is catalogue data (Decision 11) that the engine reads; no rule class inspects it.

**What each rule means:**

- **PCT** — the rate applied to the cart's *current* amount, quantized once, apportioned by the engine.
  Because each rule acts on what the previous one left, two 10% codes take 19% off, not 20%.
- **AMT** — its full declared amount, returned without clamping; the engine caps it.
- **BOGO** — the named SKU's quantity summed **across all lines**, then one unit free for every N units:
  `free = quantity // N`. Three in the cart makes one free, four or five still one, six makes two. Free
  units are drawn from the lowest-priced units first and attributed to the lines they came from — the same
  SKU really does appear at two prices in this catalogue, so cheapest-first is load-bearing.

**And they act on listed prices, whatever a listed price contains.** In `SOUTH` the amounts in the state are
tax-inclusive, so a 10% code takes `1.20` off a `12.00` shelf price and a BOGO frees a `4.00` shelf unit.
That is what the customer is promised, and it needs no rule change because a rule was never told what its
numbers included (Decision 13).

### Decision 4 — The engine is a fold, and it owns order, arbitration, the floor, and attribution

**Choice.**

```
  policy = markets.resolve(request.market)      # fails the request if unknown (Decision 12)

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
out of cart.

**Why sort by scope, then code.** Ordering is a business rule, so it should be data. The `Scope` ordinal *is*
the ordering policy, stated once. The secondary sort on code makes multiple promotions of one kind
independent of the order the customer typed them — two customers with the same basket and the same two codes
must not get different prices because one typed them the other way round. Submitted order is preserved for
*reporting*, which is a separate concern.

**Why PCT before AMT.** The requirement is that the answer be the same every time for the same cart; the
order itself was delegated to us. We keep percentage before fixed amount because it preserves the face value
of a voucher: a customer holding "10.00 off" gets 10.00 off (or whatever remains), instead of having their
voucher quietly shaved by a percentage applied after it. That is the version that can be explained at a
support desk, and it is the more generous of the two orderings.

**Attribution comes free.** `post` appends a step to each affected line's chain and one step to the cart's
chain, and the amounts move *because* those steps exist. That is the whole explainability requirement, and
it falls out of the fold rather than being a second pass that can disagree with the first.

**Why arbitration lives in the fold and not before it.** A promotion's value depends on the cart state when
its turn comes — that is the whole point of the running discounted base. So "which of these is worth more?"
is only answerable at a specific moment. The fold is where moments exist.

**The fold is where pricing ends.** Tax is not folded: no rule produces it, no step records it, and it
cannot change what any promotion took. It is assessed afterwards, from the amounts the fold left behind
(Decision 13). The fold's code contains the word "market" exactly nowhere, and that absence is the whole
compatibility guarantee for the country we already sell in.

**Line-level floor.** `apportion` cannot produce a part larger than a line's own amount, because the value is
already capped at the cart remaining and shares are proportional to line amounts — so no line can go
negative either. A line already at `0.00` has weight zero and takes nothing.

### Decision 5 — The catalogue is TOML, with money and rates written as quoted strings

**Choice.** One file per market, each naming its market in a header:

```toml
market = "SOUTH"   # whose offers these are; the file's identity, not an entry's

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
traps for a non-engineer editing it in a hurry. JSON is the serious alternative and also dependency-free,
and `json.load(parse_float=Decimal)` even defuses the float problem — but it has no comments, and a missing
comma produces a parse error at a character offset rather than at an entry. CSV cannot carry parameters that
differ by kind without a column zoo. YAML would need a dependency and is ruled out by the substrate.

**Why one file per market and not one file with a market column.** The two countries run different
campaigns, so the natural unit of editing is a market's offers: one team edits `SOUTH`'s file for `SOUTH`'s
campaign without reading a line of `NORTH`'s. A single file with a market on every entry would make the
common case — change this market's offers — touch a document the other market also depends on, and would put
a per-entry field in the path of every validation and every diff. It would also turn the most dangerous
mistake, a code silently landing in the wrong country, into a one-word typo inside an entry rather than a
mismatch the service can refuse outright.

**Why the market is a header rather than a repeated field.** It is a property of the file, so it is stated
once; repeating it per entry would let a file contradict itself, a question with no good answer. An entry
declaring a market of its own is rejected as an unknown parameter, exactly like an AMT entry carrying a SKU.

**Why the same code may exist in both files.** `SAVE10` at 10% in one country and 15% in the other is two
markets' offers sharing a name, not a duplicate definition. Uniqueness is a property within a file, which is
where "two definitions and no way to choose" actually arises.

**Why the money fields are quoted.** TOML floats are IEEE-754 binary: `amount = 10.10` parses to
`10.0999999999999996...` and the catalogue's formatting would leak into prices. Writing money and rates as
strings and parsing them with `Decimal(str)` keeps them exact. Integers are exempt because TOML integers are
exact, which is why `n = 3` is bare — the inconsistency is deliberate and worth one line of explanation in
the file header, because forcing `n = "3"` would suggest that quoting is cosmetic. The loader **rejects** a
bare float in a money field rather than coercing it, with a message that says to quote it.

**No tax appears in these files, and no market appears on an entry.** An entry declares a kind, its
parameters and its stackability. Its fixed amount comes off the listed prices of the market whose file it is
in: ten off is ten off the price on the shelf, so in a tax-inclusive market part of what it gives away is
tax (Decision 13).

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

**A missing or unrecognised market header is in that fatal class too.** It is not one broken entry; it is a
file full of real promotions whose country is unknown. Loading them under a guessed market would offer one
country's campaign to another — the invisible failure quarantining exists to avoid, not to cause. So the
file does not load, and `check-catalogue` reports the declared market on success and fails when it is absent
or undefined, keeping that alarm at publish time with the rest.

**Why this, and what it costs.** One typo must not stop the shop selling. That is the right call for a file
edited daily by people who are not engineers, and it is the opposite of what a "fail loudly at load"
instinct would produce. The cost is real: the failure moves from deploy time to checkout time. A broken code
is one the marketing email has already promised, and the customer who types it is told we have never heard
of it.

So the design compensates in two places rather than accepting that silently:

1. **The rejects are returned, not logged.** Ignoring them is then a deliberate act by the caller, not an
   oversight. The CLI writes them to stderr on every run.
2. **`check-catalogue` is the loud gate.** Since loading refuses nothing, the checker is the *only* place a
   broken entry stops something — so it reports failure whenever any entry was rejected, and publishing
   should refuse to ship a file that fails it.

Lenient at runtime, loud at publish time.

**Why a duplicate code is quarantined rather than resolved.** Two definitions of `SAVE10` is not a typo in
one entry; it is a question we cannot answer. Taking the first, or the last, would price carts on a coin
toss — the one failure mode worse than an unknown code, because it is invisible. So that code alone is
withdrawn and reported, and the rest of the file loads.

**This policy does not extend to markets.** A market that cannot be resolved stops the cart (Decision 12).
The two inputs have opposite failure modes on purpose, which is one of the reasons they are not one file
(Decision 16).

### Decision 7 — Codes are resolved before anything is applied, and every one gets an outcome

**Choice.** A resolver pass normalises each submitted code (`strip().upper()`), looks it up, and classifies
it: resolved to a rule, unknown, or a duplicate of one already seen. Only resolved rules enter the fold. The
result reports an outcome for every submitted code, in submitted order, from a closed set: applied (with the
value taken, whether it was capped, and whether it had no effect), or not applied with `UNKNOWN_CODE`,
`NOT_APPLICABLE`, `DUPLICATE`, or `SUPERSEDED` — which carries the code that beat it.

**The outcome list is the complete record of every code; the explanation is the record of the money.** Every
submitted code appears in the outcomes, whatever happened to it. Only price changes — and the supersession
decisions that chose between them — appear in an explanation. A support agent looking for "what happened to
the code I typed?" always has one place to look, and it sits beside the explanation in the same result.

**Why a closed enum and not a message.** A caller has to branch on this — "unknown code" is a typo the
customer can fix, "not applicable" is a basket they can fix, and the two deserve different words in the UI.
Free-text reasons get parsed by desperate callers.

**Why "applied, took `0.00`" is not a rejection.** The code was real and it was used; the cart just had
nothing left. Reporting it as a rejection would tell the customer their valid code was bad. It is flagged
`no_effect` so they can be told it was accepted and saved them nothing.

**Why `SUPERSEDED` is its own reason and carries a code.** "Your code was valid but the other one saved you
more" is a different sentence from "we have never heard of that code" and from "that code does not apply to
what is in your basket", and support has to be able to say it. It is the one rejection reason that names
another code, and it is the same code the `NOT_APPLIED` step in the explanation names, taken from the same
arbitration result.

**Why four reasons are enough.** Retirement is done by deleting the entry, so a retired code is simply
unknown. A quarantined entry lands in the same place for the same reason: the customer-facing answer is
"unknown code", while the operator-facing detail lives in the load report where it can be acted on.

**Separating cart errors from code errors.** A malformed *cart* — quantity `0`, negative price, **no market
or an unknown market** — rejects the whole request: that is a caller bug, and pricing it would invent an
answer. A bad *code* never does, because the rest of the cart still prices. Two different failure modes,
deliberately not unified. The market sits on the cart side of that line, and Decision 12 says why.

**A code that is simply not offered in this market needs no reason of its own.** Each market has its own
catalogue file (Decision 5), so a code absent from it is unknown here and present in the other country's
file — which is exactly what the customer should be told, and exactly what this resolver already says. The
fifth fault in the system is not a code fault at all: it is being handed the wrong market's catalogue, which
is a wiring error and is refused before any code is resolved (Decision 12).

### Decision 8 — Library with a thin CLI, not an HTTP endpoint

**Choice.** `price(request, catalogue, markets) -> PricedCart` is the contract, where `catalogue` is the
market's own. The CLI is one adapter: a `price` subcommand reading a cart as JSON on stdin and writing the
result as JSON on stdout, and a `check-catalogue` subcommand. Exit status distinguishes success; a bad cart
(which now includes a missing or unknown market); a catalogue that cannot be read, parsed, or that declares
no market or an unrecognised one; and a catalogue that is valid but belongs to another market. That last one
earns its own status because the remedy is wiring, not a file or a cart. Rejected codes affect none of it,
because a cart with an unknown code priced successfully. `check-catalogue` reports the market a file
declares and fails when that declaration is missing or undefined.

**Why not HTTP.** The substrate forbids network, persistence and multi-process anyway, so an HTTP endpoint
would buy nothing and cost a server lifecycle, request parsing, status-code mapping and a concurrency story.
A CLI over JSON is scriptable, diffable, and makes the acceptance table an exact fixture comparison. If the
product later needs HTTP, it is a second adapter over the same function.

**The JSON boundary re-introduces floats, so it is a named rule.** Money is written as strings in the output
(`"12.50"`, not `12.50`) and parsed from strings or with `parse_float=Decimal` on input. This is exactly the
leak Decision 1 exists to prevent, and the easiest one in the system to reintroduce by accident at the last
mile.

**The adapter may not do arithmetic — and that prohibition now covers tax.** The cart document carries the
market; the result document carries the tax accounts beside the explanations. The adapter writes the figures
it is handed: it may not compute, re-round, apportion or sum them, and where a market reports no per-line
tax it omits those keys rather than writing zeros. An invoice printed from this output is obliged to show
the numbers the service computed, so a "helpful" adapter re-deriving a line's tax from its amount is the
most expensive bug available here.

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
and the amount disagree" is not a bug we test for — it is a state the type cannot hold. `post` is the only
way to extend a ledger, and it constructs the new step from the previous `amount_after`, so the chain is
linked by construction too.

**Why a basis step with a zero delta.** The rule is that the deltas sum to *the difference* between list and
final. If the list price were itself a delta of `+25.00`, the deltas would sum to the final price instead,
and every consumer would need to special-case the first entry. Making the basis a step with `delta = 0.00`
keeps one uniform shape and makes the sum rule true over the whole sequence with no exceptions.

**Why no rounding line, ever.** A residue line is the classic way to make an explanation add up, and it was
explicitly refused. This design has nothing to confess: `apportion` splits an exact amount into parts that
sum to it exactly (Decision 2), and every delta is money that was already quantized once, then only added
and subtracted. The invariant is not "we corrected the residue" but "there is no residue".

**The cart ledger and the line ledgers are two views of one event.** `post` writes them together: a
promotion's cart-level step carries the cart delta, each affected line gets a step carrying its own part,
and the parts sum to the cart delta because `apportion` guarantees it. A line that receives `0.00` gets no
step at all — noise, not information.

**One placement rule: a step appears where the price changed.**

- a line that receives `0.00` of an apportioned discount gets no step;
- a promotion that takes `0.00` overall gets no step on any line *and none on the cart chain either*; it is
  reported in its outcome as applied, saving nothing;
- a code that was unknown, duplicate or not applicable never reaches an explanation at all;
- the one exception is a superseded promotion, recorded on the cart chain only. It changed no price, but it
  decided which promotion did.

**The chain ends where the money stops moving.** Tax is not a step in it, in either market, and that is
structural rather than stylistic: a step names a promotion code or the list price, and tax names neither; a
step carries a delta that moves the amount, and in `SOUTH` tax moves nothing at all — it divides an amount
already decided. Putting tax in the chain would break the delta-sum rule in one market, invent a code-less
step in both, and make the two markets structurally different shapes. So tax is a second account, joined to
the first at exactly one number (Decision 15).

**What this costs.** Result size grows with (lines x promotions), which for a cart is nothing. Building
frozen steps allocates more than mutating a running total, which for a cart is also nothing. Both are worth
naming because the trade is deliberate: we pay allocation to make a class of bug unrepresentable.

**The guard at the boundary.** `price()` re-derives the checks before returning: chains link, chains end at
the reported amounts, each cart delta equals the sum of its line deltas, each applied code that moved money
reports exactly its cart step's delta while each applied code with no step reports `0.00`, and line finals
sum to the total. Decision 15 extends the same guard over the tax account. A failure raises: a result whose
explanation contradicts its amounts is worse than no result, because it is the thing that would be shown to
a customer.

### Decision 10 — Non-stackable promotions are arbitrated once, on one basis, at the point of application

**Choice.** At most one non-stackable promotion is applied. The choice is made at a single instant — where
the first non-stackable promotion falls in the `(scope, code)` order — by evaluating every non-stackable
candidate against *that same state*, comparing the money each would actually take off after the
non-negative cap, and applying the winner's already-computed outcome right there. Ties go to the code
submitted first. Losers become `NOT_APPLIED` steps naming the winner, and `SUPERSEDED` code outcomes
carrying the winner's code.

**Why one basis.** Compare what each one actually takes off the basket in front of you — so the comparison
is made against the cart as it stands at that moment, after whatever has already been applied, never against
the list subtotal. "The one that gives the customer the larger discount" only means something if both
numbers are measured against the same cart.

**Why the winner is applied where it was compared.** If the winner were compared at the arbitration point
but applied later at its own scope position, an intervening stackable promotion could change what it
actually takes — and then the explanation would say "TENOFF beat SAVE10 by 10.00" while the line showed
`-8.50`. Comparing and applying at the same instant makes the promise and the payment the same number by
construction.

**Why after the cap.** A `10.00` voucher on a `5.00` cart gives the customer `5.00`, not `10.00`. Comparing
declared values would hand the customer the smaller real discount while the explanation claimed the larger
one.

**Ties.** Equal money is the only case where the customer's typing order matters: first entered wins. This
is the single, deliberate exception to "input order never changes the price", and it is stated in the spec
as such rather than hidden in a sort key.

**What does not compete.** A non-stackable promotion that does not qualify is `NOT_APPLICABLE` and takes no
part: it supersedes nothing and is superseded by nothing. A duplicate occurrence never reaches arbitration,
so a code cannot beat itself. A cart with exactly one non-stackable code prices exactly as it would have
before this feature existed.

**Arbitration is market-blind like everything else in the fold.** The comparison is on the money taken off
the cart as it stands — gross money in `SOUTH`, net money in `NORTH` — and in both cases it is the money the
customer sees come off. No tax-adjusted comparison is performed, because no customer compares two vouchers
by their tax content.

**Alternatives rejected.**
- *Filter before the fold, by declared value.* A percentage has no value until you know the base, so the
  filter would have to price the cart to decide, which is the fold.
- *Apply both and keep the better result.* Doubles the computation, needs two ledgers, and gives no place to
  record the loser honestly.
- *Exclusivity groups now.* Declined: one rule, two non-stackables cannot sit together. If ever wanted, the
  seam is the same one — arbitration partitions candidates by group instead of taking them as one set.

### Decision 11 — Stackability is a catalogue modifier, not a kind and not a rule

**Choice.** `stackable` is an optional boolean on any catalogue entry, defaulting to `true` when absent:

```toml
[[promotion]]
code = "TENOFF"
kind = "AMT"
amount = "10.00"
stackable = false   # bare boolean: TOML booleans are exact, like integers
```

**Why in the file.** Whether two offers may be combined is a commercial decision, made by the same people
who decide the rate and the amount, and changed on the same cadence. Putting it in code would put a release
between them and a decision they own.

**Why a modifier rather than a kind parameter.** It applies to every kind and means the same thing in each.
The entry validator therefore has two vocabularies: parameters, which are per-kind and strictly checked (an
AMT entry carrying a SKU is a mistake), and modifiers, permitted on any entry. A fourth kind gets
stackability for free.

**Why an unreadable value is rejected rather than defaulted.** `stackable = "false"` is a string, and a
string is not false. Treating an unreadable value as stackable would combine a promotion the commercial team
declared exclusive, which is a money error nobody would see.

**Why absence means stackable.** Every entry written before this modifier existed must keep its meaning.
Defaulting to non-stackable would silently turn today's stacking behaviour off.

### Decision 12 — The market is a property of the request that selects a tax policy, and selects nothing else

**Choice.** `CartRequest` carries a market name. The engine normalises it (`strip().upper()`, the same
treatment codes get), looks it up in a registry, and gets back one `TaxPolicy`. It also pairs with a
catalogue: the market's own file, checked rather than assumed (below). An unknown or absent market
is a **cart** fault: the request is rejected whole, unpriced, alongside a quantity of `0` or a negative
price. The policy is handed to the tax stage and to nowhere else.

```python
def price(request: CartRequest, catalogue: Catalogue, markets: MarketRegistry) -> PricedCart: ...
```

**Why a third argument rather than a global, or a policy passed in directly.** A global is ambient state and
would make `price()` impure, which is the one property everything else here is built on. Passing a resolved
`TaxPolicy` instead of the registry would push market resolution onto every caller, so each would invent its
own answer to "unknown market" — and that answer has to be uniform, because it is the difference between
refusing to price and charging a customer a tax law chosen by accident.

**Why an unknown market is fatal but an unknown code is not.** The catalogue rule is "one typo costs one
promotion, never the shop" (Decision 6), and a cart carrying a bad code still has an honest price. A cart
with no tax law has no honest price at all: every number we could return would be either untaxed or taxed
under a country we guessed. There is nothing to salvage.

**Why no default market.** Defaulting to the market we started with would price a `SOUTH` cart as `NORTH`
the first time a caller forgot the field — tax under-collected, a wrong invoice, no error anywhere. A
required field turns that into a refusal at the boundary. Nothing is implemented, so there is no caller to
break.

**What the market does not touch.** Not rule selection, not ordering, not arbitration, not the cap, not
apportionment, not a single step in an explanation. The fold never sees it. This is the load-bearing
consequence: with a `NORTH` policy the promotion half of the result is byte-identical to what this design
produced before markets existed, so case C6 — every earlier case unchanged — is a property of the structure
rather than a claim the table has to keep re-establishing.

**The market also names which offers apply, and that is the catalogue's business, not the engine's.** The
two countries run different campaigns, so each market has its own catalogue file (Decision 5). A code is
offered in a market by being in that market's file — no modifier, no rejection reason, no market-scoping
feature — and a code absent from a market's file is simply unknown there, which the resolver already says.

**So the engine checks one thing more: that the catalogue it was handed is this market's.** A loaded
catalogue carries the market its file declared; `price()` compares it with the resolved market and refuses
the request if they differ, naming both. This is not defensive programming, it is the only place a
deployment wiring error can be caught: every price produced from the wrong file would be arithmetically
perfect and commercially wrong, built from another country's campaign, and nothing downstream could tell. It
is reported as its own fault, distinct from a malformed cart and from an unreadable catalogue, because the
remedy is neither a corrected cart nor a corrected file but corrected wiring.

### Decision 13 — One tax model, two arms: the basis decides whether tax is added or extracted

**Choice.** A market's tax law is four declared facts and nothing else:

```python
class PriceBasis(Enum):
    TAX_EXCLUSIVE = "tax_exclusive"   # a listed price does not contain the tax
    TAX_INCLUSIVE = "tax_inclusive"   # a listed price already contains the tax

class TaxLevel(Enum):
    CART = "cart"                     # one figure, from the cart amount
    LINE = "line"                     # one figure per line; the cart's is their sum

@dataclass(frozen=True)
class TaxPolicy:
    market:   str
    name:     str          # "VAT" - what the figure is called on an invoice
    rate:     Decimal      # exact percentage: 17, 20
    basis:    PriceBasis
    level:    TaxLevel
    rounding: Rounding     # HALF_UP | HALF_EVEN, from the money module

NORTH = TaxPolicy("NORTH", "VAT", Decimal("17"), TAX_EXCLUSIVE, CART, HALF_UP)
SOUTH = TaxPolicy("SOUTH", "VAT", Decimal("20"), TAX_INCLUSIVE, LINE, HALF_EVEN)
```

The tax stage is one function over a policy and an amount:

```
  assess(policy, priced) ->
      if policy.basis is TAX_EXCLUSIVE:            # add it on
          tax     = quantize(priced * rate/100,          policy.rounding)
          net     = priced
          payable = priced + tax
      else:                                        # take it out
          tax     = quantize(priced * rate/(100+rate),   policy.rounding)
          payable = priced
          net     = priced - tax
```

**Why the basis is a dimension and not two code paths bolted together.** The two arms are the same sentence
read in two directions — a rate relates a net amount and a payable amount, and the basis says which of the
two the pipeline computed. One function with one branch keeps `net + tax == payable` in a single place for
both markets, which is what the guard and the invoice both depend on. A `NorthTax` and a `SouthTax` class
would give that invariant two places to be true differently, and the third country would add a third.

**Why the pipeline does not convert.** The tempting alternative is to normalise: strip the tax off inclusive
prices at the door, run everything on net money, and re-add tax at the end, so the engine only ever sees one
kind of price. It is wrong on the product's own terms and wrong arithmetically. On the product's terms, the
customer is promised 10% off the `12.00` they can see, and a promotion computed on a stripped `10.00` would
take `1.00`. Arithmetically, stripping rounds once per line on the way in and re-adds on the way out, so
`12.00` less 10% could fail to come back to exactly `10.80`. Keeping the pipeline in the market's own money
means nothing is converted, nothing is rounded twice, and the promotion rules are literally the same code.

**Why the extraction is `rate/(100 + rate)`.** A tax-inclusive `12.00` at 20% is `10.00` of goods and `2.00`
of tax, so the tax is one sixth of the gross, not one fifth. Writing it in the rate's own terms keeps the
`20/120` factor out of anyone's hands. The division is taken inside a `localcontext()` with generous
precision, and that is provably safe against the ties this market is full of: a tie needs an exact value
ending in 5 at the third decimal place, which only arises when the quotient terminates — and where it
terminates it is exact at any sufficient precision. A non-terminating quotient can never be a tie, so extra
precision cannot change its rounded value.

**Money is still money.** The rate is a `Decimal` parsed from a string; no float touches the tax path either.

### Decision 14 — The level decides where rounding happens, and a per-line market's cart figure is *constructed from* the lines

**Choice.** `TaxLevel` selects which of two constructors builds the result, and the two are not
interchangeable:

```
  level CART:   cart_tax   = assess(policy, cart_ledger.current)
                line_taxes = None                       # not zero - absent

  level LINE:   line_taxes = [assess(policy, line.current) for line in lines]
                cart_tax   = CartTax.summed(line_taxes, cart_ledger.current)
                             #   tax = sum(t.tax for t in line_taxes)
                             #   no assess() call, no rounding, at the cart
```

**Why this is the whole point.** In a per-line market the cart's tax is *defined* as the sum of the line
figures, because that is what the invoice shows and the invoice is what has to be right. Three `0.15` lines
owe `0.02` each and therefore `0.06`; 20% of the `0.45` cart is `0.075` and rounds to `0.08`. Both are
defensible arithmetic and only one is the law. Making the cart figure a *different constructor* — one that
takes line figures and cannot take an amount — means the wrong number is not merely forbidden, it is
unreachable: there is no code path in which a per-line market rounds at the cart. That is the same move as
Decision 9's: the mistake is made unrepresentable rather than tested for.

**Why a cart-level market reports no per-line tax at all, rather than zeros or an apportionment.** With the
tax rounded once for the whole cart, there is no true per-line figure. Reporting `0.00` per line would be a
false statement on a document people read; apportioning the cart's tax over the lines would invent figures
nobody asked for and would quietly make one market look like the other. Absent is the honest answer, and the
result says which level it used so a reader knows why.

If per-line figures are ever wanted in a cart-level market, the seam already exists and is the one piece of
machinery built for exactly that: `allocation.apportion` splits an exact amount into parts that sum to it
(Decision 2). It would be an apportionment of the cart's already-rounded tax, labelled as such, and it would
not disturb the cart figure. Not built, because nobody has asked and a fabricated line tax on a legal
document is not a default worth guessing.

**Why tax is never apportioned in a per-line market.** It never needs to be. Each line's figure comes from
that line's own final amount, which already exists by the time tax is assessed, so there is no cart-level
quantity to split and no residual cent to place. That is why the hard invariants come out free: the cart tax
is a sum by construction, and the three columns reconcile because each line's own `net + tax == payable`
does.

### Decision 15 — Tax is a second account, joined to the explanation at exactly one number

**Choice.** The result carries two artifacts per line and per cart: the ledger chain (list price to final
amount, promotions only) and the tax account. The tax account records the derivation, not just the figure:

```python
@dataclass(frozen=True)
class TaxFigure:
    policy:       TaxPolicy   # market, name, rate, basis, level, rounding
    basis_amount: Decimal     # the amount this was figured from - the chain's own end
    tax:          Decimal
    source:       TaxSource   # FIGURED (rounded here) | SUMMED (added up from lines)
    @property
    def net(self):     ...    # basis_amount, or basis_amount - tax, by basis
    @property
    def payable(self): ...    # basis_amount + tax, or basis_amount, by basis
```

`basis_amount` is the ledger's `current`, not a copy computed alongside it, so the two accounts join at one
number that exists once. `net` and `payable` are projections, so `net + tax == payable` is arithmetic the
type performs rather than an invariant the code maintains — the same discipline as `Ledger.current`.

**Why two accounts rather than one.** Decision 9 argued that an explanation must be the structure the
arithmetic runs on. Tax does not run through that structure: it names no promotion code, and in a
tax-inclusive market it moves no money at all. A tax step would therefore be a step with no code, carrying a
delta that is zero in one market and non-zero in the other, breaking both the closed step vocabulary and the
"deltas sum to final minus list" rule finance was promised. Two accounts, each sound on its own terms,
joined at a number that appears once, is the shape that keeps both promises.

**Why the derivation and not just the figure.** An explanation that cannot account for the tax is not an
explanation. A bare `tax: 3.83` cannot be checked; *17% of 22.50, added, half-up, once for the cart* can be
reproduced by a support agent with a calculator, and a `SUMMED` cart figure tells an auditor why it is not
what rounding the cart would have given. It is also what makes the two markets legible side by side in one
result format: the same fields with different values, rather than two shapes a reader must learn.

**What the result therefore reports.** Three columns, and which one the promotion pipeline computed is the
market's answer to "do listed prices include the tax?":

```
  NORTH (tax-exclusive, cart level)        SOUTH (tax-inclusive, line level)

  line:   list, chain, final(net)          line:   list, chain, final(payable)
                                                   + tax, net
  cart:   subtotal, chain, final(net)      cart:   subtotal, chain, final(payable)
          + tax, payable                           + tax (summed), net
```

**The guard extends.** Before returning, `price()` also checks: every figure's `basis_amount` is the
`current` of its own chain; `net + tax == payable` everywhere; in a per-line market the line taxes, nets and
payables each sum exactly to the cart's; in a cart-level market no line carries a figure and the line finals
sum to the cart's net. Failure raises rather than returns, for the reason it always has — except that the
document at stake is now also an invoice.

### Decision 16 — Markets are a declared table beside the code, not entries in the promotion file

**Choice.** The `markets` module holds the registry — market name to `TaxPolicy` — as a declared table, and
resolves a name to a policy. It is shaped exactly like a catalogue entry (a name and four scalar fields,
with the rate written as a quoted exact decimal) but it is not in the promotion file and is not edited by
the commercial team.

**Why not in the catalogue file.** The catalogue exists because promotion codes change constantly and must
not need an engineer. None of that is true of tax law. Rates change rarely, by legislation, on a date
everyone knows about months ahead; a wrong rate is not a lost promotion but an under- or over-charged tax
across every cart, which is a legal exposure rather than a commercial disappointment. And the catalogue's
own safety rule makes the mismatch sharp: a malformed entry there is *quarantined* so the shop keeps selling
(Decision 6), whereas a market that failed to load must stop the cart, because there is no safe fallback.
Putting the two in one file would mean one loader with two opposite failure policies, decided per entry kind
— the subtlest possible place to put a rule that expensive.

**Confirmed, not provisional.** The product owner has settled it: the market table stays with engineering,
so that nobody edits a tax rate by hand. That also settles the failure policy — a market that cannot be
resolved stops the cart — and it is the reason a rate change is a release rather than a file edit.

**Why it is nonetheless shaped like data.** Because the next country is a table entry. "In code" here means
a declaration in one module, not logic. If that decision is ever revisited, the change is a loader and a
validator over the same four fields; the policy type, the registry interface, the tax stage and the engine
are untouched. The seam is the registry.

**Why the registry is passed in rather than imported by the engine.** Same reason as the catalogue:
`price()` takes what it depends on. It also means a test, or a third country being trialled, can price
against a policy table that is not the shipped one without monkey-patching a module.

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

| # | Path through the design | Result |
|---|---|---|
| C1 | `NORTH` policy: fold gives net `22.50` (= B1); `assess` adds `22.50 * 17% = 3.825`, half-up, once at cart level | net `22.50`, tax `3.83`, payable `26.33`; lines unchanged, no line tax |
| C2 | `SOUTH` policy: PCT acts on the gross `12.00` (`-1.20`); line figure extracts `10.80 * 20/120` | final gross `10.80`, line tax `1.80`, net `9.00`; cart tax = that one line figure |
| C3 | `SOUTH`, no codes: two line figures, `0.025` and `0.075`, each rounded half-even on its own line | line taxes `0.02` and `0.08`; cart tax `0.10` (summed), net `0.50` |
| C4 | `SOUTH`, no codes: three line figures of `0.025` -> `0.02`; cart figure built by `CartTax.summed` | each line `0.02`, cart tax `0.06` — the `0.08` a cart-level figure would give is unreachable |
| C5 | `SOUTH`: BOGO frees one `4.00` gross unit -> line `12.00`; figure extracts `12.00 * 20/120` | gross `12.00`, tax `2.00`, net `10.00` |
| C6 | `NORTH` policy is tax-exclusive and cart-level, so the fold and every chain are untouched code | every A and B amount identical to the cent; tax is the only addition |

A5/B2 is the case that validates the money structure: it needs the ordering (Decision 4), cross-scope
composition (Decision 3) and apportionment back onto two lines (Decision 2) to be right at once, and it is
where the cart explanation and the two line explanations have to reconcile to the cent. B3-B5 validate the
decision structure: the same two codes, the same catalogue, three different winners, each chosen on money
measured at one moment and applied at that same moment.

Each C case is priced against its own market's catalogue, and the codes named in C1, C2 and C5 are defined
identically in both files so that the cases isolate the tax law rather than a difference in offers. A cart
priced against the other market's catalogue is refused before any of this runs (Decision 12), which is its
own case rather than a variant of these.

C3 and C4 are the pair that validates the tax structure, and C4 is the one that cannot be satisfied by
accident: `0.06` and `0.08` are both correct arithmetic over the same cart, and only the constructor choice
in Decision 14 decides which one the service can produce. C1 and C6 together validate the seam: the same
cart, one market apart, with the promotion half of the result bit-for-bit identical to what it was before
markets existed.

## 6. Risks and trade-offs

- **A rounding or apportionment bug is invisible until it is expensive** → the sum invariant is the stated
  contract of one small function with no domain knowledge, checkable exhaustively over random amounts and
  weights. Three-way splits of an odd cent are the cases worth generating rather than hand-picking.
- **An explanation that drifts from the amount is the failure that makes the feature worthless** → the
  amount is a projection of the chain (Decision 9), so drift requires bypassing the type rather than merely
  making a mistake; the boundary guard re-derives every stated relation before a result leaves `price()`,
  and raises instead of returning. The residual risk is a rendering adapter recomputing a total on the way
  out, which is why the CLI is forbidden from computing, merging or reordering anything.
- **Two rounding modes now live in one result** → half-up on every promotion amount, half-even on every
  `SOUTH` tax figure, in the same response. Mixing them at a call site would be invisible and wrong.
  Mitigated structurally: the mode is a field on the thing being applied, `money.quantize` takes it as an
  argument, and the repository check that only `money` may call `.quantize()` keeps the rounding sites at one.
- **A per-line market's cart tax is a sum, and summing is not what anyone's instinct does** → 20% of the
  cart is the natural expression and the wrong answer. The design removes the instinct's landing site: at
  `LINE` level the cart figure is built by a constructor that takes line figures and cannot take an amount,
  and C4 pins it.
- **`NORTH` reports no per-line tax, and a downstream consumer may fabricate one** → the honest per-line
  figure does not exist when the tax is rounded once for the cart, so the result omits it and says at what
  level it rounded. The risk moves outside the service: an invoicing consumer that divides the cart tax
  itself will produce figures that do not sum. That obligation belongs in the contract governing the caller,
  next to "do not recompute the total"; the seam for doing it properly is named in Decision 14.
- **A fixed amount costs the business differently in the two markets** → ten off is ten off the shelf price
  in both, which is what the customer is promised and what has been settled; but off a tax-inclusive cart
  that `10.00` is `8.33` of goods and `1.67` of tax. A commercial fact rather than a defect, and since each
  market has its own file, a market that wants a different number simply writes one. It belongs in the
  catalogue guide, so whoever writes the number knows what it costs.
- **Two catalogue files can be wired to the wrong markets, and every resulting price would look perfect** →
  the file names its own market, the loaded catalogue carries it, and `price()` refuses a catalogue that is
  not the request's market's, as its own fault pointing at the wiring. Without that check this is the one
  failure in the system that produces no wrong-looking number anywhere.
- **Two files can drift apart** → a change meant for both markets can land in one. That is the cost of the
  markets running different offers, and it is the right cost: the alternative couples two campaigns in one
  document. Nothing here can detect an intended-but-missing entry; what it can do is make each file
  independently checkable, which `check-catalogue` does per file.
- **Every caller must now name a market, and there is no default** → a hard boundary that turns a forgotten
  field into a refusal rather than a wrong tax. Nothing is implemented, so no caller breaks today; the cost
  is that the field is not optional later either, which is deliberate.
- **A result now has more than one total** → the same amount is net in one market and payable in the other,
  so a single field called "total" would mean different things in different countries. The result names the
  three columns explicitly and echoes the market. The residual risk is a consumer that reads one number
  without reading the market, which is why the rendering is specified rather than left to the adapter.
- **Tax inherits every pricing error** → the tax is figured from the amount the promotions left, so a wrong
  discount is now also a wrong tax, on a document with legal weight. This is the right dependency direction
  — there is no honest way to tax a number other than the one being charged — and it raises the value of the
  boundary guard rather than changing the design.
- **A market table in code means a new country needs a release** → judged the right trade against a
  promotion file edited daily, because tax rates change by legislation and a wrong one is a legal exposure
  rather than a lost sale. If that judgement is wrong, the cost is a loader over four fields, not a redesign.
- **The arbitration point is a subtle ordering rule** → the winner is applied where the *first* non-stackable
  promotion falls in `(scope, code)` order, which is not necessarily where that winner's own kind would sit.
  The alternative costs the property that matters more (compared value == taken value), so the rule is stated
  normatively and pinned by acceptance cases in both orderings.
- **The tie-break re-introduces submitted order into pricing** → a single, explicitly chosen exception to
  "input order never changes the price", bounded to a tie between non-stackable candidates, with a scenario
  that reverses a tied pair and expects the other winner.
- **One global non-stackable class is what was asked for** → every non-stackable code competes with every
  other one. A catalogue wanting "one shipping offer and one basket offer" cannot express it without all four
  competing. The seam is named in Decision 10, so adding groups later is a partition key, not a rework.
- **An explanation and a tax account exist only in the response** → the service keeps nothing, by substrate
  and by decision, so the artifact that settles a dispute a month later is the one the caller stored. It
  belongs in the contract governing the caller, and it is why the result is complete and self-describing
  rather than a summary that assumes a later re-price.
- **Quarantining a broken entry moves the failure from deploy time to checkout time** → the right call for
  availability, but a code the marketing email promised can fail silently in front of a customer. Mitigated
  by returning the rejects in the load result, by writing them to stderr on every run, and above all by
  `check-catalogue` reporting failure so publishing can be gated.
- **`check-catalogue` is the only loud alarm** → if nobody wires it into the publishing process, broken
  entries reach production unnoticed. That makes it an operational requirement rather than a convenience.
- **The application order encodes a business rule in a `Scope` enum** → one ordinal per kind in one place,
  read by the fold as data. The risk is not the choice but that a later reader mistakes it for an
  implementation detail; the enum carries the reasoning and the spec states the order normatively.
- **BOGO's threshold reads two ways in English** → "for every 3, one free" can mean one free at three, or a
  group of four with one free at four. Case A4 cannot tell them apart. The settled rule is the first:
  `free = quantity // N`, stated explicitly at three, four and six.
- **The service trusts the prices it is given** → no product catalogue means a caller passing a wrong unit
  price gets a confidently wrong total, a confidently wrong explanation, and now a confidently wrong tax. A
  deliberate boundary, but it belongs in whatever contract governs the caller.
- **Stacking limits are still coming and still not built** → the seam is unchanged: a limit is a filter over
  the resolved rules before the fold. It raises a policy question arbitration has already answered once
  (which ones to keep), and it should reuse the same "most money to the customer" principle.
- **The customer id still does nothing** → carried through untouched so the result is self-describing, and
  the natural hook for a future eligibility rule, which is deferred.

## 7. Deployment note

Nothing exists yet, so there is no migration, no rollback path and no compatibility surface.

There are now two production inputs, with deliberately opposite failure policies:

- **The promotion catalogues — one file per market**, owned outside engineering and edited daily. Because a
  malformed entry is quarantined rather than fatal, the service itself will never refuse a bad file, so the
  publishing process must run `check-catalogue` against each candidate and refuse to ship on failure. That
  gate is the entire safety story for a file that can otherwise take a promised promotion offline without
  anyone being told, and it now also catches a file whose market declaration is missing or unrecognised —
  which would not load at all. Deployment points each market at its own file; a crossed wire is refused at
  the first cart rather than priced, because the loaded catalogue carries its market and `price()` compares
  it with the request's.
- **The market table**, owned where tax law is owned, changed when the law changes. A market it cannot
  resolve stops the cart rather than quarantining, because there is no safe fallback. Whoever owns a rate
  change owns a release, and the release note is the rate. A cart priced before the change keeps the figures
  its caller was given; the service holds no dated rules and cannot re-derive a past cart's tax.

One obligation sits outside this service and has to be written down where a caller will read it: the
explanation and the tax account are returned and never stored, so a caller who may have to answer for a
price later — a checkout, an order service, an invoicing system, anything that can be asked "why was this
26.33?" a month afterwards — keeps the priced result it was given. It must also not recompute or re-round
what it was handed; in a cart-level market in particular, it must not derive per-line tax of its own.

Three audiences need a written page, because all three now read this service's output directly:

- the commercial team, for the catalogues: the kinds and their parameters, the quoting rule, `stackable =
  false` and what it means for a customer holding two exclusive codes, retirement by deletion, the check,
  that each market has its own file which names its market at the top, that the same code may exist in both
  files with different parameters, that a code is offered in a market simply by being in that market's file,
  and that a fixed amount comes off the shelf price — so in a tax-inclusive market part of what it gives
  away is tax;
- finance and support, for the explanation and the tax: how to read a chain, what each step kind means, that
  the deltas reconcile list to final with no rounding line, that a code which changed no price is answered
  for in the outcome list rather than in the chain, what to tell a customer whose code was superseded, and
  how the tax account hangs off the amount the chain ends at — added on top in one market, taken out from
  within in the other, and why a per-line market's cart tax is the sum of its lines and never a number to
  reproduce from the cart;
- whoever owns a rate change, for the market table: the four facts a market declares, the two markets in
  service, that a third fitting those four is a table entry, and that an unknown market refuses the request
  rather than falling back.

## 8. Settled business rules

These are confirmed, not assumptions:

| Rule | Settled as |
|---|---|
| BOGO threshold | One free for every N in the cart — three in the basket means one is free (`quantity // N`) |
| Two percentage codes | Compound: two 10% codes take 19% off, not 20% |
| Order of application | Ours to choose provided it is stable per cart; BOGO, then PCT, then AMT |
| Rounding of promotion money | To the cent and reproducible; half-up is our tie-break within that |
| Explanation content | Per line and per cart: an ordered chain from list price to final, each entry naming a code or the list price itself and its exact delta |
| Explanation arithmetic | Deltas sum exactly to final minus list, to the cent, with no residue and no rounding line |
| Explanation fidelity | It describes what actually happened, in the order it happened; explanation and amount may never disagree |
| Where a step belongs | Where the price changed: nothing that moved no money on a line is listed on that line, and nothing that moved no money at all is listed anywhere |
| Codes that changed no price | Answered for in the code outcomes — the complete, submitted-order record returned beside the explanation — not as an empty step |
| Non-stackable promotions | Marked in the catalogue; at most one applies; the larger discount wins |
| Superseded promotions | Appear in the explanation marked not applied, naming the code that superseded them |
| Ties between non-stackables | The code the customer entered first is applied, and the explanation shows it |
| What exclusives are compared on | What each actually takes off the basket as it stands at that moment, after the cap |
| Exclusivity groups | Declined for now: one rule, two non-stackable promotions cannot sit together |
| A cart is priced for a market | Every request names one; the market decides the tax law and which market's catalogue applies |
| Promotion files | One per market, each naming its market — the two markets run different offers |
| A code in one market only | It is in that market's file and not the other's; nothing else is needed |
| A fixed-amount code | Ten off is ten off the price on the shelf, in both markets — so in SOUTH part of it is tax |
| The market table | Stays with engineering; nobody edits a tax rate by hand |
| Currency | The same in both markets, and not changing |
| Historical rates | None. A rate change is an edit; a past cart is the result its caller kept |
| What a SOUTH invoice needs | What the cases state: per-line tax on final amounts, and a cart tax that is their sum — nothing against list amounts, no per-promotion breakdown |
| `NORTH` | 17%, listed prices tax-exclusive, tax added to the discounted cart, rounded half-up once at cart level, line amounts unchanged |
| `SOUTH` | 20%, listed prices tax-inclusive, promotions against the gross shelf price, tax reported per line, rounded half-even per line |
| A per-line market's cart tax | The exact sum of the line figures — it must equal what the invoice shows |
| Tax basis | Always the amount the promotions left, never the list amount |
| Explaining the tax | Everything the explanation gave us still applies in both markets; an explanation that cannot account for the tax is not an explanation |
| Earlier behaviour | Every earlier acceptance case, priced in `NORTH`, is unchanged to the cent — the numbers stay the numbers, with the tax and the payable amount beside them |
| Per-line tax in NORTH | Not reported: only SOUTH invoices have to show it |
| Retaining explanations | The caller keeps the result; the service stores nothing |
| Malformed catalogue entry | Quarantined and reported, never fatal |
| Unknown or missing market | Fatal for that request — there is nothing honest to price |
| A code that takes `0.00` | Accepted, saved nothing — not a rejection, and not a step either |
| Same SKU at two prices | Happens in practice; the cheapest units are the free ones |
| Stacking limits, customer-id rules | Expected later, deliberately not built now |
| Retiring a code | Delete the entry; a retired code is reported as unknown |

Six of these moved the design rather than confirming it. **BOGO** was originally specified as groups of N+1
(one free at four). The **catalogue** originally refused to load at all if any entry was malformed. The
**explanation** turned the result inside out: rather than computing amounts and describing them, the design
computes the description and reads the amounts off it (Decision 9). **Non-stackability** forced the one
deliberate exception to input-order independence, together with a new decision point inside the fold
(Decision 10). **Markets** forced the rounding mode to become data (Decision 1), the cart's tax figure in a per-line market
to become a constructor rather than a calculation (Decision 14), and the result to carry a second
self-describing account joined to the first at one number (Decision 15). And **one file per market** gave
the catalogue a market header, made code uniqueness a within-file property, let the same code mean different
things in the two countries, and added the one check that catches a crossed wire (Decisions 5, 6 and 12) —
while answering the market-scoping question by making the feature unnecessary.

Still ours to choose — everything put to the product owner is settled above; these are the calls this
design makes on its own, stated so a later reader can disagree with them rather than discover them:

- The market is required and has no default; an unknown market refuses the whole request, and a catalogue
  belonging to another market refuses it too, as its own distinct fault.
- Market names are normalised like codes (trimmed, upper-cased), and so is a file's market header.
- `NORTH` reports the *absence* of a line tax rather than a zero, because a `0.00` on an invoice line is a
  statement, and a false one.
- In `NORTH` the amount the earlier cases called the total is reported as the net column, with the tax and
  the payable amount named separately, rather than one field whose meaning changes by country.

## 9. Genuinely open, and safely deferrable

None of these changes the components, the seams, or the work:

- Whether an explanation step should also carry the apportionment mechanics of a cart-scoped discount (the
  weights, the remainder-cent assignment) beyond the per-line deltas it already carries. Additive: extra
  fields on an existing step, with the sum rules unaffected.
- Whether a customer-facing rendering should suppress the not-applied step that a support-facing one keeps.
  A presentation choice over one flag; the service returns the same result either way.
- Whether `check-catalogue` should eventually be its own entry point, for a publishing pipeline with no
  reason to install the pricing library.
- Whether the quarantine report should also reach an operator through a channel of its own, rather than only
  through the load result and stderr. A deployment concern; it does not change the loader.
- Where each market's catalogue file lives and how a deployment points at the right one. The loader takes a
  path either way, and the market header plus the engine's market-match check make a wrong path loud rather
  than silent — which is what makes this safely deferrable rather than merely deferred.
- Whether a future market needing more than one rate (reduced rates by product category) extends the policy
  or arrives as a second policy kind. It attaches at the same seam — the tax stage takes a policy and an
  amount — but it would need a per-line rate, which is a product-catalogue question this service
  deliberately does not have. Not answerable until such a market exists, and it changes nothing today.
