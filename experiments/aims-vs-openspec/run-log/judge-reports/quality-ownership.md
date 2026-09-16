# Code-quality / ownership reading — X, Y, Z (checkout pricing, stage 3)

Disposition: invariant-ownership and correctness-of-encapsulation. Hard on leaks across seams, on a rule
enforced in more than one place, and on the new market/tax concept escaping its boundary. Not impressed by
volume. Every load-bearing claim carries a quotation.

The three designs solve the same stage-3 problem and converge on the same core (a pure `price()`, an
append-only explanation the amounts are folded from, promotions market-blind). They **diverge on exactly one
structural question that this reading is built to judge: where does tax live relative to the invariant-bearing
record, and how tightly is market-awareness confined?**

- **X** — tax is a *second account* joined to the ledger at one shared number; market absent from the fold;
  but the engine assembles tax, runs the reconciliation guard, and renders.
- **Y** — tax is folded *into* the explanation as a fourth `AdjustmentKind`; the ledger gains an `assess_tax`
  step and a seal; `Adjustment` gains a conditional `tax` field; every money fold must now discriminate kind.
- **Z** — tax is a *separate pure component* downstream of everything; the journal and the engine are both
  provably blind to it; `tax` is the sole constructor of `TaxView`, `explain` the sole constructor of `Quote`.

---

## Design X

### 1. Code smells
Clean of the big ones. **No anemic model:** the ledger carries behavior, not just data —
`@property def current(self) -> Decimal: return self.steps[-1].amount_after` with "`current` is a projection,
not a field" (Decision 9). **No primitive obsession at the seams:** money is `Decimal` confined to one module,
`Scope` is an `IntEnum` whose ordinal *is* the ordering policy ("The `Scope` ordinal *is* the ordering policy,
stated once", Decision 4).

The one smell worth naming is a **mild god-object tendency in the engine.** Its own ownership row reads:
"`engine` | Owns | Order, arbitration, the floor, apportionment, posting steps, market resolution, refusing a
catalogue of another market, tax assembly, the boundary guard, rendering" (component table, §3). That is order
+ arbitration + floor + apportionment + tax assembly + guard + rendering in one component. It is deliberate
("exactly one place can violate the sum invariant"), and it is not a data-bag god object — but it is the
broadest single component of the three, and tax assembly and rendering are responsibilities Z factors out.

### 2. Interfaces & encapsulation
`PromotionRule(Protocol)` with `evaluate(self, state) -> RuleOutcome` is a real abstraction (three live
implementations; a fourth "picks whichever arm fits without a new concept", Decision 3). Information is hidden
by *telling*: the engine hands the rule a state and is handed an outcome; the rule "never learns which market
it is in" (Decision 3). Tax does not leak into pricing: "The fold's code contains the word 'market' exactly
nowhere" (Decision 4/12), and the two accounts "join at one number that exists once" — `basis_amount` is "the
ledger's `current`, not a copy computed alongside it" (Decision 15). No implementation type crosses a seam.

### 3. Genericity calibration
`RuleOutcome = Applied | NotApplicable`, with `Applied.per_line: Mapping[int, Decimal] | None`. Floor/ceiling
handled by an `Optional` rather than by segregating into two types: "a rule that knows, says; a rule that does
not, defers" (Decision 3). Defensible — the consumer (engine) genuinely needs both arms — though it is the one
place X resolves a two-concept tension with `None` where §2 would nudge toward two types. `TaxPolicy`'s four
enum axes (`PriceBasis`, `TaxLevel`, `rounding`, `rate`) are the honest common vocabulary of the two markets;
no per-cell dead code, one `assess` reads the axes.

### 4. Cohesion & coupling
Strong. The cart-tax-is-a-sum rule is localized so hard that the wrong answer is unrepresentable: "a different
constructor — one that takes line figures and cannot take an amount — means the wrong number is not merely
forbidden, it is unreachable" (Decision 14). The floor is owned once in the fold, not in AMT: "the floor,
applied once, here … structurally impossible for *any* rule … to drive the cart below zero" (Decision 4). A
plausible change (new promotion kind) is a new rule class only; "The engine does not learn about it" (§2).

### 5. Naming & the reasonable-reader test
Names are accurate and side-effects surfaced. `SUPERSEDED` "is the one rejection reason that names another
code" (Decision 7); the market-mismatch fault "earns its own status because the remedy is wiring" (Decision 8).
No surprise.

### 6. Single responsibility & size
Leaves each own exactly one thing ("`money` owns *there is exactly one rounding site*", §3). The engine is the
exception (group 1). X is the most **decided** of the three: its length is spent on worked reconciliations, not
on restating the mechanism.

---

## Design Y

### 1. Code smells
The load-bearing smell of this reading. **Tax is modelled as a movement it is not**, and that mismodelling
loads a value type. `AdjustmentKind` gains `TAX = "tax"` and `Adjustment` gains a kind-specific `tax: Money |
None` on top of the existing kind-specific `forgone`, `superseded_by` (§6). Validity is now conditional on
kind: "`TAX => … tax is not None and (delta.is_zero() or delta == MoneyDelta.addition(tax))`" (§6
`__post_init__`). Y itself flags it under **Watched**: "`Adjustment` is now one type with four kinds and two
kind-specific money fields (`forgone`, `tax`), policed by a shape rule per kind … the honest move is to
segregate" (§15). That is a value type doing four jobs — the §2/§8 segregation smell, acknowledged.

No anemic-model problem in the promotion rules (`free_units`, `requested_discount` carry behavior), and
`promotions.py` is genuinely untouched ("not one line of this module changes", §5) — a real strength.

### 2. Interfaces & encapsulation
`LineTaxRule` / `CartTaxRule` are two protocols with one method each, and Y's justification is sound on its own
terms: a unified `assess(amount)` "plus a flag … and the engine would branch on the flag, which is the rule
leaking back out of its owner" (§8). And `LineTaxRule` is a genuine abstraction with a second real
implementation named ("a country with tax-exclusive shelf prices that taxes per line … is a `LineTaxRule`
whose assessment returns a non-zero delta", §8).

The encapsulation cost is elsewhere: **tax-awareness is pulled into the invariant-bearing record.** The ledger
gains a tax operation — "`def assess_tax(self, rule: "TaxRule") -> None: … # new — and TERMINAL`" plus a seal
(§7) — so the mutable object that owns the money now also owns tax assessment. This is the opposite move from X
and Z, and it is what forces the rest.

### 3. Genericity calibration
The two tax protocols are calibrated well (line vs cart is a real behavioral split, each market implements
exactly one). The mis-calibration is `Adjustment`: it is *over-broad* — one type unifying list-price, promotion,
not-applied and tax, three of which need fields the others must hold as `None`. §2 says segregate when no
single type serves every producer without a foreign field; `tax` and `forgone` are exactly those foreign
fields.

### 4. Cohesion & coupling
The weak point, and it is **repeated, not local.** Because tax is an entry in the same chain the amounts fold
from, every money fold must now discriminate kind, and Y had to *repair* one that did not: "Stage-2's
`deltas_for(scope)` … is not safe now: NORTH's VAT is a `CART`-scoped entry of +3.83 … So the discount folds
are explicitly `kind == PROMOTION` folds" (§6). The "deltas sum to what came off" invariant is no longer owned
by one uniform structure — it is re-established in each fold by a kind filter, and a fifth entry kind is a
shotgun-surgery risk across all of them. The bug Y caught and fixed is the direct evidence the abstraction
leaked.

The stated benefit that justifies all this — avoiding "the second producer of one fact that an earlier recorded
decision exists to prevent" (§16 alt 1) — is **illusory relative to its cost**, because X and Z both avoid a
second producer *without* folding tax in, by joining a separate tax account to the amount at one shared number
(X Decision 15; Z I22). Y pays the coupling for a guarantee the other two get for free.

### 5. Naming & the reasonable-reader test
Good. `after_promotions` is named for exactly what it is; `amount_due` "is the new field whose name can only
mean one thing" (§10). The retained stage-2 names are defended.

### 6. Single responsibility & size
`Adjustment` and `CartLedger` each took on a second responsibility this stage (tax shape; tax assessment +
seal). Y is well-decided and mid-length; the problem is not sprawl but that its central decision loads two
components.

---

## Design Z

### 1. Code smells
Cleanest of the three on this axis. **Tax is correctly typed as a decomposition, not a movement:** "The
journal records *movements of price*. Tax is not a movement; it is a *decomposition* of a price that has
already been reached" (§1.2) — so `AdjustmentKind` stays at three members and no value type is loaded. No
anemic model (rules carry `evaluate`; the def/rule split is a strategy pattern, not a data bag). The one
exposure is *over-provision*, not under: `TaxView` publishes seven fields and `MarketProfile` a four-axis
matrix (below).

### 2. Interfaces & encapsulation
The strongest boundary of the three, and it is **structurally enforced, not merely asserted.** Market-awareness
is confined to one component and the confinement is import-checkable: "Nothing upstream of `tax` reads
`treatment`, `rate`, `granularity` or `rounding`. For one cart and one set of promotions, the journal is
identical in every market" (I26), and "The engine never reads the market's tax fields. It passes the profile
through to `explain` untouched" (§4.6). `tax` is "A pure function of two arguments and nothing else" that "may
not see the journal, a `PromotionDef`, a `CodeResult` or a list amount" (§4.8, I27). And the single-producer
rule is greppable: "if `Quote(` appears anywhere outside this module, or `TaxView(` anywhere outside `tax`, the
invariant is gone" (§4.9). The invariant-bearing mutable (the journal) has **zero** tax knowledge; the
orchestrating engine has zero tax knowledge; the entire new concept lives in two downstream pure projectors.

### 3. Genericity calibration
This is where Z is most exposed and it survives. `MarketProfile` is a four-axis matrix (treatment × granularity
× rounding × rate) with two of eight-plus cells occupied — Y explicitly attacks this shape as speculative ("a
… matrix has eight cells, six of which no country we sell in occupies", Y §15). Z's defense is real: the axes
*are* the requirement (NORTH and SOUTH differ on precisely these four independent facts), there is **no dead
per-cell code** (one `assess`/`cart_tax` reads the axes; the unoccupied `EXCLUSIVE × LINE` combination "already
composes: `tax_for` per line, `cart_tax` sums", §9), and the generality is bounded against the speculative
smell: "the profile is a closed table of named markets … Nobody can construct a market at runtime" (§2.2). A
third market is "one row + one acceptance row"; in Y's polymorphic scheme it is a new class. The seven-field
`TaxView` is justified per-consumer ("each has a distinct reader who should not have to do arithmetic to get
it", §2.4) — carries slightly more than minimal, but each field has a named present consumer.

### 4. Cohesion & coupling
Best-localized of the three. "`catalog`, `rules`, `engine` and `journal` are unchanged from stage 2" (§4) — the
second tax regime touched none of the pricing core. C4 is unreachable structurally *and* fenced by a paired
invariant precisely because a later reader is the threat: "granularity == LINE … **the cart amount is never
passed through `tax_for`**" (§4.8) with I24 (the sum) and I25 (the prohibition) stated separately "because C4
is precisely the case where a later reader … replaces the sum with a cart-level computation" (§3). A plausible
future change lands on a seam that is named and priced (§9).

### 5. Naming & the reasonable-reader test
One lexical rule governs sign ("Anything named `delta` is a signed movement … `amount`, `discount` or `tax` is
a non-negative magnitude", §5.5) and it is mechanically checkable. `SUM_OF_LINES` as a `derivation` value "is
the answer, stated on the value itself" for the C4 support question (§2.4). No surprise.

### 6. Single responsibility & size
Each component states its one reason to change; the engine "never constructs an `Explanation`, a `LineQuote`, a
`Quote` or a `TaxView`" (§4.6), so decision (engine), record (journal), projection (explain) and market
arithmetic (tax) are four separate owners. **The one caution the rubric demands:** Z is ~2× the others and
restates its core points (I24/I25, §5.6, §5.7, C4, F1, §10.1) repeatedly. But the *structure* is decided — "One
append-only journal, market-blind … four projections … no second computation path" (§13.5) — and the length is
test tables and Q-tracing, not architectural indecision. Judged on structure, the length neither earns nor
costs the verdict.

---

## Verdict

**Z.**

The deciding property is **confinement of the new concept to import-checkable ownership.** The stage-3 change is
tax + market, and the correctness question this reading cares about is whether that concept escapes into the
invariant-bearing record or the orchestrator. Z keeps *both* the append-only journal (the single mutable that
owns the money invariants) and the engine (the orchestrator) provably blind to tax and market — "the journal is
identical in every market" (I26); "The engine never reads the market's tax fields" (§4.6) — and confines the
entire regime to two downstream pure projectors whose sole-constructor boundaries are verifiable by reading
imports (§4.9). Market-awareness cannot leak because a leak is a new import, and a new import is visible.

X is a close second and loses only on this axis: it keeps *pricing* market-free ("the fold's code contains the
word 'market' exactly nowhere", Decision 4) but routes **tax assembly, the reconciliation guard, and rendering
through the engine** (component table, §3), enlarging the one component that already owns order, arbitration,
floor and apportionment. Its boundary is guarded-and-asserted where Z's is import-enforced. X's greater
concision is credited, not penalized — but the funnel it concentrates is wider than Z's.

Y is third on exactly this property: by folding tax into the movement chain it pulls tax-awareness *into* the
record (`CartLedger.assess_tax`, §7) and loads `Adjustment` with a conditional `tax` field (§6), and — the
repeated, structural cost — it dissolves the "deltas sum to what came off" invariant into per-kind folds,
evidenced by the `deltas_for` repair it had to make (§6). It pays that coupling for a single-producer guarantee
X and Z both obtain without it.
