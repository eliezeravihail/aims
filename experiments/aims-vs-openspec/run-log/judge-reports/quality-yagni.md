# Code-quality / YAGNI reading — three blind checkout-pricing designs (X, Y, Z)

Disposition: YAGNI / simplicity. Hard on abstraction built for a future nobody asked for, on
mechanisms where a rule would do, and on interfaces with one implementation that pay no rent (§2).
Every load-bearing claim below carries a `file:line` or verbatim excerpt. Length is not a merit;
smallness is not unearned; a removable local blemish does not decide the verdict.

All three solve the same shape well: a pure `price()` function, one rounding site, an explanation the
amounts are read *off of* rather than computed beside, a market that resolves to a tax law + a
catalogue, and a mismatch guard. The differences are in **how much abstraction each pays for the
second-market extension**, which is the axis this disposition cares about.

---

## Design X

### 1. Code smells
- **God object — not present.** The engine's owned-list is long ("Order, arbitration, the floor,
  apportionment, posting steps, market resolution... tax assembly, the boundary guard, rendering",
  X:189) but it is a composition root that is explicitly *forbidden* the domain logic: its "Never
  does" is "Know that PCT, AMT or BOGO exist by name, or figure a tax itself" (X:189). Pricing lives
  in leaves. One coherent reason to change (how the parts interact). Passes §8.
- **Anemic model — not present.** `Ledger.current` is a projection with behaviour (X:632-633); rules
  carry `evaluate` (X:298). Money figures are computed by the type: "`net + tax == payable` is
  arithmetic the type performs rather than an invariant the code maintains" (X:929).
- **Primitive obsession — mild.** Promotion `code: str` (X:295) and market names are raw strings
  re-normalised `strip().upper()` at more than one site (resolver X:541; market X:759). Middle of the
  three; not decisive.
- **Feature envy / shotgun surgery — notably absent.** "Adding a fourth promotion kind is a new rule
  class plus a catalogue schema entry. The engine does not learn about it" (X:105 / Decision 3).

### 2. Interfaces & encapsulation
- **`PromotionRule` Protocol earns its place: three genuinely different implementations** (PCT, AMT,
  BOGO) behind `evaluate(state) -> RuleOutcome` (X:294-310). This is the `Animal.make_sound()` case,
  not `ICat`.
- **Tax has no interface at all — it is flat data behind one function.** `TaxPolicy` is four declared
  axes (`basis`, `level`, `rounding`, `rate`, X:817-827) and `assess` is one function with one branch
  on basis (X:833-842). No protocol, no per-market class. This is the tightest tax calibration of the
  three (see §3).
- Information hiding is strong: `current` is a projection "not a field... a state the type cannot
  hold" (X:637-639); the boundary guard re-derives every relation before returning (X:679); the CLI
  "may not compute, re-round, apportion or sum" (X:606).

### 3. Genericity calibration (§2 floor/ceiling)
- **Best-calibrated tax of the three.** The two markets are modelled as *two rows of data*, not two
  types: "A third country that fits those four is a table entry, not a release of the engine" (X:98).
  X refused to invent a tax interface with one implementation per market — exactly the §2 trap the
  other two flirt with.
- No under-genericity/leak: money crosses as `Decimal`, re-stringified at the JSON seam (Decision 8,
  X:597-600); no vendor/impl type crosses a seam.
- The only forward-looking item — `allocation.apportion` — is **used today** for cart-scoped
  discounts (Decision 2), and X is honest that its per-line-tax use is hypothetical ("that is the only
  future use it has", X:282). Not speculative because it pays rent now.

### 4. Cohesion & coupling (§6)
- Four leaves each own exactly one invariant: "`allocation` owns *the parts sum to the whole*.
  `ledger` owns *the chain links...*. `money` owns *there is exactly one rounding site*. `tax` owns
  *net plus tax is payable*" (X:194-196). Change is localised; tax is assessed after the fold and
  "cannot change what any promotion took" (X:425).

### 5. Naming & reasonable-reader (§11)
- `assess`, `apportion`, `current`, `check-catalogue` all say what they do. Closed `RejectionReason`
  set with a rationale for `SUPERSEDED` carrying the winning code (X:561-564). No surprise.

### 6. Single responsibility & size (§8, §12)
- Each module states its "Owns / Never does" (X table 179-190). The document is long but
  decision-structured; the structure (10 components) is the same order as the others.

**X net:** the leanest extension. Second market = data + one branch; the only interface in the system
has three implementations; nothing is carried for a future that does not pay rent today.

---

## Design Y

### 1. Code smells
- **Union-type accretion (mild god/primitive smell), self-flagged.** `Adjustment` is one type with
  four kinds and kind-specific optional fields — `superseded_by`/`forgone` (NOT_APPLIED only) and
  `tax` (TAX only), policed by a `__post_init__` shape matrix (Y:325-342). Y itself records this as
  "Watched, not yet a problem... If a fifth kind or a third kind-specific field arrives, the honest
  move is to segregate" (Y:1042-1047). Candid, but it is real accretion X and Z both avoided.
- **Anemic — not present** (ledgers own balance + explanation + the mutating op, Y:434-464).
- **Primitive obsession — least of the three:** `PromotionCode`, `Sku`, `MarketId`, `Percent` are all
  wrapped (Y:210-217, 257-259). Arguably the best on §4, though a hard-YAGNI reader notes `MarketId`
  is "validated against nothing at construction" (Y:236) — a normalised-string wrapper.

### 2. Interfaces & encapsulation
- **The decisive over-build: two tax protocols, each with one method and exactly one
  implementation.** `LineTaxRule.assess_line` / `CartTaxRule.assess_cart` (Y:499-509), implemented by
  the single classes `VatIncludedInLine` and `VatAddedToCart` (Y:512-534). Y's own defence is that a
  single interface "would have to be `assess(amount)` plus a flag... and the engine would branch on
  the flag" (Y:551-552) — but that is a false dichotomy: X and Z take the third option (one tax
  component that owns the level branch as *data*), which needs no protocol at all. This is a §2/§3
  red flag under the stated disposition: two interfaces standing in for what is one enum field
  elsewhere.
- **`LinePromotion` — a one-implementation interface Y explicitly labels "unpaid"**: "LinePromotion
  still has one implementation... Carried forward, still unpaid" (Y:1038-1040). By the review's own
  subtractive test this is machinery whose deletion damages no current ownership.
- Encapsulation itself is good: `LineLedger.assess_tax` — "The ledger asks; the rule answers; the
  ledger records — there is no way to assess one amount and record the result against another"
  (Y:439-441).

### 3. Genericity calibration
- **Over-generic on tax.** Y's §15 cut the "TaxScope / treatment flag on one TaxRule" matrix
  (Y:981-984) — but replaced it with *two protocols*, relocating complexity rather than removing it.
  A second implementation is describable (per-line sales tax as a `LineTaxRule`, Y:556-560), which
  keeps `LineTaxRule` from being pure `ICat` — but the **Line-vs-Cart split into two single-impl
  protocols dispatched by type** is still more surface than the two-market requirement forces.

### 4. Cohesion & coupling
- Module map gives each module one "changes when…" sentence (Y:83-94) — good discipline.
- **But the choice to make tax a fourth `AdjustmentKind` couples tax into the explanation's fold and
  forced a correction:** "Stage-2's `deltas_for(scope)`... is not safe now... So the discount folds
  are explicitly `kind == PROMOTION` folds" (Y:373-379). X and Z pay nothing here because they keep
  tax out of the chain entirely.

### 5. Naming & reasonable-reader
- Strong: `VatAddedToCart` / `VatIncludedInLine`, `after_promotions`, `amount_due` all read cleanly.

### 6. Single responsibility & size
- `Adjustment` straining across four kinds is the one SRP wobble (§2 above), acknowledged by Y.
- **Genuine credit:** Y is the most self-critical — an explicit subtractive pass (§15) that cuts a
  `Market` type, a `TaxRate` wrapper, `UnknownMarketError`, per-line `amount_excluding_tax`, a market
  column, effective-dated rates (Y:973-1012). That is real YAGNI discipline visibly applied.

**Y net:** the most "programmed to interfaces" — and under this disposition that counts *against* it,
because two of those interfaces (the tax pair, and `LinePromotion`) carry one implementation and one
of them (`LinePromotion`) is self-declared unpaid. Its self-awareness is a strength; the retained
mechanism is the weakness.

---

## Design Z

### 1. Code smells
- **AdjustmentKind kept minimal — Z resists the accretion Y accepted.** Three members, deliberately:
  "An engineer who needs a tax row has not read §1.2" (Z:388-391); enforced as I16 "AdjustmentKind
  has three members" (Z:556). Cleaner than Y here.
- **Anemic-leaning but deliberate.** Z is a functional core: `model` = frozen data, logic in
  engine/journal/tax/explain. A strict OO reviewer would note Quote/TaxView/Explanation are data with
  computed properties and behaviour in services — but each invariant has "exactly one owner" (Z:537),
  so it is a chosen pure-pipeline shape, not a drifting anemic model. Not weighted heavily under a
  YAGNI (not OO-purist) lens.
- **Primitive obsession — most raw strings:** `CartLine.sku: str`, `Cart.market: str`, `codes:
  tuple[str, ...]` (Z:249-259), normalised on lookup. Mild.
- No god object; if anything the finest-grained decomposition (journal / tax / explain separated).

### 2. Interfaces & encapsulation
- **`Rule` Protocol: three real implementations** (PCT/AMT/BOGO, Z:742-756). Genuine.
- **Tax has no interface — two pure functions `tax_for` / `cart_tax`** (Z:868-878), a data-driven
  model identical in spirit to X. **No single-implementation tax interface anywhere.** This is the
  key contrast with Y and the shared virtue with X.
- Best-stated encapsulation boundary: "`explain` is the only constructor of `Quote`; `tax` the only
  constructor of `TaxView`" — checkable by reading imports (Z:933-935, I26 Z:566).

### 3. Genericity calibration
- Tax mechanism itself: tight and data-driven (peer of X).
- **The YAGNI marks are two speculative *fields*, not interfaces.** `MarketProfile` carries
  `currency` and `minor_units` (Z:205-208) that Z admits are not forced: currency "is **not forced**
  by the requirement" (Z:1491-1494) and `minor_units` "is not a claim that a 0- or 3-decimal market
  is free" (Z:1174). Carrying `minor_units` on the profile rather than as a module constant "so that
  the invariants can be *stated* against the market" (Z:1170-1173) is precisely a mechanism where a
  constant would do today — a future-currency justification for present structure.
- **The 32-invariant list (I1–I32) and the ~20-row extension catalogue (§9) are prose/planning, not
  built abstractions** — "Nothing is built, stubbed or hooked for any of them" (Z:1626). So not a
  structural over-build, but exactly the "elaborate invariant list" and volume the disposition says
  not to be impressed by. It does not create machinery; it does spend length on futures.

### 4. Cohesion & coupling
- **The strongest single earned abstraction of the three: the journal-as-matrix.** "I13 is why I3 and
  I7 come free... Given I13, I3 is a theorem" (Z:574-577). Multiple invariants fall out of one
  property. tax is import-isolated (I26). This is genuine earned-abstraction elegance and Z's best
  claim.

### 5. Naming & reasonable-reader
- Best-in-class: a mechanically-checkable lexical sign rule ("Anything named `delta` is a signed
  movement... `amount`/`discount`/`tax` is a non-negative magnitude", Z:1086-1089); a five-word money
  vocabulary fixed once (§2.1). `MarketMismatchError` gets its own failure category "because neither
  input is wrong; the *pairing* is" (Z:1550-1554). No surprise.

### 6. Single responsibility & size
- Each component one responsibility, each invariant one owner (Z:537). The document is 2010 lines —
  but it is *exhaustively decided* ("Nothing is open", §13.5), so the "longer = less decided" warning
  does not cleanly bite; the length is future-cataloguing and test-obligation prose, not indecision.

**Z net:** structurally a peer of X on the load-bearing axes (data-driven tax, one genuine Protocol,
tax kept out of the chain, minimal enum), with a stronger central abstraction (journal matrix) but a
larger speculative surface — two admitted future-facing profile fields and a heavy catalogue of
unbuilt futures.

---

## Verdict

**X.**

Deciding property — **earned-abstraction minimalism on the second-market extension: X introduces no
interface with fewer implementations than justify it, and no field or mechanism carried for a future
that pays no present rent.** All three keep tax out of the explanation and read amounts off a fold;
that is common ground. They separate on what the second market *costs*:

- **Y** pays for it with two tax protocols that have one implementation each
  (`LineTaxRule`/`CartTaxRule`, Y:499-534) plus a tax-as-`AdjustmentKind` union that forced a fold
  correction (Y:373-379), and it still carries a self-declared "unpaid" one-implementation interface
  (`LinePromotion`, Y:1038-1040). Under a disposition that hunts one-implementation interfaces, Y is
  third despite having the most explicit subtractive discipline.
- **Z** matches X's data-driven tax and beats it on one abstraction (the journal matrix, Z:574-577),
  but carries two profile fields it admits are not forced (`currency`, `minor_units`, Z:1174/1491-1494)
  — a mechanism where a constant would do — and spends its length cataloguing unbuilt futures and a
  32-item invariant list, the volume the disposition explicitly declines to credit.
- **X** models the two markets as four fields of data behind a single one-branch function
  (`TaxPolicy` + `assess`, X:817-842; "a table entry, not a release of the engine", X:98), its one
  Protocol has three real implementations (X:294-310), and its only forward-looking helper
  (`allocation`) is used today (X:282). Nothing it introduces fails the subtractive pass.

This is not a length verdict: X is not favoured for being shorter, nor Z punished for being longer.
It is that, reading strictly for the over-generic and the speculative, **X is the only one of the
three with neither a one-implementation interface nor an admitted future-facing field** — the cleanest
"pays rent on everything it introduces" of the set. The margin over Z is real but narrow (Z's marks
are small and self-admitted); the margin over Y is clear.
