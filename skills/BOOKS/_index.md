# BOOKS — Loading Guide

## Loading protocol
1. Receive required category and topic
2. Read `skills/BOOKS/<category>/_meta.md` — select highest `quality_score`, non-stale book
3. Read `skills/BOOKS/<category>/<slug>/_index.md` — scan topic list (cheap, one-liner per topic)
4. If the topic exists → load `skills/BOOKS/<category>/<slug>/<topic>.md` only
5. Cite in your answer: book title + quality_score

## Book selection rules
| Condition | Action |
|-----------|--------|
| quality_score >= 0.80, stale=false | Use |
| quality_score 0.60–0.79 | Use with caveat |
| quality_score < 0.60 | Do not use — report |
| stale = true | Do not use — suggest /project:books-update |
| duplicate_of != null | Use the original book instead |

## Folder structure
```
skills/BOOKS/
  <CATEGORY>/
    _meta.md                  ← book registry for this category
    <slug>/
      _index.md               ← topic list (load first, always cheap)
      <topic>.md              ← full condensed content (load on demand)
```
