# Record templates (co-located)

**Before reaching for a template:** a record holds only what the code *cannot*. If a docstring, a comment,
a name, a signature or a test could carry it, it goes there and nothing is filed — `references/design-record.md`
owns that gate. A skeleton's empty section is not a prompt to fill it.

Two homes. File-level knowledge → a companion beside the source file; cross-cutting → a root record.
Anchor a companion on filing: `python3 .aims/anchor.py <companion>` (system records take no anchor;
see `references/design-record.md` for the invocation and the aims-repo exception).
Dates are `YYYY-MM-DD`.

---

## File companion — `<source-file>.md` beside the source file (e.g. `src/render.py.md`)

```markdown
---
title: "render.py"
date: <date>
---
## Insights
- <what was learned about this file — tried, failed, why>
## Decisions
- <a file-level choice + the rule it imposes; append-only, supersede in place>
## Discussions
- <a trade-off weighed, an option considered, the road not taken>
```

Leave a section empty until it has content. The anchor is a `hash:` of the same-named source file,
stamped by the tool.

## Goals — `goals.md` at the root (system; no anchor)

```markdown
---
title: "goals"
date: <date>
---
## Primary goal
## Use scenarios
## Non-goals
```

## Architecture — `architecture.md` at the root (system; no anchor)

```markdown
---
title: "architecture"
date: <date>
---
## Boundaries & seams
## Invariants
## Likely change axes
```

## Base dependencies — `base-dependencies.md` at the root (the foundational substrate only)

```markdown
---
title: "base-dependencies"
date: <date>
---
- <the language / framework / pervasive base — what stands on it and why it is foundational>
```

## Dependencies — `dependencies.md` at the root (replaceable deps)

```markdown
---
title: "dependencies"
date: <date>
---
- <dependency> — what it is for, which boundary confines it (if one does), and anything known about it
  that a caller must respect
```

## Directory record — `<dir>.md` beside the directory (e.g. `src/parsers.md`; no anchor)

```markdown
---
title: "parsers"
date: <date>
---
## Insights
## Decisions
## Discussions
```

For knowledge true of every file in that directory and of nothing else.

## ADR — `decisions/NNNN-slug.md` at the root (system-wide; append-only)

```markdown
---
title: "<decision>"
date: <date>
---
Context → the decision → consequences → alternatives ("chose X over Y because Z").
If this supersedes an earlier ADR, name it here.
```
