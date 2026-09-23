---
title: "BP2 — the trajectory under a WEAKER executor (same product as BP1, cheaper model)"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Why
BP1 found the trajectory edge real but non-compounding: a strong no-method model refactored its stage-2
reopen to parity. The paper's mixed-tier claim says the edge widens when the executor is **cheaper** and
does NOT refactor deeply — rot then accumulates. BP2 reruns the identical 3-stage inventory sequence
(cards + hidden tests from `../bp1-inventory/`) with **both arms on a cheaper model (haiku)**.

# Hypothesis
Under a weaker executor, the plain arm's early stored-availability shortcut (or whatever shortcut it takes)
is NOT rewritten to parity when expiry arrives — it accumulates reopens / scattered invariant across stages,
while the aims arm (its one-owner review discipline + co-located records steering fresh sessions) stays
cleaner. Predicted: reopened-owner count aims << plain, and/or a correctness gap emerging at a later stage.

# Measure (same as BP1, fixed before running)
Correctness gate (hidden `test_stage{1,2,3}.py`); reopened-owner count per arm across stages; edit locality;
blind judge on the final anonymized modules. A tie is a null (the method didn't help a weak executor here).
n=1 product; suggestive. Both arms on the SAME cheaper model, the only change from BP1.
