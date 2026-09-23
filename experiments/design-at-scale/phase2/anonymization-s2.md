# Phase 2 stage 2 — anonymization report

As in Phase 1, before the stage-2 judge ran. Nine labels (D–M, no I) drawn with `SystemRandom`, salted; mapping sealed
by `MAPPING-SEAL-s2.sha256`. Residual mentions sit in docstrings, which the frozen rule leaves; counted, disclosed to no judge.

```
D: md reverted/removed 3 | comment lines stripped 0 | residual 0
E: md reverted/removed 7 | comment lines stripped 0 | residual 1
     mkdocs/commands/build.py: inputs changed since the recorded build, so that the result equals a full build (decisions/0003).
F: md reverted/removed 4 | comment lines stripped 0 | residual 0
G: md reverted/removed 8 | comment lines stripped 0 | residual 4
     mkdocs/commands/build.py: (`decisions/0003`).
     mkdocs/structure/languages.py: This module is the one owner of the resolution rule (see `decisions/0001`):
     mkdocs/commands/incremental.py: only the outputs whose inputs changed (`decisions/0003`). This module is the one place that says wha
     mkdocs/tests/incremental_build_tests.py: Incremental rebuilds of multi-language sites (`decisions/0003`).
H: md reverted/removed 4 | comment lines stripped 0 | residual 4
     mkdocs/structure/languages.py: This module is the one owner of the resolution rule (see `decisions/0001`):
     mkdocs/commands/incremental.py: Incremental rebuilds of a multi-language site, as `mkdocs serve` performs them (`decisions/0003`).
     mkdocs/commands/incremental.py: (`decisions/0002`) are not inputs.
     mkdocs/tests/languages_incremental_tests.py: Incremental rebuilds of a multi-language site (`decisions/0003`).
J: md reverted/removed 4 | comment lines stripped 0 | residual 0
K: md reverted/removed 6 | comment lines stripped 0 | residual 0
L: md reverted/removed 7 | comment lines stripped 0 | residual 0
M: md reverted/removed 4 | comment lines stripped 0 | residual 0
```
