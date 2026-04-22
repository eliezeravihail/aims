# knowledge-library-agents

Two independent concerns live in this repo:

1. **Agent routing system** (this PR's scope) — generic, tiered orchestration
   infrastructure in `agents/`, `skills/quality-analysis/`, and
   `/project:experts`. Domain-neutral.
2. **Books knowledge library** (pre-existing, separate concern) — data and
   skills under `skills/BOOKS/`, `books-init-queue.yaml`, and the
   `query-knowledge` / `ingest-local-sources` / `books-status` slash commands.

The two are decoupled. A book-related worker agent, if reintroduced, registers
in `agents/registry.md` like any other worker — no special casing.

---

## Agent routing system

### Tiered architecture

| Role         | File                    | Model                          | Purpose                                                          |
|--------------|-------------------------|--------------------------------|------------------------------------------------------------------|
| Executor     | `.claude/commands/experts.md` | (runs in user context)   | State machine; delegates every decision to an agent.             |
| Router       | `agents/_router.md`     | `claude-haiku-4-5-20251001`    | Pre-exec triage; post-exec dispatch based on Verdict.            |
| Planner      | `agents/_planner.md`    | `claude-opus-4-6`              | Decomposes complex requests into a Plan. Invoked only when needed. |
| Validator    | `agents/_validator.md`  | `claude-sonnet-4-6`            | Independent quality gate. Emits a Verdict against a shared rubric. |
| Workers      | `agents/<id>.md`        | per-agent frontmatter          | Do the actual task.                                              |

Each role runs as a separate Claude Code subagent — **context is not shared**.
Only the envelope crosses the boundary. That is the core cost-control mechanism.

### Always-active rules
- Every agent file conforms to `agents/_schema.md` (frontmatter + envelope + Plan + Verdict shapes).
- Agent files are pure behavior. Domain playbooks live in skills.
- Producing agents and `_validator` both load `skills/quality-analysis` — the shared quality rubric is the contract between them.
- Every infra agent and worker loads `skills/project-context` at step 0 of its procedure, and reads `.claude.md` (the shared project-structure cache) before any wide Grep/Glob/Read. The Executor bootstraps `.claude.md` on first `/project:experts` run if it doesn't exist.
- Only `agents/registry.md` lists workers. Infrastructure agents are not registered there (they are always present).
- Route all multi-agent work through `/project:experts`. Do not dispatch workers directly.

### Shared project cache (`.claude.md`)
A per-checkout (gitignored) markdown file summarising the target codebase:
layout, modules, test layout, conventions, known invariants. Built from
ground-truth sources (`pyproject.toml`, `package.json`, `CMakeLists.txt`, …)
by the **Bootstrap** procedure in `skills/project-context/SKILL.md`.
- Missing → Executor runs Bootstrap before the first worker dispatch.
- Stale (worker emits `advisory: "project-context-stale"`) → Executor runs Refresh as the next step.
- User can force: `/project:experts init project context` or `/project:experts refresh project context`.

No agent re-crawls the filesystem when the cache can answer the question.

### Failure taxonomy
| Signal    | Raised by                | Router response                              |
|-----------|--------------------------|----------------------------------------------|
| `retry`   | Worker envelope          | Re-run same agent + `retry_hint` (cap: 3/step). |
| `re-route`| Validator verdict        | Different agent, same goal (cap: 3/request).    |
| `replan`  | Validator verdict        | Return to Planner with verdict + old plan (cap: 2/request). |
| `abort`   | Worker, Validator, Router (cap exceeded) | Stop with structured report.       |

### Adding a worker agent
1. Create `agents/<id>.md`, conform to `_schema.md`.
2. In the body, declare "step 0" — load `skills/project-context` and `skills/quality-analysis`, apply their procedures as preconditions.
3. Append one row to `agents/registry.md`.
4. Done — Planner and Router see the agent automatically; no further wiring.

### Deterministic executor (`harness/`)
The markdown files are the **specification**; `harness/` is the **implementation**:
- `harness/envelope.py` — JSON schema validation (strict); `schemas/*.v1.json`.
- `harness/frontmatter.py` — parses agent `.md` frontmatter into typed specs.
- `harness/registry.py` — loads `agents/registry.md` + infra agents.
- `harness/state.py` — ExecutionState + `${sN.outputs.port}` binding resolver.
- `harness/executor.py` — state machine: preflight → Router → [Planner] → workers → Validator → Router → loop.
- `harness/dispatcher.py` — `MockDispatcher` (tests) and `LiveDispatcher` (Anthropic SDK).
- `harness/tracer.py` — per-event JSONL observability.
- `harness/cli.py` — `python -m harness.cli run "<request>"`.
- `harness/demo.py`, `harness/demo_live.py` — reproducible demos.

Run tests: `python -m pytest tests/`. 36 tests cover envelope, frontmatter, registry, state, and executor state-machine transitions (including retry, malformed envelope, binding resolution).

---

## Books knowledge library (separate concern)

Entrypoints (unchanged, independent of the routing system):
- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:ingest-local-sources` — encode a local PDF or text file
- `/project:books-status` — coverage and quality report

Rules that apply only to the books concern:
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.
- Never encode a book without a verified free source — hallucinated content is not acceptable.
