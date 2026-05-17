# ADR-0005: Two install paths; only /init-workflow ever goes global
Status: accepted
Date: 2026-05-06
Supersedes: —
Superseded by: —

## Context

aims ships as a Claude Code plugin (manifest under `.claude-plugin/`). The
standard plugin install model is global: `/plugin install aims@aims` adds
the plugin's `commands/` directory to every Claude Code session in every
directory. With our five commands (`init-workflow`, `plan`, `adr`,
`grunt`, `done`), that would mean `/plan` and friends appear in projects
where the user hasn't opted into aims discipline — visual noise at best,
surprising behaviour at worst.

We also want users to be able to install aims without touching their
global Claude config at all — by cloning the source repo, running
Claude inside it, and bootstrapping a target project. That path needs
to work without any plugin install.

The two requirements together:

- Some users will want a global install for ergonomics ("I just want
  `/init-workflow` to be available everywhere").
- No user wants the discipline commands (`/plan`, `/adr`, `/grunt`,
  `/done`) appearing in unrelated projects.
- The clone-and-bootstrap path must remain self-sufficient — running
  Claude inside the aims source repo gives access to `/init-workflow`
  with no global state involved.

## Decision

aims supports **two install paths**, and **only `/init-workflow` is ever
globally visible**, in either path.

The four discipline commands are physically separated from the
globally-installable surface:

- `commands/init-workflow.md` — the only file at the plugin's
  globally-visible commands location. If a user runs `/plugin install
  aims@aims`, this is the *only* command that shows up in every Claude
  Code session.
- `templates/commands/{plan,adr,grunt,done}.md` — the discipline
  commands, treated as templates. Never globally registered. Copied to
  `<target>/.claude/commands/` by `/init-workflow` during bootstrap.

Both install paths produce the same end state in the target:

| Install path                  | What ends up where                                       |
|-------------------------------|----------------------------------------------------------|
| **Clone-and-bootstrap** (primary) | Run `claude` inside aims source repo → `/init-workflow <target>` is available locally → it copies templates to `<target>/.claude/`. |
| **Global plugin install** (optional) | `/plugin install aims@aims` → `/init-workflow` available everywhere → run `/init-workflow <target>` from any directory → same copy happens. |

Either way:
- The target's `.claude/commands/` gets exactly the four discipline commands.
- The target's `.claude/hooks/`, `.claude/settings.json`, `CLAUDE.md`, and
  `docs/adr/` get scaffolded.
- No discipline commands ever appear in projects the user didn't
  bootstrap.

## Consequences

- ✅ Zero discipline-command pollution. `/plan`, `/adr`, `/grunt`,
  `/done` can only appear in projects explicitly bootstrapped.
- ✅ Optional ergonomics: users who want `/init-workflow` everywhere
  install the plugin globally; the cost is one extra slash command in
  their menu, not five.
- ✅ Targets are self-contained — they survive deletion of both the
  aims source repo and any global plugin install.
- ✅ Sharing works: a collaborator who clones a bootstrapped target
  gets aims discipline automatically (everything is under `.claude/`
  and `docs/`), with no aims install required on their side.
- ⚠️ Layout has two parallel "commands" locations: top-level
  `commands/` (one file) and `templates/commands/` (four files). The
  split is meaningful — visibility scope, not duplication — but it's
  a wrinkle a casual reader has to learn. Documented in this ADR and
  the README's "Layout" section.
- ⚠️ Each target carries its own copy of the discipline commands. Bug
  fixes in aims require re-running `/init-workflow` per target to
  propagate. We accept this — targets are usually long-lived and aims
  changes are infrequent.
- 🔒 Closes the door on a "discipline commands appear globally" UX.
  aims is opt-in per project, by design, in both install paths.

## Alternatives considered

- **Global install with all 5 commands** — rejected: pollutes the
  command surface in unrelated projects. The user explicitly objected.
- **Clone-and-bootstrap only, drop plugin manifest** — rejected: zero
  cost to keep the manifest, and it leaves the door open for users who
  want global `/init-workflow` ergonomics.
- **Move discipline commands to a separate sub-plugin** — rejected:
  over-engineering. The `templates/commands/` split achieves the same
  scope-isolation in one directory rename.
- **A bash bootstrap script** (no Claude Code involvement) —
  rejected: duplicates the logic in `init-workflow.md` and gives up
  the interview / diff-preview UX.

## Verification

- `commands/init-workflow.md` documents the target-path-required
  flow ("How this command is used" section), defining `AIMS_ROOT` as the
  cwd and `TARGET` as `$ARGUMENTS`, and forbidding writes outside `TARGET`.
- The plugin's globally-visible surface is exactly one file:
  `commands/init-workflow.md`. Verify with
  `find commands -maxdepth 1 -name '*.md'` → should list only
  `init-workflow.md`.
- The four discipline commands live at `templates/commands/{plan,adr,
  grunt,done}.md` and are referenced by `init-workflow.md` for copying
  to targets.
- README "Install" section documents both paths with clone-and-bootstrap
  as primary; layout diagram reflects the split.
