---
title: "correction: the shipped panel-plan trio was directly validated, not an unvalidated in-round swap"
date: 2026-09-16
---

**Context.** `decisions/0005`'s Alternatives section states: *"the experiment validates the protocol
(three independent stances + a merging master), not any specific trio; the chosen trio maps directly onto
`design-principles.md` ... at the cost of somewhat less built-in opposition between advisors"* — framing
the shipped trio (clean code / correct encapsulation / correct genericity) as an in-round substitution for
the plan-diversity experiment's tested stance trio (minimize moving parts / maximize extensibility /
optimize verifiability), without independent validation.

**This is inaccurate.** `experiments/plan-diversity/panel-vs-plain/` — committed in the **same patch** as
`decisions/0005` itself (commit `efcf0b7`, 2026-09-03) — is a dedicated sub-experiment that directly tests
the **shipped trio**, not the stance trio: three advisors (`advisor-clean-code.md`,
`advisor-encapsulation.md`, `advisor-genericity.md`) against a plain single-pass design, blind, two judges,
frozen rubrics. Its `results.md` found a real, judge-consistent improvement (panel ahead on every
load-bearing metric, both judges, "a real improvement, probably moderate, at n = 1"). The shipped trio was
not swapped in mid-round without evidence — it was validated directly, in the same body of work that
produced `decisions/0005`, and that evidentiary source was simply never cited in the ADR's own text.

**Decision.** Correct the record: `panel-vs-plain/results.md` is direct evidence *for* the specific
trio, not merely for the general protocol. The "somewhat less built-in opposition" caveat still stands as
a structural observation (the shipped trio's axes are less mutually adversarial by construction than the
original stance trio's), but it is not, as `decisions/0005` implied, an *un*mitigated, *un*tested cost —
it is a structural property of a trio whose own head-to-head result (panel vs. plain) was measured and
came back positive.

**Consequences.**
- `decisions/0005` itself is left unedited, per the append-only rule (`knowledge/format.md`) — this entry
  supersedes its Alternatives-section evidentiary claim, in place of a rewrite.
- No change to the panel-plan mechanism, the trio, or any convening rule — this is a correction to what
  evidence the record claims exists, not a design change.
- `experiments/plan-diversity/panel-vs-plain/results.md` should be treated as load-bearing evidence for the
  panel-plan trio in any future reading of `decisions/0005`, not skipped as if only the protocol were
  tested.

**Alternatives.**
- *Rewrite `decisions/0005` in place* — rejected: ADRs are append-only; a correction is a new entry, never
  a silent edit of the original.
