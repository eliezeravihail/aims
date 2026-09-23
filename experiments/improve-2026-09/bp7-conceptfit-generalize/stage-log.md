# BP7 stage-by-stage log (concept-fit axis)

## Stage 1 — three rule kinds + engine (the concept-fit choice)
- **Correctness gate:** plain **12/12**, lite **12/12**, aims **12/12** — all CLEAR.
- **The structural choice to watch (concept-fit):** does the engine dispatch **polymorphically** (each rule
  owns its `discount(cart)`) or via a **type-branch** (`isinstance`/type-tag chain inside `Engine.total`)?
  - **plain (no hint):** POLYMORPHIC — three rule classes each expose `discount(cart)`; `Engine.total` sums
    `rule.discount(cart)` with no isinstance/type-tag branch.
  - **lite (principle block):** POLYMORPHIC — same shape; a namedtuple line, one-owner `Cart.subtotal`.
  - **aims (full method):** POLYMORPHIC — a `Rule` abstraction with one `discount` method; its review
    **explicitly rejected** the isinstance/type-code switch as a type-code smell that would force reopening
    the engine per new rule kind (ADR 0001).
  - **grep across all three arms:** no `isinstance` / `__class__` / `type(` / type-tag in any `total()`.
- **Reading:** unlike derive-don't-store (BP6: ~1/6 plain builds took the stored-counter shortcut), the
  concept-fit good design was the pull for **all three** opus arms, including the un-prompted plain arm. The
  shortcut (branch-on-tag) was not taken by anyone, so there is nothing at stage 2 to reopen.

## Stage 2 — stacking policy (priority + exclusivity); the break
- **Correctness gate:** plain **19/19**, lite **19/19**, aims **19/19** — all CLEAR (stage-1 + stage-2).
- **Trajectory measure (reopen vs extend):**
  - **plain: EXTENDED, 0 reopens.** Added a small `Rule` base holding `priority`/`exclusive`; each kind
    subclasses it; every `discount()` body untouched. `Engine.total` grew from `sum(...)` to a
    `sorted(...)`-walk + accumulate + break. (diff ~43 lines, mostly the new base class + `super().__init__`.)
  - **lite: EXTENDED, 0 reopens.** Kwargs added inline on the three constructors; `discount()` untouched;
    `total()` `sum` → sorted walk + break. Leanest change (diff ~19 lines).
  - **aims: EXTENDED, 0 reopens.** Added `priority`/`exclusive` **once** on the `Rule` base as keyword-only
    dataclass fields (DRY — 0 lines changed in the three concrete constructors); `total()` `sum` → sorted
    walk + break; per-rule math byte-for-byte unchanged (diff ~48 lines incl. records). **The co-located
    record named the seam**: ADR 0001 / companion stated the engine owns "only the summation and the floor,"
    so stacking was recognized as an evolution of exactly that combination step, and a new ADR 0002 was
    appended (orthogonal to 0001, not superseding). **Q2 continuity signal, n=1.**
- **Reading:** **reopened-owner count is 0 for all three arms.** Because every arm modeled rules as
  first-class objects at stage 1, the stacking change was a pure seam extension for everyone — the engine's
  combination step is the one owner, and it was extended in place. No arm paid a reopen because no arm took
  the shortcut. The trajectory edge **did not appear on this axis** — not because aims failed, but because the
  concept-fit good design is the obvious pull for a capable model here (the shortcut base rate is ~0; the
  `baserate/` probe quantifies it).

## Totals (outcome-first)
| arm | correctness (both stages) | reopened-owner events | stage1→2 diff | records |
|---|---|---|---|---|
| **plain** | 19/19 ✓ | **0** | ~43 lines | none |
| **lite**  | 19/19 ✓ | **0** | ~19 lines | none |
| **aims**  | 19/19 ✓ | **0** | ~48 lines | companion + goals + arch + 2 ADRs |

- **Correctness: a three-way tie** — no arm shipped a wrong number at either stage.
- **Trajectory: no divergence** — 0 reopens for all three; the aims records added a continuity signal and a
  marginally cleaner kwarg placement (DRY base field vs per-constructor), but bought no avoided reopen because
  none was on offer.
