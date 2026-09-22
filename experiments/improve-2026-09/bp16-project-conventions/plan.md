---
title: "BP16 — the right category: PROJECT-LEVEL knowledge that is not in the file being edited"
date: 2026-09-22
status: pre-registered before any arm ran
---

# Why BP15/BP15b were the wrong category

Both documented **local behaviours of the file being edited**. A modifier asked to add a feature simply
wraps and does not touch them, so nothing was ever at risk (verified: a blind reviewer *did* flag all three
as suspicious/wrong, so they were genuinely counter-normative — the arms just never entered that code).

# The right category

Decisions that are **not in the file at all** and that the change **forces** a choice about:

| # | house rule | lives where | the natural (wrong) default |
|---|---|---|---|
| **K1** | all rate math goes through `common.money.bps_of` (guards rate range + negative amounts) | `common/money.py`, used by `payouts/refunds.py` | inline `total * bps // 10000` at the call site |
| **K2** | every public operation is registered in `common/registry.py` `OPERATIONS` | `common/registry.py` | forget it — nothing fails, the op is just invisible to the dashboard and the audit exporter |
| **K3** | a fee is **never** a synthetic payee weight; deduct before the split | nowhere in code — only the record | add `platform` to `shares` and let the allocator divide once (less code, reuses the allocator) |

The change (a platform fee + a preview entry point) **forces** all three: it cannot be done without doing
rate math, without adding a public entry point, and without deciding where the fee sits.

# Arms — identical project tree, independent agent per directory

Both arms get the **same** tree: `common/money.py`, `common/registry.py`, `payouts/payouts.py`,
`payouts/refunds.py`. The conventions are therefore **discoverable by exploring** — as in a real repo.
Only **R** additionally has the co-located records (`payouts/*.md`, `payouts/decisions/`).
6 independent agents (3 R, 3 N), blind to the experiment and to each other.

# Metrics (scoring-only probes, never shown to the arms)

- **K1** — calls `common.money.bps_of`, with no inlined `// 10000` in `payouts.py`.
- **K2** — `settle_preview` appears in `common/registry.py`.
- **K3** — the emitted platform row equals `total * bps // 10000` **exactly** in every case (a synthetic
  payee weight lets the rounding remainder land on the platform, so the fee wanders by a cent).
- Floor (not the measure): sum exact, `bps=0` adds no row, preview records nothing.

# Prediction

If records carry project knowledge the file cannot: **R complies on more conventions than N.** K2 is the
sharpest (silent omission, no failure). If N also complies, exploring the tree was enough and the record's
value is limited to what exploration misses. Nulls recorded as nulls.
