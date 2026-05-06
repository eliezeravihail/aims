# ais

Lean code-development discipline for Claude Code. Five slash commands, three
project-local hooks, idempotent bootstrap. No multi-agent pipeline, no
orchestration overhead — just the discipline that makes single-dispatch
sessions reliable on Opus / Sonnet baselines.

## What you get

| Command            | Model  | Purpose                                                               |
|--------------------|--------|-----------------------------------------------------------------------|
| `/init-workflow`   | Sonnet | Bootstrap ADRs, hooks, CLAUDE.md sections in any project (idempotent) |
| `/plan <task>`     | Opus   | Read-only exploration → ExitPlanMode → durable plan file              |
| `/adr <title>`     | Opus   | Record an architecture decision (append-only log)                     |
| `/grunt <task>`    | Haiku  | Mechanical edits: renames, formatting, log/config tweaks              |
| `/done [plan]`     | Opus   | Verify a plan's steps & checks; prompt for ADRs                       |

The model is pinned per command — it switches automatically and returns to
your session model after.

## Hooks (per-project, installed by `/init-workflow`)

- **SessionStart** — surfaces in-progress plans and recent ADRs.
- **UserPromptSubmit** — nudges toward `/plan` or `/adr` on trigger phrases
  (refactor, migrate, "X vs Y", new feature, …). Never blocks.
- **PreToolUse** — hard-blocks Edit/Write while a `.claude/.planning-lock`
  file exists (the lock is set by `/plan`'s read-only phase). In `block` mode
  also requires an in-progress plan when editing under `src/`, `lib/`,
  `app/`, etc. In `nudge` mode this check warns instead of blocking.

Mode switch: `echo nudge > .claude/ais-mode` / `echo block > .claude/ais-mode`.

## Install

```sh
# inside Claude Code:
/plugin install ais@<your-marketplace>
```

(See `.claude-plugin/marketplace.json` for the entry shape.)

## Use

In any project:

```
/init-workflow
```

Answers a few questions (test command, lint, ADR location, hook mode), then
shows a diff preview and applies only after you approve. Re-running is a no-op.

After init:

```
/plan add OAuth2 callback handler
   ↳ Opus, plan-mode discipline, ExitPlanMode → plan file written
/model sonnet                # for implementation
   ↳ implement against the plan
/adr use httpx over requests
   ↳ records the decision before it gets buried
/done
   ↳ verifies steps, runs the verification commands, asks about ADRs
```

For mechanical work that needs no judgment:

```
/grunt rename CamelCase to snake_case in scripts/
   ↳ Haiku, refuses to make architectural decisions
```

## Layout

```
.claude-plugin/
  plugin.json
  marketplace.json
commands/
  init-workflow.md
  plan.md
  adr.md
  grunt.md
  done.md
templates/
  CLAUDE.md.tmpl
  adr-readme.md.tmpl
  adr-template.md.tmpl
  adr-0001.md.tmpl
  plan-template.md.tmpl
  settings.json.tmpl
  hooks/
    session-start.sh
    prompt-submit.sh
    pre-write.sh
```

## Design principles

1. **Lean over orchestrated.** The 2025–2026 evidence on multi-agent LLM
   systems is consistent: with a strong baseline (Opus / Sonnet), single
   dispatch with discipline beats orchestrated pipelines on accuracy, cost,
   and debuggability. Pipelines pay off mainly for weak baselines.
2. **Discipline through artifacts, not exhortation.** A plan that lives only
   in conversation context evaporates at compaction. A plan on disk survives,
   gets reviewed, and grounds the implementation session.
3. **Hooks as guardrails, not handcuffs.** The lock on `/plan` is enforced.
   Everything else is a nudge by default — the user decides when to upgrade
   to `block` after they've felt the pain themselves.
4. **Idempotent and merge-aware.** Running `/init-workflow` on an existing
   project must not damage existing CLAUDE.md, settings, or layout.

## License

MIT
