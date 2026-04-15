---
description: "Encode books from queue with configurable limit"
allowed-tools: Read, Write, Bash
---

## Usage
```
/project:books-init --count 1
/project:books-init --count 5
/project:books-init              (default: 20)
```

## Steps
1. Parse `--count N` from command (default 20)
2. Read `books-init-queue.yaml`
3. Read `.claude/books_checkpoint.json` — skip completed entries
4. For the first N pending books:
   a. Check if book has `free_url` — skip if null
   b. Call book_encoder agent via claude --print
   c. Write skill files to `skills/BOOKS/<category>/`
   d. Update `_meta.md`
   e. Update checkpoint with completed slug
5. Report summary: encoded + skipped + failed

## Checkpoint format
```json
{
  "completed": ["slug1", "slug2"],
  "failed": [],
  "knowledge_stats": { "average_quality_score": 0.85 }
}
```
