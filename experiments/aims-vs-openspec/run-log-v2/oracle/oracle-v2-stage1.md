# Oracle log — v2 stage 1. Answers reused VERBATIM from v1 (oracle-stage1.md) to hold the product constant.

| v2 # | maps to v1 | Answer given, verbatim |
|---|---|---|
| 1 (line cost incl. share, lines sum) | O5 | "What the customer actually pays for that line: the number on the invoice. The line prices have to add up to the total." |
| 2 (BOGO qty//N vs qty//(N+1)) | O1 | "With three of them in the cart, one is free." |
| 3 (order of PCT+AMT stacking) | O2 | "Whatever order you pick, the answer has to be the same every time for the same cart." |
| 4 (duplicate codes) | O6 | "Count it once, and tell the customer it was entered twice." |
| 5a (retire: delete vs inactive) | O8 | "Take it out of the file. If someone types it, telling them we do not know that code is fine." |
| 5b (JSON vs TOML/CSV) | scripted fallback | "I don't know; choose a simple sensible technical approach." |
| 6 (rounding mode) | O7 | "It has to come out to the cent, and the same cart has to give the same answer twice." |

All identical to what the v1 arms were told. No new product facts introduced.

## Declared deviation (v2 only)
v2 did not ask about PCT-compounding (19% vs 20%) or case-sensitivity in round 1, so I volunteered both —
they are product facts every v1 arm ended up with, and the re-run measures the DESIGN output, so equal
information in matters more than identical question paths. This breaks the strict "oracle volunteers
nothing" rule for these two facts; logged rather than hidden. The wording matches v1's O3 and O13 exactly.
