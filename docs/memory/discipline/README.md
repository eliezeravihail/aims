# discipline/

The four slash commands that define the aims discipline. Each
command pins itself to a model tier (Opus for planning / closing /
ADRs, Haiku for mechanical work) via its frontmatter.

## Leaves

- **plan.md** — `/plan`: creates the planning-lock and a durable
  plan file before any Edit/Write is allowed.
- **done.md** — `/done`: verifies a plan's steps, runs verification
  commands, prompts for ADRs, and (since ADR-0007) forces a memory
  consolidation pass.
- **adr.md** — `/adr`: append-only architecture decisions and the
  templates that seed them in new projects.
- **grunt.md** — `/grunt`: Haiku-tier mechanical edits (renames,
  log/config tweaks, format fixes) — no architectural judgment.

Related: `hooks/pre-write.md` enforces the planning-lock contract.
