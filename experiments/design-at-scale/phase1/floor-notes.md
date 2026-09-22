# Phase 1 — floor results

The frozen probe (`../hidden/probes/stage1_probe.py`), unchanged from Phase 0. A failure marks the arm-stage
BLOCKED; passing earns nothing (`decisions/0021`). The floor does not enter the verdict, which is decided on
design; it is reported as given.

| arm | condition | probes | floor | change size | usage |
|---|---|---|---|---|---|
| w2 | aims | **12/12** | **CLEAR** | 9 files changed, +276 / −89, plus 3 new code/test files | 159.7 k tokens to its questions; 288.1 k reported at hand-back |

*Usage note: an arm that stops to ask and is then continued reports usage twice — once at the question, once at
hand-back. Whether the second figure includes the first is not stated by the tooling; both are recorded as given.*
| w5 | unaided | 11/12 | BLOCKED (P10) | 20 files changed, +535 / −26, plus 2 new files | 287.7 k tokens, 86 tool calls |
| w3 | aims | **12/12** | **CLEAR** | 10 files changed, +235 / −4, plus 5 new files | 162.5 k tokens to its questions; 320.9 k reported at hand-back, 75 tool calls |
| w1 | aims | **12/12** | **CLEAR** | 14 files changed, +327 / −8, plus 4 new files | 155.9 k tokens to its questions; 318.7 k reported at hand-back, 74 tool calls |
| w6 | unaided | 11/12 | BLOCKED (P10) | 20 files changed, +664 / −118, plus 5 new files | 328.2 k tokens, 121 tool calls |
| w4 | unaided | 11/12 | BLOCKED (P10) | 55 files changed, +906 / −106, plus 6 new files (32 of the changed files are theme message catalogues) | 373.0 k tokens, 115 tool calls |

**Floor by condition.** aims: 3 of 3 CLEAR (12/12 each). Unaided: 0 of 3 CLEAR — all three fail only P10, and all
three for the same reason: each edited the theme's `messages.pot` to add its new labels, so a site with no
`languages` no longer builds byte-for-byte as before. The aims arms added their labels without touching it.
