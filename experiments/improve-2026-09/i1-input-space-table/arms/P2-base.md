# Design — Discount-Code Applicability Engine (design only)

Produced by a single aims planning pass, then the one mandatory review-and-revise round (decisions/0011). Graded against `skills/aims-guide/references/design-principles.md`. The body below is the **final, post-revision** design; the review round and what it changed are recorded at the end.

Kind: `design`. Deliverable is a buildable architecture (concrete types, operations + contracts, full R×X input-space handling) — no implementation code.

---

## 0. Substrate note and one modeling finding

- **Substrate.** aims requires the foundational substrate (language/framework) to be *asked* of the user, not guessed. For this design-only pass I pin an illustrative typed substrate — **Python 3.12**, frozen dataclasses for value objects, sealed sums expressed as a closed class family consumed with `match`, `abc.ABC` for the one open extension interface — because the design must be concrete enough to type against. The algebra is language-agnostic (any language with sum types + one interface realizes it identically); a real run would confirm the substrate first.
- **Finding surfaced during planning (stated, not silently decided).** The card says "given a shopping cart and a discount code," but R2's own starter kind `first_order` is a *customer* fact, not a cart fact, and X2's named example `weekday` is a *time* fact. A bare `Cart` cannot answer the starter conditions. The honest input is therefore the **evaluation situation** — the cart, the customer it is for, and the moment it is evaluated at — bundled as `EvaluationContext`. This changes no observable product behavior; it is the minimal faithful input, and it is the stable seam that makes X2 localizable (below).

---

## 1. Domain types — the concrete representation

### 1.1 Foundational value objects (§0 inside-module currency, §4 value objects over primitives)

```python
@dataclass(frozen=True, order=True)
class Money:                       # a monetary amount in one implicit currency
    minor_units: int               # e.g. cents; >= 0 for prices, validated at construction
    # ops: __ge__ (total order), times(n: Quantity)->Money, plus(Money)->Money, classmethod zero()->Money
    # Invariant: the engine operates in a single configured currency (see review round, finding 1).

@dataclass(frozen=True)
class Quantity:
    count: int                     # >= 1; construction rejects 0/negative (fail fast, §1)

@dataclass(frozen=True)
class Category:
    code: str                      # normalized (trimmed, lower-cased) at construction; non-empty

@dataclass(frozen=True)
class CodeId:
    value: str                     # e.g. "SAVE50"; non-empty, normalized; identity of a code

@dataclass(frozen=True, order=True)
class Priority:
    rank: int = 0                  # higher = preferred; default 0 (X3 "may carry a priority")
```

`Money` is a real value object (not a bare int) so `MinSubtotal(threshold: Money)` reads as money and money arithmetic has one home (DRY §7). It carries **no currency field** — see review finding 1.

### 1.2 The cart side (§4 rich domain model; §11 immutable)

```python
@dataclass(frozen=True)
class LineItem:
    category: Category
    unit_price: Money
    quantity: Quantity
    def line_total(self) -> Money:            # unit_price.times(quantity)

@dataclass(frozen=True)
class Cart:
    lines: tuple[LineItem, ...]               # empty tuple is a valid (empty) cart
    def subtotal(self) -> Money:              # sum of line_totals; empty -> Money.zero()  (derived, one source of truth)
    def categories_present(self) -> frozenset[Category]   # union of line categories (derived)

@dataclass(frozen=True)
class Customer:
    prior_order_count: int                    # >= 0 ; == 0 means the customer's first order
    # deliberately minimal: a genuinely new fact a future kind needs (e.g. member tier)
    # is added to the entity it belongs on — the one localized touch X2 costs.

@dataclass(frozen=True)
class EvaluationContext:                      # the situation a code is judged in — the seam conditions read
    cart: Cart
    customer: Customer
    evaluated_at: datetime                    # the moment of evaluation (a real fact of the situation, not a guard)
```

Facts are **derived, not stored** (`subtotal`, `categories_present`) → one source of truth. `EvaluationContext` is the published seam type every condition depends on (§0 speak published types across seams; §5 program to an interface).

### 1.3 The two-layer condition model — the heart

The design splits the two change-axes (X1, X2) into two independently-varying layers (§7 localize change axes; §5 one owner per rule), because the boolean connectives and the atomic predicates change for different reasons at different rates.

**Layer A — the open, extensible predicate set (owns X2).** A leaf check is a strategy that judges itself against the context and returns an outcome that *cannot* be a reasonless false:

```python
class CheckOutcome:                # sealed sum — a reason is structurally mandatory
    ...
@dataclass(frozen=True)
class Met(CheckOutcome): pass
@dataclass(frozen=True)
class Unmet(CheckOutcome):
    detail: str                    # consumer-facing "what the cart had", e.g. "no books in cart"

class LeafCheck(ABC):              # THE extension point for X2 — the only place new kinds touch
    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> CheckOutcome: ...
    @abstractmethod
    def descriptor(self) -> "ConditionDescriptor": ...   # static "what I require", cart-independent

# The three starter kinds (R2), each self-evaluating (§4 Tell-Don't-Ask, §8 no type-code switch):
@dataclass(frozen=True)
class MinSubtotal(LeafCheck):
    threshold: Money
    # Met iff ctx.cart.subtotal() >= threshold  (>=, inclusive boundary)
@dataclass(frozen=True)
class CategoryPresent(LeafCheck):
    category: Category
    # Met iff category in ctx.cart.categories_present(); else Unmet(detail=f"no {category.code} in cart")
@dataclass(frozen=True)
class FirstOrder(LeafCheck):
    # Met iff ctx.customer.prior_order_count == 0; else Unmet(detail="customer has previous orders")
```

Because `CheckOutcome`'s only non-`Met` inhabitant is `Unmet(detail)`, **it is impossible to author a leaf that reports non-application without a reason** — this is how R3 survives X2 *structurally* rather than by convention.

**Layer B — the closed boolean structure (owns X1).** A `Condition` is a sealed sum: the atoms wrap any `LeafCheck`, and the connectives are the fixed algebra AND/OR/NOT. Well-formed by construction (§4 make illegal states unrepresentable — you cannot build an `All` with a non-`Condition` child):

```python
class Condition: ...                          # sealed sum
@dataclass(frozen=True)
class Atom(Condition):
    check: LeafCheck                           # the seam between closed connectives (B) and open predicates (A)
@dataclass(frozen=True)
class All(Condition):
    members: tuple[Condition, ...]             # n-ary AND
@dataclass(frozen=True)
class Any(Condition):
    members: tuple[Condition, ...]             # n-ary OR
@dataclass(frozen=True)
class Not(Condition):
    member: Condition                          # unary NOT — a first-class connective, NOT "absence of an allow"
```

The `Atom` wrapper is the seam that lets X1 (connectives) and X2 (predicates) vary without touching each other: adding a connective never touches leaves; adding a leaf never touches the connective recursion. (Concept-fit: `Not` is an explicit node, not a missing condition — deliberately avoiding the "deny modeled as a missing allow" trap in §4.)

### 1.4 The diagnostic reason — structured "why not" (R3 under X1)

A failing boolean tree needs a reason that respects the boolean structure (a flat set of failed leaves is *wrong* under OR, which fails only when all branches fail). So the reason mirrors the failing structure:

```python
@dataclass(frozen=True)
class ConditionDescriptor:                     # renderable, cart-independent "what a condition requires"
    text: str                                  # e.g. "requires a books item"
    sort_key: str                              # canonical key for order-independent reasons (R4)

class UnmetReason: ...                          # sealed sum
@dataclass(frozen=True)
class LeafUnmet(UnmetReason):
    descriptor: ConditionDescriptor
    detail: str                                # from the leaf's Unmet(detail), e.g. "no books in cart"
@dataclass(frozen=True)
class AllUnmet(UnmetReason):
    unmet: tuple[UnmetReason, ...]             # the conjuncts that FAILED (AND fails if >=1 fails); non-empty
@dataclass(frozen=True)
class AnyUnmet(UnmetReason):
    failures: tuple[UnmetReason, ...]          # EVERY disjunct's failure (OR fails only if ALL fail); non-empty
@dataclass(frozen=True)
class ExclusionUnmet(UnmetReason):
    excluded: ConditionDescriptor              # NOT failed: the excluded thing was present
    detail: str                                # e.g. "a gift_card item is in the cart, which the code excludes"
```

The `AllUnmet`/`AnyUnmet` asymmetry is exact concept-fit: AND reports *which* members failed; OR reports *all*, because all had to fail. NOT's positive side uses the child's static `descriptor()` (no symmetric positive-reason tree is built — see review, subtractive pass). Both member tuples are stored **sorted by `sort_key`**, making the reason permutation-invariant (R4 extends to the diagnostic, not just the boolean).

### 1.5 Code, verdict, selection — the public boundary types

```python
@dataclass(frozen=True)
class DiscountCode:
    id: CodeId
    condition: Condition                       # exactly one root condition (typically All([...]))
    priority: Priority = Priority()            # X3, optional with a default

class Verdict: ...                              # sealed sum — the PUBLIC product-language result
@dataclass(frozen=True)
class Applicable(Verdict):
    code_id: CodeId
@dataclass(frozen=True)
class NotApplicable(Verdict):
    code_id: CodeId
    reason: UnmetReason                         # ALWAYS present — no bare-false inhabitant exists (R3)

class Selection: ...                            # result of choosing among many codes (X3)
@dataclass(frozen=True)
class Chosen(Selection):
    code: DiscountCode
    verdict: Applicable
@dataclass(frozen=True)
class NoneApplicable(Selection):
    reasons: tuple[tuple[CodeId, UnmetReason], ...]   # why nothing applied (R3 at the selection boundary)
```

`Verdict` is the boundary vocabulary (§5 errors/results speak the consumer's concept): "Applicable"/"NotApplicable" in the product's language, carrying the code identity. **There is no boolean-returning public path** — non-application is representable *only* as `NotApplicable(code_id, reason)`. That is the strongest possible guarantee of R3's "never a silent false": reasonless non-application is unrepresentable.

---

## 2. Operations and contracts

Everything is pure and immutable (§2 CQS — all queries, no mutation; §11 functional core, no globals, no clock read inside — time enters only as `ctx.evaluated_at`).

### `evaluate_condition(cond: Condition, ctx) -> Outcome`  *(internal fold; owner of R1 + R4)*
`Outcome = Holds | Fails(UnmetReason)`. Total structural recursion over the closed sum:
- `Atom(check)` → lift `check.evaluate(ctx)`: `Met`→`Holds`, `Unmet(d)`→`Fails(LeafUnmet(check.descriptor(), d))`.
- `All(members)` → `Holds` iff every member Holds; else `Fails(AllUnmet(sorted failed members))`. **Empty identity: `All(())` → Holds** (vacuous truth).
- `Any(members)` → `Holds` iff some member Holds; else `Fails(AnyUnmet(sorted all members))`. **Empty identity: `Any(())` → Fails(AnyUnmet(()))** rendered "no applicable alternatives".
- `Not(member)` → if member Holds → `Fails(ExclusionUnmet(descriptor(member), detail))`; if member Fails → `Holds`.
- **Contract:** total (defined for every context and well-formed condition); pure/deterministic; terminates (finite tree). **R4 invariant:** `evaluate_condition` output — both the `Holds/Fails` and the reason — is invariant under any permutation of `All`/`Any` members at any depth (boolean by commutativity/associativity; reason by `sort_key` canonicalization).

### `decide(ctx: EvaluationContext, code: DiscountCode) -> Verdict`  *(public seam)*
- **Precondition:** `ctx` well-formed (validated at construction of its parts); `code` well-formed.
- **Postcondition:** `Applicable(code.id)` iff `evaluate_condition(code.condition, ctx)` Holds; otherwise `NotApplicable(code.id, reason)` with the structured reason. Priority is **not** read here (single-code applicability is priority-independent — SRP §6).
- **Invariants:** R1 (applies iff the root condition holds); R3 (the only non-applicable result carries a reason); R4 (permutation-invariant); determinism (same inputs → same output).

### `select(ctx: EvaluationContext, codes: frozenset[DiscountCode]) -> Selection`  *(public seam, owns X3)*
- **Precondition:** code ids are **distinct** (duplicate id → boundary error, fail fast §1).
- **Behavior:** compute `decide(ctx, c)` for each; among those `Applicable`, choose the maximum under the total order `CodePreference` = **(priority.rank descending, then code.id.value ascending)**. Distinct ids ⇒ the order is total ⇒ a unique winner. Return `Chosen(winner, its Applicable)`; if none applies, `NoneApplicable((id, reason) for each code)`.
- **Invariants:** deterministic and **independent of the input order** of `codes` (X3 "chosen deterministically" — the winner is the max of a total order, not a function of iteration order); if ≥1 applies exactly one is chosen; if exactly one applies it is chosen; empty `codes` → `NoneApplicable(())`.
- `CodePreference` is a single named owner of the tie-break rule (§5 one owner per rule) — not inlined in `select`.

### `render(reason: UnmetReason) -> str`  *(presentation layer, domain-independent §10)*
Folds a reason tree into a consumer string (`LeafUnmet`→its `detail`; `AllUnmet`→joins failed parts; `AnyUnmet`→"none of: …"; `ExclusionUnmet`→its `detail`). Domain never depends on this; this depends inward on the reason types only.

---

## 3. Architecture — modules, seams, dependency direction

```
domain/      money.py (Money,Quantity)  catalog.py (Category,LineItem,Cart)
             customer.py (Customer)      context.py (EvaluationContext)     ← most stable
conditions/  checks.py  (LeafCheck + MinSubtotal/CategoryPresent/FirstOrder, CheckOutcome)   ← owns X2 (open)
             condition.py (Atom/All/Any/Not sealed sum, ConditionDescriptor)                 ← owns X1 (closed)
             reason.py  (UnmetReason sum + canonicalization)
             evaluate.py (evaluate_condition, Outcome)                                        ← owns R1, R4
engine/      code.py    (DiscountCode, CodeId, Priority, CodePreference)                      ← owns X3 order
             decide.py  (decide, Verdict)                                                     ← public seam
             select.py  (select, Selection)                                                   ← public seam
presentation/render.py  (render)                                                              ← depends inward only
```

- **Published seam types** (the only things crossing module boundaries, §0/§5): `Money`, `Category`, `Cart`, `EvaluationContext`, `LeafCheck`, `Condition`, `UnmetReason`, `Verdict`, `Selection`, `DiscountCode`. No module references another's internal implementation class; `select` depends on `decide`'s `Verdict` and `code`'s `CodePreference`, never on `evaluate`'s internals.
- **Dependency direction** (§6 acyclic, toward the more stable/abstract): domain ← conditions ← engine ← presentation. Domain never depends on presentation (§10 UI/domain separation). No cycles.
- **Change-axis ownership** (§7 localize change axes; each axis one home): X1 → `condition.py` (closed sum) + the fold; X2 → `checks.py` (open `LeafCheck` interface); X3 → `code.py`/`select.py`.

---

## 4. R × X — full input-space handling

Cells state how each rule is upheld and how it survives each axis. `∅` = base (no axis).

| | ∅ (single condition, single code) | X1 (AND / OR / NOT combination) | X2 (new condition kinds) | X3 (priority selection) |
|---|---|---|---|---|
| **R1** *applies iff conditions hold* | `decide` returns `Applicable` iff the root `Condition` Holds under the fold. | "Hold" is defined by the closed fold over `All/Any/Not`; R1 is unchanged — applies iff the *root* (now a tree) holds. | New kinds plug into the same `LeafCheck.evaluate`→`Atom`→fold path; "applies iff root holds" is unchanged. | R1 is per-code; `select` layers *choice* on top and never alters any single code's applies-iff semantics. |
| **R2** *starter kinds* | `MinSubtotal`, `CategoryPresent`, `FirstOrder` are three `LeafCheck`s. | Starter kinds are leaves; connectives wrap them without changing them. | Starter kinds are **untouched** when a kind is added (open/closed §7): a new kind is a new `LeafCheck` subtype; existing ones don't change. | Orthogonal — priority lives on the code, not the kinds. |
| **R3** *not-applicable carries a reason; never silent false* | `Unmet` requires `detail`; `NotApplicable` requires `reason`; there is **no** bare-`false` inhabitant. | A failed tree yields `AllUnmet`/`AnyUnmet`/`ExclusionUnmet` — structured, never bare false; OR reports *all* branches (correct), NOT reports what was present. | **Structural guarantee:** the extension point's return type `CheckOutcome = Met \| Unmet(detail)` makes a reasonless leaf *unrepresentable*, so every future kind satisfies R3 by construction. | `select` returns `NoneApplicable(reasons)` when nothing applies — R3 upheld one level up (a reasonless "nothing" would be the very silent-false R3 forbids). |
| **R4** *order-independent verdict* | Single condition — trivially order-free. | `All`/`Any` folds are commutative/associative → boolean is permutation-invariant; reasons are canonicalized by `sort_key` → the **diagnostic** is permutation-invariant too; `Not` is unary. | A new kind is a self-contained pure predicate; it introduces no ordering dependence. | `select`'s winner is the max of a **total** order (priority desc, id asc), so it is independent of the order `codes` are supplied; distinct ids guarantee no tie. |

### Full input-space enumeration (§1 trace the procedure, not just the listed cases)
Edge/boundary cases each have a defined result:
- **Empty cart** → `subtotal()=zero`, `categories_present()=∅`: `MinSubtotal` unmet unless threshold is zero; `CategoryPresent` unmet with detail; `FirstOrder` still evaluable (customer fact). Defined.
- **Exact threshold** → `MinSubtotal` uses `>=` (inclusive): subtotal == threshold ⇒ Met. (C1's $60≥$50, and the boundary $50, both apply.)
- **Empty `All(())`** → Holds (vacuous truth); **empty `Any(())`** → Fails with "no applicable alternatives". Defined identities, tested.
- **All-fail OR** → `AnyUnmet(all branch reasons)` — every alternative reported (not one). 
- **NOT of a present exclusion** → `ExclusionUnmet` naming what was present ("a gift_card item is in the cart"). 
- **Empty `codes` set** → `NoneApplicable(())`. **Duplicate code id** → boundary error (fail fast). **Priority tie** → broken by ascending id → unique winner.
- **Deep nesting** (e.g. `All[electronics, Any[first_order, MinSubtotal(100)], Not[gift_card]]`) → the fold is total and recursive; the reason mirrors exactly the failing sub-tree; permutation of any node's members changes neither verdict nor reason.

### Acceptance criteria
- **C1** `MinSubtotal(Money(5000))`, cart subtotal `Money(6000)`: `6000 >= 5000` ⇒ `Met` ⇒ `evaluate` Holds ⇒ `decide` → **`Applicable`**. ✓
- **C2** `CategoryPresent(Category("books"))`, cart categories `{electronics}`: `books ∉ {electronics}` ⇒ `Unmet(detail="no books in cart")` ⇒ `Fails(LeafUnmet(desc "requires a books item", "no books in cart"))` ⇒ `decide` → **`NotApplicable(reason)`**, `render(reason)="no books in cart"`. ✓

### Worked X2 extension (localization proof, no code shipped for it)
Adding `Weekday(day)`: implement one `LeafCheck` reading `ctx.evaluated_at`; wrap in `Atom`. **Untouched:** the connective sum, the fold, `decide`, `select`, `Verdict`, every existing kind, and R3 (its `Unmet(detail)` is forced by the return type). Adding `MemberTier(tier)`: same, plus one new field on `Customer` (the single localized touch a genuinely new *data source* costs — irreducible, and it lands on the entity the fact belongs to). This is the X2 axis discharged: extension is one new subtype at one seam.

---

## 5. The mandatory review-and-revise round (decisions/0011)

A `design` objective is never read as met on its first pass. I measured the first-pass design against `design-principles.md`, ran the **subtractive** and **concept-fit** passes, and revised. Findings and the revisions folded into the final design above:

1. **§7 subtractive / tie-break (S1) — dropped `Currency` from `Money`.** First pass modeled `Money{minor_units, currency}` with cross-currency fail-fast. Falsifier: name the X-item multi-currency serves — none of X1/X2/X3 is multi-currency; the currency field guarded a caller the stated product doesn't have. Revised to a single-currency invariant on `Money` (kept the value object to avoid primitive obsession §4; cut the unpaid field). Noted: add `Currency` if multi-currency becomes a real force.
2. **§7 subtractive (S1) — trimmed `Selection`.** First pass carried `also_applicable` and per-rejected reasons on the winning branch. No stated force needs the losers' ids/reasons on a successful selection (a caller wanting a specific code's reason calls `decide`). Revised to `Chosen(code, verdict)` and `NoneApplicable(reasons)` — the latter kept because a reasonless "nothing applied" would violate R3 at the selection boundary.
3. **§7 subtractive — dropped `Sku` from `LineItem`.** No rule needs line identity; only category/price/quantity are read. Cut.
4. **§1 contracts — made the empty-fold identities and the inclusive boundary explicit.** `All(())`=Holds, `Any(())`=Fails, and `MinSubtotal` uses `>=` are now stated contracts with tests, not implied.
5. **§4 concept-fit — confirmed and kept two decisions.** (a) `Not` is a first-class connective node, not "a missing allow" (avoids the §4 deny-as-absence trap). (b) NOT's positive side uses the child's static `descriptor()` rather than a symmetric `MetReason` tree — the symmetric tree was unpaid machinery (no force needs rich positive explanation of a satisfied sub-tree); `descriptor()` gives a correct exclusion reason at a fraction of the surface.

Re-measured after revision: the leaner Money, leaner Selection, explicit identities, and confirmed concept-fit hold; no substantial finding remains. The two-layer condition model (closed X1 connectives vs open X2 predicates joined at the `Atom` seam) is the load-bearing decision and survived both passes — its `Atom` seam is justified by the named X1×X2 independence (falsifier: both axes are named product change-axes), so it is under-provision to omit, not over-build to keep.

---

## 6. Where this would be filed (aims records, for a real run)
- `goals.md` — product intent (decide applicability; select among codes) and non-goals (no pricing/discount-amount math, single currency).
- `architecture.md` — the two-layer condition model, the `EvaluationContext` seam, the module/dependency map, and the X1/X2/X3 ownership table.
- `decisions/` ADRs — (a) two layers: closed connective sum vs open leaf interface; (b) reasonless-false made unrepresentable via the outcome/verdict sums (R3 by construction); (c) `select` determinism via a total `CodePreference` order.
- Companions on `checks.py` (X2 extension recipe), `evaluate.py` (R4 canonicalization + empty-fold identities), `select.py` (total-order determinism), anchored on filing with `python3 knowledge/anchor.py <companion>`.

**Buildability check (design-objective bar):** substrate pinned, module skeleton and every public signature given, seam types named, all edge/boundary results defined, R×X fully traced, acceptance C1/C2 shown falling out — a Worker could start the first sprint against this without inventing the ground it stands on.