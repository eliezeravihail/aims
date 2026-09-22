# Phase 1 — anonymization report

Applied to all six per `PROTOCOL-NOTES.md`, before any judge ran. Labels P–U drawn with `SystemRandom`, salted; the
mapping stays outside the repository until the verdict, sealed by `MAPPING-SEAL.sha256`.

```
P md reverted/removed: 4 | comment lines stripped: 0 | residual mentions: 0
Q md reverted/removed: 7 | comment lines stripped: 0 | residual mentions: 0
R md reverted/removed: 4 | comment lines stripped: 0 | residual mentions: 0
S md reverted/removed: 3 | comment lines stripped: 0 | residual mentions: 0
T md reverted/removed: 5 | comment lines stripped: 0 | residual mentions: 0
U md reverted/removed: 5 | comment lines stripped: 0 | residual mentions: 1
    mkdocs/structure/languages.py: This module is the one owner of the resolution rule (see `decisions/0001`):
```

The one residual is inside a docstring, so the frozen rule leaves it; it is counted here and disclosed to no judge.
