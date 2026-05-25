---
description: Append a note to the right leaf of the aims memory tree
argument-hint: "<note text>"
model: haiku
---

# /remember

You are filing a note into the **aims memory tree**: pick the best-fit
leaf (or propose a new one), then append the note to the appropriate
body section.

Note: **$ARGUMENTS**

This command is the cheap, fast lane (Haiku). It is NOT the right place
for project conventions, build commands, or model preferences — those
belong in `CLAUDE.md` via Claude Code's native `/memory` slash command.
Per ADR-0007 the tree and CLAUDE.md don't duplicate each other.

## Steps

### 1. Read the memory tree

- `cat docs/memory/README.md` (the tag list).
- For each tag, `cat docs/memory/<tag>/README.md` to see the leaves.
- Don't read every leaf — keep the read scan shallow.

### 2. Decide where this note belongs

The note maps to one of three outcomes:

| Note is about…                              | Action                                                  |
|---------------------------------------------|---------------------------------------------------------|
| an existing leaf's domain                   | append to that leaf                                     |
| a domain not yet covered, but significant   | scaffold a new leaf with `new-leaf.sh`, then append    |
| a project convention / build / models       | tell the user to use `/memory` (Claude-native) instead |

### 3. Pick the body section

Within the chosen leaf, append to the section that fits:

- `## Logical rules & invariants` — "X must always Y", invariants.
- `## Editing considerations` — gotchas, ordering requirements,
  things-not-to-do.
- `## Deliberations & history` — why a choice was made; links to ADRs.
- `## Open questions` — uncertainty, deferred decisions.

If none clearly fits, default to `## Open questions`. Do not invent
new section headings.

### 4. Append

- Use `Edit` to insert the note as a bullet in the chosen section.
  Single line if possible; prepend with today's date in ISO format
  (`YYYY-MM-DD: <note>`) so chronology is preserved.
- The PostToolUse marker hook will flip the leaf to `dirty: true`
  automatically — you don't need to do that yourself.

### 5. Confirm

Print: `noted in docs/memory/<path>.md → ## <Section>`

## Hard rules

- **Don't write to CLAUDE.md from this command.** If the note belongs
  there, suggest `/memory` and stop.
- **Don't open the Anthropic API.** This is a structural file-edit;
  Haiku's job is just to pick the right leaf and section.
- **Don't create a new leaf for a one-off note.** If the note doesn't
  justify a whole topic, file it under the nearest existing leaf's
  `## Open questions`.
- **Don't edit any frontmatter directly.** The marker hook owns
  `dirty:` and `last_touched:`.
