# discipline/

The slash commands that define the aims discipline. Per ADR-0010 the
surface is now **two commands**: `/plan` (with inline close-out) and
`/install-on`. Everything previously fronted by `/done`, `/adr`,
`/grunt`, and `/remember` moved inline.

## Leaves

- **plan.md** — `/plan`: creates the planning-lock, drafts a plan
  (≤80 lines, starts with `## TL;DR`), persists it under
  `docs/plans/`, then implementation runs normally; close-out
  (verify, auto-ADR, mark completed, memory consolidation) happens
  inline, nudged by the Stop hook when an in-progress plan exists.
- **done.md** — `/done` is removed (ADR-0010). Kept here as a
  historical leaf so older sessions resolving the path still find
  context; the file body documents what the close-out now does
  inline.
- **adr.md** — `/adr` is removed (ADR-0010). ADRs are now proposed
  automatically during plan close-out per a confidence rule (create
  on clear architectural commitment; skip on bug/refactor/doc/test/
  mechanical; ask when borderline). Manual ADR creation is still
  fine: copy `docs/adr/_template.md` to `NNNN-slug.md`.
- **grunt.md** — `/grunt` is removed (ADR-0010). Mechanical edits
  are just ordinary inline work now.

Related: `hooks/pre-write.md` enforces the planning-lock contract;
`installer/init-workflow.md` documents `/install-on` (renamed).
