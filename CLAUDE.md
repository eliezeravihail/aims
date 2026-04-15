# knowledge-library-agents

## Always-active rules
- Always read `agents/prompts/prompt_versions.yaml` before invoking any agent, then load the exact versioned prompt file listed there.
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.
- Never encode a book without a verified free source — hallucinated content is not acceptable.

## Agent map
| Agent | Role | Model |
|-------|------|-------|
| book_finder  | Find best foundational book for a domain | claude-haiku-4-5-20251001 |
| book_encoder | Encode book topics into skill files      | claude-sonnet-4-6 |

## Primary entrypoints

### End-user commands
- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:encode-book`             — encode a single book (interactive)
- `/project:ingest-local-sources`    — encode a local PDF or text file

### Advanced / discovery
- `/project:find-book <domain>`      — find the best book for a domain (web search)
- `/project:books-init`              — encode all pending books from queue

### Maintenance
- `/project:books-status`            — coverage and quality report
- `/project:books-update`            — find new editions, refresh stale books
- `/project:books-audit`             — knowledge hygiene

## Encoding rules
- Books with no `free_url` must be ingested locally via `/project:ingest-local-sources`
- Each topic = one file: `skills/BOOKS/<CATEGORY>/<slug>_<topic>.md`
- Update `_meta.md` after every encode
