---
title: "BP18 — does a SINGLE root decisions file deliver the records' only proven benefit, without the machinery?"
date: 2026-09-22
status: pre-registered before arm C ran
---

# The proposal under test

Six nulls (I5, BP15, BP15b, BP16, BP16b, BP17) show that a record does **not** change which decision a blind
modifier reaches — the code's conventions, documentation and shape already encode that. The **one** positive
signal in the whole arc is BP15b's blind design-quality read: the records arm produced structurally better
*new code* (mean 33.3 vs 29.0 /40; worst case 30 vs 20).

If the genuinely-unrecoverable cases are as rare as six failed attempts suggest, then a per-file companion
beside every source file — plus the anchoring tool and the staleness hook — is enormous machinery for content
that almost never exists. The proposal: **one `DECISIONS.md` at the project root**, holding only deliberations
the code and its own documentation cannot convey.

# Design — a direct three-way comparison on identical ground

Same product, same change request, same probes, same rubric as BP15b, so two arms already exist:

| arm | what it carries | source |
|---|---|---|
| **A** none | code only | BP15b `n1/n2/n3` — measured **29.0** mean (worst 20) |
| **B** per-file | companion + architecture + goals + 3 ADRs (**142 lines, 6 files**) — today's aims | BP15b `r1/r2/r3` — measured **33.3** mean (worst 30) |
| **C** single root | the same three deliberations in one **49-line** `DECISIONS.md` | **this round** |

3 independent agents for C, blind to the experiment. Then a blind judge scores all **nine** modules on the
design rubric in one shuffled pass.

# Metrics
- **Design quality (primary)** — blind rubric score /40, the correct measure (`decisions/0021`).
- **Decision survival (floor)** — the same scoring probes; expected 4/4 everywhere, as in BP15b.
- **Cost of the instrument** — 49 lines / 1 file vs 142 lines / 6 files + anchor tool + staleness hook.

# Prediction
If **C ≈ B > A**, the proposal is validated: the same floor-raising at a third of the content and none of the
per-file machinery — a subtractive win by aims' own §7. If **C ≈ A < B**, co-location per file is doing real
work that a root file cannot, and the machinery is earning its keep. Either is a clean answer.
