# BP5 stage-by-stage log

## Stage 1 — post / balance (single currency)
- Correctness: aims 5/5, plain 5/5.
- Structure (the divergence to watch):
  - **aims:** a single **flat append-only journal** `list[Posting(id, account, amount)]`; balance derived by
    filtering. Its review explicitly **rejected a per-account index and a stored total** (§5/§7: second
    sources of truth). The flat journal carries posting **id**, so void-by-id (stage 4) is a natural lookup.
  - **plain:** `dict[account -> list[(id, amount)]]`; balance derived by summing the account's list. Good
    (derived, not stored) but **keyed by account, not id** — so void-by-id (stage 4) has no direct lookup.
- Prediction: currency (s2) and as-of (s3) are additive for both (add a field, filter). The divergence, if
  any, is **stage 4 void-by-id**: aims' flat id-bearing journal absorbs it; the plain account-keyed structure
  may need an index or restructure (a reopen).

## Stages 3 & 4 + totals
- Stage 3 (as-of-time): aims 10/10, plain 10/10 — both EXTENDED (added `at`, one filter clause), 0 reopens.
- Stage 4 (void): aims 13/13, plain 13/13 — both added a `_voided: set[str]` + a `id not in _voided` filter
  clause. **Identical approach. 0 reopens.** (My prediction that the plain arm's account-keyed storage would
  force a void-by-id reopen was WRONG: void needs no storage lookup — a voided-set filter, which balance's
  scan already respects, absorbs it.)

## BP5 totals
| | correctness (all 4 stages) | reopened-owner events | module lines s1/s2/s3/s4 |
|---|---|---|---|
| aims | 13/13 ✓ | **0** | 46 / 61 / 76 / 96 |
| plain | 13/13 ✓ | **0** | 39 / 53 / 61 / 75 |

**No compounding. No divergence.** Both arms chose a derive-by-scanning posting journal at stage 1, and that
design makes every one of the four breaks (currency, time, void) a single filter clause — nothing ever
reopened. The predicted stage-4 divergence did not occur.
