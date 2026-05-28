# aims — memory tree

Navigable, hand-curated documentation of what lives where, why it's
shaped the way it is, and what you should know before editing it.
Maintained automatically per ADR-0007 + ADR-0009: the
`post-edit-marker` hook flags leaves as `dirty` when their referenced
source changes; the throttled `Stop` hook injects an in-band
consolidation prompt that the active Claude Code session executes
via Edit (no external API key required).

This tree is a **navigator** over other memory sources. It references
`CLAUDE.md` sections, ADRs, plans, and tests — it never copies them.

## Tags

- **discipline/** — the slash commands that define the aims workflow.
  Post-ADR-0010 the active surface is `/plan` and `/install-on`;
  historical nodes for `/done`, `/adr`, `/grunt`, `/remember` are
  kept as superseded breadcrumbs.
- **hooks/** — the runtime enforcement layer outside the memory
  subsystem (pre-write gating, session-start info, prompt-submit
  context injection).
- **memory/** — the ADR-0007 subsystem itself: helpers, Phase A
  marker, Phase B throttled in-band consolidation (ADR-0009).
- **installer/** — the clone-and-bootstrap path (`/install-on` +
  the `templates/*.tmpl` files it substitutes).
- **testing/** — bash smoke tests for the marker + consolidation
  pipeline.

## Navigation

The model usually navigates by reading this README plus one or two
per-tag READMEs, then a specific leaf. To browse manually:

    cat docs/memory/<tag>/README.md
    cat docs/memory/<tag>/<leaf>.md

To check tree health: `bash .claude/memory/lint.sh`.
