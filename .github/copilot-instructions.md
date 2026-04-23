# expert-system — Copilot Instructions

## Project structure

```
agents/                 # Markdown agent specs (router, planner, workers, validator)
skills/                 # Reusable methodology skills loaded into worker system prompts
commands/               # Slash commands: experts.md (lean), agents-experts.md (pipeline)
harness/                # Python executor that runs the agent pipeline
schemas/                # JSON schemas for envelope validation
tests/                  # pytest suite (47 tests)
.claude-plugin/plugin.json  # Claude Code plugin manifest
```

## Two invocation modes

| Mode | Command | Use when |
|------|---------|----------|
| Lean (default) | `/experts <task>` | Claude Opus / Sonnet baseline — single dispatch |
| Pipeline | `/agents-experts <task>` | Copilot / weaker model — decomposed pipeline |

## Running tests

```bash
python -m pytest tests/      # full suite (47 tests)
python -m pytest tests/ -x   # stop on first failure
```

## Adding a worker agent

1. Create `agents/<id>.md` — conform to `agents/_schema.md` (frontmatter + envelope shape)
2. Body must be a thin wrapper that loads a skill from `skills/`
3. Append one row to `agents/registry.md`
4. Update lean Router decision rule in `agents/_router.md` §"Decision rule"

## Adding a skill

Create `skills/<name>/SKILL.md`. Workers reference it by name in their body.

## Harness entry points

```python
from harness.executor import Executor
executor = Executor(registry)
executor.run_lean(request, cwd)   # lean mode
executor.run(request, cwd)        # pipeline mode
```

## Key constraints

- Infra agents (`_router`, `_planner`, `_validator`, `_baseline`) are **not** listed in `agents/registry.md`
- Router (lean) must be `tools: []` — no file access allowed
- Every agent output must conform to the envelope schema in `schemas/`
- `.claude.md` (gitignored) is the per-checkout project cache — do not commit it
- BOOKS knowledge lives in a companion repo (`knowledge-library-agents`); load by `quality_score` descending
