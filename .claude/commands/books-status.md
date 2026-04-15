---
description: "Coverage and quality report for the BOOKS knowledge base"
allowed-tools: Read
---

Read all `skills/BOOKS/*/` directories and `.claude/books_checkpoint.json`.

## Report sections
1. Encoded books — slug, category, quality_score, last_used
2. Pending books — remaining entries from books-init-queue.yaml
3. Failures — what failed and why
4. Dedupe candidates — books with topic overlap > 80%
5. Stale knowledge — not accessed in > 18 months
6. Average quality_score per category
