# expert-system

Two independent concerns live in this repo:

1. **Agent routing system** — a dual-mode Claude Code orchestrator. One
   framework supports two invocation modes, picked based on the baseline
   model's capability. Generic and domain-neutral.
2. **Books knowledge library** — a pre-existing knowledge base under
   `skills/BOOKS/` with its own slash commands. Not coupled to the routing
   system.

**Created by [Eliezer Avihail](https://www.linkedin.com/in/eliezer-avihail/) · MIT License**

---

## Installation

### As a Claude Code plugin (recommended)

```bash
claude plugin install eliezeravihail/expert-system
```

This registers the five slash commands below (`/experts`, `/agents-experts`,
`/books-status`, `/query-knowledge`, `/ingest-local-sources`) in your
Claude Code session. Auto-discovered from `commands/`, `agents/`, and
`skills/` at the repo root per the
[plugin spec](https://code.claude.com/docs/en/plugins-reference.md).

### Local development

Clone the repo and point Claude Code at it directly:

```bash
git clone https://github.com/eliezeravihail/expert-system.git
cd expert-system
claude --plugin-dir .
```

Changes to `commands/`, `agents/`, or `skills/` are picked up on the next
Claude Code restart — no reinstall needed.

### VS Code Copilot (pipeline mode)

For Copilot users, two global agents are provided under `.github/agents/`:

- `experts.agent.md` — lean mode
- `agents-experts.agent.md` — pipeline mode

Copy either into your VS Code user profile's agents directory to enable
them in Copilot agent mode. See `.github/copilot-instructions.md`.

### Python harness (for running pilots / CI)

```bash
pip install -e .              # installs the `harness` package only
pip install -e '.[live]'      # add Anthropic SDK for live dispatch
pip install -e '.[dev]'       # add pytest for the test suite
python -m pytest tests/       # 47 tests
```

---

## Agent routing system

### Two modes

| Command            | When to use                                              | What runs                                                |
|--------------------|----------------------------------------------------------|----------------------------------------------------------|
| `/experts` (default) | Strong baselines (Claude Opus / Sonnet).               | One lean worker with methodology skills preloaded.       |
| `/agents-experts`  | Weak baselines (Copilot, smaller OSS, constrained clouds). | Decomposed pipeline: Router → Planner → workers → Validator loop. |

### `/experts` (lean) — the default

```
User → /experts "<request>"
         │
         ▼
  Router (Haiku, tools:[]) ── emits {model, skills_to_load, rationale}
         │
         ▼
  One worker on the chosen model ── skills composed into its system prompt
         │
         ▼
  [Validator (Sonnet)] ── optional terminal, only if worker wrote files
         │
         ▼
       done
```

Why it exists: pilot data showed that on bounded feature builds, a single
capable Opus dispatch produced a correct implementation where a 7-tier
pipeline produced a subtly broken one (see `PILOT_FEATURE_REPORT.md`).
The lean mode exposes that pattern as a first-class command.

### `/agents-experts` (pipeline) — for weaker baselines

```
User → /agents-experts "<request>"
         │
         ▼
  Router (Haiku) ── triage + post-exec dispatch ── cheap
         │
   ┌─────┼───────────────┐
   ▼     ▼               ▼
trivial  simple      complex
 (worker  (worker +   (Planner (Opus) → workers → Validator ←─┐
  only)   Validator)   per step; Router decides next step)    │
                                   │                           │
                                   ▼                           │
                         Validator (Sonnet) ── objective ──────┘
                         quality gate; runs tests; catches
                         lying artifacts (empirically verified
                         on cookiecutter-4 stretch)
```

Each role is an isolated subagent. Only JSON envelopes cross role
boundaries — no shared context. That's how cost stays bounded and how
the Validator can make independent judgements.

### Shared across modes

- **Skills** (under `skills/`) — methodology playbooks loaded by the
  worker (in lean) or the corresponding wrapper agent (in pipeline):
  - `project-context` — the `.claude.md` codebase cache procedure.
  - `quality-analysis` — 7-dimension self-check rubric.
  - `debug-methodology` — reproduce → isolate → fix → verify → test-gap.
  - `test-strategy` — design / assess coverage plans.
  - `test-authoring` — author deterministic tests from a `TestTarget` list.
  - `feature-build` — design → implement → verify.
- **Schemas** (`agents/_schema.md`, `schemas/*.v1.json`) — envelope / Plan
  / Verdict / frontmatter contracts. Identical in both modes.
- **Validator** (`agents/_validator.md`) — independent quality gate.
  Optional-terminal in lean; per-step in pipeline.
- **Registry** (`agents/registry.md`) — the list of worker agents, thin
  wrappers that each load one skill.

### Contracts

Every exchange uses shapes defined in `agents/_schema.md`:

- **Envelope** — one of `{ok, outputs}` / `{retry, reason, hint}` / `{abort, reason}`.
- **Plan** (pipeline only) — ordered DAG of `AgentStep{agent, inputs, validate, depends_on}` with `${sN.outputs.port}` binding.
- **Verdict** — `{passed, score, issues[], suggested_action, objective_checks}`.

### Failure taxonomy (pipeline mode)

| Signal     | Who raises it         | What happens next                                       |
|------------|-----------------------|---------------------------------------------------------|
| `retry`    | Worker envelope       | Re-invoke same agent with `retry_hint` (cap: 3/step).   |
| `re-route` | Validator verdict     | Try a different agent, same goal (cap: 3/request).      |
| `replan`   | Validator verdict     | Back to Planner with the verdict + old plan (cap: 2).   |
| `abort`    | Any agent / cap blown | Stop with a structured report.                          |

Lean mode uses `retry` and `abort` only — no `re-route` or `replan`, since
there's no decomposition to adjust.

### Defining a new worker

1. Create `agents/<id>.md` with YAML frontmatter conforming to `agents/_schema.md`. The body is a **thin wrapper**: 3-5 lines telling the worker to load a specific skill (usually a new one under `skills/<methodology>/`) and emit the envelope declared in the frontmatter.
2. Append one row to `agents/registry.md`.
3. If the new worker enables a class of tasks, add a line to the decision rule in `agents/_router.md` so the lean Router can route to it via skill selection.

Pipeline mode sees the new agent automatically through the registry.

### Deterministic executor

`harness/` is the Python implementation of the spec. The markdown files
are the contract; the harness enforces it:

- `harness/envelope.py` — strict JSON schema validation.
- `harness/executor.py`:
  - `run(request, cwd)` — pipeline entry point (`_router_pipeline` → …).
  - `run_lean(request, cwd)` — lean entry point (`_router` → single worker).
- `harness/dispatcher.py` — `MockDispatcher` (tests) and `LiveDispatcher` (Anthropic SDK).
- `harness/tracer.py` — per-step JSONL observability.

Run `python -m pytest tests/` — the full suite exercises both modes on
mocked responses (47 tests covering envelope, registry, state machine,
retry, malformed envelopes, lean dispatch with skills, etc.).

### Empirical support

Four pilots are committed:

- **`tests/pilot_medium/`** — BugsInPy/cookiecutter-4 on pipeline mode.
  Validator caught an injected wrong-fix artefact baseline would have
  shipped. Pipeline cost ~4× baseline tokens.
- **`tests/pilot_feature/`** — TODO CLI on pipeline. Pipeline produced a
  subtly broken implementation (id-reuse) where Opus single-shot was
  correct. This pilot motivated the dual-mode split.
- **`tests/pilot_holistic/`** — contacts CLI. First pilot where the Router
  routed to `dispatch-baseline` (pipeline holistic escape hatch); cost
  ratio dropped from 6.8× to 2.23×.
- **`tests/pilot_medium_lean/`** — cookiecutter-4 on **lean mode**.
  Commits the numbers that justified promoting lean to the default.

See `PILOT_*_REPORT.md` at repo root for the write-ups and
`FRAMEWORK_EVAL_PLAN.md` for how to run new pilots.

---

## Books knowledge library (separate, pre-existing)

Decoupled from the routing system. Slash commands:

- `/query-knowledge <topic>` — query the knowledge base
- `/ingest-local-sources` — encode a local PDF or text file
- `/books-status` — coverage and quality report
