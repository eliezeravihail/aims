# How to run an aims experiment (pilot)

A step-by-step protocol for adding an experiment that actually **discriminates** — a controlled,
blind-judged comparison, not a demonstration. It is the aims port of the method the Balash pilots learned
the hard way; every aims experiment must instantiate it (or say explicitly which part it waives and why).

The whole method exists to answer honest questions, so keep them in view the entire time. aims makes two
claims, judged **separately** (never merged into one score):

> **Q1 — direction.** When a product evolves through requirements nobody stated up front, does the aims
> arm (design made the goal) end up **architecturally better** than an equally capable agent with no
> method — even when that agent is free to refactor at every step?
>
> **Q2 — continuity.** Does a **fresh session with no history** continue correctly from the *co-located
> records* (read the prior conclusion, build on it, avoid the recorded trap) rather than re-deriving or
> repeating a mistake?

Writing code is cheap and a strong model refactors deeply, so "nicer code in one shot" is not the bar.
Only the **quality of the final architecture** at the point the product kept changing counts.

---

## 0. Decide what kind of pilot this is, and name the axis

- **A build pilot** — both arms build a real product across staged reveals; you judge the final
  architecture (and, separately, the product behavior).
- **A feasibility-gate pilot** — the premise itself is unproven or false. Success is a **reasoned stop**,
  not a build: the arm must detect the shaky assumption, ask the one concrete product question, and refuse
  to silently substitute another route. The clean arm reaching the same stop is a fair result *against*
  aims, not a failed experiment.

Pick **one product** and **one architectural axis** its evolution stresses (identity/ownership introduced
late; a second variant that reveals a missing abstraction; a delivery/format boundary; a feasibility
gate). If you can't name the axis, the pilot won't discriminate.

## 1. Freeze the experiment package *before* any agent runs

Do not edit mid-run:

1. **`starter/`** — identical for both arms: runtime, test tool, fixtures, run instructions, permissions.
2. **Stage cards** (`cards/stage-N.md`), one per evolution step. Only the current card is visible; the
   next is revealed **only after both arms close the current one**. **A stage card must not hint that a
   later stage exists** (no "later we will export…"). Forward-looking language is a leak (see §4).
3. **A hidden staged spec + oracle answers** (`hidden/`) the agents never see — the whole product
   including future stages, and canonical answers to likely questions per stage.
4. **Visible acceptance per stage** and separately **hidden final probes**, derived *only* from
   requirements already revealed. No surprise test that invents a feature nobody asked for.
5. **One equal time/cost ceiling** per arm. A failed acceptance is recorded and charged against the same
   budget — it does not buy free retries.

## 2. The two arms

| | aims arm | clean arm |
|---|---|---|
| Prompt | identical minimal request **+ one line**: "follow the `aims-guide` skill" | the identical minimal request, told nothing about method ("build it well") |
| Structure | Guide selects a design objective, delegates to a Worker, measures, files **co-located records**; a fresh session continues each later stage by navigating those records | one capable agent, free to plan/inspect/code/test/refactor as it likes |
| Right to ask | yes — one material product question at a time, to the oracle | yes — same channel, same right, same oracle |

Keep everything else identical (§3). The aims arm may spend more model calls — that extra reasoning loop
**is the treatment**; record the cost, never equalize it by feeding the clean arm hidden architecture hints.

For **Q2 specifically**, the aims arm's later stages must be run by a **fresh subagent with no memory of
the earlier stage**, given the product + the co-located records + the stage card, and told to consult the
records — *not* told where the seam is. That a fresh session finds the seam by navigation is the result.

## 3. Controlled variables

Hold constant across arms: model + version, reasoning/budget setting, tools and repo permissions, fresh
empty repositories, the exact stage requirements, the test/runtime environment, and **no access to any
later-stage file before the current stage is complete**. Two standing conventions:

- **Pin the method commit.** Record the `aims-guide` / repo commit the run executed under — the skill
  changes, so "which aims" is part of the result. A pilot whose pin you can't name is not reproducible.
- **A load-bearing wording change wants n ≥ 2 per arm.** A single internal A/B validating a *skill* wording
  change is directional, not robust. Per-product build pilots are typically n = 1 and read as
  *suggestive*; strength comes from the **sequence**, not any single unit.

## 4. Oracle policy — strict, passive, no volunteering

The operator plays an ordinary product owner, **not an architect**. Asking the right question is itself
under test; an arm that doesn't probe an invariant simply doesn't get told it.

1. Answer only from facts in the hidden spec for the **current** stage.
2. Volunteer nothing the arm did not ask for.
3. **Never reveal a later-stage requirement.** "Will there be X later?" → "not now — build for today."
4. For a technical choice an ordinary user would not make → *"I don't know; choose a simple sensible
   technical approach."*
5. **Word answers neutrally.** One leak word ("still", "yet", "for now") disqualifies the run — discard and
   re-run that stage.
6. Log every question and the verbatim answer. If the other arm asks the same question, it gets the **same
   answer, word for word**.

## 5. Run procedure (each arm, each stage)

1. Ensure only current + previous requirements are visible; the arms never see each other's repo, code,
   reasoning, or output.
2. Deliver the current stage card verbatim.
3. Let the arm work until it claims the behavior is complete.
4. Run the project's tests; run the visible acceptance.
5. Commit with a `stage-N` tag; save transcript, Q&A log, and cost (turns, tokens, wall-clock, model
   calls). A failed acceptance is recorded, not silently retried.
6. Only then reveal the next stage — to **both** arms.

## 6. Judge blind — with a separate judge, and then scrutinize the judge

The judge is **not** the Guide who ran the aims arm. Use **separate judge subagents** that did not build
either product.

1. **Anonymize.** Strip method-revealing names (`.aims/`, companions' provenance, branch/commit messages,
   any `*.md` record that names "aims"). Relabel the two codebases **X / Y**; the judges must not know
   which is which. *(Records are aims' treatment — a design judge that would see them must get a records-
   stripped snapshot; a separate continuity check, §Q2, is where the records are read on purpose.)*
2. **Three separate reports, never merged into one score:**
   - **Design** — judged against aims' own
     [`../skills/aims-guide/references/design-principles.md`](../skills/aims-guide/references/design-principles.md)
     and [`review.md`](../skills/aims-guide/references/review.md). Use **two opposite-disposition judges**
     (invariant-ownership vs. YAGNI/simplicity) reading the *same* two codebases — this catches a verdict
     that is a taste artifact.
   - **Product** — a black-box judge given only the product cards (not the method label), checking
     acceptance / probes / an exact UI or API path.
   - **Cost** — a recorder (tokens, time, rounds, model calls, deps); no quality verdict.
3. **Refinements, now standard:** a verdict must turn on **structural** properties (can an invariant be
   bypassed? is a boundary one seam or N? is a new variant one sibling or scattered edits?) — a *removable
   local blemish* must not flip it; and **"small is not unearned"** — a private field with no setter or a
   one-line funnel is small **and** load-bearing, not ceremony.
4. **Verify the judge, don't trust it.** Every load-bearing claim carries a reproduction (input → wrong
   output, a failing test) or a precise `file:line`. Re-run each arm independently
   (`install`/`test`/`build`) before believing any "tests pass." An abstract verdict is not a measurement.

## 7. Interpretation rules, fixed in advance

- Judges pick **aims**, **clean**, or **no clear advantage** for design and for product — no percentages,
  no weighted composite.
- A design win does **not** cancel a product loss, or vice versa. Report a trade-off as a trade-off.
- The honest strength is the **sequence** — the same effect recurring across different products — not a
  win tally. n = 1 per product is suggestive.
- Record aims' own recurring cost honestly: over-build at the seams, extra discovery rounds, delayed builds.

## 8. Artifacts to keep (so the judges can be audited)

Per pilot: the stage cards + versions, the oracle Q&A logs, per-stage `stage-N` commits, cost logs, the
anonymized X/Y snapshots, the design-principles docs used, and the three measurement reports — each finding
carrying a reproduction or `file:line`.

## 9. Record it

Add a `results.md` verdict: build pilot or feasibility gate; blind or an initial non-blind audit; n; the
pinned method commit; the single axis it stressed; and — separately — the Q1 and Q2 readings.

---

*Lineage: this is the aims port of Balash's `HOW-TO-RUN-A-PILOT.md`. A demonstration (one arm, self-judged)
is not an experiment; the control arm and the separate blind judge are what make it one.*
</content>
