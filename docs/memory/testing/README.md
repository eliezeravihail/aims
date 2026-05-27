# testing/

Bash smoke tests that exercise the memory subsystem and hooks.
These are the closest thing the plugin has to an integration suite —
no language runtime, just `bash` + a few `python3 -c` helpers.

## Nodes

- **smoke-tests.md** — `tests/marker.sh` (PostToolUse marker /
  `_inbox` routing / find-dirty) and `tests/consolidate.sh`
  (Stop-hook consolidation). Pure bash, no Anthropic API.
