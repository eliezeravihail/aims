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
- Only `agents/registry.md` lists workers. Infrastructure agents are not registered there (they are always present).
- Route all multi-agent work through `/project:experts`. Do not dispatch workers directly.

### Failure taxonomy
| Signal    | Raised by                | Router response                              |
|-----------|--------------------------|----------------------------------------------|
| `retry`   | Worker envelope          | Re-run same agent + `retry_hint` (cap: 3/step). |
| `re-route`| Validator verdict        | Different agent, same goal (cap: 3/request).    |
| `replan`  | Validator verdict        | Return to Planner with verdict + old plan (cap: 2/request). |
| `abort`   | Worker, Validator, Router (cap exceeded) | Stop with structured report.       |

### Adding a worker agent
1. Create `agents/<id>.md`, conform to `_schema.md`.
2. In the body, load `skills/quality-analysis` and treat its pre-submit checklist as mandatory.
3. Append one row to `agents/registry.md`.
4. Done — Planner and Router see the agent automatically; no further wiring.

---

## Books knowledge library (separate concern)

Entrypoints (unchanged, independent of the routing system):
- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:ingest-local-sources` — encode a local PDF or text file
- `/project:books-status` — coverage and quality report

Rules that apply only to the books concern:
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.
- Never encode a book without a verified free source — hallucinated content is not acceptable.
