# Record templates (co-located)

Two homes. File-level knowledge → a companion beside the source file; cross-cutting → a root record.
Anchor a companion on filing: `python3 knowledge/anchor.py <companion>` (system records take no anchor).
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

## Dependencies — `dependencies.md` at the root (confined, replaceable deps)

```markdown
---
title: "dependencies"
date: <date>
---
- <dependency> — what it is for, and which boundary confines it
```

## ADR — `decisions/NNNN-slug.md` at the root (system-wide; append-only)

```markdown
---
title: "<decision>"
date: <date>
---
Context → the decision → consequences → alternatives ("chose X over Y because Z").
If this supersedes an earlier ADR, name it here.
```
