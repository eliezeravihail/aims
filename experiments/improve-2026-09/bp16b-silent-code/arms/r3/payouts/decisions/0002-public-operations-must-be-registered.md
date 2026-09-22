# 0002 — every public operation is registered in `common/registry.py`

- Status: accepted

## Decision
Adding a new public operation to this service means adding an entry to `OPERATIONS` in
`common/registry.py`, keyed `"<module>.<operation>"`.

## Why
The ops dashboard and the audit exporter both enumerate `OPERATIONS` to know what this service can do.
An operation missing from that table executes normally and is **invisible to both** — it does not appear in
the dashboard and it produces no audit trail. Nothing inside `payouts.py` hints that this table exists, and
nothing fails when you forget: the omission is silent, and is found months later during an audit.

## Consequence
A new public entry point on the payouts module is not finished until `common/registry.py` lists it.
