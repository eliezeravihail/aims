# aims
*AI Manager System*

📄 **Site:** https://eliezeravihail.github.io/aims/

Lean code-development discipline for Claude Code. Two slash commands, six
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

Two slash commands — that's the whole user-facing surface (see ADR-0010):

| Command              | Model | Purpose                                                                       |
|----------------------|-------|-------------------------------------------------------------------------------|
| `/plan <task>`       | Opus  | Read-only exploration → ExitPlanMode → durable plan file → inline close-out   |
| `/install-on <path>` | Opus  | Bootstrap (or idempotently re-install) ADRs, hooks, memory tree, CLAUDE.md    |

Everything that used to be its own command now happens **inline**, with no
command to remember:

- **Plan close-out** (verify steps, run `## Verification`, decide ADRs, mark
  the plan `completed`, consolidate memory) runs at the end of the
  implementation session, nudged by the Stop hook when an `in-progress` plan
  exists.
- **ADRs** are auto-decided per change: created when it's a clear
  architectural commitment, skipped for bug/refactor/doc/test/mechanical work,
  asked only when borderline. They always start `proposed`.
- **Memory bootstrap** runs at the end of `/install-on`; maintenance after
  that is the automatic marker + consolidation loop (ADR-0007 / ADR-0009).
- **Mechanical edits and notes** are just ordinary edits — do the work.

The model is pinned per command — it switches automatically and returns to
your session model after.

## Hooks (per-project, installed by `/install-on`)

- **SessionStart** — surfaces in-progress plans, recent ADRs, and the
  memory-tree overview.
- **UserPromptSubmit** — **router** (informs, never locks). Detects intent
  (bug, feature, refactor, decision, mechanical, question) and, for an
  actionable prompt, injects a FACTUAL planning-convention note. It never
  creates a lock. Suppresses on slash-prefixed prompts and short follow-ups.
  See ADR-0004 + ADR-0020.
- **PreToolUse** (`pre-write`) — never blocks. On the first source edit of a
  session with no in-progress plan, injects the planning convention once, as a
  factual note. "Source" is defined by exclusion (anything outside `docs/`,
  `tests/`, `*.md`, `.claude/`); no project path is hardcoded. See ADR-0020.
- **PostToolUse** (`post-edit-marker`) — when an edit touches a file a memory
  node references, flags that node `dirty`, injects a factual note naming the
  node to update, and stamps an **advisory** marker (`<leaf>.lock`; NOT a
  block) for cross-session coordination (ADR-0007, ADR-0019/0020).
- **Stop** (`stop-consolidate`) — throttled. Injects the in-band memory
  consolidation prompt for any `dirty` nodes (ADR-0009), and emits the plan
  close-out nudge when an `in-progress` plan exists (ADR-0010).
- **SessionEnd** — flushes any pending memory state at session shutdown.

All injected text is factual, never an imperative command (ADR-0020): an
imperative trips Claude's prompt-injection defense and is shown to the user
instead of being treated as context. No hook ever blocks an edit — there is no
`aims-mode` and no planning lock.

When the assistant's user-facing reply touches aims-internal topics (memory
nodes, consolidation queue, inbox, dirty markers, plan close-out, hook
status), that part of the reply is prefixed with `==== AIMS (internal) ====`
and kept terse — one line or a short phrase ("nodes updated", "queue
drained", "4 dirty"). No per-node prose unless the user asks (ADR-0021).

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
global surface entirely: the `/plan` discipline command lives exclusively
inside target projects you've explicitly bootstrapped. The only file aims
can ever expose globally is `/install-on`, and only if you opt into the
plugin install path — otherwise even that stays scoped to the aims source
repo.

If/when Claude Code grows a real per-project plugin scope, aims should
adopt it and retire its custom split. For now, the split below is the
mechanism.

## Install

Two paths. Both end with the same per-project state. **Only `/install-on`
is ever globally available** — the `/plan` discipline command lives
exclusively in target projects you've bootstrapped.

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
   The repo is dogfooded — its own `.claude/commands/install-on.md`
   makes `/install-on` available locally without any global install.

3. **Bootstrap your target project.**
   ```
   /install-on /path/to/my-project
   ```
   Sniffs the target (read-only), asks a few gap-filling questions, shows
   a diff preview, applies only after you approve, then seeds the memory
   tree against the target as its final step.

4. **From now on, use the target project.**
   ```sh
   cd /path/to/my-project
   claude
   ```
   The target's own `.claude/` provides `/plan` plus hooks and CLAUDE.md.
   **Nothing is installed globally** — open Claude in any unrelated
   directory and aims isn't there.

### Path B — Global plugin install (one global command for ergonomics)

If you'd rather not have to `cd ~/tools/aims` every time you bootstrap a
new project:

```sh
# inside Claude Code, anywhere:
/plugin marketplace add /path/to/this/repo
/plugin install aims@aims
```

This adds **only `/install-on`** to your global Claude config — not the
`/plan` discipline command. From any directory:

```
/install-on /path/to/my-project
```

Bootstraps the target identically to path A. `/plan` still appears only
inside bootstrapped projects.

The split is enforced by the repo layout: `commands/install-on.md` is
the single globally-visible file; `templates/commands/{install-on,plan}.md`
are templates the bootstrap copies into each target. See ADR-0005 for the
rationale.

### What ends up in the target (either path)

```
TARGET/
├── CLAUDE.md                    # created or merged section-aware
├── docs/
│   ├── adr/
│   │   ├── README.md            # decision index
│   │   ├── _template.md
│   │   └── 0001-record-architecture-decisions.md
│   └── memory/                  # seeded by /install-on's final step (ADR-0007)
└── .claude/
    ├── commands/                # install-on, plan
    ├── hooks/                   # session-start, prompt-submit, pre-write,
    │                            # post-edit-marker, stop-consolidate, session-end
    ├── memory/                  # _lib, mark, new-node, find-dirty, lint,
    │                            # check-refs, consolidate, classify-inbox,
    │                            # doctor (.sh)
    ├── settings.json            # wires the hooks
    └── aims-mode                # nudge | block
```

`/install-on` is **idempotent** and doubles as the upgrade path: re-running
it overwrites hooks, memory scripts, and the two commands (with a diff
preview), deletes obsolete commands from a previous install, and **never
touches** existing CLAUDE.md sections, ADRs, plan files, or memory node
bodies. Update aims by `git pull` in the source repo (and `/plugin update`
if you took path B), then re-run `/install-on` against your targets.

## How it feels in practice

The router-as-secretary case (no slash command needed):

```
you: TypeError: cannot unpack non-iterable NoneType at parser.py:42

  [router fires, intent=bug]
  Claude (via AskUserQuestion):
    Which workflow?
      (a) /plan a real fix       (b) quick patch inline
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
   ↳ httpx-over-requests is a clear architectural call → ADR written
     inline (status: proposed), no command needed
   ↳ at the end, the Stop hook nudges close-out: verify steps, run
     `## Verification`, mark the plan completed, consolidate memory
```

Mechanical or note-taking work needs no command — just describe it and
the edit happens inline:

```
you: rename CamelCase to snake_case in scripts/
   ↳ ordinary inline edit; the router stays out of the way for
     obviously-scoped mechanical work
```

## Layout

```
.claude-plugin/
  plugin.json
  marketplace.json
commands/                    ← the only globally-installable surface
  install-on.md              ← becomes /install-on if plugin is installed
templates/                   ← never globally registered; copied per target
  commands/                  ← these become the target's .claude/commands/
    install-on.md
    plan.md
  hooks/                     ← these become the target's .claude/hooks/
    session-start.sh
    prompt-submit.sh
    pre-write.sh
    post-edit-marker.sh
    stop-consolidate.sh
    session-end.sh
  memory/                    ← memory subsystem scripts copied per target
  CLAUDE.md.tmpl
  adr-readme.md.tmpl
  adr-template.md.tmpl
  adr-0001.md.tmpl
  plan-template.md.tmpl
  settings.json.tmpl
.claude/                     ← dogfood install (this repo is itself a target)
  commands/                  ← lets us run /install-on + /plan here
  hooks/                     ← live hooks for working on aims itself
  memory/                    ← live memory scripts for the dogfooded tree
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
3. **Hooks inform, they never block (ADR-0020).** No hook can stop an edit;
   each only injects factual context. Discipline comes from awareness — the
   planning convention and node-update reminders are surfaced at the moment
   they matter, and the human stays in control.
4. **Idempotent and merge-aware.** Running `/install-on` on an existing
   project must not damage existing CLAUDE.md, settings, or layout.
