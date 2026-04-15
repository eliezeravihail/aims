---
description: "Book Encoder — encode a single book from the internet into BOOKS"
allowed-tools: Read, Write, WebSearch
---

1. Read `agents/prompts/prompt_versions.yaml`
2. Load the Book Encoder version defined there

## Required input (from books-init-queue.yaml)
slug, title, authors, category, free_url, topics_to_encode

## Steps
1. If free_url is set — fetch with WebSearch or Read
2. Run dedupe check before encoding
3. Per topic — create `skills/BOOKS/<category>/<slug>_<topic>.md`
4. Update `skills/BOOKS/<category>/_meta.md`
5. Update `.claude/books_checkpoint.json`
