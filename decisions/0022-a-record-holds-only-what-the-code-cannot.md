---
title: "a record holds only what the code cannot; the filing decision gates on placement first"
date: 2026-09-22
---

**Context.** aims' second goal is **knowledge that does not belong to the code** (`goals.md`). The filing
guidance did not enforce the "does not belong to the code" part. `design-record.md` asked *which home*
(companion vs root record) and *whether it is durable*, but never *should this be in the code instead*.
Its only nearby clause — "if the code and its own documentation already carry it, do not file it" — is a
**redundancy** test (is it already there), not a **placement** test (should it be there), and it sat in the
last section rather than first.

Observed failing instance, from aims' own output: in
`experiments/improve-2026-09/bp19-aims-filed-records/`, where the real skill filed the records, the
companion `flags.py.md` states *"the product rule is an ordering over the verdicts that apply… nothing
answered, so it is off"* and *"the instant is a parameter… one call is answered as of a single moment"* —
while `Resolver.is_enabled`'s own docstring already says *"The strongest verdict among the rules that
apply decides it. A flag no rule speaks about is off"* and *"it is read once here and handed to every
rule, so one call answers as of one instant."* The same facts, filed twice. The guidance permitted it.

**Why it matters, specifically.** A record that restates the design is **duplicate state**, and it is the
only part of a record that can go wrong *on its own*: the code changes, the restatement becomes false, and
the anchor + staleness hook only **flag** the drift — nothing repairs it. Knowledge the code cannot hold
has no such failure mode, because nothing else asserts it. So restatement is not merely verbose; it is the
one thing in the record layer that manufactures the exact problem the layer exists to avoid.

**Decision.** The filing decision gates on **placement first**. `design-record.md` gains a *First gate* —
before which home, ask whether the code should carry it at all:

| if it is… | it belongs in… |
|---|---|
| what the code does now | the docstring |
| why *this line* is surprising | a comment right there |
| an invariant you can make unbreakable | the signature, the type, a private field, a guard |
| a behaviour worth guaranteeing | a test |
| a concept | a name |

Only what survives is a record, and all of it shares one property — **nothing in the code asserts it**:
a rejected alternative, a non-goal or deliberate boundary, a failed attempt and its symptom, an unproven
assumption, the now-vanished context of a decision, the history of a superseded one.

The one-line test: **if you could delete the entry, write it as a docstring, and lose nothing, it was a
docstring.**

**Consequence.** `references/design-record.md` — new *First gate* section, "the split, sharply" now leads
with it, and the three section descriptions say what they are *not* for. `SKILL.md` — three record rules
become four, with this as rule 1. `knowledge/format.md` — the pointer now carries the gate, and the
companion example was rewritten so it no longer models restatement (it previously recorded "render must
not know how the maze was generated (it takes a finished maze)", which the signature carries).
`assets/record-templates.md` — the gate precedes the skeletons: an empty section is not a prompt to fill it.

**Status of the evidence — tested.** `experiments/improve-2026-09/bp21-code-first-gate/`, against a clean
control (the companion the real skill filed for this same module *before* the gate existed):

- **The gap is real, blind.** An auditor given only the code and two anonymized candidate documents rated
  **8 of the old companion's 13 entries (62%) RECOVERABLE**, each with a `file:line` quote — the fact was
  already in a docstring or pinned by a test.
- **The gate removes them without losing the rest.** With the *full* design history handed to it as one
  undifferentiated list of 14 items, the arm dropped **8/8** code-carried items and kept **6/6** the code
  cannot hold — matching a prediction registered before it ran (`bp21-…/run2/PREREGISTERED.md`), which was
  stated to *fail* if the rejected alternatives or the unproven assumptions were also dropped.
- **Convergent, from outside.** The blind auditor — before that run existed, not knowing of this gate —
  wrote that the ideal document would be "X's entries 9–13 plus Y's single entry — six bullets, no
  restatement". That is exactly what the gate produced.

n = 1 product. The untested risk is the mirror one: a gate read as "file less" could suppress a rejected
alternative nobody wrote down. Run 2 had them spelled out in its input; an agent that must *remember* them
is the next test.
