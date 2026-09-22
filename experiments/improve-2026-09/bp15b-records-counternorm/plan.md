---
title: "BP15b — the valid record-layer test: COUNTER-NORMATIVE decisions a competent modifier would 'fix'"
date: 2026-09-22
status: pre-registered before any arm ran
---

# Why BP15 was invalid

BP15 documented three decisions that turned out to be **accepted norms of the field** (idempotency-key replay,
deterministic tie-break, don't-drop-rows). The no-records arm preserved all of them by professional instinct:
4/4 in both arms. A record can only be load-bearing where the competent default points **the other way**.

# The fix: three decisions AGAINST the norm, where the code looks like a defect

| # | decision | the code reads as | rationale that lives only in the record |
|---|---|---|---|
| C1 | a repeat settlement **recomputes and overwrites** | a forgotten idempotency guard (a store written but never read) | upstream issues corrections under the same id; the downstream ledger is append-only, latest-wins |
| C2 | the **whole remainder goes to the largest-share payee** | a systematic fairness bug | the partner agreement makes the lead partner the residual party |
| C3 | **zero-amount rows are dropped** | silent data loss | the payment rail rejects a zero-amount transfer and fails the whole batch |

Each is the choice a good engineer would "fix" on sight. Each ADR names the incident the instinctive fix caused.

# The change (identical for both arms)

Platform fee (deducted before the split, emitted as a `"platform"` row, sum still exact) + `settle_preview`
that records nothing. It forces contact with all three: the fee changes the remainder (C2), pushes payees to
zero (C3), and a preview invites "fixing" the store path (C1).

# Arms — **independent agent per directory** (BP15's flaw: one agent emitted identical output 3x)

- **R:** 3 agents, each one directory, code **+ records**.
- **N:** 3 agents, each one directory, code only.
Blind to the experiment, to each other, and to aims.

# Metrics
1. **Decision survival (primary)** — the scoring-only probes (C1/C2/C3 + sum invariant), never shown to arms.
2. **Design quality (§0–§14), blind** — the correct design measure.

# Prediction
If records carry knowledge the code cannot: **N breaks C1/C2/C3** (it "fixes" them) while **R preserves them**.
If N also preserves them, a careful modifier simply does not touch what it was not asked to touch — and the
records' value lies elsewhere (e.g. the structural quality of the *new* code, as BP15's addendum found).
Nulls recorded as nulls.
