# Survival count — three teams, two transitions each

A count, not an opinion. For each transition, every named component and named seam in the EARLIER
document is classified against the LATER one. Quotations are verbatim from the documents; `S1`, `S2`,
`S3` mark which stage a quotation comes from.

Classification rules applied uniformly across all three teams:

- A rename with the same responsibility and boundary is **survived** (noted as renamed).
- A type or enum gaining new members of a category it already owned, with every existing member keeping
  its name, meaning and value, is **extended** — including when the *derivation* of an existing figure
  changed while its name, meaning and value did not.
- A component whose stated responsibility list gained or lost a clause naming new work is **reopened**
  unless the earlier document had named that place as a seam.
- A stated dependency direction or an interface type changing is a boundary change: **reopened**.

---

## 1. Team X

### 1.1 X, stage 1 → stage 2

| Component / seam | Class | Earlier text | Later text |
|---|---|---|---|
| `money` (quantize / parse / clamp, `ROUND_HALF_UP`) | survived | — | — |
| `allocation` / `apportion` (largest remainder) | survived | — | — |
| `models` | **reopened** | S1: "`models` \| Request and result shapes; cart validity; `CartState` and its transition"; "(everything depends on models; models depends on money only)" | S2: "`models` \| Request and result shapes; cart validity; `CartState` over the ledgers"; "(everything depends on models; models depends on money and ledger only)" |
| `CartState` + its transition (`LineState`, `reduced_by`) | **reopened** | S1: "state = one LineState per submitted line, current_amount = list amount"; "state = state.reduced_by(parts, attributed_to=rule.code)" | S2: "state = one LineLedger per submitted line, opened at its list amount (a ledger's current amount IS the end of its chain - Decision 9)"; "state = state.post(parts, code=rule.code, capped=capped)   # steps only where a price changed" |
| `rules` component | survived | — | — |
| `PromotionRule` protocol (`code`, `scope`, `evaluate`) | extended | S1: "code: str            # canonical, upper-cased / scope: Scope / def evaluate(self, state: CartState) -> RuleOutcome: ..." | S2: same, plus "stackable: bool      # catalogue data; the rule itself never reads it" |
| `RuleOutcome` = `Applied \| NotApplicable`, `per_line \| None` | survived | — | — |
| `Scope` IntEnum (ordering as data) | survived | — | — |
| `catalogue` component + TOML entry schema | extended | S1: "`catalogue` \| The file format, the entry schema, validation, quarantining bad entries, building rule objects" | S2: "`catalogue` \| The file format, the entry schema and modifiers, validation, quarantining bad entries, building rule objects" |
| `LoadResult` / quarantine policy (Decision 6) | survived | — | — |
| Resolver pass + closed rejection enum | extended | S1: "`UNKNOWN_CODE`, `NOT_APPLICABLE` or `DUPLICATE`"; "**Why three reasons are enough.**" | S2: "`UNKNOWN_CODE`, `NOT_APPLICABLE`, `DUPLICATE`, or `SUPERSEDED` — which additionally carries the code that beat it"; "**Why four reasons are enough.**" |
| `engine` / the fold (Decision 4) | **reopened** | S1: "`engine` \| Order, the floor, apportionment, attribution, rendering"; "for rule in sorted(resolved, key=(rule.scope, rule.code)):" | S2: "`engine` \| Order, arbitration between non-stackables, the floor, apportionment, posting steps, the boundary guard, rendering"; "while queue: … candidates = [rule] + [r for r in queue if not r.stackable]" |
| `cli` adapter + subcommands + exit statuses | survived | — | (Owns unchanged; the "Never" column gains "or compute, merge or reorder an explanation step") |
| `price(request, catalogue) -> PricedCart` contract | survived | — | — |
| Named future seam for exclusivity | **reopened** | S1: "the seam is named so it is an addition later, not a rework: a limit is a filter over the resolved rules before the fold, and exclusivity is a catalogue field plus the same filter. Neither touches `money`, `allocation`, or the rules themselves." | S2: "*Filter before the fold, by declared value.* Simple, and wrong: a percentage has no value until you know the base, so the filter would have to price the cart to decide — which is the fold."; "**non-stackability** forced … a new decision point inside the fold (Decision 10)" |

Reopened + discarded, S1→S2: **4** (4 reopened, 0 discarded).

### 1.2 X, stage 2 → stage 3

| Component / seam | Class | Earlier text | Later text |
|---|---|---|---|
| `money` | **reopened** | S2: "`money` \| The single rounding rule; exact parsing; the non-negative clamp primitive"; "quantize to two places with `ROUND_HALF_UP`" | S3: "`money` \| The rounding primitive under a named mode; exact parsing; the non-negative clamp \| … choose a mode of its own"; "`quantize` takes the mode as an argument, and **the mode is a property of the rule being applied**" |
| `allocation` / `apportion` | survived | — | — |
| `ledger` (`Step`, `Ledger`, `post`, `current`) | survived | — | (Owns sentence verbatim identical; tax deliberately kept out of the chain) |
| `models` / `CartRequest` | survived | — | (Owns sentence identical; the request gains a `market` field) |
| `rules` + `PromotionRule` + `Scope` + `RuleOutcome` | survived | — | S3: "it needs no rule change because a rule was never told what its numbers included" |
| `catalogue` component and file format | **reopened** | S2: "\| Catalogue: code -> PromotionRule"; entries only, no file-level key | S3: "\| Catalogue: market + (code -> rule)"; "market = \"SOUTH\"   # whose offers these are; the file's identity, not an entry's"; "`catalogue` \| The file format, **the market a file declares**, the entry schema and modifiers…" |
| Quarantine policy (Decision 6) | extended | S2: "only an unreadable file is fatal" | S3: "**A missing or unrecognised market header is in that fatal class too.**" |
| Resolver + four rejection reasons | survived | — | S3: "A code that is simply not offered in this market needs no reason of its own." |
| `engine` | **reopened** | S2: "`engine` \| Order, arbitration between non-stackables, the floor, apportionment, posting steps, the boundary guard, rendering" | S3: "`engine` \| Order, arbitration, the floor, apportionment, posting steps, **market resolution, refusing a catalogue of another market, tax assembly**, the boundary guard, rendering" |
| The fold loop itself (Decision 4 pseudocode) | survived | — | (loop body identical; one `policy = markets.resolve(...)` line added above it) |
| Arbitration (Decision 10) | survived | — | — |
| `stackable` modifier (Decision 11) | survived | — | — |
| Boundary guard | extended | S2: "`price()` re-derives the stated relations before returning" | S3: "Decision 15 extends the same guard over the tax account." |
| `cli` (subcommands, exit statuses) | extended | S2: "Exit status distinguishes success, bad cart, and bad catalogue" | S3: "…and a catalogue that is valid but belongs to another market. That last one earns its own status" |
| `price(request, catalogue) -> PricedCart` contract | **reopened** | S2: "`price(request, catalogue) -> PricedCart` is the contract." | S3: "`price(request, catalogue, markets) -> PricedCart` is the contract, where `catalogue` is the market's own." |

Reopened + discarded, S2→S3: **4** (4 reopened, 0 discarded).

### 1.3 X totals

- **Reopened + discarded across both transitions: 8** — S1→S2: **4**; S2→S3: **4**. Discarded: 0.

### 1.4 X's single most expensive reopening

The inversion of the cart state into ledgers at S1→S2. Every amount in the system stopped being a value
and became the end of a chain, taking `models`, `CartState` and the fold's transition with it.

> S1: "`models` \| Request and result shapes; cart validity; `CartState` and its transition";
> "state = state.reduced_by(parts, attributed_to=rule.code)"

> S2: "`models` \| Request and result shapes; cart validity; `CartState` over the ledgers";
> "state = state.post(parts, code=rule.code, capped=capped)"; "the **explanation** turned the result
> inside out: rather than computing amounts and describing them, the design now computes the
> description and reads the amounts off it (Decision 9)"

---

## 2. Team Y

### 2.1 Y, stage 1 → stage 2

| Component / seam | Class | Earlier text | Later text |
|---|---|---|---|
| `money.py` / `Money` | extended | S1: parse/zero/add/sub/times/percentage/allocate/is_zero/format | S2: "Stage-1's `Money` is unchanged"; "# new in stage 2: def after(self, delta: \"MoneyDelta\") -> \"Money\"" |
| `Money.percentage` as the only rounding point | survived | — | — |
| `Money.allocate` (largest remainder) | survived | — | (contract identical; called per promotion instead of once) |
| `Percent` | survived | — | S2: "# stage-1, unchanged" |
| `cart.py` (`Sku`, `CartLine`, `Cart`) | survived | — | S2: "## 4. The request domain — unchanged" |
| `promotions.py` (both scope protocols, all three kinds) | survived | — | S2: "The promotion seam is **unchanged by this stage**" |
| `PromotionCatalog.lookup` | **reopened** | S1: "def lookup(self, code: PromotionCode) -> Promotion \| None: ..." | S2: "def lookup(self, code: PromotionCode) -> CatalogEntry \| None: ..."; "`lookup` returns the **entry**, not the promotion" |
| `CatalogProblem` / `load_catalog` / `CatalogError` / `is_disabled` | survived | — | — |
| `_PARSERS` kind-registration table | survived | — | S2: "`stackable` is read by the loader itself, outside the table" |
| `promotions.toml` entry schema | extended | S1: kind/percent/amount/sku/every | S2: "`stackable` is a new optional boolean on any entry, **defaulting to `true`**" |
| `canonical_order` | extended | S1: "def canonical_order(promotions: Iterable[Promotion]) -> list[Promotion]" | S2: "def canonical_order(resolved: \"Iterable[ResolvedCode]\") -> list[ResolvedCode]" (same sort key `(stage, kind rank, code)`; input is now the wrapper carrying the submission index) |
| `CodeStatus` (3 members) | extended | S1: "Three statuses, because the caller has exactly three responses" | S2: "APPLIED / SUPERSEDED / NO_EFFECT / UNKNOWN"; "Four statuses, four genuinely different conversations" |
| `CodeOutcome` | extended | S1: code/status/amount/detail | S2: plus "forgone: Money \| None" and "superseded_by: PromotionCode \| None" |
| `PricedLine` | extended | S1: stored "gross / line_discount / cart_discount_share / net" | S2: same four names as properties over a stored "explanation: Explanation"; "Every figure stage-1 reported is still reported, with the same meaning and the same name" |
| `Quote` | extended | S1: stored subtotal/total/line_discount_total/cart_discount_total | S2: same four names as folds, plus "explanation: Explanation" |
| `UnitLedger` | **discarded** | S1: "class UnitLedger: \"\"\"Units of one cart line that are still being paid for.\"\"\"  … def free(self, units: int) -> int" | S2: "**Cut, and why:** … **`UnitLedger` as a thing of its own.** … three facts, one owner: `LineLedger`." |
| `MoneyLedger` | **discarded** | S1: "class MoneyLedger: \"\"\"Money still takeable from the cart.\"\"\" … def take(self, requested: Money) -> Money" | S2: "**Cut, and why:** … **The separate cart money balance (`MoneyLedger`).** The cart's remaining is the sum of the lines'." |
| `engine.py` module + its 8-step pipeline | **reopened** | S1: "`pricing/engine.py` \| how promotions interact — order, clamping, allocation, reporting — changes"; step 7 "**Allocate** \| `Money.allocate` \| The cart discount is split across lines in proportion to each line's post-line-promotion net" | S2: "`pricing/engine.py` \| how promotions interact — order, exclusion, clamping, spreading, reporting — changes"; "Stage-1 allocated the *aggregate* cart discount to the lines once, at the end; stage-2 allocates **each** cart-level discount as it is taken." |
| `price_cart(cart, catalog) -> Quote` public seam | survived | — | — |
| `cli.py` (commands, exit codes, JSON) | extended | S1: exit codes 0/2/3 | S2: "Exit codes are unchanged"; the JSON gains explanation arrays |

Reopened + discarded, S1→S2: **4** (2 reopened, 2 discarded).

### 2.2 Y, stage 2 → stage 3

| Component / seam | Class | Earlier text | Later text |
|---|---|---|---|
| `Money` | extended | S2: "`percentage` … THE ONLY ROUNDING POINT (ROUND_HALF_UP)" | S3: "# new in stage 3 — THE rounding point, now with the mode named by the caller: def portion(self, numerator, denominator, rounding)"; "`percentage` … unchanged in behaviour and signature" |
| `MoneyDelta` | extended | S2: opening/reduction/nothing/between/total | S3: plus "addition", "is_addition" |
| `Percent` | extended | S2: parse/format | S3: plus "as_fraction" |
| `AdjustmentKind` / `Adjustment` | extended | S2: "LIST_PRICE / PROMOTION / NOT_APPLIED" | S3: plus "TAX         # new: the market's tax on this amount" and "tax: Money \| None" |
| `Explanation.deltas_for(scope)` | **reopened** | S2: "def deltas_for(self, scope: Scope) -> MoneyDelta: ...        # the fold the report uses (§9)" | S3: "**The fold that had to be corrected.** Stage-2's `deltas_for(scope)` summed every delta of a scope, which was safe while every non-opening entry was a promotion. It is not safe now"; "def promotion_deltas_for(self, scope: Scope) -> MoneyDelta" |
| `Explanation.final` as the reported total | **reopened** | S2: "def total(self) -> Money: ...               # explanation.final" | S3: "def total(self) -> Money: ...               # explanation.after_promotions — the cart when every promotion has applied. C1: 22.50"; "`final` is what the customer pays" |
| `cart.py` (`Sku`, `CartLine`, `Cart`) | survived | — | S3: "`cart.py` is otherwise untouched"; the request gains the required "market: MarketId" |
| `promotions.py` (protocols + three kinds) | survived | — | S3: "— not one line of this module changes in stage 3" (verified: `PercentOffCart`, `AmountOffCart`, `OneFreeInEveryN` and the three protocols are identical) |
| `catalog.py` `load_catalog` / `PromotionCatalog` / `CatalogEntry` / `_PARSERS` | survived | — | S3: "`load_catalog` keeps its signature and its behaviour" |
| `promotions.toml` (the catalogue file) | **reopened** | S2: "`promotions.toml` \| the business adds, retires, or re-marks a **code** (no engineer, no deploy)" | S3: "`promotions.<MARKET>.toml` \| that market's business adds, retires, or re-marks a **code**"; "One catalogue per market, selected by the cart" |
| `LineLedger` | **reopened** | S2: "# and nothing else: every entry in a line's explanation moved that line (Q13b), so a line has no record-only operation." | S3: "def assess_tax(self, rule: \"LineTaxRule\") -> Adjustment: ...       # new"; the SOUTH rule returns "delta=MoneyDelta.nothing()", i.e. a line entry that moves nothing |
| `CartLedger` | **reopened** | S2: "def remaining(self) -> Money: ...   # Σ line.remaining — the cart has no balance of its own"; the interface is propose/commit/record only | S3: "def assess_tax(self, rule: \"TaxRule\") -> None: ...   # new — and TERMINAL … Either way the ledger is SEALED afterwards"; "after it the cart's *explanation* (26.33) and Σ line amounts (22.50) differ by exactly the cart-level tax" |
| `Proposal` / `LineProposal` / `ResolvedCode` / `Choice` / `choose_non_stackable` / `canonical_order` | survived | — | S3: "Unchanged by this stage" |
| `engine.py` module + pipeline | **reopened** | S2: "`pricing/engine.py` \| how promotions interact — order, exclusion, clamping, spreading, reporting — changes"; 7 steps | S3: "`pricing/engine.py` \| how the parts of pricing interact — order, exclusion, clamping, spreading, **when tax is assessed**, reporting — changes"; new "6 \| **Tax stage**" |
| `price_cart(cart, catalog) -> Quote` public seam | **reopened** | S2: "def price_cart(cart: Cart, catalog: PromotionCatalog) -> Quote: ..." | S3: "def price_cart(cart: Cart, catalogs: PromotionCatalogs) -> Quote: ...  # The one signature change in the stage" |
| `PricedLine` | extended | S2: gross/net/line_discount/cart_discount_share | S3: same four, plus "def tax(self) -> Money" |
| `Quote` | extended | S2: subtotal/total/line_discount_total/cart_discount_total/explanation/codes | S3: same names, plus "market", "tax", "amount_due" |
| `CodeStatus` / `CodeOutcome` | survived | — | — |
| `cli.py` | extended | S2: "$ python -m pricing quote --catalog promotions.toml" | S3: "--catalog MARKET=PATH is repeatable"; exit 3 "now includes a missing or unknown `market`" |

Reopened + discarded, S2→S3: **7** (7 reopened, 0 discarded).

### 2.3 Y totals

- **Reopened + discarded across both transitions: 11** — S1→S2: **4**; S2→S3: **7**. Discarded: 2 (both in S1→S2).

### 2.4 Y's single most expensive reopening

The stage-1→2 rebuild of the ledger layer: two named collaborators deleted and the allocation moved from
one end-of-pipeline step into every cart-level commit.

> S1: "| 7 | **Allocate** | `Money.allocate` | The cart discount is split across lines in proportion to
> each line's post-line-promotion net, exactly."; "class MoneyLedger: \"\"\"Money still takeable from the
> cart.\"\"\""

> S2: "**The separate cart money balance (`MoneyLedger`).** The cart's remaining is the sum of the
> lines'. Deleting it turned I6 from a maintained property into a definition."; "Stage-1 allocated the
> *aggregate* cart discount to the lines once, at the end; stage-2 allocates **each** cart-level
> discount as it is taken. The two differ only in the pennies"

---

## 3. Team Z

### 3.1 Z, stage 1 → stage 2

| Component / seam | Class | Earlier text | Later text |
|---|---|---|---|
| `money` (rounding mode, quantum, percentage helper, allocator) | survived | — | Owns sentence verbatim identical |
| `model` (frozen dataclasses + cart-shape validation) | survived | — | Owns sentence identical; new dataclasses are members of the category it already owned |
| `catalog` (format, parsing, validation, quarantine) | survived | — | S2: "Stage 2 adds one field, `stackable` (§7.3), and no new validation shape." |
| `rules` (`Rule` protocol, `CartView`, `CartProposal`/`LineProposal`/`NotApplicable`) | survived | — | S2: "**This component required no change at all in stage 2**" (verified: protocol and proposal types identical) |
| Phase table (10 / 20 / 30) | survived | — | — |
| Largest-remainder allocator (§5.3) | survived | — | — |
| `price(cart, catalog) -> Quote` | survived | — | — |
| `Cart` / `CartLine` | survived | — | — |
| `CodeStatus` (7 members) | extended | S1: "APPLIED / CAPPED / NO_EFFECT / NOT_APPLICABLE / UNKNOWN / UNAVAILABLE / DUPLICATE" | S2: plus "SUPERSEDED      # qualified, but a non-stackable rival gave a larger discount" |
| `CodeResult` | extended | S1: code/status/amount/requested_amount/label/detail | S2: plus "superseded_by: str \| None" |
| `LineQuote` | extended | S1: gross/line_discount/allocated_cart_discount/net | S2: same four names, "now **folds of the journal**", plus "explanation: Explanation" |
| `LineQuote.attribution` | **discarded** | S1: "attribution: tuple[Attribution, ...] # (code, amount) pairs making up the two discount figures" | S2: "**`LineQuote.attribution` is removed**, replaced by `explanation`. … it is removed outright rather than kept as a deprecated alias" |
| `Quote` | extended | S1: currency/lines/gross_subtotal/total_discount/total/code_results | S2: same, plus "explanation: Explanation" |
| `ledger` | **reopened** (renamed to `journal`) | S1: "`ledger` — the single mutable object … A per-request accumulator … It exposes `apply_line(index, code, amount)` and `apply_cart(code, amount)`; both cap internally against available money" | S2: "Stage 1 called this the `ledger` and described it as an accumulator with attribution attached. Stage 2 inverts the emphasis: it is a **record** from which the accumulation is derived. The rename is not cosmetic"; interface replaced by "would_take / append / resolve / view" |
| `engine` | **reopened** | S1: "Owns, in order: resolve … dedupe … group by phase; order within phase; call evaluators; cap and apply each proposal through the ledger; **assemble the `Quote` and the verdict list**." | S2: "walk it, holding the exclusion contest at the first contender (§6.5); cap and append each proposal through the journal; record one resolution per submitted code"; "The engine **never constructs an `Explanation`, a `LineQuote` or a `Quote`.**" |
| `api` / `cli`, incl. the `explain` subcommand | extended | S1: "python -m pricing explain … # human-readable trace" | S2: "`explain` existed in stage 1 as a debug trace. It is now a renderer over a first-class structure"; a four-part support view with invariant I20 |
| Predicted seam: "'Best of' instead of stacking" | survived | S1: "Engine-level: evaluate candidate subsets, keep the cheapest total. Rules stay pure and unchanged" | S2 built the contest in the engine with "rules" untouched; the mechanism is a ranking of single candidates rather than subset evaluation, but the named location held |
| Invariants I1–I9 | survived | — | Ownership of I2–I6 follows the `ledger`→`journal` rename; I7 moves to `explain` |

Reopened + discarded, S1→S2: **3** (2 reopened, 1 discarded).

### 3.2 Z, stage 2 → stage 3

| Component / seam | Class | Earlier text | Later text |
|---|---|---|---|
| `money` | **reopened** | S2: "Here there is one `ROUND_HALF_UP`, one `Decimal('0.01')`, and code review can grep for stray `quantize` outside this module." | S3: "**Stage 3 gives up one stage-2 claim and must say so.** … It no longer does: there are now two rounding modes and, in principle, a per-market quantum. The claim is replaced by something weaker but still checkable — **one rounding *function*, whose mode is an argument**" |
| `model` | extended | S2: "cart-shape validation only (non-empty SKU, `quantity >= 1`, `unit_price >= 0` and 2dp)" | S3: "…and at the market's quantum, and `market` being a name the profile table knows"; "`model` may import `market`" |
| `catalog` component | extended | S2: "Produces an immutable `PromotionCatalog` plus a list of `CatalogDiagnostic`" | S3: "Produces an immutable `PromotionCatalog` — now carrying a resolved `MarketProfile` — plus a list of `CatalogDiagnostic`"; "adds one required settings key (`market`) and removes one (`currency`)" |
| The catalogue file (one file for the shop) | **reopened** | S2: "# promos.toml — settings, then one table per code."; `[settings]` holds only `currency` | S3: "# south.toml — settings, then one table per code."; "**`[settings].market` is required.**"; "**One catalog prices one market**" |
| `[settings].currency` | **discarded** | S2: "**Currency is configured once**, in `[settings].currency`, and copied into every `Quote`. Not a field on the cart and not a CLI flag" | S3: "**`[settings].currency` is removed.** The currency comes from the market profile." |
| `rules` (`Rule`, `CartView`, proposals) | survived | — | S3: "This component required no change in stage 2 and none in stage 3" (verified; `CartView`'s fields are renamed per §2.1 but identical in content) |
| `journal` (`Entry`, `Resolution`, `would_take`/`append`/`resolve`/`view`) | survived | — | — |
| Phase table | survived | — | S3: "There is **no tax phase**" |
| Largest-remainder allocator | survived | — | — |
| `engine` | **reopened** | S2: "### 4.5 `engine` — the orchestrator, and the only place policy lives" | S3: "### 4.6 `engine` — the orchestrator, and the only place **promotion** policy lives"; "It does own one new step, before everything else: **the market check.**" |
| `explain` (the projector) | extended | S2: "A pure function `project(journal, cart, catalog_currency) -> Quote`"; "Three projections of one record" | S3: "A pure function `project(journal, cart, profile) -> Quote`. It reads the journal, calls `tax`"; "Four projections of one record" |
| **I14** ("every money figure is a fold of the journal") | **reopened** | S2: "**I14** \| Every money figure in the `Quote` is a fold of the journal; no figure is computed by a second path \| boundary (§4.7)" | S3: "I14 \| Every money figure in the `Quote` is a fold of the journal, **or a function of such a fold and the `MarketProfile` computed in `tax`** \| boundary (§4.9)" |
| Predicted seam: "Tax / shipping" | **reopened** | S2: "\| Tax / shipping \| New phases after 30; allocation is already the mechanism for apportioning them to lines, and each becomes an ordinary row in the explanation. \|" | S3: "The obvious alternative — and the one stage 2's own extension table predicted (*\"Tax / shipping: new phases after 30\"*) — is to make tax a phase … **Stage 3 rejects that prediction**, having now seen the actual requirement." |
| `Adjustment` / `AdjustmentKind` / `Explanation` | survived | — | S3: "**Unchanged from stage 2, deliberately and completely.**" (verified field by field) |
| `LineQuote` | extended (renamed fields) | S2: "gross", "net" | S3: "list_amount", "amount" — "identical" values per §2.7 — plus "tax: TaxView \| None" |
| `Quote` | extended (renamed fields) | S2: "gross_subtotal", "total" | S3: "list_subtotal", "amount" — "identical" values — plus "market", "payable", "tax" |
| `CodeStatus` / `CodeResult` | survived | — | S3: "**Unchanged from stage 2.**" |
| `Cart` / `CartLine` | survived | — | The request gains a required "market: str" |
| `price(cart, catalog) -> Quote` | survived | — | S3: "The signature of `price()` is **unchanged** at this stage" (verified) |
| Support view (four parts, I20) | extended | S2: "render **four parts, in this order**" | S3: "render **five parts, in this order**" — part 4 is the tax |
| `api` / `cli` | extended | S2: JSON money as strings, ordered explanation array | S3: plus tax figures, "`LineQuote.tax` serialises as `null` in NORTH", "No stage-2 key spellings are emitted" |

Reopened + discarded, S2→S3: **6** (5 reopened, 1 discarded).

### 3.3 Z totals

- **Reopened + discarded across both transitions: 9** — S1→S2: **3**; S2→S3: **6**. Discarded: 2
  (`LineQuote.attribution` in S1→S2, `[settings].currency` in S2→S3).

### 3.4 Z's single most expensive reopening

The `ledger` → `journal` inversion at S1→S2, which the document itself declines to call cosmetic. It
changed the responsibility of the one mutable object, replaced its entire interface, and moved `Quote`
construction out of the engine into a new component.

> S1: "### 4.6 `ledger` — the single mutable object — A per-request accumulator: per-line gross, per-line
> applied discounts with attribution, and the running subtotal. … It exposes `apply_line(index, code,
> amount)` and `apply_cart(code, amount)`; both cap internally against available money"

> S2: "Stage 1 called this the `ledger` and described it as an accumulator with attribution attached.
> Stage 2 inverts the emphasis: it is a **record** from which the accumulation is derived. The rename is
> not cosmetic — it is the difference between \"a total, plus some notes about it\" and \"a history,
> whose fold is the total\"."

---

## 4. Self-assessments my reading contradicts

Each of these is a claim a document makes about itself or about an earlier stage, checked against the
actual text of both versions.

1. **X, S1 — "the seam is named so it is an addition later, not a rework."** Stage 1 predicted that
   exclusivity would land as "a catalogue field plus the same filter [over the resolved rules before the
   fold]". Half of that prediction failed: stage 2 rejects the filter outright — "*Filter before the
   fold, by declared value.* Simple, and wrong" — and instead adds "a new decision point inside the fold
   (Decision 10)", replacing the `for` loop with a queue-and-arbitrate walk. The catalogue-field half
   held; the engine half was a rework.

2. **X, S1 — "Why three reasons are enough."** Stage 1 argues a closed set of three rejection reasons is
   sufficient ("Retirement is done by deleting the entry … Two audiences, two channels, one closed
   enum"). Stage 2 needs a fourth, `SUPERSEDED`, and re-runs the same argument under the heading "Why
   four reasons are enough." The sufficiency claim was a prediction, and it did not hold.

3. **X, S2 → S3 — "Exactly one place in the system rounds" quietly became "Exactly one module rounds."**
   S2's goals say "Exactly one place in the system rounds, and exactly one place can violate the sum
   invariant"; S3's say "Exactly one **module** rounds". S2 also said `quantize` is "reached from exactly
   two kinds of site"; S3 says "exactly three kinds of site" and adds a mode argument. The weakening is
   real and is not flagged as a retraction anywhere in S3 (compare Z, which flags the identical
   weakening explicitly).

4. **X, S3 — "the promotion half of the result is byte-identical to what this design produced before
   markets existed" / "bit-for-bit identical."** The *amounts* are unchanged — that part I can confirm
   from the A/B tables. "Byte-identical" is not: X's own "Still ours to choose" section says "In `NORTH`
   the amount the earlier cases called the total is reported as the net column, with the tax and the
   payable amount named separately", and the result gains three named columns. The serialized result
   differs; the arithmetic does not.

5. **X, S3 — "The fold's code contains the word 'market' exactly nowhere."** True of the loop body, but
   the Decision 4 block it appears in now opens with "policy = markets.resolve(request.market)      #
   fails the request if unknown". The claim is defensible only if "the fold" excludes the first line of
   the block that defines it.

6. **Y, S2 — "so a line has no record-only operation at all and every entry it holds came from a
   balance moving."** Contradicted by Y's own stage 3: `LineLedger.assess_tax` appends a `TAX` entry, and
   in SOUTH `VatIncludedInLine.assess_line` returns "delta=MoneyDelta.nothing()". That is exactly a
   record-only entry on a line. Stage 3 does not acknowledge the reversal; its I9 row simply adds
   `assess_tax` to the list of operations that "move a balance".

7. **Y, S3 — "I6 survives word for word as a result" / "**exactly as stage-2 stated it**".** The sentence
   survives; the mechanism behind it does not survive unchanged. S2 made I6 definitional because
   `Quote.total` was `explanation.final` and `CartLedger.remaining` was Σ line remaining. In S3 the cart
   explanation's `final` is the payable — S3's own §7 says "the cart's *explanation* (26.33) and Σ line
   amounts (22.50) differ by exactly the cart-level tax" — and the invariant is kept only by re-pointing
   `total` at a newly-introduced fold, `explanation.after_promotions`. "Word for word" is true of the
   words and not of the definition.

8. **Y, S3 — "The one signature change in the stage."** `price_cart`'s signature is one change; it is not
   the only one to a published surface. `Cart` gains a required `market` field (so `cart.json` gains a
   required key), `Explanation.deltas_for` is renamed and re-specified, `LineLedger` and `CartLedger`
   each gain a method, and the CLI's existing flag grammar changes incompatibly from
   "--catalog promotions.toml" to "--catalog MARKET=PATH".

9. **Y, S3 — "Nothing else in the system knows there is more than one country."** As literally written
   this is false: `cart.py` gains `MarketId`, `catalog.py` gains `PromotionCatalogs.for_market`,
   `quote.py` gains `Quote.market`, `money.py` gains a `Rounding` enum, `explanation.py` gains a `TAX`
   kind, the engine gains a resolve step and the CLI gains per-market catalogue routing. The accurate
   and still-substantial claim is the narrower one Y makes in the same paragraph: "the promotion kinds
   and the contest are untouched by this stage", which I verified.

10. **Z, S3 — "`catalog`, `rules`, `engine` and `journal` are unchanged from stage 2" / "the second time
    a stage has landed without touching the engine."** Contradicted twice inside the same document:
    §4.4 says the catalog "adds one required settings key (`market`) and removes one (`currency`)" and
    now produces a `PromotionCatalog` "carrying a resolved `MarketProfile`"; §4.6 says the engine "does
    own one new step, before everything else: **the market check**", and its section heading narrows
    from "the only place policy lives" to "the only place promotion policy lives". `rules` and `journal`
    are genuinely unchanged; the blanket four-way claim is not.

11. **Z, S3 — "an entire second tax regime landed as **one data row and one new pure function**."** By
    the count above it also required: `money` to abandon its single-mode rounding claim and gain exact
    integer-rational rounding (§5.7), a new `market` module, a new required catalog settings key, the
    removal of `[settings].currency`, four payload field renames, a new top-level `payable` field, a new
    engine guard step with a new error category, a fifth part in the support view, and a widened I14.
    That is a smaller footprint than the other two teams', but "one data row and one pure function" is
    the marketing version of it.

12. **Verified claims that did hold, recorded because they were tested rather than taken on trust:**
    Y, S3 "not one line of this module changes in stage 3" about `promotions.py` (confirmed — both scope
    protocols and all three kinds are identical); Z, S2/S3 "This component required no change at all"
    about `rules` (confirmed across both transitions); Z, S3 "The signature of `price()` is **unchanged**
    at this stage" (confirmed — alone among the three teams); X, S3 that the fold's loop body is
    unchanged from S2 (confirmed line by line). Z is also the only team that announces its own retracted
    claim rather than restating it: "**Stage 3 gives up one stage-2 claim and must say so.**"
