# Phase 2 — floor results

The frozen probes (`../hidden/probes/`). A failure marks the arm-stage BLOCKED; passing earns nothing
(`decisions/0021`). The floor enters no verdict; it is reported as given.

## Stage 2 — `stage1_probe.py` (regression) and `stage2_probe.py`

| arm | stage-1 probes | stage-2 probes | floor | INFO | change size | usage |
|---|---|---|---|---|---|---|
| c1 | stage-1 12/12 | 6/8 — D1n, D2n fail: a one-off `build --dirty` rebuilds every page | BLOCKED | dirty output exact in D1–D5 (search index too); D6 `serve --dirty` correct; D7 single-language unchanged | 5 files, +470 / −14, 1 new | 231.9 k tokens, 68 tool calls |
