# Phase 2 stage 3 — anonymization report

As in Phase 1, before the stage-3 panel ran. Nine labels (N–W, no O) drawn with `SystemRandom`, salted; mapping sealed by
`MAPPING-SEAL-s3.sha256`. Residual mentions sit in docstrings (and one JavaScript `//` comment, which the frozen
rule — `#` comment lines only — does not strip); counted here, disclosed to no judge.

```
N: md reverted/removed 5 | comment lines stripped 0 | residual 0
P: md reverted/removed 6 | comment lines stripped 1 | residual 0
Q: md reverted/removed 10 | comment lines stripped 0 | residual 0
R: md reverted/removed 7 | comment lines stripped 1 | residual 1
     mkdocs/commands/export.py: `decisions/0001-no-reader-language-detection.md`.
S: md reverted/removed 5 | comment lines stripped 0 | residual 0
T: md reverted/removed 6 | comment lines stripped 0 | residual 6
     mkdocs/commands/incremental.py: Incremental rebuilds of a multi-language site, as `mkdocs serve` performs them (`decisions/0003`).
     mkdocs/commands/incremental.py: (`decisions/0002`) are not inputs.
     mkdocs/structure/languages.py: This module is the one owner of the resolution rule (see `decisions/0001`):
     mkdocs/tests/languages_incremental_tests.py: Incremental rebuilds of a multi-language site (`decisions/0003`).
     mkdocs/commands/export/__init__.py: (`decisions/0004`).
     mkdocs/commands/export/choose_language.js: // language when the export file for it exists (decisions/0004, decision 7).
U: md reverted/removed 11 | comment lines stripped 0 | residual 6
     mkdocs/commands/build.py: (`decisions/0003`).
     mkdocs/commands/incremental.py: only the outputs whose inputs changed (`decisions/0003`). This module is the one place that says wha
     mkdocs/structure/languages.py: This module is the one owner of the resolution rule (see `decisions/0001`):
     mkdocs/tests/incremental_build_tests.py: Incremental rebuilds of multi-language sites (`decisions/0003`).
     mkdocs/commands/export.py: its pages, navigation and stylesheets are then put into one file (`decisions/0005`). What a
     mkdocs/commands/export_references.py: Where a reference in a built site lands inside an offline export (`decisions/0005`).
V: md reverted/removed 8 | comment lines stripped 0 | residual 0
W: md reverted/removed 10 | comment lines stripped 0 | residual 4
     mkdocs/commands/build.py: inputs changed since the recorded build, so that the result equals a full build (decisions/0003).
     mkdocs/commands/export.py: `mkdocs export`: every language's site as one self-contained HTML file (decisions/0004).
     mkdocs/commands/export.py: same fallback and untranslated notice (decisions/0002) — but into a scratch directory, never `site_d
     mkdocs/tests/export_tests.py: """`mkdocs export`: one self-contained HTML file per language (decisions/0004)."""
```
