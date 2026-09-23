---
title: "real-decision-trap — with the record, 3 of 3 kept a real maintainers' decision; without it, 0 of 6"
date: 2026-09-23
---

# Result

**requests — records carry the decision: supported**, by the rule frozen in `DESIGN.md` before any session ran
(one case passed the gate, so A ≥ 2 of 3 **and** B ≤ 1 of 3):

| arm | kept the decision (probe) | surfaced it | the feature works (floor) | what it built |
|---|---|---|---|---|
| **A** — aims + the record | **3 of 3** | 3 of 3 — each stopped and named the conflict, citing the record | 3 of 3 | a default on the transport adapter (`HTTPAdapter(timeout=…)`), `Session` untouched |
| **B** — aims, no record | 0 of 3 | 0 of 3 | 3 of 3 | `Session.timeout` |
| **C** — unaided | 0 of 3 | 0 of 3 | 3 of 3 | `Session.timeout` |

A vs C, the same arithmetic: supported. B vs C (aims' process without the record): no difference — 0 and 0.

**PyTorch — stopped at the gate.** All three unaided sessions kept the decision without any record (probe: 3 of 3
respected, 3 of 3 floor clear), so by the frozen gate the case had no live trap and A and B were not run. It tells
nothing about records either way.

# What happened, requests

The decision (maintainers, 2013–2022): a timeout is not `Session` state — `Session` holds HTTP concerns, transport
adapters hold connection concerns. Nothing in the code or docs says so; `Session.__attrs__` simply leaves `timeout`
out, beside `stream`, `verify` and `cert`, which invites adding it.

- **Every A session** read `src/requests/sessions.py.md` (the record aims filed from the discussion), checked it was
  current, and stopped before building: the request "directly contradicts" / "would go against" / "rules out exactly
  what was asked for" a standing decision. Each offered two ways — override the decision, or meet the need on the
  transport adapter — and leaned to the second. The product owner answered with the maintainers' position; all
  three built the default on `HTTPAdapter`, left `sessions.py` unchanged, and appended to the record that the
  decision was reaffirmed (`oracle-log.md`, `replies/`, `diffs/`).
- **Every B and C session** added `Session.timeout`, merged in `Session.send` — the change the maintainers
  rejected in #4560 and #5230. The three B sessions stopped to ask a product question (no C session asked anything) — each
  about what an explicit `timeout=None` should mean — none about whether `Session` should hold a timeout at all.
  The three B sessions each filed a companion `sessions.py.md` recording their own `None` choice: aims' process ran;
  what it had no way to know was the decision.
- The probe and a reading of every diff agree on all nine classifications.

# What happened, PyTorch

The decision (maintainers, 2021): without a `generator`, each `__iter__` creates its own generator, seeded from the
global RNG — so `torch.manual_seed` before an epoch reproduces its order, and iterators of one sampler stay
independent. A contributor once broke it by keeping the generator on `self` (#63026, merged, then reverted).

All three unaided sessions built the checkpoint the other way: they kept the per-iteration generator and saved its
state (or seed) and position for `state_dict`. None mentioned re-seeding or concurrent iterators; the existing code
already put the generator inside `__iter__`, and each extended that shape. Two stopped to ask about DataLoader
workers prefetching ahead (a real gap in the card, not the decision); one asked the same after building. The
upstream grader test (withheld) passes on all three.

**What this says about the trap, not about records:** a decision whose violation the current code's own shape
steers you away from is not a test of records. The requests decision is different: the code's shape — `stream`,
`verify`, `cert` all on `Session` — steers you *into* the violation.

# The records aims filed

One aims session per case read the maintainers' discussion (`discussions/`) and filed exactly one companion beside
the file the decision is about (`records/`), anchored, with no code changed:

- **requests → `src/requests/sessions.py.md`.** A Decisions entry (no `Session` timeout; what that rules out; the
  maintainers' reason; its scope, 2.x) and a Discussions entry (the maintainers' claim of an earlier session
  timeout, marked unverified). One caveat it added *from the code*: `HTTPAdapter` stores no default either — true,
  and useful to the A sessions, which all three built exactly that.
- **PyTorch → `torch/utils/data/sampler.py.md`.** Insights (the merge and the revert, why a per-`__iter__` attribute
  also fails, that no test guards either property), a Decisions entry (a per-iteration generator; what it rules
  out), and Discussions (the cost — a paused epoch cannot be resumed from the sampler — and that the follow-up was
  never rejected on its merits).

**Does it hold only what the code cannot say** (the experimenter's reading, not blind)? The requests record: every
sentence but the adapter caveat is from the discussion; the caveat is code-derivable and flagged as a check. The
PyTorch record: all from the discussion, except "no test guards either property" — code-derivable, and true here
only because this checkout withholds the test that does (`DESIGN.md`).

# Limits

- **One case decided the verdict**, n = 3 per arm, one model. The effect is as large as n = 3 allows (3 of 3 against
  0 of 6), but it is one decision in one codebase.
- **The record was written by aims from the maintainers' own words** — a best case for what a record can hold. It
  does not show a team would have written it at the time.
- **The product owner answered with the decision** once asked. The primary measure is the code; the A sessions
  earned the answer by asking about the decision, which only the record told them to.
- **No arm had upstream history, `.github/`, or the "feature freeze" paragraph**, by design (`DESIGN.md`); in the real
  repository a diligent session might find the refusals there.
- **The PyTorch case shows a limit of this kind of test**, not of records: a trap must be one the code invites.

# Cost

Arm and record sessions ≈ 1.54 M tokens (from the subagent usage reports): records 74 k + 77 k; requests A 135 k,
130 k, 151 k; B 124 k, 135 k, 131 k; C 72 k, 73 k, 77 k; PyTorch C 138 k, 129 k, 97 k. The A sessions cost about as
much as B; both about 1.8× the unaided sessions.
