# Divergence map — arm A (cand-1 · cand-2 · cand-3)

Cross-examination of the three independent MVP designs. First what they **agree** on (robust, kept
without change), then the **axes where they split** and why the synthesized design picks what it picks.

---

## Where all three agree (robust — kept as-is)

These convergent choices are treated as load-bearing and carried into `final.md` unchanged:

1. **`Citation` is a sealed type with a private constructor** — the only value the outside world may
   receive. (cand-1 "Kernel", cand-2 "Gate", cand-3 "Gateway".)
2. **Exactly one choke-point module** is the sole constructor of that type; it takes **references,
   never content** — no text parameter, no generation step.
3. **`Citation = (Source × ReportedState)`**, where the reported half is `Present | Absence`. Absence
   is a first-class typed value so a gap is still a well-formed citation.
4. **The nudge is a citation, not advice.** "Ask your doctor" is a fixed template constant on an
   `open/no-plan` status; no template names a course of action.
5. **`manager → subject(s)` is one edge** (`Stewardship`/`Link`); self/family/clinician differ only by
   `role` + `scope`; multi-subject is cardinality, never a mode; the doctor is unprivileged past the
   boundary and re-enters as a `DOCTOR_INSTRUCTION` source.
6. **Pathways are declarative data, not code**; adding a rail is a data row.
7. **Expected and reported are physically distinct stores, joined at read time**; gaps are computed,
   never enumerated per example.
8. **Confidence tier is a property of the source, stamped at ingest, immutable, copied into the
   citation** — a citation without a resolvable source cannot be built.
9. **Out of MVP (identical across all three):** the overview (*המכלול*), inference/suspicion engines,
   advice generation, unstated source types, cross-subject analytics, scheduling/delivery, auto-coding.

---

## Axis 1 — Confidence-tier ordering (the sharpest genuine conflict)

| | Top of ladder | Ordering |
|---|---|---|
| cand-1 | measured result | `measured > clinician_directive > guideline > self_reported > uncoded` |
| cand-2 | **public guideline** | `A_AUTHORITATIVE (guideline) > B_DIRECTED (doctor) > C_SELF_REPORTED` |
| cand-3 | doctor instruction | `T1 doctor/prescription > T2 public_guideline > T3 self_reported` |

This is a real, mutually contradictory decision: does a population **guideline** outrank an
individualized **doctor instruction**, or the reverse?

**Chosen:** cand-3's ordering — `clinician_directive > guideline` — extended with cand-1's
`self_reported` and `uncoded` low tiers. **Why:** a tier tells the user how authoritative the basis of
a flag is; an instruction issued **for this subject** is more authoritative for that subject than a
population rail, and cand-3 states this rationale explicitly. cand-2's guideline-on-top inverts that
and is rejected. cand-1's separate `measured` top tier is dropped as a *source* tier because
results are modeled on the **reported** side, not as sources (Axis 2) — but cand-1's `uncoded` tier is
kept, since it is the only design that handles the coding-failure case the shared assumption creates.

## Axis 2 — Is a lab result a `Source` or a `ReportedItem`?

- cand-1 / cand-2: **four source classes**, including `result_source` / `REPORTED_RESULT` — a result is
  a Source (and gives its reported item a "measured" tier).
- cand-3: **three source classes** (`PUBLIC_GUIDELINE`, `DOCTOR_INSTRUCTION`, `PRESCRIPTION`); a result
  is a `ReportedItem`, not a source.

**Chosen:** cand-3's three classes. **Why:** it makes the citation's two halves crisp — the **source**
side is always the authoritative, expectation-*defining/authorizing* artifact; the **reported** side is
always the observed fact. Modeling a result as a source blurs that split and forces the awkward
"measured" source tier. cand-1's optional `linked_source` on a reported item is kept as the mechanism
for a result's own provenance/attachment, giving cand-1's backing idea a home without making results
sources.

## Axis 3 — Materialize expectations, or compute on read?

- cand-1: persists `ExpectedItem` (materialized rails per subject) **and** `LedgerEntry` rows.
- cand-2 / cand-3: expected steps and the ledger are **computed on read**; nothing materialized.

**Chosen:** compute-on-read (cand-2/cand-3), with cand-1's **addressable referent** preserved. **Why:**
storing materialized expectations invites drift between the rail data and the persisted expansion, and
the ledger is cheap to recompute. But cand-1 is right that an `Absence` needs a concrete thing to point
at (cand-2's bare `ABSENT` marker is too thin). Synthesis: instantiate steps **ephemerally** at
reconciliation but make each addressable `(subject_id, step_code, window)`, so `Absence(expected_step_ref)`
resolves — cand-1's referent discipline without cand-1's stored-state drift risk.

## Axis 4 — Status / relation grammar

- cand-1: `done, due, overdue, gap, open_unplanned` (5 — `gap` overlaps `overdue`).
- cand-2: `SATISFIED_BY, OUTSTANDING, NO_PLAN` (3 — collapses all timing).
- cand-3: `DONE, DUE, OVERDUE, OPEN_NO_PLAN` (4).

**Chosen:** cand-3's four. **Why:** cand-2's three-value grammar is elegant but discards the
due-vs-overdue timing distinction that Pillar 1 (steering *next steps*) needs. cand-1's fifth value
`gap` is redundant with `overdue`/`due`. Four statuses keep cand-2's insight — a small closed grammar
with no advice value — while retaining the timing the product requires.

## Axis 5 — Is "one writer of state" an explicit invariant?

- cand-2 / cand-3: **yes** — the Ingestion Port is the *only* module that can write state; this is what
  structurally forecloses inference.
- cand-1: has ingestion but leans on the Kernel's no-inference property; single-writer is implicit.

**Chosen:** make it explicit (cand-3's framing, "inference is designed out"). **Why:** the sealed
Citation constructor stops *fabricated output*, but non-**inference** is a separate guarantee — it needs
a rule that no module but ingestion can write a medical fact. Promoting single-writer to a named
invariant closes the gap cand-1 leaves implicit and pairs cleanly with the single egress.

## Axis 6 — Doctor instruction: source-only, or dual-role?

- cand-1 / cand-2: a doctor instruction enters as a `Source`.
- cand-3: a `DOCTOR_INSTRUCTION` reported item **dual-registers** a same-id `Source`, so "repeat in 3
  months" is at once a recorded fact and an authorized expected step.

**Chosen:** cand-3's dual-role registration. **Why:** without it, a doctor's instruction that *creates a
new expectation* has to be entered twice (once as fact, once as source) or drives the two axes out of
sync. Dual registration keeps expected and reported aligned **at ingest, without any inference step** —
exactly the property the invariant needs.

## Axis 7 — Module decomposition (minor)

All three share the same seven roles; they differ only in folding. cand-1 folds Sources into Ingestion;
cand-3 gives Sources its own module (owning the tier ladder). **Chosen:** cand-3's separate **Sources**
module, because Axis 1 makes the tier ladder a first-class thing that should have exactly one owner and
one place to change (criterion 5). Naming follows cand-3 ("Gateway", "Ingestion Port").

---

## Summary of picks

| Axis | Winner | One-line reason |
|---|---|---|
| Tier ordering | cand-3 (+cand-1 low tiers) | individualized directive outranks population guideline; keep `uncoded` |
| Result = source? | cand-3 | crisp source/reported split; results are reported facts |
| Materialize vs compute | cand-2/3 shape + cand-1 referent | no stored drift, but `Absence` still resolves |
| Status grammar | cand-3 (4) | keeps timing without cand-1's redundant `gap` |
| One writer of state | cand-2/3 explicit | non-inference needs its own named invariant |
| Doctor instruction | cand-3 dual-role | keeps both axes in sync at ingest, no inference |
| Module split | cand-3 | Sources owns the tier ladder as a single-owner change |
