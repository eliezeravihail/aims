# Phase 2 — floor results

The frozen probes (`../hidden/probes/`). A failure marks the arm-stage BLOCKED; passing earns nothing
(`decisions/0021`). The floor enters no verdict; it is reported as given.

## Stage 2 — `stage1_probe.py` (regression) and `stage2_probe.py`

| arm | stage-1 probes | stage-2 probes | floor | INFO | change size | usage |
|---|---|---|---|---|---|---|
| c1 | stage-1 12/12 | 6/8 — D1n, D2n fail: a one-off `build --dirty` rebuilds every page | BLOCKED | dirty output exact in D1–D5 (search index too); D6 `serve --dirty` correct; D7 single-language unchanged | 5 files, +470 / −14, 1 new | 231.9 k tokens, 68 tool calls |
| b3 | stage-1 12/12 | 6/8 — D1n, D2n fail: a one-off `build --dirty` rebuilds every page | BLOCKED | dirty output exact in D1–D5 (search index too); D6 correct; D7 unchanged. Minimal rebuilding lives in `serve` only, which D1n/D2n do not measure | 4 files, +131 / −21, plus 3 new code/test files and a companion | 256.2 k tokens at hand-back, 64 tool calls |

*The rows above were measured with the stage-2 probe as frozen. They are superseded by the final table below, which
re-runs all nine arms with the one corrected probe.*

### Correction to `stage2_probe.py`, made after the first stage-2 results — disclosed

**What happened.** a2 failed D1n/D2n ("does not rebuild pages the edit cannot affect") on exactly four pages:
`index.html`, `en/`, `fr/`, `he/index.html`. Diffing each before and after the `--dirty` build: the only changed line
is `Build Date UTC : …` — the built-in theme stamps the build time on every home page. The probe's equality check
masks that line (a full build is compared with it masked), but its rebuild count did not: an arm that keeps its
output byte-for-byte equal to a fresh full build must rewrite the home pages, and was counted as over-rebuilding;
an arm that leaves them stale passed. The probe contradicted itself.

**The correction.** A page rewritten only to carry a new build date is not counted as rebuilt — the same line the
equality check masks. A page rewritten with identical bytes still counts. The pages excluded this way are listed
as INFO for every arm, so the uncorrected result can be read off.

**Its effect, stated plainly:** it was found after seeing results. Measured on all nine (table below), it turns two
arms from BLOCKED to CLEAR — **a2 (aims) and c3 (unaided)** — and changes no other arm's result. The floor enters no
verdict.

## Stage 2 — final floor, all nine arms, one probe version

Measured on the frozen snapshots (`s2/<arm>`), with `stage1_probe.py` (regression) and the corrected `stage2_probe.py`.

| arm | condition | stage-1 regression | stage-2 probes | floor | without the build-date correction | minimal when the first build is also `--dirty` (INFO) | usage at hand-back |
|---|---|---|---|---|---|---|---|
| a1 | A | 12/12 | 6/8 — D1n, D2n | BLOCKED | same | **yes** — its record of the last build is kept only by `--dirty` builds | 148.3 k to its questions; 410.3 k after (38 tool calls) |
| a2 | A | 12/12 | **8/8** | **CLEAR** | BLOCKED (home pages, date only) | — | 135.8 k to its question; 304.8 k after (79) |
| a3 | A | 12/12 | **8/8** | **CLEAR** | CLEAR | — | 143.7 k to its questions; 328.8 k after (83) |
| b1 | B | 12/12 | 7/8 — D1n | BLOCKED | same | no | 164.2 k to its questions; 342.4 k after (95) |
| b2 | B | 12/12 | 6/8 — D1n, D2n | BLOCKED | same | no | 151.4 k to its questions; 323.9 k after (94) |
| b3 | B | 12/12 | 6/8 — D1n, D2n | BLOCKED | same | no | 144.7 k to its questions; 256.2 k after (64) |
| c1 | C | 12/12 | 6/8 — D1n, D2n | BLOCKED | same | no | 231.9 k (68) |
| c2 | C | 12/12 | 6/8 — D1n, D2n | BLOCKED | same | **yes** — its record is kept only once a `--dirty` build has run | 109.4 k to its questions; 401.1 k after (142) |
| c3 | C | 12/12 | **8/8** | **CLEAR** | BLOCKED (home pages, date only) | — | 362.4 k (106) |

**Every arm's `--dirty` output equals a full build** in all five edit scenarios (D1–D5), and `serve --dirty` is correct
(D6) in all nine. Every failure is the same one: rebuilding pages an edit cannot affect, in a one-off `build --dirty`
after a plain build. D7 (single-language `--dirty`, INFO): unchanged in eight; a1 extended its mechanism to
single-language sites by choice, so it changed there.

**By condition:** A 2 of 3 CLEAR; B 0 of 3; C 1 of 3. The floor enters no verdict.

## Stage 3 — `stage1_probe.py` (regression) and `stage3_probe.py`, all nine arms

**A correction to `stage3_probe.py`, made after the first stage-3 results — disclosed.** E3 allows a link to another
language's exported file (the reader chooses the file), but it compared the file name after dropping only a `#`
fragment, not a `?` query. b2 and c2 link to sibling files with a query (`fr.html?chosen-language#…`,
`probe.en.html?lang=en`) — exactly the links the allowance meant to admit — and failed E3 on them alone. The name is
now compared without the query. The change only widens the allowance, so it cannot turn a passing arm into a failing
one; it turns b2 and c2 from BLOCKED to CLEAR, and changes no other arm.

| arm | condition | stage-1 regression | stage-3 probes | floor | before the correction | browser-language detection in the export (INFO) | network resources in the export (INFO) |
|---|---|---|---|---|---|---|---|
| a1 | A | 12/12 | 7/7 | CLEAR | same | none | none |
| a2 | A | 12/12 | 7/7 | CLEAR | same | none | none |
| a3 | A | 12/12 | 7/7 | CLEAR | same | none | none |
| b1 | B | 12/12 | 7/7 | CLEAR | same | none | none |
| b2 | B | 12/12 | 7/7 | CLEAR | BLOCKED (E3, query on sibling links) | **en, fr, he** | 1 stylesheet (highlight.js CDN) per file |
| b3 | B | 12/12 | 7/7 | CLEAR | same | none | none |
| c1 | C | 12/12 | 7/7 | CLEAR | same | none | none |
| c2 | C | 12/12 | 7/7 | CLEAR | BLOCKED (E3, query on sibling links) | **en, fr, he** | none |
| c3 | C | 12/12 | 7/7 | CLEAR | same | **en, fr, he** | none |

**All nine CLEAR at stage 3**, and every arm's `mkdocs build` output is unchanged by its export (E7). The INFO
column confirms the goal-2 record from the code: the three arms that did not surface the conflict (b2, c2, c3) are
exactly the three whose exported files detect the browser's language.
