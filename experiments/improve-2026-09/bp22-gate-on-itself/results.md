---
title: "BP22 — the record gate run on aims' own session (dogfood)"
date: 2026-09-22
goal: 2 (knowledge that does not belong to the code)
---

# Setup

aims manages itself, so the filing guidance was pointed at the work this session had just done on aims.
A blind agent was given: the filing guidance; **everything this repo has already filed** (here the first
gate's "code" is the shipped guidance and the existing records); and this session's design history as
**14 unordered items** ([`input-session-material.md`](input-session-material.md)), with nothing marking
which mattered. It was told explicitly: if something is worth keeping but has no home, **leave it unfiled
and say so** — do not force it, do not invent a record kind.

# Result — 10 declined, 4 filed

**Declined (10), each because the repo already asserts it:** the rubric-leads rule and the tests-are-a-floor
rule (`decisions/0021`, `measurement.md`), `0019`'s supersession, the 43-vs-16 separation, the six
retracted record-layer experiments, the two-goals split, the 3/3-vs-0/3 result, the code-first gate itself,
its 62% / 8-of-8 / 6-of-6 measurements (`decisions/0022`), and the gate's own untested mirror risk.

**Filed (4):**

| item | where | why it survived |
|---|---|---|
| the measurement-error **pattern** — one shape, three times: the thing aims optimizes replaced by a proxy easier to observe | `goals.md` | each instance was logged; the **pattern** was nowhere |
| both shipped guidance defects had one form: **the rule was present but not where it is read** | a companion beside `design-record.md` | a file cannot assert how it is misread |
| the single-root-file alternative is **considered-but-untested**, not rejected (bp18 withdrawn) | `decisions/0023` | `0002`'s alternatives list is incomplete on this point |
| the 3/3 partly measures instruction-following; the **0/3** is the half no instruction explains | `goals.md` | a caveat qualifying a claim already made |

The third and fourth are sharper than what I had written myself: I had recorded the instruction-following
caveat as a flat threat to validity, where the filing splits it — the 3/3 is contaminated, the **0/3 is
not**, because no instruction could make a code-only arm reconcile an intent that exists nowhere in the code.

# What it found that I had not — five defects in the shipped guidance

All five verified against the repo before acting:

1. **Cross-cutting learning has no root-level home.** Insights and Discussions exist **only** at file level;
   every root record is intent, shape, dependencies, or a decision. Both root filings above were, in the
   agent's word, **smuggled** into `goals.md` — and fit only because *this* repo's `goals.md` has outgrown
   the template it ships (Primary goal / Use scenarios / Non-goals). A project following that template hits
   the gap immediately. → recorded, and the fix **deliberately deferred**, in `decisions/0024`.
2. **ADR-as-correction was practice, not rule.** `0007`, `0008`, `0010` are findings and corrections, not
   decisions; the written rule ("a system-wide decision + rejected alternatives") would have left the
   `0023` filing impossible. → now documented in `design-record.md`.
3. **The gate's "code" was undefined when the product *is* prose** — the dogfooding case `CLAUDE.md`
   declares. → now stated: the gate reads *could the file itself simply say it?*, and what survives is what
   a text cannot assert about itself.
4. **A companion for a Markdown file produces `guide.md.md`** — the anchor derivation handles it correctly,
   but nothing said so and it looks like a slip. In a Markdown product it recurs. → now documented in both
   `design-record.md` and `format.md`.
5. **ADR frontmatter was unspecified** while shipped ADRs carry `supersedes:`. → now specified, including
   that a *correcting* ADR carries none.

# Reading

**My own hypothesis was falsified, then half-restored.** I predicted three items would be homeless. The
agent placed all three without inventing a record kind — so the format is more capacious than I judged. But
it then reported that two of those placements only worked because this repo's `goals.md` is non-standard,
which restores the gap for every project that follows the template. The honest verdict is the agent's, not
my prediction and not my correction of it.

**The gate held on a hostile case.** 10 of 14 items declined as already-carried, in a repo where "the code"
is prose and the temptation to restate is at its highest. Nothing filed was a restatement.

# Limits

- One session, one filer, one repo — and the repo is the method's own author, the least independent
  possible subject.
- The 14 items were handed over as a list. A real filer derives them from its own work, where what it just
  wrote is freshest and hardest to decline.
- Five defects found is a floor, not a ceiling: nothing here searched for what the filing **missed**.
