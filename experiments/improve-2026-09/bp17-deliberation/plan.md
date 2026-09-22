---
title: "BP17 — the only thing a record can carry: the DELIBERATION (why A and not B)"
date: 2026-09-22
status: pre-registered before any arm ran
---

# What four nulls taught

I5, BP15, BP15b, BP16, BP16b all tested **rules/conventions** — and a rule is always recoverable (from the
code, a docstring, or one usage example). Records are genuinely redundant there; good documentation replaces
them. What nothing else can carry is **the deliberation**: *why A and not B* — what was weighed, what was
rejected, and on what grounds. That leaves **no trace in the code by construction**, and documentation does
not capture it either, because it is a history, not a usage rule. It is exactly what an agent present in the
deciding session knows and a blind agent cannot.

# The fork

`Ledger` records settlements. **Nothing about undoing one exists yet.** The change asks for `reverse(id)`.
Two designs, **both defensible**, no rule in the code favouring either:

- **(A) mutate the original** — zero it, drop it, or flag it `reversed`. Less state; `get(id)` stays the
  whole truth. *This is what a reasonable engineer reaches for first.*
- **(B) append a linked reversal** — leave the original untouched, add an opposing entry. More entries;
  `get(id)` no longer self-contained.

The project settled on **(B)**, and the deciding argument is **entirely outside this module**: the audit
exporter streams `entries()` as an append-only outward feed, so mutating an already-exported entry rewrites
history downstream irreparably; and finance reconciles a reversal as its own line against a bank statement
showing two movements. Neither fact is inferable from `payouts.py`.

# Arms

Identical code for both. **R** additionally has `payouts/payouts.py.md` + `decisions/0001` carrying the
deliberation. **N** gets code only. 3 independent agents each, blind to the experiment.

# Metric — coherence with the settled direction, not rule-compliance

Scoring-only probe (never shown to the arms): after `reverse("s1")` —
1. the original entry is still present, 2. byte-identical (amounts untouched), 3. the ledger **grew** (a new
entry was appended), 4. no status/flag was smuggled onto the original. Score /4.
Floor (not the measure): the net effect per payee is zero.

# Prediction

N implements (A) at least sometimes — it is the simpler, natural design and nothing in the code argues
against it. R implements (B), citing the deliberation. If N also appends, then the append-only shape was
inferable from the code after all (a list + frozen entries) and the confound returns — which would be
recorded as such.
