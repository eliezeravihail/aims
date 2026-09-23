---
title: "a record sits next to what it is about — beside a file, beside a folder, or at the root"
date: 2026-09-22
---

**Context.** `0002` gave design knowledge two homes: a companion beside one source file, or a root record for
the whole project. That leaves no place for knowledge that is true of a folder and of nothing else — a
constraint every file in `src/parsers/` obeys and nothing outside it does. Measured: in a blind placement probe
answered from the guidance alone, such a fact was promoted to `architecture.md`, which claims the whole system
obeys it. The anchor tool already accepted a folder record (`src/parsers.md` beside `src/parsers/`), filing it
unanchored; only the text had no place for it.

The deeper defect was that the guidance was tables with no rule behind them. Where a row matched, placement
worked; where none did, a filer guessed (3 of 8 probe cases determined before, 6 of 8 after).

**Decision.** State the one rule the tables were instances of, and let the homes follow from it:

> Discussions and decisions **not evident from the code itself** go in a `.md` file next to what they are
> about — beside the relevant file, in the relevant module's folder, or at the project root if they concern
> the whole project. **Everything else belongs in the code's own documentation.**

A folder record is `<dir>.md` beside the folder, with the companion's three sections and no anchor (a folder
has no single content to hash). `0002`'s co-location stands; this widens where "co-located" can point.

**Rejected.** *Counting the files a fact binds* as the placement procedure — it was tried, and it turned an
idea into a procedure that a reader had to execute rather than understand. *Promoting folder-scoped knowledge
to `architecture.md`* — overstates its scope. *Copying it into each file's companion* — understates it, and
multiplies a single fact into copies that drift apart.

**Consequence.** `design-record.md`, `format.md`, `record-templates.md`, `SKILL.md`, `CLAUDE.md` and `README.md`
state the rule first. `tests/coherence.sh` now fails if a shipped surface still says "two homes".
