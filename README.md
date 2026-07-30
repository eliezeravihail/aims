# aims
*AI Manager System*

📄 **Site:** https://eliezeravihail.github.io/aims/

Lean code-development discipline for Claude Code. Two slash commands,
project-local hooks that inform but never block, idempotent bootstrap.
No multi-agent pipeline, no orchestration overhead — just the discipline
that makes single-dispatch sessions reliable on Opus / Sonnet baselines.

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

Planning is a project **behavior**, not a command to remember (ADR-0022).
For a non-trivial change, the assistant runs read-only discovery → writes a
`status: draft` plan to `.capsa/plans/` → asks for approval → implements →
inline close-out. The `prompt-submit` hook describes this convention
factually for every actionable prompt.

aims stores its management truth as a conforming **Capsa 0.2.0** capsule at
`.capsa/` — aims is the active self-maintenance layer over that passive,
schema-backed capsule (decision 0031). Decisions live in
`.capsa/decisions/`, plans in `.capsa/plans/`, the code-anchored memory in
`.capsa/insights/`, with a `charter.md` and a `capsule.yaml` manifest; a
vendored stdlib-only validator (`validator/validate.py`) checks conformance.

Two slash commands exist as optional shortcuts (see ADR-0010, ADR-0022):

| Command              | What it does                                                                                          |
|----------------------|--------------------------------------------------------------------------------------------------------|
| `/plan <task>`       | Dispatches Phase 1-2 to an Opus subagent (read-only discovery + draft write); main session resumes for approval / implementation / close-out. Use when the session model is not Opus. |
| `/install-on <path>` | Bootstrap (or idempotently re-install) a Capsa capsule (`.capsa/`) + the vendored validator, hooks, and CLAUDE.md.        |

Everything that used to be its own command now happens **inline**, with no
command to remember:

- **Plan close-out** (verify steps, run `## Verification`, decide ADRs, mark
  the plan `completed`, consolidate insights) runs at the end of the
  implementation session, nudged by the Stop hook when an `in_progress` plan
  exists.
- **ADRs** (Capsa decision records) are auto-decided per change: created when
  it's a clear architectural commitment, skipped for bug/refactor/doc/test/
  mechanical work, asked only when borderline. They always start `proposed`.
- **Insight bootstrap** runs at the end of `/install-on`; maintenance after
  that is the automatic marker + consolidation loop (ADR-0007 / ADR-0009).
- **Mechanical edits and notes** are just ordinary edits — do the work.

`/plan` does NOT switch the main session model — only the Phase 1-2
subagent runs on Opus (ADR-0022). Implementation and close-out run on
whatever the main session is on.

## Hooks (per-project, installed by `/install-on`)

- **SessionStart** — surfaces in-progress plans, recent decisions, and the
  charter for orientation.
- **UserPromptSubmit** — **shape-gated convention note** (informs, never
  locks). For a task-shaped prompt (length ≥ 30 chars, no code fence, not
  a trailing-`?` question) injects a FACTUAL planning-convention note —
  no intent classification, language-neutral by construction (ADR-0029).
  It never creates a lock. Suppresses on slash-prefixed prompts and short
  follow-ups. See ADR-0020 + ADR-0029.
- **PreToolUse** (`pre-write`) — never blocks. On the first source edit of a
  session with no `status: draft`/`status: in_progress` plan in `.capsa/plans/`,
  injects a **state-aware** factual note that names the specific file being
  edited, the missing plan, and the approval-semantics rule (brief
  `yes`/`do it` approvals authorize Phase 2, not Phase 4). "Source" is
  defined by exclusion (anything outside `.capsa/`, `docs/`, `tests/`, `*.md`,
  `.claude/`); no project path is hardcoded. The note fires once per
  session. See ADR-0020 + ADR-0023.
- **PostToolUse** (`post-edit-marker`) — when an edit touches a file an insight's
  `code_globs` covers, names that insight (its staleness is then **computed**
  from the insight's `updated:` date vs git — Capsa §1.4, no stored flag) and
  refreshes an **advisory** marker kept OUTSIDE the capsule (NOT a block) for
  cross-session awareness (ADR-0007, ADR-0024/0030 — the strict `.lock` mutex
  is retired).
- **Stop** (`stop-consolidate`) — throttled. Injects the in-band consolidation
  prompt for any **stale** insights: **delta-append by default**, full
  compaction only past size thresholds (ADR-0009/0028), ending with
  `mark.sh <insight> consolidated` which bumps `updated:`. Also emits the plan
  close-out nudge when an `in_progress` plan exists (ADR-0010).
- **SessionEnd** — flushes any pending memory state at session shutdown.

All injected text is factual, never an imperative command (ADR-0020): an
imperative trips Claude's prompt-injection defense and is shown to the user
instead of being treated as context. No hook ever blocks an edit — there is no
`aims-mode` and no planning lock.

When the Stop / consolidation-update hook reports its result, that report
is emitted as a single short line `===[aims: <message>]===` — examples:
`===[aims: insights updated]===`, `===[aims: queue drained]===`,
`===[aims: 4 stale]===`. The marker applies ONLY to the update-hook
result, not to regular conversational mentions of aims topics elsewhere
in a reply (ADR-0021).

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
├── .capsa/                      # the Capsa capsule (bootstrapped by /install-on)
│   ├── capsule.yaml             # manifest
│   ├── charter.md               # project vision / conventions
│   ├── decisions/               # ADRs (NNNN-slug.md)
│   ├── plans/                   # plans (NNNN-slug.md)
│   └── insights/{code,dev,design}/   # code-anchored memory (ADR-0007)
├── validator/validate.py        # vendored Capsa validator (stdlib only)
├── schema/*.json                # vendored Capsa schemas
└── .claude/
    ├── commands/                # install-on, plan
    ├── hooks/                   # session-start, prompt-submit, pre-write,
    │                            # post-edit-marker, exit-plan-mode,
    │                            # stop-consolidate, session-end, pre-compact
    ├── memory/                  # _lib, mark, new-insight, find-dirty, lint,
    │                            # consolidate, classify-inbox, doctor (.sh)
    └── settings.json            # wires the hooks
```

`/install-on` is **idempotent** and doubles as the upgrade path: re-running
it overwrites hooks, memory scripts, the vendored validator, and the two
commands (with a diff preview), deletes obsolete commands from a previous
install, and **never touches** existing CLAUDE.md sections or capsule records
(decisions, plans, insight bodies, the charter). Update aims by `git pull` in
the source repo (and `/plugin update` if you took path B), then re-run
`/install-on` against your targets.

## How it feels in practice

The natural-planning case (no slash command needed):

```
you: TypeError: cannot unpack non-iterable NoneType at parser.py:42

  [prompt-submit injects the planning convention as factual context]
  Claude: <reads, judges non-trivial, writes
           .capsa/plans/NNNN-fix-parser-none.md with status: draft>
  Claude: Draft saved to .capsa/plans/…. Approve / edit / abort?
  you: approve
  Claude: <flips status to in_progress, implements, runs verification,
           writes a decision if architectural, marks completed, refreshes
           the affected insights — all inline, no /done command>
```

The Opus-subagent case (main session is on Sonnet/Haiku and you want
Opus-quality planning):

```
you: add an OAuth2 callback handler
  Claude: This is non-trivial and the session is on Sonnet — use
          /plan for an Opus planner subagent, or plan inline here?
  you: /plan add OAuth2 callback handler
  Claude: <dispatches Phase 1-2 to an Opus subagent; main session
           stays on Sonnet, receives the draft path, resumes for
           Phase 3 → 5 — approval, implementation, inline close-out>
```

Trivial / mechanical work skips planning, but the judgement is
declared (CLAUDE.md "Trivial-skip must be declared"):

```
you: rename CamelCase to snake_case in scripts/
  Claude: Trivial — no plan, proceeding inline.
          <ordinary edit; the pre-write note still fires once per
           session as a factual reminder, never blocks>
```

On every edit, the `post-edit-marker` hook names affected insights (their
staleness is computed from `updated:` vs git); the throttled `Stop` hook
later injects the in-band consolidation prompt, and the consolidation result
is reported back in a single `===[aims: <message>]===` line (ADR-0021).

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
    exit-plan-mode.sh
    stop-consolidate.sh
    session-end.sh
    pre-compact.sh
  memory/                    ← insight/consolidation scripts copied per target
  CLAUDE.md.tmpl
  charter.md.tmpl
  capsule.yaml.tmpl
  decision.md.tmpl
  plan-template.md.tmpl
  settings.json.tmpl
validator/                   ← vendored Capsa validator (copied per target)
schema/                      ← vendored Capsa schemas (copied per target)
.capsa/                      ← this repo's own capsule (aims is its own target)
  capsule.yaml  charter.md  decisions/  plans/  insights/
.claude/                     ← dogfood install (this repo is itself a target)
  commands/                  ← lets us run /install-on + /plan here
  hooks/                     ← live hooks for working on aims itself
  memory/                    ← live insight scripts for the dogfooded capsule
  settings.json
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
   planning convention and insight-update reminders are surfaced at the moment
   they matter, and the human stays in control.
4. **Idempotent and merge-aware.** Running `/install-on` on an existing
   project must not damage existing CLAUDE.md, settings, or layout.
