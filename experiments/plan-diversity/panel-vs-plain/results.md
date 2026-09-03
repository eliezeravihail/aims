# Results — panel-plan vs plain aims planning (blind, two judges, frozen rubrics)

**Question.** Does the panel-plan mechanism just designed (three axis advisors — clean code / correct
encapsulation / correct genericity — planning independently under the same design-as-goal framing, then a
master planner harvesting strengths into a best-of-all-three composition) produce a **better design** than
a regular single aims plan pass? Same frozen brief (the "responsible doctor" MVP), same generator model for
every pass (Fable), so the only variable is the protocol. Judged blind on the judges' previously frozen
rubrics. *(The planned Opus judge was unavailable — API overloaded on three attempts — and was substituted
by Fable-on-its-frozen-rubric; with both contestants Fable-generated, lineage bias is symmetric and cancels
between them.)*

## Un-blinding and totals

| Blind | Arm | Sonnet /40 | Fable /40 |
|---|---|:-:|:-:|
| design-R | **Panel** (3 advisors → master composition) | **39** | **40** |
| design-S | **Plain** (single aims design pass) | 38 | 35 |

## Per-metric picture

- **Sonnet:** near-tie — level on the load-bearing M1/M3/M4; R leads M2 and M6 (S carries a dead
  "for later" `relation` enum on its Grant); S leads M5 (tighter single-module source extension). Verdict:
  R edges by 1 — "two small, opposite-direction structural choices, not a gap in rigor."
- **Fable:** R leads 5 of 8, level on the rest, behind on none. The decisive readings are load-bearing:
  S leaves its `covered()` matching rule **undefined**, and doctor instructions **never become expected
  items** in S — while R has directive-sourced expectations and an owner-defined NO_PLAN coverage rule;
  S's parallel `SourceClass`/`kind` enums break one-owner source addition. Verdict: R clearly stronger
  (40–35).

## Reading — is there an improvement?

1. **Direction: yes, consistently.** Both judges put the panel arm ahead; on no metric except Sonnet's M5
   was the plain arm ahead, and the panel never trailed on a load-bearing axis.
2. **Magnitude: judge-dependent — modest to clear.** Sonnet's +1 sits inside the ±1 judge-noise band
   measured earlier; Fable's +5 is well outside it and rests on named structural defects in the plain
   design (an undefined matching rule; an unwired instruction→expected path; a broken one-owner change).
   Honest summary: **a real improvement, probably moderate,** at n = 1 objective.
3. **The wins match the mechanism.** Where R beat S is exactly where the axes pulled: the
   directive-to-expectation wiring (the genericity advisor's floor/ceiling move), the closed code registry
   (clean code), explicit one-place ownership and no dead fields (encapsulation). S's defects — a "for
   later" label, an undefined rule — are precisely what a single pass ships and an adversarial pull
   catches. The composition also carried three honest **gap notes** the single pass never surfaced.
4. **Secondary finding — the aims framing itself does heavy lifting.** Today's plain-aims single pass
   (design-as-goal + design-principles) scored 38/40 with Sonnet, versus 34/40 for the earlier
   principle-less baseline on the same brief and rubric. The panel's gain sits **on top of** an already
   strong single pass — which is consistent with the convening decision to spend it on opening rounds
   only.
5. **Cost.** 4 passes + composition vs 1 pass. The measured gain justifies it where the design is
   load-bearing (an opening round); it would not justify it per ordinary round — matching `decisions/0005`.

## Caveats

n = 1 objective, one generator model; the Opus judge is missing (substituted, with the symmetric-lineage
argument above); the brief is one both arms' model family has now seen many times in this experiment line —
a fresh objective is the next discriminating step.

*Artifacts: `arms/aims-plain/design.md`, `arms/panel/{advisor-*,final,harvest}.md`,
`judge/scores-{sonnet,fable}.md`, `judge/mapping-SECRET.md`.*
