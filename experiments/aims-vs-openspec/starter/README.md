# Starter — identical for all three arms

Copied verbatim into each arm's fresh, empty repository before stage 1. It fixes the **substrate** and
nothing else: it states no structure, names no module, and suggests no design. Any file in here that hints
at a shape is a leak.

## Substrate (fixed, not the agent's choice)

- **Python 3.11+**, standard library only for the product itself.
- **pytest** for tests. No other runtime dependency without asking the product owner.
- **`decimal.Decimal`** is available; nothing requires or forbids it. *(Stated only because "which numeric
  type" is a technical choice the oracle would otherwise have to answer three times, differently.)*
- No network access at runtime. No database. No UI.
- The entry point may be a library plus a CLI, or a local HTTP endpoint — the agent's call.

## The repository as handed over

```
./                 empty except for this file and the files below
pyproject.toml     name, python version, pytest dev-dependency — nothing else
tests/             empty; the agent writes its own
.gitignore         __pycache__, .pytest_cache, .venv
```

No `src/` skeleton, no module names, no interfaces, no example. The shape of the code is the thing under
measurement and the starter must not pre-decide any of it.

## How the operator runs it

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q                     # the arm's own suite
python -m acceptance stage-N  # the operator's visible acceptance for the stage, run from outside the repo
```

The visible acceptance harness lives **outside** every arm's repository and is run against each arm's stated
entry point. It is written once, before stage 1, from the cards' acceptance tables — and it is never shown
to any arm, because a test file is a design hint.

## Permissions, identical per arm

Read/write inside its own repository; run `pytest`; no internet; no access to any other arm's repository, to
`hidden/`, or to any card but the current one.

## Per-arm additions (the only permitted difference)

| Arm | Added before stage 1 | Must be absent |
|---|---|---|
| aims | the aims plugin installed per `/install-on .` | any `openspec/` directory, any OpenSpec command |
| OpenSpec | `npm i -g @fission-ai/openspec@latest` then `openspec init`, per its own docs | the aims plugin, skill, hooks, `CLAUDE.md`, and every aims record |
| plain | nothing | both of the above |

Paste the session's loaded-skills/plugins listing into each arm's log at the start of every stage. An arm
that turns out to have had the other method's files in context invalidates that stage — discard and re-run.
