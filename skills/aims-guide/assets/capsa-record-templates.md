# capsa record templates (aims lean profile)

Copy a block, fill `title` + `date` + the body, place the file at the node it governs, add a `code:`
line if it concerns specific code, then anchor it: `python3 tools/aims_anchor.py <record>`. The tool
writes the `hash:`/`shape:` line — never you. Everything beyond `title`/`date`/`code` is optional; add
a field only when it earns its place. Dates are `YYYY-MM-DD`.

---

## Manifest — `.capsa/core/capsule.yaml` (create once)

```yaml
capsa_version: "0.8.0"
project: { name: "<Name>", slug: <kebab-slug>, created: <date> }
status: active
```

## Charter — `.capsa/charter.md` (root; pure intent, no anchor)

```markdown
---
title: "<Product> — charter"
date: <date>
---

## Primary goal
<what this product is for, in a sentence or two.>

## Non-goals
<what we deliberately do not design for yet.>
```

## Requirement — `.capsa/requirements/NNNN-slug.md`

```markdown
---
title: "<need>"
date: <date>
code: <path or dir/** it is satisfied by>   # omit if not tied to code yet
---

<the need, who needs it, why. A product-rule invariant goes here.>
```

## Decision (ADR) — `.capsa/decisions/NNNN-slug.md` (append-only)

To change a decision, write a new one; name the superseded one in the body.

```markdown
---
title: "<decision>"
date: <date>
code: <the file(s) or dir this decision governs>   # omit for a pure-thesis decision
---

Context → the decision → consequences → alternatives ("chose X over Y because Z").
If this supersedes an earlier decision, say which and why here.
```

## Component — `.capsa/components/<slug>/component.md` (anchor is `shape:`)

```markdown
---
title: "<component>"
date: <date>
code: <the directory this component owns>
---

## Purpose
## Boundaries & seams   <!-- what it separates; what may cross -->
## Invariants          <!-- structural rules; point to the guarding test -->
## What it must not know
```

## Insight — `.capsa/insights/{dev,design,code}/slug.md`

```markdown
---
title: "<lesson>"
date: <date>
code: <file(s) it is tied to>   # omit for a dev/design lesson not tied to code
---

<what was learned: what was tried, what failed, why — fact + reason, not a transcript.>
```
