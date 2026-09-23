# Design — Discount-code applicability engine

Design only (no implementation), produced with the aims method: one planning pass, then the one mandatory review-and-revise round (`decisions/0011`). Graded against `arm-table-design-principles.md`. The mandatory round's findings and how the final design resolves them are in §7; everything above §7 is the **final, post-revision** design.

---

## 1. Product intent and scope (goals)

**Primary question the engine answers:** given a shopping cart and one discount code, *does this code apply to this cart?* — returning a **verdict**, never a bare boolean.

- In scope: deciding applicability of a code against a cart; producing a reason when it does not apply (R3); combining conditions with all/any/not (X1); adding new condition kinds (X2); choosing deterministically among several applicable codes by priority (X3).
- Out of scope (stated, so the subtractive pass can hold the line): computing the *discount amount*, applying it to the cart, code redemption/inventory, and multi-currency (see §7, deliberately omitted as speculative).

## 2. Substrate note

The product card fixes no language; for a design-only exercise the host is a **technical freedom**. I express types in a typed ADT notation (sealed sum types + value objects) and give each its concrete backing representation, because the principles require the design to say *what a condition / code / verdict actually is as a type*. Any host with real sum types and immutable value objects (Kotlin sealed, Rust enum, TS discriminated union, Swift enum, or Python 3.12 frozen dataclasses + `match`) realizes it directly.

## 3. Domain types (concrete representation)

Everything is an **immutable value object** (§4 immutability by default). Illegal states are removed at construction by **smart constructors** (`.of(...)`), so `evaluate` is a total pure function over already-valid inputs (§1 defensive at the edge, trusting inside).

### 3.1 Foundational value objects

```
Money                       # store's single currency, exact
  repr:  minor_units: BigInt          # integer cents — never a float (§4)
  of(minor_units) -> Money            # rejects nothing; any integer is a valid amount
  zero() -> Money = Money(0)
  >=, >, +, -   (total order; addition saturates in BigInt, no overflow)

NonNegativeMoney            # a *threshold* / price must be ≥ 0
  repr:  Money
  of(m: Money) -> NonNegativeMoney    # smart ctor: rejects m < 0  (fail fast, §1)

Quantity
  repr:  int
  of(n) -> Quantity                   # smart ctor: rejects n <= 0  (§1)

Category
  repr:  slug: str (normalized, non-empty)         # value object, not a bare string (§4)
  of(s) -> Category                   # rejects empty/blank

DayOfWeek                   # enum MON..SUN  (used by the X2 example, §3.4)
Timestamp                   # captured on the cart; exposes .weekday() -> DayOfWeek
CodeId                      # value object over a non-empty string; total order for tie-breaks
```

`Money` is **integer minor units** so subtotal arithmetic and the `min_subtotal` comparison are exact (no float drift) and cannot overflow (BigInt). Currency is a single store currency and is *not* a field — see §7.

### 3.2 The cart and its published read model

```
LineItem
  product_id: ProductId
  category:   Category
  unit_price: NonNegativeMoney
  quantity:   Quantity
  line_total() -> Money = unit_price * quantity

CustomerContext
  prior_order_count: int (>= 0)       # 0 ⇔ first order
  tier:              Tier?            # present for the X2 member_tier example; None otherwise

Cart
  lines:    List<LineItem>            # may be empty
  customer: CustomerContext
  placed_at: Timestamp               # captured value — the clock is read here, once, not inside evaluate
  of(...) -> Cart                     # validates each line via its own smart ctors
```

**`CartFacts` — the published seam conditions read through** (the OCP seam for X2). Conditions never touch a `Cart` directly (Law of Demeter, §5); they read a small read-model that returns *existing value objects*:

```
CartFacts   (a view over one Cart)
  subtotal()   -> Money              = sum of line_total(), or Money.zero() for an empty cart
  categories() -> Set<Category>      = union of line categories (empty for an empty cart)
  customer()   -> CustomerContext
  placed_at()  -> Timestamp
```

Design rule that makes X2 cheap: **`CartFacts` exposes cart *data* as value objects, not one accessor per condition kind.** A new condition kind reads `customer().tier` or `placed_at().weekday()` from what is already there; it does **not** force a new method on `CartFacts` (that would be the shotgun-surgery / OCP smell). A genuinely new datum (something the cart doesn't yet hold) is the only case that extends the cart, and that is inherent, not accidental.

### 3.3 Conditions — the extensible atom (Strategy)

The **atomic predicate**. This is the X2 extension point. Its result type is what structurally guarantees R3:

```
Assessment  =  Satisfied
            |  Unsatisfied(reason: Reason)      # sum type — Unsatisfied CANNOT be built without a Reason

Condition  (interface)
  evaluate(facts: CartFacts) -> Assessment      # returns Assessment, never a bare bool
  describe() -> str                             # canonical human phrasing of what it requires (for NOT + reasons)
  canonical_key() -> Key                        # (kind_tag, sorted params) — a total order over conditions
```

Because there is **no `false` variant** — only `Unsatisfied(reason)` — a condition *cannot* report non-application without a reason. R3 is enforced by the type, and it is enforced for **every future kind (X2)** because the interface's return type admits nothing else (§4 make illegal states unrepresentable).

Starter kinds (R2), each owning both its predicate *and* its failure phrasing (§5 one owner per rule, §3 failure speaks the consumer's concept):

```
MinSubtotal(threshold: NonNegativeMoney)
  evaluate: facts.subtotal() >= threshold  ? Satisfied
                                           : Unsatisfied(Reason.Leaf("subtotal {subtotal} is below {threshold}"))
  describe: "subtotal ≥ {threshold}"
  canonical_key: ("min_subtotal", threshold.minor_units)

CategoryPresent(category: Category)
  evaluate: category in facts.categories() ? Satisfied
                                           : Unsatisfied(Reason.Leaf("no {category} in cart"))
  describe: "cart contains {category}"
  canonical_key: ("category_present", category.slug)

FirstOrder()
  evaluate: facts.customer().prior_order_count == 0 ? Satisfied
                                                    : Unsatisfied(Reason.Leaf("customer has previous orders"))
  describe: "customer's first order"
  canonical_key: ("first_order",)
```

### 3.4 New condition kinds (X2) are new `Condition` implementers only

Adding a kind touches **no** existing condition, **no** combinator, **no** `CartFacts` method:

```
Weekday(days: Set<DayOfWeek>)
  evaluate: facts.placed_at().weekday() in days ? Satisfied
                                                : Unsatisfied(Reason.Leaf("not eligible on {weekday}"))
MemberTier(min_tier: Tier)
  evaluate: facts.customer().tier >= min_tier ? Satisfied
                                              : Unsatisfied(Reason.Leaf("membership tier too low"))
```

Both read data already on the cart. Both are forced by the interface to return a `Reason` on failure (R3 under X2) and to expose a `canonical_key` (R4 under X2).

### 3.5 Requirement — the combination (Composite, the X1 axis)

X1 ("the three combine") is modeled as a **boolean expression tree**, a first-class sum type — *not* a flat list with special cases:

```
Requirement  =  Atom(condition: Condition)
             |  All(children: List<Requirement>)     # smart ctor rejects empty (§1) — see §6 empty corner
             |  Any(children: List<Requirement>)     # smart ctor rejects empty
             |  Not(child: Requirement)

  evaluate(facts) -> Assessment
  describe() -> str
  canonical_key() -> Key
```

Evaluation is a fold; each node returns an `Assessment`:

```
Atom(c) : c.evaluate(facts)

All(cs) : if every child Satisfied         -> Satisfied
          else                             -> Unsatisfied(Reason.AllOf( sort(unmet child reasons) ))

Any(cs) : if some child Satisfied          -> Satisfied
          else (all failed)                -> Unsatisfied(Reason.AnyOf( sort(all child reasons) ))

Not(r)  : match r.evaluate(facts):
            Unsatisfied(_)                 -> Satisfied
            Satisfied                      -> Unsatisfied(Reason.MustNot( r.describe() ))
```

`Not` is a **real node**, so an exclusion is a first-class effect — not "the absence of an allow" (the §4 concept-fit trap is avoided by construction). The unmet-`Not` reason is built from the child's `describe()` (a satisfied child has no failure reason of its own).

`canonical_key`: `All`/`Any` sort their children's keys; `Not` wraps its child's; `Atom` wraps the condition's. This yields a **total order over any requirement tree**, which is the mechanism for R4 (§3.6).

### 3.6 Reason — the explanation (mirrors the tree, canonicalized → R4)

R3 needs a reason; X1 means that reason must faithfully explain an AND/OR/NOT failure; R4 means it must be independent of the order children were listed in. A flat "first failing condition" string satisfies none of these, so `Reason` is a small structured tree with canonical ordering:

```
Reason  =  Leaf(message: str)             # condition-authored, e.g. "no books in cart"
        |  AllOf(parts: List<Reason>)     # parts are canonically SORTED and de-duplicated
        |  AnyOf(parts: List<Reason>)     # "none of these held: …"
        |  MustNot(requirement_desc: str) # "the cart must not: …"

  render() -> str
```

**Canonicalization = R4 for reasons.** `AllOf`/`AnyOf` store their parts sorted by `canonical_key` and de-duplicated, so `All[A,B]` and `All[B,A]` — and `All[A,A]` — produce the *same* `Reason`, hence the same rendered message. The verdict boolean is already order-independent (AND/OR are commutative/associative); canonical reasons extend that guarantee to the *explanation*.

### 3.7 The code and the verdict

```
Priority   =  int   (higher = preferred)          # a plain comparable scalar; see §7 subtractive note

DiscountCode
  id:          CodeId
  requirement: Requirement                          # the applicability expression (R1, generalized by X1)
  priority:    Priority?                             # optional (X3); None ⇔ unranked
  of(id, requirement, priority?) -> DiscountCode     # requirement already validated (non-empty All/Any)

Verdict  =  Applicable(code_id: CodeId)
         |  NotApplicable(code_id: CodeId, reason: Reason)   # reason is MANDATORY — no silent false (R3)
```

`Verdict` encodes R3 in the type: the only way to say "does not apply" is `NotApplicable`, and it **cannot be constructed without a `Reason`**. There is no boolean anywhere in the output.

Priority lives on the code but is **read by no part of `evaluate`** — it only orders *already-applicable* codes (§3.8). Applicability (a filter) and priority (a ranking) are kept separate concepts with separate operations, so priority is never a score that secretly blocks (the §4 "filter-as-score" trap is avoided).

### 3.8 Selection among several codes (X3)

```
Selection  =  Chosen(code_id: CodeId, verdict: Applicable)
           |  NoneApplicable(reasons: Map<CodeId, Reason>)   # every code's reason — never an empty silence (R3 × X3)
```

## 4. Operations and contracts

### `evaluate(cart: Cart, code: DiscountCode) -> Verdict`  — the single owner of applicability (R1)

- **Precondition:** `cart` and `code` are valid (established by their smart constructors; nothing else to check — no error channel).
- **Body:** `a = code.requirement.evaluate(CartFacts(cart))`; `Satisfied → Applicable(code.id)`; `Unsatisfied(r) → NotApplicable(code.id, r)`.
- **Postcondition:** returns `Applicable(code.id)` **iff** `code.requirement` holds for the cart's facts; otherwise `NotApplicable(code.id, reason)`. Never a bare boolean (R3), never `NotApplicable` without a reason (R3, type-enforced).
- **Purity / determinism:** a pure function of `(cart, code)`. The only clock read is the cart's captured `placed_at` (so a `Weekday` condition is deterministic, not dependent on wall-clock at evaluation).
- **Invariant (R4):** `evaluate(cart, code) == evaluate(cart, code')` whenever `code'` differs from `code` only by reordering children inside any `All`/`Any` node — **both** the `Applicable/NotApplicable` tag **and** the rendered `reason` are identical (verdict by commutativity of AND/OR; reason by canonicalization, §3.6).
- **Single owner (§5):** this is the *only* place applicability is decided; `select_best` composes it and never re-derives it.

### `select_best(cart: Cart, codes: List<DiscountCode>) -> Selection`  (X3)

- Evaluate every code through `evaluate`; partition into applicable / not.
- If none applicable → `NoneApplicable({ code.id: reason for each NotApplicable })`.
- Else → `Chosen` = the applicable code maximizing the **total order** `key(code) = (priority_rank, code.id)`, where `priority_rank = p` for `Some(p)` and `-∞` for `None`; higher priority wins, ties broken by **smallest `code_id`**.
- **Postcondition (determinism, R4-for-selection):** the result is independent of the order `codes` is given in, because the ordering key is total and the tie-break is deterministic.

### Supporting contracts

- `Condition.evaluate`, `Requirement.evaluate` → return an `Assessment`; `Unsatisfied` always carries a `Reason`.
- `describe()` → a *canonical* string (combinators render children sorted by `canonical_key`), so a `Not`-over-a-combo reason is itself order-independent.
- Smart constructors (`NonNegativeMoney.of`, `Quantity.of`, `Category.of`, `All.of`, `Any.of`, `DiscountCode.of`) reject invalid inputs at construction (fail fast, §1), which is why `evaluate` needs no error path.

## 5. Architecture / module skeleton (buildable) and dependency direction

```
money/          Money, NonNegativeMoney, BigInt-backed arithmetic
domain/         Category, Quantity, LineItem, CustomerContext, Cart, Timestamp, DayOfWeek, Tier
facts/          CartFacts  (published read model over Cart)         ── depends on money, domain
conditions/     Condition (iface) + MinSubtotal, CategoryPresent, FirstOrder (+ future kinds)  ── depends on facts, money, domain
reasons/        Reason, Assessment, canonical ordering (Key)         ── depends on nothing domain-heavy
requirements/   Requirement (Atom/All/Any/Not) + evaluate/describe   ── depends on conditions, reasons
codes/          DiscountCode, Priority, CodeId, Verdict, Selection   ── depends on requirements
engine/         evaluate(), select_best()                            ── depends on codes, facts
```

Dependencies point inward toward the more stable/abstract side; no cycles (§6). Conditions depend only on the published `CartFacts` seam, never on `Cart` internals or on each other. Adding a condition kind (X2) adds a file in `conditions/` and nothing else.

## 6. How each rule R × each change-axis X is handled — the input-space table

Required artifact (§1). Columns: **corner (which X × R)** · **concrete extreme value** · **required output** · **the chosen type represents it?**

| corner | concrete extreme value | required output | represented? |
|---|---|---|---|
| **R1 × X1** all/any/not combine | `All[ Atom(cat=electronics), Any[Atom(first_order), Atom(min_subtotal 100)], Not(Atom(cat=gift_card)) ]`; cart: electronics, not-first, subtotal 120, no gift-card | Applicable | **yes** — `Requirement` sum type nests to any depth; fold returns `Satisfied` |
| **R1 × X2** new kind decides applicability | code = `Atom(Weekday{Sat,Sun})`; cart `placed_at` = Saturday | Applicable | **yes** — new `Condition` impl reading `facts.placed_at().weekday()`; no combinator change |
| **R1 × X3** priority irrelevant to a single code | one code, `priority=7`; conditions hold | Applicable (priority ignored) | **yes** — `evaluate` reads only `requirement`; `priority` is a separate field |
| **R2 × X1** starter kinds under any/not | `Any[Atom(min_subtotal 100), Atom(cat=books)]`; subtotal 40 but books present | Applicable | **yes** — `Any` fold: one child `Satisfied` ⇒ `Satisfied` |
| **R2 × X2** a new "starter-like" kind | `Atom(MemberTier(gold))`; `customer.tier = gold` | Applicable | **yes** — new `Condition` reading `facts.customer().tier` |
| **R2 × X3** rank two min_subtotal codes | codes A(min 50, prio 1), B(min 50, prio 5); both apply | `Chosen(B)` | **yes** — `select_best` max by `(priority, code_id)` |
| **R3 × X1** unmet NOT / unmet ANY still gives a reason | `Not(Atom(cat=gift_card))` but gift-card IS in cart | `NotApplicable(reason = MustNot("cart contains gift_card"))` | **yes** — `Reason.MustNot` from child `describe()`; `AnyOf` for an all-failed `Any` |
| **R3 × X2** a new kind cannot return silent false | `Atom(Weekday{Sat,Sun})` on a Tuesday | `NotApplicable(reason = Leaf("not eligible on Tue"))` | **yes** — `Condition.evaluate` return type is `Assessment`; `Unsatisfied` *requires* a `Reason`; no `false` variant exists for any kind |
| **R3 × X3** none of several codes applies | codes A,B,C all fail | `NoneApplicable({A:r_A, B:r_B, C:r_C})` | **yes** — `Selection.NoneApplicable` carries a `Reason` per code; never an empty silence |
| **R4 × X1** order of listed conditions | `All[A,B]` vs `All[B,A]`; `All[A,A]` | identical verdict **and** identical rendered reason | **yes** — verdict by AND/OR commutativity; reason by `canonical_key` sort + de-dup in `AllOf/AnyOf` |
| **R4 × X2** a new kind must stay orderable | mix `Weekday`, `MinSubtotal` in one `All`, listed either way | identical verdict + reason | **yes** — `Condition` interface *requires* `canonical_key()`; new kinds join the total order |
| **R4 × X3** selection order-independence | same applicable set passed in any order; two codes tie on priority | same `Chosen` every time | **yes** — total order `(priority_rank, code_id)`; tie-break = smallest `code_id` |
| edge: boundary **exactly on the edge** | `min_subtotal(50)`, subtotal exactly `$50.00` | Applicable (`>=` is inclusive) | **yes** — `Money >=`; documented inclusive |
| edge: **empty** cart | no lines; `min_subtotal(50)` / `category_present(books)` | `NotApplicable` with each condition's reason | **yes** — `subtotal()=Money.zero()`, `categories()=∅` |
| edge: **one / many** lines & categories | 500 lines across 30 categories | subtotal = exact sum; `category_present` = set membership | **yes** — `subtotal()` sums `BigInt`; `categories()` is a `Set` |
| edge: **zero** threshold | `min_subtotal(0)` | Applicable always (subtotal ≥ 0) | **yes** — `NonNegativeMoney.of(0)` valid; `>=` holds |
| edge: **negative / non-positive** inputs | `min_subtotal(-5)`, `quantity(0)`, `unit_price(-1)` | rejected at construction (never reaches evaluate) | **yes** — `NonNegativeMoney.of` / `Quantity.of` fail fast; the illegal value is unrepresentable downstream |
| edge: **overflow** | 10^9 lines near max unit price | exact subtotal, no wrap | **yes** — `Money` = `BigInt` minor units |
| edge: **absent optional** (priority) | applicable code with `priority = None` vs one with `Some(3)` | the `Some(3)` code wins; two `None` codes tie → smallest `code_id` | **yes** — `priority_rank(None) = -∞`, total order still defined |
| edge: **empty requirement** (`All([])`/`Any([])`) | a builder emits `All([])` | rejected at `Requirement` construction (fail fast) | **yes** — smart ctor forbids empty `All`/`Any`; accidental vacuous-truth / vacuous-false is unrepresentable (a truly unconditional sitewide code is out of scope — it needs no applicability check) |
| edge: **duplicate** conditions | `All[Atom(cat=books), Atom(cat=books)]`, books absent | same verdict; reason shows `books` once | **yes** — `AllOf` de-dups by `canonical_key` |

Every row is representable — no `no`, no blank — so there is no S4 unrepresentable-required-case (§1).

## 7. The mandatory review-and-revise round (`decisions/0011`)

Measured the first-pass design against `arm-table-design-principles.md` with the subtractive and concept-fit passes (`references/review.md`). Findings returned as direction, and how the **final design above** resolves each:

1. **[§1/R4 — S4 correctness] first-pass reason was "the first failing condition."** Order-dependent, so `evaluate(cart, code)` on reordered `All`/`Any` children rendered different reasons — a direct R4 violation, the exact S4-class gap 0011 exists to catch. **Fixed:** `Reason` is a structured tree with **canonical ordering + de-dup** (§3.6); reason is now order-independent, and the R4 invariant covers verdict *and* reason.
2. **[§4/R3 — precondition] first pass had `Condition.evaluate -> bool`.** A future kind (X2) could return `false` with no reason — silent-false through the extension point. **Fixed:** the shared `Assessment = Satisfied | Unsatisfied(Reason)` return type; `Unsatisfied` cannot be built without a `Reason`, so R3 is type-enforced for *every* current and future kind.
3. **[§7/§10 — OCP smell] first pass gave `CartFacts` one accessor per condition kind** (`has_books()`, `is_weekday()`…), making X2 shotgun surgery. **Fixed:** `CartFacts` exposes cart *data as value objects* (`subtotal/categories/customer/placed_at`); a new kind reads existing data with no central edit.
4. **[§4 concept-fit] priority risked being a score that also gates applicability.** **Fixed:** applicability (`evaluate`, a filter) and priority (`select_best`, a ranking) are separate operations; `evaluate` never reads `priority`. `Not` likewise is a real node, not "absence of allow."
5. **[§7 subtractive / YAGNI] first pass carried a `Currency` field + `IncoherentInputError` on mismatch.** No present force — the card is single-currency ($). **Fixed:** removed; `Money` is single-store-currency `BigInt` minor units. Multi-currency is recorded as a *localized* future extension (add `Currency` to `Money` + a boundary check), not built now.
6. **[§1 — S3] empty `All([])`/`Any([])` was silently vacuously-true/false.** **Fixed:** rejected at `Requirement` construction (fail fast); the accidental vacuous corner is unrepresentable.

Residual subtractive check on the *final* design: `Reason`'s tree, `describe()`, and `canonical_key()` each answer to a present force (X1 makes AND/OR/NOT reasons first-class; R4 needs a total order) — a flat string was considered and rejected because it cannot render an unmet `Any`/`Not` order-independently. They stay.

## 8. Acceptance

- **C1** — code `Atom(MinSubtotal($50))`, cart subtotal `$60`: `$60 >= $50` ⇒ `Satisfied` ⇒ **`Applicable(code.id)`**. ✓
- **C2** — code `Atom(CategoryPresent(books))`, cart electronics-only: `books ∉ categories()` ⇒ `Unsatisfied(Reason.Leaf("no books in cart"))` ⇒ **`NotApplicable(code.id, reason="no books in cart")`**. ✓

---

**Buildability:** language/host is a stated technical freedom; module skeleton (§5), concrete type representations (§3), operation contracts (§4), and the full R×X input-space table (§6) are pinned — a Worker could start the first sprint against this. The load-bearing correctness choices are the three that the mandatory revise round hardened: `Assessment`/`Verdict` making silent-false unrepresentable (R3), canonical `Reason` making the explanation order-independent (R4), and the `CartFacts`-as-data seam making new kinds additive (X2).
