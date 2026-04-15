---
description: "Agent 4 — find the best foundational book for a given domain (Haiku)"
allowed-tools: Read, WebSearch
---

1. Read `agents/prompts/prompt_versions.yaml`
2. Load the Agent 4 version defined there (runs on Haiku — return concise structured output only)

## Required input
Technical domain (e.g. "object detection", "NLP transformers")

## Required output
Full BOOK_RECOMMENDATION per Agent 4 format.
If more than one candidate — rank by tier then relevance.
