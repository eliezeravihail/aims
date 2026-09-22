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

**Its effect, stated plainly:** it was found after seeing results, and it turns one aims arm (a2) from BLOCKED to
CLEAR. It changes nothing for b3 or c1 (both rewrite unaffected pages with identical bytes). The floor enters no
verdict.
