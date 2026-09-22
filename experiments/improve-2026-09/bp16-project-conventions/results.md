---
title: "BP16 result — NULL (3/3 both arms): I wrote the conventions into the code's own docstrings"
date: 2026-09-22
---

# Result

| arm | conventions met |
|---|---|
| r1 / r2 / r3 (records) | **3/3 each** |
| n1 / n2 / n3 (no records) | **3/3 each** |

Floor checks (sum exact, 0 bps no row, preview records nothing) passed everywhere.

# Why — the confound, a third time, in a new form

The no-records arms said outright where they learned the rules:

- n1: *"`common/money.py` says all monetary arithmetic goes through it… `common/registry.py` states that an
  operation missing from `OPERATIONS` is invisible to the ops dashboard and audit exporter."*
- n3: *"learned from the files themselves."*

I wrote the conventions **into the code's own docstrings** when I built the project tree:
`common/money.py` opened with "All monetary arithmetic in this service goes through here", and
`common/registry.py` with "An operation that is missing from this table is invisible to both". The records
were therefore **redundant with the code**, and a modifier that reads the tree gets everything.

This is the same confound as I5, BP15 and BP15b, in a third costume. The pattern is now clear and worth
stating as a finding in its own right:

> **When I construct a project, I document it well — so the knowledge ends up recoverable from the code, and
> the record layer has nothing left to carry.** A record only earns its keep where the codebase is *silent*.

# Follow-up: BP16b

Identical experiment with the declarations **stripped from the code**: `common/money.py` and
`common/registry.py` keep the helper and the table but say nothing about them being mandatory, and
`refunds.py` merely *uses* `bps_of` (one module's choice, not a stated rule). The knowledge still exists in
the tree; nothing declares it binding. That is the realistic case — and the one where a record can matter.
