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
