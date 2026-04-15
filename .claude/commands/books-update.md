---
description: "Find new editions and update stale books"
allowed-tools: Read, Write, WebSearch
---

For each book in `_meta.md`:
1. Search online for a newer edition
2. Is there a Tier-1 replacement for the same topic?
3. Is last_used > 18 months? → mark stale
4. Is there overlap with another book?

## Actions
- `refresh`  — update content, keep slug
- `replace`  — new book is 10%+ better
- `merge`    — two books with high overlap → merge
- `keep`     — no change needed

## Output
Report with recommendation and action per book.
