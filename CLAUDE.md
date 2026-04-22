# knowledge-library-agents

## Always-active rules
- Agent definitions live in `agents/<name>.md`. Read the relevant file before invoking — the frontmatter declares model + tools, the body is the full behavior spec.
- Route multi-agent work through `/project:experts`. The registry of available agents is `agents/router.md`.
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.
- Never encode a book without a verified free source — hallucinated content is not acceptable.

## Agents
| Agent | File | Role | Model |
|-------|------|------|-------|
| book_finder  | agents/book_finder.md  | Find best foundational book for a domain | claude-haiku-4-5-20251001 |
| book_encoder | agents/book_encoder.md | Encode a book into `skills/BOOKS/<cat>/<slug>/` | claude-sonnet-4-6 |

## Primary entrypoints

### End-user commands
- `/project:experts <request>`     — route the request: single agent, cascade (find→encode), or loop (encoder retries on quality failure)
- `/project:query-knowledge <topic>` — query the knowledge base
- `/project:ingest-local-sources`    — encode a local PDF or text file (read-only local FS path, bypasses the router)

### Maintenance
- `/project:books-status` — coverage and quality report

## Router modes (`/project:experts`)
| Intent  | Mode    | Pipeline                       |
|---------|---------|--------------------------------|
| FIND    | SINGLE  | book_finder                    |
| ENCODE  | LOOP    | book_encoder (max 3 retries)   |
| BUILD   | CASCADE | book_finder → book_encoder     |
| REFRESH | CASCADE | book_finder → book_encoder per stale slug |

Loops are driven by the `STATUS: RETRY <reason>` protocol: an agent that fails its own
quality gate returns that line instead of the normal output, and the router feeds the
reason back as `retry_hint` on the next iteration.

## Encoding rules
- Books with no `free_url` must be ingested locally via `/project:ingest-local-sources`
- Output: `skills/BOOKS/<CATEGORY>/<slug>/_index.md` + one `<topic>.md` per topic
- Update `_meta.md` after every encode
