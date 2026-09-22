# Change request: reverse a settlement

Add to `Ledger`:

`reverse(settlement_id)` — undo a settlement that was previously made. The money goes back: after the
reversal, the **net effect of that settlement on the ledger is zero** for every payee.

Raise `KeyError` if the settlement id is unknown.

Money is integer cents throughout. No external dependencies.
