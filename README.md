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
- **UserPromptSubmit** — **router**. Detects intent (bug, feature, refactor,
  decision, mechanical, question) and injects context that tells Claude to
  ask via `AskUserQuestion` which workflow to follow before doing any work.
  Hook is a deterministic shell classifier; Claude is the conversational
  router. Suppresses on slash-prefixed prompts, during planning lock, and
  for short follow-ups. See ADR-0004 for the design rationale.
- **PreToolUse** — hard-blocks Edit/Write while a `.claude/.planning-lock`
  file exists (the lock is set by `/plan`'s read-only phase). In `block` mode
  also requires an in-progress plan when editing under `src/`, `lib/`,
  `app/`, etc. In `nudge` mode this check warns instead of blocking.

Mode switch: `echo nudge > .claude/ais-mode` / `echo block > .claude/ais-mode`.

## Install

Two paths depending on how you want commands available.

### A. Global plugin install (recommended)

One-time, gives you `/plan`, `/adr`, `/grunt`, `/done`, `/init-workflow` in
every Claude Code session, in any directory.

```sh
# inside Claude Code:
/plugin marketplace add /path/to/this/repo
/plugin install ais@ais
```

Then in any project:

```
/init-workflow
```

Bootstraps that project's `.claude/` (hooks, settings, CLAUDE.md, ADRs).
From then on, every Claude session you open in that directory loads the
discipline automatically — hooks fire, CLAUDE.md is in context, the router
asks before edits.

### B. Self-contained per project (no global install)

If you don't want the plugin in your global Claude config, or you want to
share a repo with collaborators who don't have ais installed:

```
/init-workflow --self-contained
```

Copies the commands into the project's `.claude/commands/`. The project
becomes self-aware — works without anything globally installed. Trade-off:
each project carries its own copy of the commands, so updates to ais
require re-running `/init-workflow` to refresh.

### Triggering ais without any install

If you cloned this repo and want to try it before installing anything,
the repo is itself a working ais project (dogfooded). Open Claude Code
inside this directory and the `.claude/` config takes effect.

## How it feels in practice

The router-as-secretary case (no slash command needed):

```
you: TypeError: cannot unpack non-iterable NoneType at parser.py:42

  [router fires, intent=bug]
  Claude (via AskUserQuestion):
    Which workflow?
      (a) /plan a real fix       (b) /grunt a quick patch
      (c) diagnose only — root cause, no edits
  you: a
  Claude: <enters /plan discipline: lock, read-only exploration,
           ExitPlanMode, plan written to docs/plans/>
```

The explicit-command case (you already know what you want):

```
/plan add OAuth2 callback handler
   ↳ Opus, plan-mode discipline, ExitPlanMode → plan file written
/model sonnet
   ↳ implement against the plan
/adr use httpx over requests
   ↳ records the decision before it gets buried
/done
   ↳ verifies steps, runs verification commands, asks about ADRs
```

Mechanical, no-judgment work:

```
/grunt rename CamelCase to snake_case in scripts/
   ↳ Haiku, refuses on judgment calls
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
