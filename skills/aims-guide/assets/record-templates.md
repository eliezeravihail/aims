# Record templates (co-located)

Copy a block, fill `title` + `date` + the body, place the file **in the code tree** at the node it
governs, then anchor it: `python3 knowledge/anchor.py <record>`. The tool writes the `hash:`/`shape:`
line — never you. There is no `code:` field: the record's own directory is its subject. Dates are
`YYYY-MM-DD`.

---

## Charter — `charter.md` at the repo root (cross-cutting; no anchor)

```markdown
---
title: "<Product> — charter"
date: <date>
---

## Primary goal
<what this product is for.>

## Non-goals
<what we deliberately do not design for yet.>
```

## Component — `<component-dir>/component.md` (inside the code directory; anchor is `shape:`)

```markdown
---
title: "<component>"
date: <date>
---

## Purpose
## Boundaries & seams   <!-- what it separates; what may cross; what it must not know -->
## Invariants          <!-- structural rules; point to the guarding test -->
```

## Decision — `<component-dir>/decisions/NNNN-slug.md`, or root `decisions/…` if cross-cutting (append-only)

```markdown
---
title: "<decision>"
date: <date>
---

Context → the decision → consequences → alternatives ("chose X over Y because Z").
If this supersedes an earlier decision, name it here.
```

## Requirement — `requirements/NNNN-slug.md` (root, or under the component it constrains)

```markdown
---
title: "<need>"
date: <date>
---

<the need, who needs it, why. A product-rule invariant goes here.>
```

## Insight — `<component-dir>/insights/{dev,design,code}/slug.md` (or root)

```markdown
---
title: "<lesson>"
date: <date>
---

<what was learned: what was tried, what failed, why — fact + reason, not a transcript.>
```

## Project-wide norm — a `decisions/` record at the repo root (no anchor)

A convention that applies to *all* code uniformly ("all types are PascalCase"). Root placement gives it
capsule-wide scope; it carries no anchor because a norm does not drift from a file.
