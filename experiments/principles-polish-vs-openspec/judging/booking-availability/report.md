# Blind design judgement — booking-availability (X vs Y)

*Blind, structural-only, scored against `design-principles.md` via the fillable instrument, with the hidden
oracle as the correctness key. No method named. Sealed mapping (revealed after scoring): **X = aims-single,
Y = OpenSpec**. Rows 16/17 N/A for both (pure, side-effect-free computation; no trust boundary).*

## D1 — First-round quality (stage-1 only)

**X-stage-1 — grade 10 · worst 10 · (0,0).** All applicable rows 10. `Interval` is the sole owner of
half-open overlap/intersection ("defined once and every consumer inherits it"); `TimeOfDay`/`Duration`/
`Interval` frozen value objects keep instant and delta distinct ("the common value-correct cram is one int
serving both"); `free_windows`/`pack`/service split with alignment isolated "because alignment is the most
likely rule to change." The mandatory subtractive round cut `Resource`, `Slot`, `SlotPacker` with the §7
falsifier "no present X-item forces it."

**Y-stage-1 — grade 7.5 · worst 5 · (1,0).** §4 primitive obsession = **5 [S3]**: "Times are represented as
minutes-from-midnight … integer interval arithmetic," bookings as `{start,end}` records, duration bare — the
exact §4 cram, no `Interval`/`TimeOfDay`/`Duration`; §9 one-owner = 8 [S1]: the half-open convention is
applied as arithmetic in two stages (normalize's overlap-merge and enumerate's fit test) rather than funneled
through one owner; §2 = 8 [S1]: the seam crosses an untyped bag `{open,close}`/`{start,end}`/duration.

**D1 winner: X (aims), clear structural advantage.** Both stage-1-correct and both isolate alignment for the
coming grid; the difference is structure the rubric guards hardest for ("the dominant failure is too little
structure … the graver risk is too little structure") — X supplies the value objects and the single half-open
owner that Y omits. **10 vs 7.5.**

## D2 — Change absorption (stage-1 → stage-2)

**Survival (reading = reopened + discarded):**
- **X (aims):** 4 survived, 3 extended, 1 genuine reopen (`pack` — alignment generalized to an (origin,step)
  grid but "stayed one owner"; "because stage 1 isolated alignment, the reopen landed in exactly one place
  instead of smearing across the loop"), + 1 additive new owner (`Resource` — "Stage 1's YAGNI refusal of
  Resource was correct then … and correctly reopened now"), 0 discarded. **Net ≈ 1 confined reopen.**
- **Y (OpenSpec):** 8 survived, 4 extended, 3 reopened (alignment; the packing decision — same substance;
  the clock-free property, narrowed to take `now`), 0 discarded. **Net ≈ 2 substantive reopens.**

Both contain the alignment reopen behind a stage-1 seam and keep old packing as the granularity-unset
fallback; survival is close and not the decider.

**Stage-2 forms:** X-stage-2 = **10 · (0,0)**; Y-stage-2 = **7.5 · worst 5 · (2,0)**.

**Oracle-trap check:**
1. Buffer modeled as its own concept, not a booking? **BOTH PASS** (X "never instantiated as a Booking"; Y
   "Buffer is occupancy, never an entity").
2. **One owner for "bookable"? X PASSES, Y FAILS (decisive).** X keeps the buffer inside `free_windows` as a
   symmetric "minimum inter-booking separation N" so "pack and the fit test are untouched" — the occupied
   footprint is computed in one place. Y splits the buffer rule across normalize (leading side) and a
   separate candidate filter (trailing side): "the leading side is handled by occupancy; this requirement
   handles the trailing side" — the oracle's named trap-2 scatter, an **S3 one-owner breach** under change.
3. Interaction coverage? Both strong; X marginally more systematic (a D1–D12 matrix incl. buffer×granularity,
   buffer×notice, notice-does-not-reanchor-grid).

*Correctness note:* X's symmetric buffer was verified equivalent to trailing-buffer semantics (usable gap
g−2N, matching the oracle); its concept-fit review caught the substitution and renamed the rule to keep ONE
owner **and** concept-honesty. Y's buffer is concept-literal (trailing) but pays with split ownership.

**D2 winner: X (aims), clear, on the registered trap.** The axis under test is exactly "is 'bookable' a
computation whose rules get scattered as stage 2 adds them?" — X keeps it one place; Y scatters it and
accretes a new S3 under change (weighted 8.67→8.0), while X stays a clean 10 across both stages. **10 vs 7.5.**

## Residual tells

Scored blind/structural; excluded from scoring but recorded. **Sharpest tell:** X's prose mirrors this repo's
`design-principles.md` house method — "subtractive pass," "concept-fit pass," "the §7 falsifier," candidate
"axes (A1/A2)" — while Y uses a spec/Gherkin register. A non-blind judge sharing the rubric's vocabulary
could be pulled toward X by familiarity; controlled for by requiring a quoted structural basis for every
sub-10 row and not crediting X for speaking the rubric's language. Honest cross-check on the lopsided 10/10:
X was re-scrutinised for a genuine sub-10 (dual error channels; `Resource` as a data class; a speculative
projection) and each resolved to "holds by construction" — but the vocabulary overlap is the one place a
reader should independently re-audit. This is the same rubric-bias limitation recorded in the series
`results.md`; D2's survival reading is the rubric-free cross-check and there X still led (≈1 vs ≈2).
