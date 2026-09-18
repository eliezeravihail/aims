# Frozen Step-0 inventory (R / X / C) — identical for every arm and the judge

## Rules (R)
- R1 an event fires a rule iff metric name, host, and value-predicate all match.
- R2 threshold predicates: `>`, `>=`, `<`, `<=` on a numeric bound.
- R3 return every fired rule for an event, deterministically.

## Change-axes (X) — STATED capabilities, present forces
- X1 host match may be a single host OR a set of hosts.
- X2 a value predicate may be a single bound OR an inclusive BAND `[lo, hi]`.
- X3 an event value may be a single reading OR an aggregated RANGE `min–max`; a threshold matches a range by
  its max, a band matches a range by INCLUSIVE OVERLAP. (This is the input-space corner §1 must trace: a
  ranged event value is unrepresentable in a single-scalar model, and a band-vs-range match is not
  `contains(point)`.)

## Correctness cases (C)
- C1 single value vs single bound (stage-1 behaviour preserved exactly).
- C2 event value "72–88" vs band [80,95] → fires (overlap).
- C3 event value "72–88" vs band [90,99] → does not fire (no overlap).
- C4 event value "72–88" vs threshold ">85" → fires (max 88 > 85).
- C5 host in a set; a single host is the degenerate set {h}.
