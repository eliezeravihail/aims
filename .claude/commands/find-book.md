---
description: "Book Finder — find the best foundational book for a given domain (Haiku)"
allowed-tools: Read, WebSearch
---

1. Read `agents/prompts/prompt_versions.yaml`
2. Load the Book Finder version defined there (runs on Haiku — return concise structured output only)

## Required input
Technical domain (e.g. "object detection", "NLP transformers")

## Required output
Full BOOK_RECOMMENDATION per Book Finder format.
If more than one candidate — rank by tier then relevance.
