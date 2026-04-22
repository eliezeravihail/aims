# knowledge-library-agents

Two independent concerns live in this repo:

1. **Agent routing system** — a tiered Claude Code orchestrator. A single
   slash command dispatches work across isolated subagents (Router, Planner,
   Validator, workers), each in its own context. Generic and domain-neutral.
2. **Books knowledge library** — a pre-existing knowledge base under
   `skills/BOOKS/` with its own slash commands. Not coupled to the routing
   system.

**Created by [Eliezer Avihail](https://www.linkedin.com/in/eliezer-avihail/) · MIT License**

---

## Agent routing system

### What runs where

```
User → /project:experts "<request>"
                │
                ▼
        Router (Haiku) ─── triage + post-exec dispatch ─── cheap
                │
   ┌────────────┼─────────────┐
   ▼            ▼             ▼
trivial     simple         complex
(worker     (worker +    (Planner (Opus) → workers → Validator ←─┐
only)       Validator)    per step; Router decides next step)    │
                                    │                             │
                                    ▼                             │
                              Validator (Sonnet) ─── objective ───┘
                              quality gate; runs tests; catches
                              lying artifacts (empirically verified)
```

Each role runs as a separate subagent. Only a JSON envelope crosses the
boundary between them — no shared context. That's how costs stay bounded
and how the Validator can make independent judgements.

### Contracts

Every exchange uses schemas in `agents/_schema.md` and `schemas/*.v1.json`:

- **Envelope** — one of `{ok, outputs}` / `{retry, reason, hint}` / `{abort, reason}`.
- **Plan** — ordered DAG of `AgentStep{agent, inputs, validate, depends_on}` with `${sN.outputs.port}` binding.
- **Verdict** — `{passed, score, issues[], suggested_action, objective_checks}`.

### Failure taxonomy

| Signal     | Who raises it         | What happens next                                       |
|------------|-----------------------|---------------------------------------------------------|
| `retry`    | Worker envelope       | Re-invoke same agent with `retry_hint` (cap: 3/step).   |
| `re-route` | Validator verdict     | Try a different agent, same goal (cap: 3/request).      |
| `replan`   | Validator verdict     | Back to Planner with the verdict + old plan (cap: 2).   |
| `abort`    | Any agent / cap blown | Stop with a structured report.                          |

### Defining an agent

Create `agents/<id>.md` with YAML frontmatter conforming to `agents/_schema.md`
(`name`, `model`, `tools`, `capabilities`, `inputs`, `outputs`, `effects`,
`idempotent`, `strategy`). The body is a pure behavior spec: role, input
semantics, output contract, pre-submit checklist. Step 0 of every worker
loads `skills/project-context` and `skills/quality-analysis`. Append one row
to `agents/registry.md` and you're done — Planner and Router see the new
agent automatically.

### Deterministic executor

`harness/` is the Python implementation of the spec. The markdown files are
the contract; the harness enforces it:

- `harness/envelope.py` — strict JSON schema validation.
- `harness/executor.py` — state machine: preflight → Router → [Planner] → workers → Validator → Router → loop.
- `harness/dispatcher.py` — `MockDispatcher` (tests) and `LiveDispatcher` (Anthropic SDK).
- `harness/tracer.py` — per-step JSONL observability.

Run `python -m pytest tests/` — the full suite exercises the state machine
on mocked responses (retry, malformed envelope, binding resolution, etc.).

### Empirical support

Two pilots are committed:

- **`tests/pilot_medium/`** — BugsInPy/cookiecutter-4. Both baseline and
  pipeline fixed the bug; the pipeline's diff was ~3× smaller (closer to
  upstream) and added 4 regression tests that would catch the bug on
  revert; the Validator caught an injected wrong-fix artifact that
  baseline would have shipped. Cost: ~4× baseline tokens. See
  `PILOT_MEDIUM_REPORT.md`.
- **`harness/demo.py`** + **`harness/demo_live.py`** — reproducible
  demos of the mock and live paths.

---

## Books knowledge library (separate, pre-existing)

Decoupled from the routing system. Slash commands:

- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:ingest-local-sources` — encode a local PDF or text file
- `/project:books-status` — coverage and quality report

Knowledge layout:
```
skills/BOOKS/<CATEGORY>/<slug>/
  _index.md        ← topic list (one line per topic — load this first)
  <topic>.md       ← condensed, actionable content for this topic
```

Categories in use: `ANN` · `CNN` · `VISION` · `OBJECT_DETECTION` · `REFACTORING` · `ALGORITHMS` · `NLP` · `RL` · `TRAINING_OPTIMIZATION` · `DISTRIBUTED_SYSTEMS`

---

## Install

1. Clone this repo into your Claude Code plugins folder.
2. Open the folder in Claude Code.
3. Use the slash commands above — the routing system and the books library are
   available independently.
