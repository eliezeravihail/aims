---
title: "[WITHDRAWN] BP16b result — NULL again (3/3 both arms): one usage example is enough to infer a convention"
date: 2026-09-22
status: WITHDRAWN — the records in this run were written by hand, not filed by aims, so it tested that construction rather than aims (AUDIT-record-layer-claims.md).
---

Conventions stripped from the code's docstrings. Still **3/3 in both arms**.

The no-records arms inferred the rules from a single instance:
- n2: *"learned from reading the four files in the repo: `payouts/refunds.py` already imports its rate math
  from `common.money`… `common/registry.py` is the operations catalogue, so I registered
  `payouts.settle_preview`."*
- n3: same — `refunds.py` as the worked example, the registry's shape as the instruction.

# The convergent finding across I5, BP15, BP15b, BP16, BP16b

Four attempts, four nulls, three different confounds — and they converge on one conclusion:

> **A convention or a rule is always recoverable.** From the code, from a docstring, or from one usage
> example. Records are genuinely **redundant** for that class of knowledge, and good documentation replaces
> them.

What a record can carry that nothing else can is **the deliberation**: *why A and not B* — what was weighed
and rejected, and on what grounds. That knowledge leaves **no trace in the code by construction** (the code
shows only the outcome), and good documentation does not capture it either, because it is not a usage rule —
it is a history. It is precisely what an agent who was present in the session that decided it knows, and a
blind agent cannot.

That reframes the measurement too: not *"did it comply with a rule"* (documentation teaches that), but
**"did it re-open a settled question and introduce a second, competing direction?"** The cost of losing the
record is **incoherence**, not rule-violation. BP17 tests that.
