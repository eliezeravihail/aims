# HIDDEN corner probes — P1 shipping (frozen before any arm ran; arms never see this)

Each probe is a **representability fact about the delivered type model**, scored blind yes/no:
"can the arm's chosen types hold this input value and produce the required output *without* a type change?"
This is not a rubric grade — it is whether the value is expressible.

| # | corner (which X × R) | concrete value | required output | representable iff the design… |
|---|---|---|---|---|
| H1 | R3 boundary exact | actual 2.000 kg, zone A | one unambiguous tier (design must **state** which side 2.0 falls; boundary is defined, not left to a float `<`/`≤` accident) | brackets carry an explicit inclusive/exclusive boundary convention, not two bare floats compared ad hoc |
| H2 | X1 × R3 spanning range | scale reads **1.9–2.1 kg**, zone A | billed at the **max 2.1** → tier `2–5kg` | the weight value can be a **range**, and billing reads its max; a single `float` weight cannot hold this |
| H3 | X1 single as degenerate | scale reads exactly **2.0 kg** (a point) under the same model as H2 | same as a range `[2.0,2.0]`; no second code path | a point is expressible as (or unified with) the range type — one representation, not a `float | Range` tag with a branch |
| H4 | R2 dimensional > actual | actual 0.5 kg, dims 40×40×40 cm → dim wt = 12.8 kg | billable 12.8 → tier `5kg+` | billable weight is a computed value distinct from the reported reading; the type carries both actual and dimensional, not one scalar |
| H5 | R1/R3 zero | actual 0.0 kg | lowest tier `0–1kg` = base × multiplier, **not** an error | zero is a valid weight in the lowest bracket, not rejected as invalid |
| H6 | X3 × R1 surcharge | zone C carries a $3 surcharge; 3.0 kg | `(12 × mult) + 3.00` — surcharge is additive after bracketing, its own owner | price is composed (bracket → multiplier → surcharge) so a surcharge slots in without reopening the bracket rule |

**Scoring.** Score = # of H1–H6 the delivered design's **types can represent** (a fresh reader can point to
the type/constructor that holds the value and yields the output). H2/H3 are the range corners; H1 the
boundary corner; H4 the compound-value corner; H6 the composition corner. A design that models weight as a
bare `float` and price as a single formula fails H2, H3, and likely H1 and H4.
