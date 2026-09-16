# Q3 — continuity. Verdict: all three arms "navigated and built on it".

No arm re-derived. Every stage-2 and stage-3 session found and used a specific record written before the
requirement existed, and the judge proved each with git.

| Arm | Load-bearing evidence | What happens to a conclusion that turns out wrong |
|---|---|---|
| aims | stage-1 ADR 0003 predicted a "signed sibling"; stage-2 built `MoneyDelta` citing it by number | superseded in place, original text kept — 5 times out of 6. Missed once (0003 → 0017) |
| OpenSpec | stage-1 named exclusivity as "a catalogue field"; stage-2 built exactly that and rewrote the stage-1 bullet in place | overwritten. The superseded claim survives only in git. The spec format's own MODIFIED/REMOVED markers went unused in all three stages |
| plain | stage-1 "rules stay pure… this is why they return proposals"; stage-2 §4.4 cashes it in. stage-2 predicted "tax = new phases"; stage-3 quotes and rejects it | a paragraph headed "Stage 3 gives up one stage-2 claim and must say so" — 3 times out of 3 |

## The finding that matters most, and it is against aims' distinctiveness

**The three durable layers did not differ in whether knowledge survived. They differed only in what
happens to a conclusion that turns out to be wrong.**

The plain arm — three markdown files, no ADR directory, no spec schema, no anchor stamping, no hooks, no
state file — reached the same continuity verdict as `decisions/0001`–`0019` plus two hooks plus
`.aims/state.md`. The judge states it plainly: "That is a real result against the value of the other two
teams' machinery, and it should be read as one."

Qualifications the judge attached, in both directions:
- plain's mechanism is **total restatement** (766 → 1340 → 2009 lines per stage). A conclusion dropped
  during restatement would vanish without trace; nothing structural prevents it. It did not happen here.
- Restatement is O(n) per stage; a navigable record set is O(1). At three stages that difference has not
  bitten. **This exercise cannot say what happens at stage 8** — which is precisely the scenario aims'
  goals.md is written for.
- The OpenSpec arm's `openspec/specs/` was empty at every tag (only `.gitkeep`), because the baseline is
  populated by the archive step, which runs after implementation. Confirmed limitation of my exercise
  design, not a fault of the arm. It inherited the un-archived change folder instead — which the judge
  notes carried *more* rationale than the baseline would have, since `design.md` never merges into
  `specs/` and leaves the default read path on archive.
