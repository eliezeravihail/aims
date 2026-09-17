# Step-0 inventory (fixed before any scoring; held for both arms, both stages)

Pinned from the stage cards' exit criteria — **not** from any design. Every scored sub-check cites an item
here or a named seam. This is the shared denominator that makes the two arms comparable (`measurement.md`,
"Comparability").

## R — rules / invariants

- **R1** Identification maps observed features → the set of candidates consistent with them, **ranked**; the
  result need not be a single species/mineral.
- **R2** Partial input is normal: only observed features constrain; a missing feature never counts as a
  mismatch.
- **R3** An unknown or invalid feature value is **reported**, never silently dropped and never a crash.
- **R4** **No-match** and **many-match** are two distinct valid results, each communicated as itself (not an
  empty list read as an error).
- **R5** Reference data is ingested from **Wikipedia**; the identification core must **not** depend on
  Wikipedia's page shape — ingestion is behind a seam/adapter.
- **R6** The ranking is **explainable**: for each candidate, which observed features matched and which
  excluded others.
- **R7** *(stage 2)* The mineral feature schema is **disjoint** from the plant one; neither leaks into the
  other's model.
- **R8** *(stage 2)* Adding minerals leaves plant identification **unchanged** (behavioural regression: every
  stage-1 plant case still holds).
- **R9** *(stage 2)* The shared match / rank / explain machinery is **reused**, not duplicated per domain.

## X — change axes (last is an unstated but plausible variant)

- **X1** Add an **identifiable domain** with a disjoint feature schema (plants → minerals → birds).
- **X2** Add or adjust a **feature** or its match semantics within a domain.
- **X3** Swap or extend the **data source** (Wikipedia → another catalogue / a local file).
- **X4** *(unstated)* A **numeric-range** feature (species height 20–40 cm; Mohs hardness 6.5–7) matched
  against a single observed figure — different match logic from a categorical feature, and a range-vs-range
  or figure-vs-range overlap test.

## C — acceptance / capability checks

- **C1** Identify a plant from a few observed features → a ranked candidate set + an explanation.
- **C2** Partial / unknown input → sensible narrowing; the unknown value is reported, not dropped.
- **C3** No-match and many-match come back as **distinct** results.
- **C4** *(stage 2)* Identify a mineral by hardness / lustre / streak; the plant path is unchanged.
- **C5** *(stage 2)* Plant and mineral share the match/rank/explain engine over **disjoint** schemas, and a
  third domain slots in without reopening either.
- **C6** A numeric-range feature (height, hardness) matches a single observed figure correctly at the range
  boundaries (X4) — the probe a clean-but-wrong design fails.
