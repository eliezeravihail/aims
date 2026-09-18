# Stage 2 — Buffer · Minimum notice · Granularity (aims, single arm)

Design objective, **Kind: design**. The change arrived after stage 1 was frozen; aims was re-run from
`plan` — first *consulting the stage-1 records* (`goals.md`, `architecture.md`, `decisions/0001–0003`,
`.aims/state.md`), then delta-discovery, then re-planning. New durable records filed:
`decisions/0004–0007`, plus a Stage-2 evolution section appended to `architecture.md`. One mandatory
design review-and-revise round taken. Architecture only — no implementation code.

## 1. The change, and the hard decision

Three new per-resource rules, applied together:
1. **Buffer N** — cleanup after every booking; makes the resource not free but is **not a booking**
   (never returned, no booker); no booking may sit so a buffer overlaps a neighbour's booking.
2. **Minimum notice X** — a slot may not start within X of `now`.
3. **Granularity G** — offered starts align to a per-resource grid, every G from the top of working
   hours.

The hard decision the stage-1 boundaries let us pose sharply: **does each new rule slot into one
existing owner, or force an owner open?** — and the concept trap in the buffer (it is phrased "after a
booking" but its availability effect is a *separation*).

## 2. Delta-discovery — new open product decisions (surfaced)

Filed with defaults in `decisions/0004–0007`; would be confirmed with the user:
- **SD1** a new booking's trailing buffer need **not** fit within working hours — only `[t, t+D)`
  must be in hours. (Default.)
- **SD2** `now` is an absolute instant injected at the boundary (not read from a wall clock — keeps
  the core pure/testable); queries are same-day, with cross-day projection defined but out of scope.
- **SD3** the granularity grid is anchored at **working-hours open** (grounded: "from the top of
  working hours"), and notice does **not** re-anchor it.
- **SD4** N/X/G are per resource, each defaulting to a no-op, so a resource with none reproduces
  stage-1 behavior exactly.

## 3. How each rule was placed

- **Buffer → one owner, `free_windows`** (`decisions/0005`). The availability-relevant concept is a
  **minimum separation N between any two bookings** (the earlier booking's trailing buffer *and* the
  new booking's own trailing buffer each consume N; usable space in a gap of length `g` is `g − 2N`).
  Implemented by expanding each existing booking's blocked interval to `[start − N, end + N)` (clamped
  to working hours) before the union/subtraction. A slot that fits an already-shrunk window is
  automatically buffer-safe, so `pack` and the fit test are untouched. The buffer is a `Duration` on
  `Resource`; it is never instantiated as a `Booking` and never emitted — satisfying "not a booking."
- **Minimum notice → the boundary** (`decisions/0007`). `notice_floor = now + X`, projected onto the
  query day at the imperative shell; the effective window becomes `[max(open, notice_floor), close)`.
  If it lands past close → `[]`. The domain stays within-day; only the boundary touches `datetime`.
- **Granularity → reopen `pack`, still one owner** (`decisions/0006`). Generalize the alignment owner
  to a `(origin, step)` grid: G set → `(open, G)`; G `None` → `(window.top, D)` = stage-1 behavior.
  `pack` gains the global anchor as an input when G is set.

## 4. The three applied together (interactions)

Composition order at the boundary, earliest-first:
```
effective   = [max(open, now + X), close)                 # notice narrows the window
windows      = free_windows(effective, buffer=N, bookings) # buffer shrinks each window
starts       = for each window, pack(window, D, grid)      # grid = (open,G) if G else (window.top,D)
             filtered to t >= notice_floor                 # grid stays anchored at open
```
Key interaction subtleties (each a checkable criterion below):
- **Notice × granularity:** the grid is anchored at **open**, not at the narrowed window start —
  notice removes grid points below `notice_floor`, it does not shift the grid. Re-anchoring would
  silently offer off-grid starts.
- **Buffer × granularity:** grid points are enumerated inside buffer-shrunk windows, so a grid start
  can never place a booking whose buffer collides with a neighbour.
- **Buffer × notice:** independent — one shrinks windows, one raises the window's left edge.

## 5. Adversarial exit criteria (stage-2 additions)

- [ ] D1 buffer only, one booking → free windows pulled in by N on the side(s) facing the booking;
  no start whose `[t,t+D)` sits within N of the booking.
- [ ] D2 gap exactly `2N` between two bookings → no start (usable `= g − 2N = 0`).
- [ ] D3 gap `2N + D` → exactly the one aligned start that fits.
- [ ] D4 booking's trailing buffer runs past close → allowed; the last window still ends at close
  (SD1), the new booking need not carry a trailing buffer before close.
- [ ] D5 buffer N = 0 → identical to stage 1 (no-op default).
- [ ] D6 notice: `now + X` before open → no effect; inside the day → starts `< now+X` dropped;
  after close → `[]`.
- [ ] D7 notice does not re-anchor the grid: with G set, a narrowed window still offers only
  `open + kG` starts (never `notice_floor + kG`).
- [ ] D8 granularity: starts are exactly `open + kG` that fit; `D` no longer sets the step.
- [ ] D9 G `None` → stage-1 back-to-back (`window.top + kD`) preserved.
- [ ] D10 all three together: a start is returned iff on the grid, `≥ now+X`, and `[t,t+D)` clears
  N from every booking on both sides and is inside working hours.
- [ ] D11 a buffer is never returned as a bookable start (no phantom bookless slot).
- [ ] D12 defaults: a `Resource` with N=0, X=0, G=None reproduces every stage-1 C-case bit-for-bit.

## 6. SURVIVAL (per stage-1 component)

| Stage-1 element | Fate | Why |
|---|---|---|
| `TimeOfDay` | **survived** | within-day model held; notice's `datetime` stayed at the boundary (SD2) |
| `Duration` | **survived** | reused verbatim as the type of N, X, and G |
| `Interval` | **extended** | one new op `expanded_by(Duration)` for buffer; half-open rules untouched |
| `Booking` | **survived** | buffer is *not* a booking, so no change to the entity |
| `free_windows` (free/busy owner) | **extended** | buffer folded into its input transform; union/subtract logic unchanged |
| `pack` (alignment owner) | **reopened** | its core rule (origin+step) generalized to a grid — but stayed **one owner** |
| `bookable_start_times` (boundary) | **extended** | notice narrowing + passes new policy; still owns I1 by composition |
| — *(stage 1 declined a `Resource`)* | **reopened → introduced** | three per-resource values are a new present force; `Resource` now earns its place |
| Invariants I1–I5 | **survived** | all preserved; four new invariants added atop them |
| Discarded | **none** | nothing from stage 1 was removed or contradicted |

**Did rules slot in, or force an owner open?**
- Buffer → **slotted in** (one owner, `free_windows`; concept named as separation so value and concept agree).
- Minimum notice → **slotted in** (a one-line window narrowing at the boundary; zero domain change).
- Granularity → **forced its owner open** — `pack`'s alignment rule was genuinely reopened (step D →
  grid). This is the predicted change axis **A1**; because stage 1 isolated alignment, the reopen
  landed in exactly one place instead of smearing across the loop.
- Per-resource-ness → **forced a new owner open** (`Resource`). Stage 1's YAGNI refusal of `Resource`
  was correct *then* (no rule to own) and correctly reopened *now* (three rules to own) — the
  §7 falsifier flipped: a present X-item now forces the seam.

Net: 4 survived, 3 extended, 1 rule-level reopen, 1 new owner, 0 discarded. The stage-1 seams held —
every rule found a single home, and the one destructive reopen was confined to the owner built to
absorb it.

## 7. Mandatory review-and-revise round (design objective — one round)

Measured with the assessment form; building projection (fix-list, most-severe-first, no aggregate).

**Concept-fit pass — the substantive finding.** The first-pass buffer design placed buffer as a
*symmetric expansion* while the spec calls it "buffer **after** a booking." The pass flagged the
mismatch: modeling the *new* booking's trailing clearance as a *leading* pad on existing bookings is
a value-correct-but-concept-substituted shape (the §4 cram risk). Two honest resolutions exist:
- (a) name the owned rule **"minimum inter-booking separation N"** (which *is* symmetric) — then the
  symmetric expansion matches the concept, and it stays one owner; or
- (b) keep buffer strictly trailing and add a trailing-clearance check inside `pack` — concept-literal
  but splits one rule across two owners (§5 violation).

**Revision:** adopt (a) and record it explicitly (`decisions/0005`), so the concept is "separation,"
not "trailing buffer with a phantom leading pad" — no inert member, value and concept aligned, and
§5 one-owner-per-rule preserved. This is the round's real content.

**Subtractive pass.** Checked the new `Resource`: does it own a rule, or is it a stage-1-style empty
wrapper? It now holds three policy values each with a present force (N, X, G) — it earns its place
(unlike the stage-1 `Resource` that held only working hours and was cut). `Resource` holds policy and
computes nothing, so it did not swell into a god object. No new ceremony to cut. Post-revision
fix-list empty at S2+; §0/§5 seams and one-owner hold; §1 covers D1–D12; §4 concept-fit resolved.
Design reads **met**. **Frozen here.**

## Cost

| | Stage 1 | Stage 2 |
|---|---|---|
| Plan passes | 1 (single-pass `plan`) | 1 (re-plan on the received change) |
| Design review rounds | 1 mandatory (3 subtractions) | 1 mandatory (1 concept-fit revision) |
| New durable records | goals, architecture, base-deps, `decisions/0001–0003` | `decisions/0004–0007` + architecture Stage-2 section |
| Open product decisions surfaced | 4 (carried as assumptions) | 4 (SD1–SD4, defaults filed) |
| Owners forced open | — | 1 rule-reopen (`pack`) + 1 new owner (`Resource`) |
| Approx word count | ~1,350 | ~1,150 |

Stage-2 cost was low because the change mostly *consulted* stage-1 records and reused their owners:
two of three rules slotted into existing seams, and the only new writing was four ADRs plus one
architecture delta.
