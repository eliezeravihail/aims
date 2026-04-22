# knowledge-library-agents

This repo houses two independent concerns:

1. **Agent routing system** (this PR's scope) — generic infrastructure in
   `agents/` + `/project:experts`. Domain-neutral.
2. **Books knowledge library** (pre-existing) — skills and data under
   `skills/BOOKS/`, `books-init-queue.yaml`, and the `books-*` /
   `query-knowledge` / `ingest-local-sources` slash commands.

The two are decoupled: the routing system does not reference the books project,
and the books project does not depend on the routing system. An agent file for a
book-related agent would register itself in `agents/router.md` like any other
consumer would — no special casing.

## Agent routing system

### Always-active rules
- Agent definitions live in `agents/<id>.md`. Read the relevant file before invoking — the frontmatter declares `model` + `tools`, the body is the full behavior spec.
- Route multi-agent work through `/project:experts`. The registry of available agents is `agents/router.md`.
- Agent files are pure behavior (role, inputs/outputs contract, retry protocol). Domain playbooks live in skills, never in agent files.

### Retry protocol
An agent signals an unacceptable result with a single line `STATUS: RETRY <reason>`.
The router feeds `<reason>` back as `retry_hint` on the next loop iteration.
Default cap: 3 retries per agent per pipeline stage.

### Router modes
| Mode    | When                                                               |
|---------|--------------------------------------------------------------------|
| SINGLE  | One agent, read-only / idempotent request                          |
| LOOP    | One agent with a quality gate; retries on `STATUS: RETRY`          |
| CASCADE | Multi-stage pipeline; stage N's `outputs` bind into stage N+1's `inputs` |

## Books knowledge library (separate concern)

Entrypoints (unchanged, independent of the routing system):
- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:ingest-local-sources` — encode a local PDF or text file
- `/project:books-status` — coverage and quality report

Rules for the books project (apply only when working on that concern):
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.
- Never encode a book without a verified free source — hallucinated content is not acceptable.
