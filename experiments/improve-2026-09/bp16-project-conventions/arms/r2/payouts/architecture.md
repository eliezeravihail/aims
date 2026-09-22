# Architecture — payouts service

`payouts/payouts.py` splits a settled total across payees. `payouts/refunds.py` issues refunds.
Shared money arithmetic lives in `common/money.py`. The service's public surface is enumerated in
`common/registry.py`.

House rules that are **not visible from inside `payouts.py`** and that every change here must follow:
see `decisions/`.
