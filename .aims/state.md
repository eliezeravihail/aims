# aims Guide State

## Mode

stepped

## Loop cursor

reviewed:awaiting-decision <panel-plan mechanism build — 7/7 conformance criteria met; one low-significance wording reading (aims-panel-plan.md "always convenes") awaiting the human's call>

## Current objective

**Kind:** implementation

**Objective:** Build the **panel-plan mechanism** as prose artifacts of the plugin, conforming to the
amended design in `.aims/worker-result-panel-plan.md`: a new reference
(`skills/aims-guide/references/panel-plan.md`, owning the axis trio's operating definition per
`decisions/0006`) and a new stepped-mode command (`commands/aims-panel-plan.md`), plus one-line/one-
sentence touches wiring the convening rule into `SKILL.md` step 2, the inline-convention exception into
`references/modes.md`, and the auto-mode opening-round routing into `commands/aims-plan-and-build.md`.
`commands/aims-plan.md` stays untouched (user decision: single-pass, always).

**Why now:** the design objective (below, superseded) closed with all 7 exit criteria met and two amending
decisions filed (`decisions/0006`; the harmonization-filing and `modes.md`-downgrade amendments in
`.aims/worker-result-panel-plan.md` §10). Nothing left to design — the Open Guide TODO named the build as
the next objective directly.

**Exit criteria:** (traceability restated as implementation-conformance checks; each source design
clause is `.aims/worker-result-panel-plan.md`, cited by section)
- [x] `skills/aims-guide/references/panel-plan.md` exists and covers, in order: when it convenes (§1) →
      the axis trio as sole operating definition (§6) → the grounding package (§2) → isolation per mode
      incl. the declared stepped-mode downgrade and the honest decline (§3) → the 6-step master procedure
      (§4) → all four output destinations, ADR alternatives carrying *both* decided conflicts and
      harmonizations (§5) → "not a gate, never a score" (§4 step 6).
- [x] `commands/aims-panel-plan.md` exists, mirrors `commands/aims-plan.md`'s stepped-mode plan-phase
      shape (steps 1–3, no delegation, no code, parks at `planned:awaiting-build`), routes objective
      drafting through the reference, and states it always convenes — never silently falls back to
      single-pass (§1, §8).
- [x] `SKILL.md` step 2 gains the auto-mode convening sentence, scoped to the opening design round only;
      it points at the reference rather than restating the axes (§1 row 3).
- [x] `references/modes.md` gains the declared exception beside the inline-convention rule it qualifies,
      stating the visibility trade plainly (arbitration stays watchable; the three drafts are only
      inspectable after the fact) rather than claiming the rationale intact (§1 row 4, §3, and amendment
      3 in §10).
- [x] `commands/aims-plan-and-build.md` gains the one-line routing of the opening round through the
      reference; `commands/aims-plan.md` is untouched (§1 rows 5–6).
- [x] The axis trio appears verbatim in exactly one place across the whole plugin
      (`references/panel-plan.md` §Axes) — every other touched file (`SKILL.md`, `modes.md`,
      `aims-plan-and-build.md`, `commands/aims-panel-plan.md`) names or points at it without restating it
      (criterion 6 of the design objective, now an implementation conformance check).
- [x] No hooks, no runtime code, nothing added outside `.md` prose (`decisions/0004` stands).

**Preserve:**
- `.aims/state.md` schema contract (headings + markers) — unchanged by this build.
- `/aims-plan` stays single-pass in stepped mode; its file is untouched.
- `references/review-panel.md` untouched; `references/panel-plan.md`'s opening paragraph states the
  plan-side/review-side relationship instead.
- `architecture.md` and `decisions/0005`, `decisions/0006` — already amended in the design round; not
  reopened here.

**Do not optimize for:**
- Rewording or re-deriving the design already settled in `.aims/worker-result-panel-plan.md` — this
  round transcribes it into prose artifacts, it does not re-design.
- Any mechanism, config, or hook beyond the plugin's existing prose-only shape.

## Worker handoff (conformed to — executed inline, stepped mode, no subagent)

ROLE — Guide executing the build phase inline (`references/modes.md`, stepped mode: explicit commands run
on the currently selected model, no subagent).

DESIGN GOAL — Author the two new prose artifacts and the three touches listed in the Objective above,
verbatim in structure to `.aims/worker-result-panel-plan.md` §1 and §8 (the file table and the two
skeletons), carrying forward all four amendments from §10.

BEHAVIOR IT MUST SATISFY — The Exit criteria above; the Preserve list; `decisions/0005` and `decisions/0006`
for the axis trio and its ownership split.

RETURN TO GUIDE — Evidence pointer: the files themselves —
`skills/aims-guide/references/panel-plan.md` (new), `commands/aims-panel-plan.md` (new),
`skills/aims-guide/SKILL.md` (step 2 addition), `skills/aims-guide/references/modes.md` (exception added
after "Explicit commands run inline"), `commands/aims-plan-and-build.md` (routing line added). No new
engineering lesson surfaced worth an Insight — the design was already fully buildable per the prior
review's closing note.

## Open Guide TODO

- [x] Build the panel-plan mechanism's prose artifacts. **Done** — see Current objective and the evidence
      pointer above; awaiting the review phase.
- [x] Route `/aims-plan-and-build`'s opening round through panel-plan automatically. **Done as part of
      this same build** — `SKILL.md` step 2 and `commands/aims-plan-and-build.md` both gained the routing
      line, since the design's own file table (§1) already scoped this as a one-line touch, not a
      separate objective.

## Last evaluated result

**panel-plan mechanism BUILD** (`implementation` lens, roles run inline per `references/modes.md`, on
Opus 4.8). **7/7 conformance criteria met.** One low-significance reading; no scores.

**1 — `aims-panel-plan.md` says "always convenes" one line after allowing an honest decline. (low)**
`commands/aims-panel-plan.md:16` permits the command to "decline honestly … if no subagent facility
exists", while `:18` states it "always convenes the panel — it never falls back to single-pass planning
silently." The two coexist in one file; the word *always* is imprecise against its own line 16. The
**substance is correct** — the reference (`references/panel-plan.md:86`) makes the no-facility decline an
*out-loud* refusal, and the falsifier the criterion actually cares about is a **silent** single-pass
fallback, which neither file allows. So this is a wording precision reading, not a behavior defect: a
strict reader momentarily sees "always" contradict "decline". Suggested fix (the human's call, not
auto-applied): soften `:18` to "always convenes when it can, and declines out loud otherwise — never a
silent single-pass fallback." No other file repeats the imprecision (`state.md:37` already phrases it as
"never silently falls back").

**Confirmed met, each by citation:**
- Criterion 1 (reference completeness + order): `references/panel-plan.md` sections run convening →
  axes-as-sole-operating-definition → grounding package → isolation-per-mode (incl. declared downgrade
  `:81-84` + honest decline `:86`) → 6-step master procedure → four output destinations with ADR carrying
  *both* decided conflicts and harmonizations (`:110-119`) → "Not a gate, never a score". Order matches §8
  skeleton.
- Criterion 2 (command shape): `commands/aims-panel-plan.md` runs steps 1–3, "Do not delegate and do not
  write implementation code", parks `planned:awaiting-build`, routes drafting through the reference —
  mirrors `commands/aims-plan.md`.
- Criterion 3 (SKILL wiring): `SKILL.md` step 2 adds the auto-convening sentence scoped to the opening
  round only, points at the reference, does not restate the axes.
- Criterion 4 (modes.md exception): `references/modes.md` adds the exception directly after "Explicit
  commands run inline", stating the visibility trade plainly (arbitration watchable; the three drafts only
  inspectable after the fact) — not claiming the rationale intact.
- Criterion 5 (routing + untouched): `commands/aims-plan-and-build.md` gains the routing line;
  `git diff origin/master...HEAD -- commands/aims-plan.md` is **empty** — untouched.
- Criterion 6 (one operating owner): a repo-wide grep for the axis phrasing returns the operating
  definition only in `references/panel-plan.md` among shipping surfaces; `review.md:32` is an incidental
  "tell-don't-ask" mention, not a restatement; `decisions/0005` holds the frozen-rationale copy per
  `decisions/0006`; the four wiring files point without restating.
- Criterion 7 (prose only): `git diff --name-only origin/master...HEAD` shows **six `.md` files, zero
  non-`.md`** — no hook, no runtime code.

**Fidelity checks that passed (probed, not defects):** the stepped-mode advisor-subagent spawn does *not*
silently contradict the "explicit commands run inline" rule — it routes through the reference, which owns
the declared exception (aims' own refer-don't-restate discipline). Harmonizations are filed durably in the
ADR (`panel-plan.md §Where the outputs land`), not left in the ephemeral plan report — the exact regression
the design review's reading 2 fixed is not reintroduced.

**Implication for direction.** The build conforms to the amended design end to end; the mechanism's core
(isolation, composition, one owner) transcribed faithfully. The single reading is a one-word precision fix
in a command file, safe to fold into any later touch — it blocks nothing. The design objective's own
"Convening falsifiers" criterion (v3 pilot already demonstrated the *panel arm wins*, `experiments/aims-vs-openspec/results-v3.md`) is now backed by a shippable command, not just a manually-reproduced procedure.

---

*(Prior round — design — retained below for the append-only trail.)*

**panel-plan mechanism design** (`design` lens, roles run inline per `references/modes.md`). Five of seven
exit criteria met. Four readings, each cited; no scores.

**1 — Two records each claim sole ownership of the axis trio. (blocks criterion 6)**
`architecture.md:15` states the trio has "exactly one owning definition — in
`decisions/0005-panel-plan-three-advisors.md`; it is not restated here or anywhere else," and the handoff
repeated it (`.aims/state.md:16`). The returned design relocates it:
`.aims/worker-result-panel-plan.md:78-80` makes `references/panel-plan.md` §Axes "the **operating
definition**" and demotes 0005 to "history." As written the design produces exactly the second
drift-capable copy criterion 6 fails on. **Counterevidence preserved — the relocation has a real force the
records did not anticipate:** `decisions/` is aims' own history and does not ship to a target project,
while `references/` does, so a target project running panel-plan would never see 0005; and `decisions/`
is append-only (CLAUDE.md), a poor home for a definition already revised once in-round (0005 line 12,
"revised in-round"). This is a genuine collision, not a Worker error — but the design picked a side
silently. Resolving it is a decision that amends either `architecture.md:15` or the design, not a wording
fix. Until it is made, a Worker authoring §Axes has contradictory instructions — the one place the design
is not buildable.

**2 — Harmonized divergences are never filed durably. (criterion 3 partial)**
Criterion 3 requires each split axis to land in the round's ADR, "divergence living only in the
conversation fails" (`.aims/state.md:39-41`). The design files only *decided conflicts* there
(`worker-result:66-68`); harmonizations go to the plan report (`worker-result:73-74`), which
`references/modes.md:58` defines as "compiled from the objective and the design docs … **not a new stored
file**" — ephemeral. Because §4 harmonizes first and decides only genuinely irreconcilable conflicts, the
*common* case is a real advisor split whose resolution reaches no durable record — and "two axes pulled
apart here; this shape satisfies both" is among the most valuable knowledge the panel produces. Met for
decided conflicts, unmet for harmonized ones.

**3 — Fidelity: the modes.md reconciliation claims more than it delivers.**
`references/modes.md:26-30` names two harms of a subagent under an explicit command: it "would run on a
different model **and** put the work behind a boundary they can't watch turn by turn."
`worker-result:38-47` preserves model choice, then substitutes after-the-fact *inspectability* (raw
drafts written to `.aims/panel/`) for *turn-by-turn watchability* while presenting the convention's
rationale as fully preserved. That is a narrowing, not an equivalence. Structurally the move is sound —
the design asks for an exception "declared next to the rule" rather than violating it silently — but the
amendment should state the downgrade plainly instead of claiming the rationale is intact.

**4 — Subtractive: `master-notes.md` has no named content and no stated consumer.**
`worker-result:71-72` introduces `.aims/panel/<date>-<slug>/advisor-<axis>.md` **+ `master-notes.md`**,
glossed "(inspectable raw drafts)" — which describes the advisor files, not it. No section says what it
holds or who reads it: the harvest goes to the ADR, the drafts to the advisor files, the reasoning to the
plan report. Deleting it damages no current rule, invariant, or boundary. (The `.aims/panel/` directory
itself earns its place — reading 3's reconciliation leans on it. Only the extra file is unforced.)

**What is solid.** Criterion 1 is the strongest part: §3 names isolation per mode, explicitly excludes
sequential-shared-context, and adds an honest decline when no subagent facility exists rather than
simulating independence. Criterion 2's merge procedure (harvest → harmonize-first → glue-only authorship →
subtractive pass, with winner-picking/union/averaging each a named failure) is a real mechanism, not a
restatement of the goal. Reusing the ADR's existing alternatives slot instead of inventing a record type
(§5) is the right subtractive instinct.

**Implication for direction.** Two gaps, of different kinds. Reading 1 needs a *decision* (which record
owns the trio) before any build can proceed — it is the one thing blocking buildability. Reading 2 needs a
*design amendment* (file harmonizations durably, most likely in the same ADR alternatives section).
Readings 3 and 4 are cheap corrections to fold into whichever round addresses the first two. The
mechanism's core — isolation and composition — measured sound; the gaps are at the record-keeping seam.

## Decision on the review readings (2026-09-15)

The Guide's decision at `reviewed:awaiting-decision`. All four readings mattered to the product and all four
are closed **before** any build — the blocking one by a recorded decision, the rest by amending the design.

1. **Axis-trio ownership (reading 1, blocking).** Decided in favor of the design's instinct, for the reason
   the design did not state: `decisions/` does not ship to a target project and `skills/` does, so a
   definition an advisor must operate from cannot live only in an ADR. Filed as
   `decisions/0006-shipping-surface-owns-operating-definitions.md` — ownership splits **by kind of text**
   (shipping surface owns the operating definition; the ADR owns the decision and its rationale, frozen as
   of its date). `architecture.md`'s panel-plan bullet is amended to match; `decisions/0005` is untouched
   (append-only) and 0006 carries the amendment. The rule generalizes past the trio.
2. **Harmonizations filed durably (reading 2).** Design amended — the round's ADR files every axis split in
   one of two named shapes, harmonization or decided conflict. The common case now lands durably.
3. **The `modes.md` reconciliation (reading 3).** Design amended to state the downgrade plainly:
   inspectable-after-the-fact advisor drafts are weaker than turn-by-turn watchability, and the exception
   declares the trade rather than claiming the rationale is intact.
4. **`master-notes.md` (reading 4).** Cut. `.aims/panel/` keeps the advisor drafts only.

Cursor moves `reviewed:awaiting-decision` → `ready-to-choose-next`. The design objective is reached; the
next objective is the **build** of the two prose artifacts, not more design.
