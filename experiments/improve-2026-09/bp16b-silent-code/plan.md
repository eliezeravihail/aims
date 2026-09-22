---
title: "BP16b — same conventions, but the code no longer declares them"
date: 2026-09-22
status: pre-registered before any arm ran
---

BP16 was null because the project tree's own docstrings stated the conventions ("all monetary arithmetic goes
through here"; "an operation missing from this table is invisible"). The no-records arms read them and
complied. Records were redundant with the code.

BP16b strips exactly that: `common/money.py` is `"""Money helpers."""` and `common/registry.py` is
`"""Operation names."""`. The helper and the registry still exist; `payouts/refunds.py` still *uses* `bps_of`
— but as one module's choice, not a declared rule. Nothing states that inlining rate math is forbidden, that
a new operation must be registered, or that a fee must not be a synthetic payee weight.

Everything else is unchanged: identical tree for both arms, records only for R, same change request, same
scoring probes (K1 house helper / K2 registered / K3 fee exact), independent agent per directory.

**Prediction:** N now has no statement of the rules. K2 is the sharpest — nothing fails if you skip it.
Expect N to inline the rate math or skip registration at least sometimes; R to comply. If N still complies
3/3, then inference from one usage example is enough and the record adds nothing even in a silent codebase.
