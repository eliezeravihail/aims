# capsa record templates (aims profile)

Copy the relevant block when filing a record, fill it, place the file at the node it governs, then
anchor it with `tools/aims_anchor.py` (see `references/design-record.md`). Fields follow the vendored
capsa spec (`vendor/capsa/project/SPEC.md`); `anchors:` / `shape:` are aims additions (unknown keys
capsa preserves — `docs/format-profile.md` §2). Dates are `YYYY-MM-DD`.

---

## Manifest — `.capsa/core/capsule.yaml` (create once)

```yaml
capsa_version: "0.8.0"
project:
  name: "<Human Name>"
  slug: <kebab-slug>
  repo: "<repo url, optional>"
  created: <YYYY-MM-DD>
status: active        # planning | active | maintained | paused | archived
```

## Charter — `.capsa/charter.md` (root, normative)

```markdown
---
updated: <YYYY-MM-DD>
---

# <Product> — charter

## Primary goal
<one or two sentences: what this product is for.>

## Use scenarios
<only the start-to-useful-result scenarios that materially shape engineering decisions.>

## Non-goals
<what we deliberately do not design for yet, so the Worker does not build for it.>
```

## Requirement — `.capsa/requirements/NNNN-slug.md` (normative)

```markdown
---
id: <N>
title: "<need>"
level: must            # must | should | may
status: accepted       # proposed | accepted | met | unmet | dropped
opened: <YYYY-MM-DD>
verification:
  status: unverified   # verified | unverified | failed
  method: none         # test | scan | ci | manual | none
  evidence_ref: null   # a test id / path / commit once met
  checked_at: null
anchors: []            # [{path, hash}] on the code that satisfies it, once there is any
---

<the need in prose — who needs it, why, acceptance nuance. A product-rule invariant goes here as a
`must` requirement.>
```

## Decision (ADR) — `.capsa/decisions/NNNN-slug.md` or `.capsa/components/<c>/decisions/NNNN-slug.md`

Append-only. To change a decision, write a new one that `supersedes:` it and set the old one's
`superseded_by:` + `status: superseded`.

```markdown
---
id: <N>
title: "<decision>"
status: accepted       # proposed | accepted | superseded | deprecated
date: <YYYY-MM-DD>
supersedes: null       # <id> of the ADR this replaces, if any
superseded_by: null
tags: []
anchors: []            # [{path, hash}] on the files that carry the decision
---

## Context
<the forces — product/repository facts that make this decision necessary now.>

## Decision
<the choice.>

## Consequences
<what follows, including the cost accepted.>

## Alternatives considered
<"chose X; Y not chosen because Z" — the road not taken lives here.>
```

## Component — `.capsa/components/<slug>/component.md` (normative)

The current structure of a part. Anchor with `--shape` on its source subtree.

```markdown
---
title: "<component>"
status: active         # planned | active | deprecated | retired
created: <YYYY-MM-DD>
code_globs: []         # paths in the product repo this component owns
links: []              # e.g. {rel: depends_on, to: components/<other>/component}
shape: null            # {root, children_hash, depth} — stamped by aims_anchor --shape
---

## Purpose
<what this part is for.>

## Boundaries & seams
<what it separates, and the payload that crosses. Only foundational deps + framework domain types may
cross a public seam.>

## Invariants
<structural rules that must hold (e.g. "normalization has a single owner"). Point to the guarding test.>

## What it must not know
<the knowledge this part is deliberately kept ignorant of.>

## Likely change axes
<expected independent variation that justifies a seam — with the reason, not speculation.>

## Confined dependencies
<heavy but replaceable deps and which boundary confines each.>
```

## Insight — `.capsa/insights/{dev,design,code}/slug.md` (descriptive)

```markdown
---
kind: dev              # dev | design | code (MUST match the subdirectory)
title: "<lesson>"
created: <YYYY-MM-DD>
code_globs: []         # REQUIRED iff kind: code
tags: []
anchors: []            # [{path, hash}] if tied to specific code
---

<what was learned: what was tried, what failed, why — fact + reason, not a transcript.>
```
