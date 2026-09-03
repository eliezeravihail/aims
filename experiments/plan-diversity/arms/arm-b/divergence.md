# Divergence map — three MVP designs for the "responsible doctor"

Reading: **cand-sonnet**, **cand-opus**, **cand-fable**. All three converge on the load-bearing shape,
which is why that shape is safe to keep. They split on a handful of real architectural decisions; each is
resolved below with the reason the chosen option wins in `final.md`.

## Where all three AGREE (kept without change)
- **Citation is the sole outward type**, minted by a single chokepoint module (`cite` / Kernel / Gateway)
  with a private/sealed constructor; the presentation seam can only receive `Citation`.
- **Rendering quotes, never authors** — the human string is a fixed template interpolating a source excerpt
  and a reported value; there is no free-text/advice field on the outward type.
- **Confidence tier is a fixed property of the source class**, assigned once at ingestion, copied onto the
  citation, never recomputed downstream.
- **`manager → subject` is one relation** (Mandate/Grant); self / family / clinician are cardinalities of one
  table, and `basis`/`role` never branches output logic.
- **Expected (declarative pathway rails) and Reported (human-asserted facts) are distinct stores**, joined
  by one pure, recomputable, example-independent function; gaps are the join's residue.
- **A doctor is just a manager** who authors instruction sources; no elevated egress.
- **~7 modules, one dependency direction toward the kernel; nothing imports egress.**
- **Out of MVP:** Pillar 2/המכלול, all inference, extra source types, notification delivery, consent
  workflows.

## Axis 1 — Is a nudge a Citation, or a second constructor? **(most consequential)**
- **sonnet:** `Citation` is a two-constructor union; `NudgeCitation` carries **fixed text and no source**.
- **opus:** a nudge *is* a citation, cited against a shipped synthetic `Source(ASK_YOUR_DOCTOR)` guideline.
- **fable:** a nudge is an **ordinary `NO_PLAN` gap** — the opening doctor instruction compiles to a one-step
  rail, and the nudge cites *that real instruction* as its source.
- **Chosen: fable.** Sonnet's second constructor punches a hole in the invariant — a citation with no source
  is exactly the "value that isn't `(source × reported)`" the architecture exists to forbid, and it needs a
  separate code path. Opus repairs uniformity but with a *fabricated* source, which is mild advice-origination
  dressed as a guideline. Fable keeps one citation form *and* cites a genuine authority (the doctor's own
  referral that opened the process), so the nudge falls out of the same join with no special path.

## Axis 2 — What may open a process / trigger a nudge?
- **sonnet:** "a ReportedState indicating an open process, **e.g. an abnormal result**" opens a gap.
- **opus:** an `on_open_no_plan` flag on an expected step, when unsatisfied with no personal source governing.
- **fable:** `opens_process` is allowed **only** on human `INSTRUCTION` rows, enforced by a schema
  `CHECK (opens_process IS NULL OR kind = 'INSTRUCTION')`.
- **Chosen: fable.** Sonnet's "abnormal result" is a direct invariant breach — judging a result abnormal *is*
  inference, the one thing the system must never do. Fable moves the guard into the database schema so no
  code path (or raw SQL) can let a bare result open a process. Strongest, and it closes Sonnet's leak.

## Axis 3 — How is the non-advice boundary enforced?
- **sonnet / opus:** type-level — sealed type, single constructor, no upstream inference surface (four/five
  narrated structural facts).
- **fable:** the same type-level guard **plus** a CI dependency/architecture test **plus** database schema
  (`source_id`/`locator_id` NOT NULL, `citation_basis ≥ 1` by trigger, **no text column**).
- **Chosen: fable.** Type visibility alone holds only within the type system; Fable's two extra layers make
  the invariant hold against a wiring mistake (CI test) and against a raw-SQL bypass (schema). The brief
  calls this boundary "non-negotiable," which earns defense in depth.

## Axis 4 — How does verbatim source text travel?
- **sonnet:** `raw_ref` on the source; excerpt mechanism unspecified.
- **opus:** `content_ref` — "the only text the system may quote."
- **fable:** a `source_locator` table — an exact citable position (section/page/line) **with the verbatim
  excerpt**; each step and citation points at a locator (NOT NULL).
- **Chosen: fable.** A citation should point to an exact quotable span, not "the source" in the abstract.
  The locator makes "the system quotes, never authors" concrete and gives the render layer a bound slot.

## Axis 5 — Confidence-tier ordering
- **sonnet / opus:** personal directive **outranks** population guideline (personal = tier A).
- **fable:** documentary strength — `GUIDELINE` = A, instruction/prescription = B (with document) / C
  (relayed, no document).
- **Chosen: a considered merge (neither verbatim).** Two orthogonal axes were being conflated: *authority for
  this subject* (sonnet/opus) and *evidential backing* (fable). `final.md` keeps three tiers and one clear
  axis — A = personal directive, document-backed; B = population guideline; C = personal directive, relayed
  without a document — capturing the MVP-relevant "my doctor said…" vs. "here is the instruction document"
  distinction that fable surfaced while keeping a personal directive able to be the strongest source. Tier
  remains a fixed source property owned by one policy table, which is the part all three agree on.

## Axis 6 — Where is the mandate check enforced, and is the ledger stored?
- **sonnet:** account service consulted by every module as a read-only scoping filter; ledger stored per
  subject. **opus:** every request resolves a `SubjectContext`; ledger is an internal draft.
- **fable:** the check runs in **exactly two places** (`reports` on write, `cite` on read); the ledger is a
  **truncatable cache of a pure function** storing only references.
- **Chosen: fable.** Two named checkpoints are more auditable than "every module filters," and "ledger =
  recomputable cache of references" makes staleness a non-issue and keeps zero medical prose materialized.
