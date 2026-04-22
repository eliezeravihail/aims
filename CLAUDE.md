# knowledge-library-agents

Two independent concerns live in this repo:

1. **Agent routing system** — generic orchestration infrastructure in
   `agents/`, `skills/`, `harness/`, and the two slash commands.
   Domain-neutral.
2. **Books knowledge library** (pre-existing, separate concern) — data and
   skills under `skills/BOOKS/`, `books-init-queue.yaml`, and the
   `query-knowledge` / `ingest-local-sources` / `books-status` slash commands.

The two are decoupled. A book-related worker agent, if reintroduced,
registers in `agents/registry.md` like any other worker — no special casing.

---

## Agent routing system — two modes

One framework, two invocation modes, picked by the user based on the
baseline model they are running under.

### `/project:experts` — lean mode (default, strong baselines)

Single dispatch on the right model with methodology skills preloaded in
its system context. No Planner, no per-step Validator loop. Use when the
baseline is Claude Opus / Sonnet.

```
/project:experts fix the off-by-one in src/loop.py
```

Pipeline:
```
Router (Haiku, tools: []) → Worker (Sonnet/Opus, skills loaded) → [Validator, if write effects] → done
```

Router emits `{action: "dispatch-lean", model, skills_to_load, rationale}`.
The Executor composes the worker's system prompt from the named skills and
dispatches once. Optional terminal Validator runs on write-effect outputs.

### `/project:agents-experts` — pipeline mode (weak baselines)

Decomposed pipeline. Use when the baseline is weak at single-dispatch —
Copilot, smaller OSS models, constrained cloud contexts. Each role runs as
an isolated subagent; only envelopes cross the boundary.

```
/project:agents-experts fix the off-by-one in src/loop.py
```

Pipeline:
```
Router (Haiku) → Planner (Opus) → workers (Sonnet, isolated) → Validator (Sonnet) → Router post-exec → loop
```

### Which to pick

- **Claude Opus / Sonnet as your baseline** → `/experts`.
- **Copilot, smaller OSS, cloud with mandatory small models** → `/agents-experts`.
- **Unsure** → `/experts`. It's the default for a reason.

### Tiered components by mode

| Role                      | Lean mode (`/experts`)                 | Pipeline mode (`/agents-experts`)             |
|---------------------------|----------------------------------------|------------------------------------------------|
| Router (Haiku)            | `agents/_router.md` (tools: [], inline classification) | `agents/_router_pipeline.md` (tools: [Read], scope classification) |
| Planner (Opus)            | — (no decomposition)                   | `agents/_planner.md`                           |
| Worker                    | Single dispatch, skills composed in    | `agents/<id>.md` (one per role, each is a thin wrapper around its skill) |
| Validator (Sonnet)        | `agents/_validator.md` (optional terminal) | `agents/_validator.md` (per step)          |
| Baseline escape hatch     | n/a (lean *is* the baseline)           | `agents/_baseline.md` (holistic path inside the pipeline) |

### Shared components (used by both modes)

| File                                   | What                                              |
|----------------------------------------|---------------------------------------------------|
| `agents/_schema.md`                    | Envelope / Plan / Verdict / frontmatter contracts |
| `agents/registry.md`                   | Registered worker agents                           |
| `skills/project-context/SKILL.md`      | `.claude.md` cache procedure                       |
| `skills/quality-analysis/SKILL.md`     | 7-dimension quality rubric                         |
| `skills/debug-methodology/SKILL.md`    | reproduce → isolate → fix → verify → test-gap     |
| `skills/test-authoring/SKILL.md`       | locate → author → verify for tests                 |
| `skills/test-strategy/SKILL.md`        | design / assess coverage plans                     |
| `skills/feature-build/SKILL.md`        | design → implement → verify for features           |
| `harness/`                             | Deterministic Python executor for both modes       |

### Always-active rules

- Every agent file conforms to `agents/_schema.md` (frontmatter + envelope + Plan + Verdict shapes).
- **Agent bodies are wrappers.** Methodology lives in skills. A worker's body points to its skill; both modes load the same content.
- **Infra-agent tool discipline is mandatory** (`_schema.md` §9). Routers are `tools: []` (lean) or `[Read]` (pipeline). The lean Router inlines the skill registry; the pipeline Router reads `agents/registry.md`.
- Every worker loads `skills/project-context` before wide Grep/Glob/Read. The Executor bootstraps `.claude.md` on first run if missing.
- Only `agents/registry.md` lists workers. Infrastructure agents are not registered there.
- Route all multi-agent work through `/experts` or `/agents-experts`. Do not dispatch workers directly.

### Shared project cache (`.claude.md`)

A per-checkout (gitignored) markdown file summarising the target codebase.
Built from ground-truth sources by the **Bootstrap** procedure in
`skills/project-context/SKILL.md`. Both modes use it. Missing →
Executor runs Bootstrap before the first worker dispatch. Stale (worker
emits `advisory: "project-context-stale"`) → Refresh on next step.

### Failure taxonomy (pipeline mode)

| Signal    | Raised by                | Router response                              |
|-----------|--------------------------|----------------------------------------------|
| `retry`   | Worker envelope          | Re-run same agent + `retry_hint` (cap: 3/step). |
| `re-route`| Validator verdict        | Different agent, same goal (cap: 3/request).    |
| `replan`  | Validator verdict        | Return to Planner with verdict + old plan (cap: 2/request). |
| `abort`   | Worker, Validator, Router (cap exceeded) | Stop with structured report.       |

Lean mode uses `retry` and `abort` only; no `re-route` / `replan` (no decomposition to adjust).

### Adding a worker agent

1. Create `agents/<id>.md`, conform to `_schema.md`. Body is a **wrapper** that loads a methodology skill (or create a new one under `skills/`).
2. Append one row to `agents/registry.md`.
3. If the new worker is specialized, update the lean Router's skill map in `agents/_router.md` §"Decision rule".

Pipeline mode sees the new agent automatically via the registry. Lean mode needs a line in the Router's decision rule.

### Deterministic executor (`harness/`)

The markdown files are the **specification**; `harness/` is the **implementation**:

- `harness/envelope.py` — JSON schema validation (strict); `schemas/*.v1.json`.
- `harness/frontmatter.py` — parses agent `.md` frontmatter into typed specs.
- `harness/registry.py` — loads `agents/registry.md` + infra agents (both Routers).
- `harness/state.py` — ExecutionState + `${sN.outputs.port}` binding resolver.
- `harness/executor.py`:
  - `run(request, cwd)` — pipeline mode entry point (`_router_pipeline` → ...).
  - `run_lean(request, cwd)` — lean mode entry point (`_router` → single worker).
- `harness/dispatcher.py` — `MockDispatcher` (tests) and `LiveDispatcher` (Anthropic SDK).
- `harness/tracer.py` — per-event JSONL observability.
- `harness/cli.py` — `python -m harness.cli run "<request>"`.

Run tests: `python -m pytest tests/`. 47 tests cover envelope, frontmatter, registry, state, and executor state-machine transitions for both modes.

---

## Books knowledge library (separate concern)

Entrypoints (unchanged, independent of the routing system):
- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:ingest-local-sources` — encode a local PDF or text file
- `/project:books-status` — coverage and quality report

Rules that apply only to the books concern:
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.
- Never encode a book without a verified free source — hallucinated content is not acceptable.
