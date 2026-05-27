---
description: Append a note to the right section of the right node in the aims memory tree
argument-hint: "[--section <name>] [--node <path>] <note text>"
model: haiku
---

# /remember

You are filing a note into the **aims memory tree**: pick the best-fit
node (or use `--node` to target one), then append the note to the
appropriate body section (or use `--section` to target one). The tree's
schema is ADR-0008 (six sections per node).

Note: **$ARGUMENTS**

This command is the cheap, fast lane (Haiku). It is NOT the right place
for project conventions, build commands, or model preferences — those
belong in `CLAUDE.md` via Claude Code's native `/memory` slash command.
Per ADR-0007 the tree and CLAUDE.md don't duplicate each other.

## Argument grammar

```
/remember [--section "<section name>"] [--node <repo-relative-path>] <free text>
```

Both flags are optional. Examples:

```
/remember the OAuth callback must validate redirect_uri exactly
  → auto-pick node, auto-pick section.

/remember --section "Known issues" "open: race on first call"
  → auto-pick node, target the named section.

/remember --node docs/memory/installer/init-workflow.md \
          --section "Invariants & gotchas" \
          "the memory tree install is mandatory, not optional"
  → target both node and section explicitly.
```

The six valid section names (ADR-0008):

- `Purpose`
- `Design rationale`
- `Invariants & gotchas`
- `Known issues`
- `Pointers`
- `Open questions`

If `--section` is given but the value doesn't match (case-insensitive,
ignoring punctuation), refuse and list the valid names.

## Steps

### 1. Parse arguments

Split `$ARGUMENTS` into flags + free text. Trim quotes around flag
values. Extract:

- `SECTION` (if `--section` present) — must be one of the six valid
  names; canonicalise capitalisation.
- `NODE` (if `--node` present) — must be a path that exists under
  `docs/memory/`; the file must have `node:` in frontmatter.
- `NOTE` — everything that's left.

If `NOTE` is empty after parsing, refuse and print the usage above.

### 2. Pick the node (if `--node` not given)

- `cat docs/memory/README.md` (the tag list).
- For each tag, `cat docs/memory/<tag>/README.md` to see node summaries.
- Don't read every node — keep the read scan shallow.

Map the note to one of three outcomes:

| Note is about…                              | Action                                                  |
|---------------------------------------------|---------------------------------------------------------|
| an existing node's domain                   | append to that node                                     |
| a domain not yet covered, but significant   | scaffold a new node with `new-node.sh`, then append     |
| a project convention / build / models       | tell the user to use `/memory` (Claude-native) instead  |

### 3. Pick the section (if `--section` not given)

Within the chosen node, choose the section that fits:

- `## Purpose` — one-line clarification of what the code does.
- `## Design rationale` — *why* the code is shaped this way.
- `## Invariants & gotchas` — "X must always Y"; things-not-to-do.
- `## Known issues` — bugs (open or fixed). Note prose may start with
  `open:` or `fixed:` to be clear.
- `## Pointers` — ADRs / plans / commits / external URLs.
- `## Open questions` — uncertainty, deferred design decisions.

If none clearly fits, default to `## Open questions`. Do not invent
new section headings.

### 4. Append

- Use `Edit` to insert the note as a bullet in the chosen section.
  Single line if possible; prepend with today's date in ISO format
  (`YYYY-MM-DD: <note>`) so chronology is preserved.
- If the section is `## Known issues` and the note doesn't already
  start with `open:` or `fixed:`, prepend `open: ` by default.
- The PostToolUse marker hook will flip the node to `dirty: true`
  automatically — you don't need to do that yourself.

### 5. Confirm

Print: `noted in <node-path> → ## <Section>`

## Hard rules

- **Don't write to CLAUDE.md from this command.** If the note belongs
  there, suggest `/memory` and stop.
- **Don't open the Anthropic API.** This is a structural file-edit;
  Haiku's job is just to pick the right node and section.
- **Don't create a new node for a one-off note.** If the note doesn't
  justify a whole topic, file it under the nearest existing node's
  `## Open questions`.
- **Don't edit any frontmatter directly.** The marker hook owns
  `dirty:` and `last_touched:`.
- **All references in the note must be repo-relative** per ADR-0008.
  No absolute paths or host-bound URLs back into this repo.
