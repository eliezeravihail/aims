# aims
*AI Manager System*

📄 **Site:** https://eliezeravihail.github.io/aims/

Lean code-development discipline for Claude Code. Five slash commands, three
project-local hooks, idempotent bootstrap. No multi-agent pipeline, no
orchestration overhead — just the discipline that makes single-dispatch
sessions reliable on Opus / Sonnet baselines.

## What this is for (and what it isn't)

The point of aims is **not** to make the agent smarter or more correct.
The model's reasoning capability is whatever it is — aims doesn't change it.

What aims actually does:

- **Keeps the human side of the work organized.** Plans on disk, decisions
  in ADRs, a router that asks before edits — a workflow you can fall into
  without having to remember ceremony every time.
- **Lets the agent know the project better.** CLAUDE.md, the ADR log, and
  plans on disk all become durable context that survives session
  compaction and crosses sessions. The Claude session that picks up your
  work tomorrow has access to what was decided yesterday and why.

What aims explicitly doesn't try to do:

- It doesn't change how the model reasons.
- It doesn't turn wrong answers into right ones.
- It doesn't substitute for tests, domain knowledge, or careful prompts.
- It doesn't add an "intelligence layer" via routers, validators, or
  multi-agent orchestration. (That was the previous design; see ADR-0002
  for why we dropped it.)

If the agent is making bad calls, aims will not fix that — better tests,
clearer requirements, or a different model will. aims addresses a different
problem: the human-side cost of remembering what was decided and why,
session after session.

## What you get

| Command            | Model  | Purpose                                                               |
|--------------------|--------|-----------------------------------------------------------------------|
| `/init-workflow`   | Sonnet | Bootstrap ADRs, hooks, memory tree, CLAUDE.md sections (idempotent)   |
| `/plan <task>`     | Opus   | Read-only exploration → ExitPlanMode → durable plan file              |
| `/adr <title>`     | Opus   | Record an architecture decision (append-only log)                     |
| `/grunt <task>`    | Haiku  | Mechanical edits: renames, formatting, log/config tweaks              |
| `/done [plan]`     | Opus   | Verify a plan's steps & checks; prompt for ADRs                       |
| `/memory-init`     | Sonnet | One-time scan to seed `docs/memory/` (per ADR-0007)                   |
| `/remember <note>` | Sonnet | Append a note to the right leaf of the memory tree                    |

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

Mode switch: `echo nudge > .claude/aims-mode` / `echo block > .claude/aims-mode`.

## A note on plugin sprawl

Command and tool pollution in AI coding environments is a real and growing
problem, not a hypothetical one. By early 2026 unofficial registries index
**16,000+ MCP servers** and GitHub hosts **20,000+ repositories**
implementing them. Teams routinely exceed Claude's 128-tool soft ceiling,
at which point tool-calling accuracy degrades — and every enabled plugin
contributes its full surface area (command definitions, agent descriptions,
MCP schemas) to the model's context on every turn, whether or not the
current task actually needs it. Five MCP servers with thirty tools each is
already 150 tool definitions, ~150K tokens, injected into every prompt.

The community is exploring partial mitigations:

- **Claude Code namespaces** plugin commands (`pluginname:command`) to
  avoid hard collisions. Helpful, but namespacing is mandatory in
  practice even when docs say otherwise (issue #15882), and subagents
  struggle to discover namespaced commands (issue #11328).
- **MCP gateways** apply the API-gateway pattern to tool fan-out: a
  single entry point, centralized auth/budgeting/filtering. Enterprise
  scope.
- **Dynamic / lazy tool loading** (MCP Tool Search and similar) loads a
  tool only when invoked, instead of pre-injecting all of them.
- **Sandboxing** (microVMs, gVisor, hardened containers) addresses
  *runtime* isolation but doesn't help with command-namespace scope.

What's still missing at the platform level is the equivalent of Python's
`venv` or Node's per-project `node_modules` — a real **per-project
scope** where a tool is *available here, invisible everywhere else*,
with no global registration step. Anthropic's namespacing is a step in
that direction but not a substitute for true per-project scoping.

Until that gap closes at the Claude Code level, aims opts out of the
global surface entirely: the four discipline commands (`/plan`, `/adr`,
`/grunt`, `/done`) live exclusively inside target projects you've
explicitly bootstrapped. The only file aims can ever expose globally is
`/init-workflow`, and only if you opt into the plugin install path —
otherwise even that stays scoped to the aims source repo.

If/when Claude Code grows a real per-project plugin scope, aims should
adopt it and retire its custom split. For now, the split below is the
mechanism.

## Install

Two paths. Both end with the same per-project state. **Only `/init-workflow`
is ever globally available** — the four discipline commands (`/plan`,
`/adr`, `/grunt`, `/done`) live exclusively in target projects you've
bootstrapped.

### Path A — Clone-and-bootstrap (recommended; zero global state)

1. **Clone (or download + extract) this repo** somewhere convenient.
   ```sh
   git clone https://github.com/eliezeravihail/aims.git ~/tools/aims
   ```

2. **Open Claude Code inside the aims source repo.**
   ```sh
   cd ~/tools/aims
   claude
   ```
   The repo is dogfooded — its own `.claude/commands/init-workflow.md`
   makes `/init-workflow` available locally without any global install.

3. **Bootstrap your target project.**
   ```
   /init-workflow /path/to/my-project
   ```
   Sniffs the target (read-only), asks a few gap-filling questions, shows
   a diff preview, applies only after you approve.

4. **From now on, use the target project.**
   ```sh
   cd /path/to/my-project
   claude
   ```
   The target's own `.claude/` provides `/plan`, `/adr`, `/grunt`, `/done`,
   `/memory-init`, `/remember` plus hooks and CLAUDE.md. **Nothing is
   installed globally** — open Claude in any unrelated directory and
   aims isn't there.

5. **Seed the memory tree (one-time).**
   ```
   /memory-init
   ```
   Inside the target, run this once to scan the codebase and populate
   `docs/memory/` (see ADR-0007). After that the tree maintains itself
   via the `post-edit-marker` and `stop-consolidate` hooks.

### Path B — Global plugin install (one global command for ergonomics)

If you'd rather not have to `cd ~/tools/aims` every time you bootstrap a
new project:

```sh
# inside Claude Code, anywhere:
/plugin marketplace add /path/to/this/repo
/plugin install aims@aims
```

This adds **only `/init-workflow`** to your global Claude config — not
the discipline commands. From any directory:

```
/init-workflow /path/to/my-project
```

Bootstraps the target identically to path A. The four discipline
commands still appear only inside bootstrapped projects.

The split is enforced by the repo layout: `commands/init-workflow.md` is
the single globally-visible file; `templates/commands/{plan,adr,grunt,
done}.md` are templates the bootstrap copies into each target. See
ADR-0005 for the rationale.

### What ends up in the target (either path)

```
TARGET/
├── CLAUDE.md                    # created or merged section-aware
├── docs/
│   ├── adr/
│   │   ├── README.md            # decision index
│   │   ├── _template.md
│   │   └── 0001-record-architecture-decisions.md
│   └── memory/                  # seeded later by /memory-init (ADR-0007)
└── .claude/
    ├── commands/                # /plan, /adr, /grunt, /done, /memory-init, /remember
    ├── hooks/                   # session-start, prompt-submit, pre-write,
    │                            # post-edit-marker, stop-consolidate, session-end
    ├── memory/                  # _lib, mark, new-leaf, find-dirty, lint,
    │                            # check-refs, consolidate, classify-inbox (.sh)
    ├── settings.json            # wires the hooks
    └── aims-mode                # nudge | block
```

Updating aims means `git pull` in the source repo (and `/plugin update` if
you took path B) plus re-running `/init-workflow` against your existing
targets to refresh hooks and commands. The merge-aware logic preserves
your CLAUDE.md customizations and existing ADRs.

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
commands/                    ← the only globally-installable surface
  init-workflow.md           ← becomes /init-workflow if plugin is installed
templates/                   ← never globally registered; copied per target
  commands/                  ← these become the target's .claude/commands/
    plan.md
    adr.md
    grunt.md
    done.md
  hooks/                     ← these become the target's .claude/hooks/
    session-start.sh
    prompt-submit.sh
    pre-write.sh
  CLAUDE.md.tmpl
  adr-readme.md.tmpl
  adr-template.md.tmpl
  adr-0001.md.tmpl
  plan-template.md.tmpl
  settings.json.tmpl
.claude/                     ← dogfood install (this repo is itself a target)
  commands/                  ← lets us run /init-workflow + the 4 disciplines here
  hooks/                     ← live hooks for working on aims itself
  settings.json
  aims-mode
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
