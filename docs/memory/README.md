# aims — memory tree

Navigable, hand-curated documentation of what lives where, why it's
shaped the way it is, and what you should know before editing it.
Maintained automatically per ADR-0007: the `post-edit-marker` hook
flags leaves as `dirty` when their referenced source changes; the
throttled `Stop` hook calls Sonnet to update them.

This tree is a **navigator** over other memory sources. It references
`CLAUDE.md` sections, ADRs, plans, and tests — it never copies them.

## Tags

- **discipline/** — the four slash commands that define the aims
  workflow (`/plan`, `/done`, `/adr`, `/grunt`). Where you go to
  understand how aims wants you to work.
- **hooks/** — the runtime enforcement layer that lives outside the
  memory subsystem (pre-write gating, session-start info,
  prompt-submit context injection).
- **memory/** — the ADR-0007 subsystem itself: helpers, Phase A
  marker, Phase B throttled consolidation, and the user-facing
  slash commands (`/memory-init`, `/remember`).
- **installer/** — the clone-and-bootstrap path (`/init-workflow`
  + the `templates/*.tmpl` files it substitutes).

## Navigation

The model usually navigates by reading this README plus one or two
per-tag READMEs, then a specific leaf. To browse manually:

    cat docs/memory/<tag>/README.md
    cat docs/memory/<tag>/<leaf>.md

To check tree health: `bash .claude/memory/lint.sh`.
