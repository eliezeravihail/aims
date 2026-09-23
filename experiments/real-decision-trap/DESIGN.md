---
title: "real-decision-trap — does a co-located record carry a decision the code cannot show?"
date: 2026-09-23
status: frozen before any session ran; run 2026-09-23 — see results.md
---

# The question

aims' second goal: knowledge that is **not in the code** — decisions reached in discussion — is kept in a record
beside the code it is about, and a later session acts on it. design-at-scale tested this with a trap the experiment
wrote itself (goal 2: no clear advantage, `../design-at-scale/phase2/results.md`). A fair objection to that trap:
anything a session can reconstruct from the code is not a test of records. This experiment uses two **real**
decisions, each reached on GitHub by the project's maintainers and **absent from the code and its docs**, each one
that a careful contributor once broke in a real pull request.

# The two cases

| | PyTorch — `torch.utils.data` | requests |
|---|---|---|
| the checkout | PyTorch 2.14.0's `torch/utils/data/` (≈10 k lines), its test file, its docs page; the rest of PyTorch installed | requests at `611c6162` (≈6.4 k lines of source), tests, docs |
| the decision | Without a `generator`, `RandomSampler` creates a fresh generator in each `__iter__`, seeded from the global RNG at the first `next()`: users re-seed with `torch.manual_seed` before each epoch, and several iterators of one sampler must stay independent | A timeout is not `Session` state: `Session` holds HTTP concerns, transport adapters hold connection concerns, timeouts included |
| where it was decided | PRs #53085, #63026 (merged, then reverted by #63646), issue #63609, PR #65857 | issues #1130, #2011; PRs #2094, #4560, #5230 |
| absent from code and docs | `__iter__` builds the generator with no comment; the docstring says "Generator used in sampling"; open issue #49727 calls the re-creation a bug | `Session.__attrs__` simply omits `timeout`; no doc says where timeouts belong or why |
| the feature request (the card) | make `RandomSampler`'s order checkpointable — `state_dict` / `load_state_dict`, resume mid-epoch | a default timeout, set once, for every request made through a session |
| the natural wrong turn | keep the generator on `self` so its state can be saved — exactly #63026 | a `Session.timeout` merged into each request — exactly #4560 / #5230 |
| a design that respects it | a per-iteration generator whose seed/state and position are recorded for `state_dict` | the default held and applied by a transport adapter mounted on the session |

Removed from the checkouts so they do not carry the decision: PyTorch's `test_sampler_reproducibility` (the one test
that encodes it — withheld and used as the grader); requests' `.github/` and the "perpetual feature freeze"
paragraph of `docs/dev/contributing.rst` (a generic "no new features" signal). No checkout carries upstream git
history: each is a fresh repository with one commit. `build.sh` builds every checkout; `strip_test.py` withholds the
test.

# Arms — n = 3 per case

| arm | method | record |
|---|---|---|
| **A** | aims | the record(s) a separate aims session filed from the GitHub discussion (below), identical in all three A checkouts, anchored; the prompt opens with aims' session-start note, verbatim |
| **B** | aims | none (same checkout otherwise; aims' per-project layer `.aims/` installed) |
| **C** | unaided | none |

**The record is written by aims, not by the experimenter.** One aims session per case gets a fresh checkout and
`discussions/<case>.md` — the maintainers' words, quoted with links — and is asked to record what aims says should be
recorded, where aims says it belongs (`record-prompt.md`). It is not told what will be requested later. Whatever it
files is frozen and copied into every A checkout. It also answers a second question: **does aims file only what the
code cannot say?** (reported, below).

Prompts: `arm-prompt.md` (identical but for the aims lines), `record-prompt.md`. The product owner:
`hidden/oracle.md` — a session that asks about the decision gets the maintainers' answer; asking is itself
surfacing it.

# The gate — run first

C runs first in each case. **If C respects the decision in 3 of 3, that case has no live trap:** A and B are not run
for it, and that is reported. If neither case passes the gate, the experiment ends there.

# What is measured

**Primary — the decision respected in the code**, by the case's probe (`probes/`), automatic, written and validated
before any run (each probe tells a reference violation from a reference compliant implementation):

- PyTorch: respected iff the withheld upstream `test_sampler_reproducibility` passes **and** re-seeding before an
  epoch reproduces the order (with and without replacement), two interleaved iterators stay independent, and
  `DataLoader(shuffle=True)` re-seeds the same way (T0–T3).
- requests: violated iff a timeout is `Session` state: in `Session.__attrs__`, an attribute of a fresh `Session`,
  a parameter of `Session.__init__`, or read from `self` by `Session.request` / `send` /
  `merge_environment_settings` (V1–V4).

A session that pushes back and builds nothing respects the decision.

**Secondary (reported, no separate verdict):** surfaced the decision (asked the product owner about it, or its reply
states it); the floor — the feature works (PyTorch F1–F4; requests F1–F3 through a snippet written from the arm's own
summary); where the session learned it (record, tests, own reasoning — from its reply and code comments).

**The record itself (reported):** what the aims record session filed, where, and — sentence by sentence — whether
the code could have told it (the experimenter's reading, not blind).

# Verdicts — frozen

Counts are of sessions whose code respects the decision.

- **Records carry the decision (A vs B), pooled over the cases that pass the gate** (n = 3 per case per arm):
  **supported** if A ≥ ⅔ of its sessions **and** B ≤ ⅓; **falsified** if A ≤ B; otherwise **no clear advantage**.
  (Both cases: A ≥ 4 of 6 and B ≤ 2 of 6. One case: A ≥ 2 of 3 and B ≤ 1 of 3.)
- **A vs C:** the same arithmetic, reported.
- **B vs C** (aims' process without the record): reported, no claim.
- Each case is also reported on its own.

# Limits, known now

- n = 3 per arm per case, one model. Suggestive.
- The quotes were fetched through a page tool and may differ in small ways from the originals (marked in
  `discussions/`).
- No arm has upstream git history. In the real projects part of the reason sits in commit messages (PyTorch's
  revert) — a diligent session could find it there; here only A has any carrier.
- Hooks do not run inside a subagent: A's prompt carries the session-start note verbatim, as in design-at-scale;
  the read-time staleness hook is not emulated (the records are freshly anchored).
- The record session is aims reading the maintainers' words — a best case for what a record can hold. Whether a
  team would have written it at the time is not tested.

# Cost

About 20 sessions (2 record + up to 18 arms) ≈ 4–6 M tokens.
