# Divergence map — where the three designs split, and why the chosen option wins

Three MVP designs written under three biases: **minimal-structure** (M), **extensibility-first**
(E), **verifiability-first** (V). This maps the axes where they genuinely pull apart and names the
winning choice folded into `final.md`.

## Where all three AGREE (robust — kept without debate)

- **One sealed egress.** A single `CitationGateway` is the only place a `Citation` is constructed,
  with a private constructor and no free-text advice field. (All three.)
- **`Citation = Source × ReportedState` with references, not copied prose.** (All three.)
- **Confidence tier lives on `Source`, never on the engine/ledger; copied, never recomputed.** (All three.)
- **`Grant`/`Membership` single edge is the whole account model; multi-subject = cardinality.** (All three.)
- **Expected = declarative rails (data); reported = subject state; gaps = the join's output, not enumerated.** (All three.)
- **The nudge is a citation of (rail expecting a plan) × (reported no-plan), not advice.** (All three.)
- **Out of MVP:** Pillar 2 overview, inference/suspicion engine, extra sources, notifications. (All three.)

These are the spine of `final.md` and were never in contention.

## Where they DIVERGE (real decision points)

### Axis 1 — How rendered text stays non-advice
- **M:** a "rendered surface derived only from source + fact" — under-specified; the surface is where advice could leak.
- **E / V:** a **closed template catalog**; slots fillable only by verbatim source text and codes/values from referenced records; "ask your doctor" is a constant string.
- **Winner: E/V's closed catalog.** M's vaguer "surface" is the one place an originated sentence could slip in. A fixed projection-only catalog makes non-advice a property you can test ("delete every non-projection template and the system still runs"). *Chosen.*

### Axis 2 — How "never infers state" is enforced
- **M / E:** *no module writes a `ReportedItem`*; state arrives only via ingestion adapters (a boundary rule).
- **V:** the `Origin` enum has **no `SYSTEM` member** — the store rejects any fact whose author can't be named; inference is *unrepresentable*, not just un-coded.
- **Winner: V's `Origin`-without-`SYSTEM`.** M/E rely on "no module happens to do it," which a future module could violate. V pushes the guarantee into an enum the type system enforces everywhere at once. *Chosen — the single strongest move in the model.*

### Axis 3 — Source/reported payload shape
- **M:** `item_code` + `value` (controlled code, measured datum).
- **E:** `type` (closed) + open `subtype` + `payload`.
- **V:** typed `SourceClaim` / `ObservedFact` **variants** — closed structured vocabulary, no prose.
- **Winner: V's typed variants + E's open code namespace.** V's structure guarantees no prose channel exists; E's namespaced-string `code`/`subtype` is the right growth seam. `final.md` marries them: **closed typed claim/fact shapes over an open namespaced code vocabulary** — no prose hole, no migration to add a concept.

### Axis 4 — The extensibility seam (the E-vs-M crux)
- **M:** adapters "assumed to exist, internals out of scope" — under-delivers the seam exit 5 wants to be legible.
- **E:** self-registering `SourceAdapter` + **hot-registerable** `PathwayPack` plugin framework — a runtime the MVP doesn't need (brief §6 penalizes speculation).
- **V:** `Ingestors` + `PathwayLibrary` + a per-owner change table — a contract, not a runtime.
- **Winner: the seam as a contract (V), with M's restraint on the runtime.** Exit 5 requires "adding a pathway/source is *one owner's change*" — that needs a registry **interface**, not a hot-plugin engine. `final.md` defines `Ingestor.parse` and `Pathway`-as-data, ships a fixed day-zero trio, and puts the plugin runtime explicitly out of scope. This is the deliberate middle that beats both M (too thin) and E (speculative).

### Axis 5 — One Catalog or two registries?
- **M:** one `Catalog` module owns both `Source` and `Pathway`.
- **E / V:** separate `SourceRegistry` and `PathwayLibrary`.
- **Winner: split (E/V).** Exit 5's "*one owner's* change" is sharper when the owners are distinct: a source *ingester* and a clinical *library author* are different people. Splitting keeps each change local to its true owner. *Chosen.*

### Axis 6 — Is the ledger persisted?
- **M:** computed, "optionally materialized as a cache."
- **E:** `LedgerEntry` appears as a persisted entity (`computed_at`).
- **V:** strictly a derived view, **never** persisted — a stored ledger is a second truth that can drift from its citations.
- **Winner: V's derived view.** A persisted ledger can diverge from the sources it cites, defeating the citation guarantee. `final.md` keeps it a view; a pure input-keyed cache is allowed but never authoritative — capturing M's perf option without E's drift risk.

### Axis 7 — Immutability / append-only
- **V:** all authored records immutable and append-only; corrections are new versions (`supersedes`).
- **M / E:** not emphasized.
- **Winner: adopt V's append-only** for `Source` and `ReportedState` (+ versioned pathways). It's cheap and directly serves citation *re-verifiability* — a chosen pick, not gold-plating, because it makes "any citation ever emitted re-checks against exactly the record it cited" true.

### Axis 8 — Grant role vs. scope, and where trust comes from
- **M:** `role` on the membership, and a doctor's own items get their tier **from role** — leaking tier logic into the account model.
- **E / V:** closed ordered `scope` (READ<REPORT<MANAGE) + an **open `relation` label that changes nothing in logic**; tier comes only from `Source`.
- **Winner: E/V's scope + inert relation label.** M's role→tier coupling contradicts the shared rule that tier lives only on `Source`. Keeping `relation` logic-free and tier source-only removes the one place M let clinical trust leak into accounts. *Chosen.*

### Axis 9 — Is "no plan" reported or inferred?
- **M / E:** absence of a matching plan/`plan_marker` record triggers the nudge (absence observed by the join).
- **V:** requires an explicitly reported `PlanPresence(has_plan=false)` — the system never even concludes absence.
- **Winner: a considered middle.** V's insight worth keeping: **the openness of a process must be a reported fact** (`ProcessOpen`), never system-invented. But requiring the user to explicitly report "I have no plan" is too heavy for an MVP. `final.md` fires the nudge on a *plan-required step / reported open process* with **no matching `PlanMarker`** — logical absence over reported data (same category as "overdue"), which is arithmetic, not clinical inference. Takes V's guard (don't invent the open process) without V's ergonomic tax.

### Axis 10 — Confidence tier granularity
- **M:** 3 tiers (A/B/C). **E:** 4 named (public/personal/derived/self). **V:** 4, strict total order.
- **Winner: V's clean total order**, assigned by source class in one file, with **E's cross-tier rule** (when expected and reported sources differ, carry both and surface the *lower* as effective). Ordering makes "which source do we trust" decidable; the reconciliation rule handles mixed-provenance ledger items.

## One-line summary of the synthesis strategy

Take **V's unrepresentability moves** (no `SYSTEM` origin, sealed citation, pure total join, derived-view ledger, append-only) as the backbone; take **E's closed-core/open-registry split and template catalog** as the shape; and apply **M's restraint** to reject E's speculative plugin runtime — landing a design that is minimal where the brief is silent and provably closed where the brief is strict.
