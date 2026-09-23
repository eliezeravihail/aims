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

**Floor by condition.** aims: 3 of 3 CLEAR (12/12 each). Unaided: 0 of 3 CLEAR — all three fail only P10.

**What P10 caught — checked before any judge ran.** Each of the six arms' plain (no-`languages`) site was built and
diffed file by file against the pristine build. For w1, w2, w3 nothing differs. For w4, w5, w6 exactly one file
differs, and every HTML page, asset and search index is identical: `messages.pot`, the theme's template for
translators, which pristine mkdocs happens to copy into every built site. The three unaided arms added their new
labels ("Language", "Languages") to that template — the step mkdocs' own translation guide asks for when a label is
added. The aims arms did not: w1 and w3 added translatable labels to the templates without adding them to the
translator template; w2 added none.

**So the floor gap is an artefact of the probe, not a difference a reader would see.** If anything, on this one
point the unaided arms did the fuller job. The frozen result stands as given — 3/3 CLEAR against 0/3 — and the
pre-registered prediction (`../DESIGN.md` §6) comes out true by its letter. It is **not** counted as evidence for
aims: it rests entirely on this one file. The probe is not changed now; a later phase that reuses it should ignore
`messages.pot`, fixed before that phase runs.
