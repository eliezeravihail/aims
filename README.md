# knowledge-library-agents

Two independent concerns live in this repo:

1. **Agent routing system** — a generic Claude Code primitive that wires a
   natural-language request to the right agent(s) and orchestrates them in
   single, loop, or cascade mode. Domain-neutral.
2. **Books knowledge library** — a pre-existing knowledge base under
   `skills/BOOKS/` with its own slash commands. Not coupled to the routing
   system.

**Created by [Eliezer Avihail](https://www.linkedin.com/in/eliezer-avihail/) · MIT License**

---

## Agent routing system

### How it works
One slash command — `/project:experts <request>` — reads the registry at
`agents/router.md`, resolves which agent(s) match the request, loads their
definitions, and runs them.

Three execution modes, chosen by the router:

| Mode    | When                                                               |
|---------|--------------------------------------------------------------------|
| SINGLE  | One agent, read-only / idempotent request                          |
| LOOP    | One agent with a quality gate; retries up to 3× on `STATUS: RETRY` |
| CASCADE | Multi-stage pipeline; stage N's `outputs` bind into stage N+1's `inputs` by field name |

An agent signals an unacceptable result with a single line
`STATUS: RETRY <reason>` instead of its normal output. The router feeds
`<reason>` back as `retry_hint` on the next loop iteration.

### Defining an agent
Create `agents/<id>.md` with YAML frontmatter + a behavior body. Frontmatter
fields: `name`, `model`, `tools`, `inputs`, `outputs`. The body declares the
role, input semantics, the output contract, and when to emit `STATUS: RETRY`.
Append a row for the new agent to `agents/router.md`.

Agent files are pure behavior — no domain playbooks. Domain-specific logic
belongs in the skills the agent invokes.

### Why this layout
- `agents/<id>.md` = what an agent is.
- `agents/router.md` = which agents exist.
- `/project:experts` = how they get invoked.

No code needed to add an agent. The registry + per-agent behavior file is the
full contract.

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
