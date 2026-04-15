---
description: "Book encoding queue — isolated subprocess per book with checkpointing"
allowed-tools: Read, Write, Bash
---

1. Read `books-init-queue.yaml`
2. Read `.claude/books_checkpoint.json` — skip completed entries
3. For each pending book:
   a. Run isolated subprocess: `claude --print < encode_prompt`
   b. Write result to checkpoint (success / failed)
   c. Do not start the next book until the current one finishes

## Dedupe check before each encode
Read `skills/BOOKS/<category>/_meta.md`.
If a similar book exists — skip and record "skipped: duplicate".

## Checkpoint update after each book
```json
{
  "completed": ["<slug>"],
  "failed": [],
  "knowledge_stats": { "average_quality_score": <updated> }
}
```
