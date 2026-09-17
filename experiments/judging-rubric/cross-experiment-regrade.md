---
title: "Cross-experiment re-grade under the unified principles"
date: 2026-09-17
---

# Cross-experiment re-grade

Blind, neutral grades of the experiments' design/code outputs under the single source
([`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md)
§1–§18) with the scoring layer in [`quality-metrics.md`](quality-metrics.md) and a fixed Step-0 inventory per
product. One neutral judge per product; labels shuffled and method names stripped.

## Checkout pricing (5 designs) — detail in [`regrade-results.md`](regrade-results.md)

| design | grade | capped by |
|---|---|---|
| OpenSpec | 3.94 | — |
| plain | 3.89 | — |
| aims-old | 3.0 | S3 (tax cram) |
| aims single-pass (corrected principles) | 3.0 | S3 (OCP) |
| aims panel-upgraded | 2.0 | **S4 (no cart-discount→line allocation)** |

Building single-pass to the corrected §13 (correctness, with a full-space trace) removed the panel's S4
(2.0 → 3.0). aims ties aims-old, below OpenSpec/plain, capped by an OCP gap.

## Marketplace, furniture + cars (3 designs) — inventory [`marketplace-spec-inventory.md`](marketplace-spec-inventory.md)

| design | grade | worst | note |
|---|---|---|---|
| **aims** | **3.5** | 3 | designed plugin seams (`Transport <: Fulfillment`, `FeePolicy`, domain-typed port, VOs) score §2/§4 by construction |
| OpenSpec | 3.45 | 3 | logistics rendered as a method-typed switch (§2=3); no VO/interface basis |
| plain | 3.29 | 2 (§6) | reopens the purchase-saga orchestrator to weave in the inspection gate |

All three S2-capped, no S3/S4 — narrow gaps. aims first: its seams were designed for the extension; the
others widened or reopened. (plain's §6 is borderline S3; scoring it S3 widens but does not change the order.)

## Ledger continuation (2 implementations, code) — from `../continued-development/`

| impl | grade | note |
|---|---|---|
| capsule-aware (prior-knowledge record) | 4.0 | named `Statement{account, entries, closing_balance}` type |
| blind | 3.5 | S2 — `statement` returns a bare positional `tuple[list, int]` (data clump) |

Both preserve the load-bearing invariant (memoize the derivation, invalidate on post; no stored balance
field), so they tie on §9/§13; the capsule-aware arm edges ahead only on a named return type.

## Cross-product reading

aims' rank is **product-dependent**: **last** on checkout (its lean, change-local instinct left a
correctness gap the panel version failed outright, and an OCP ceiling in single-pass), **first** on the
marketplace (its pre-built plugin seams absorbed the change as extensions where the others widened or
reopened), a **small edge** on the ledger. No single product is a verdict on the method. Every reading is
**n = 1**, judged by an LLM against a fixed inventory; the value is in the sequence, not any one grade.
