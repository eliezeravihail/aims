# Onboarding

This repo has two independent surfaces.

## Agent routing system
1. Install the plugin.
2. Read `agents/router.md` to see which agents are registered.
3. Invoke one with `/project:experts <request>` — the router picks SINGLE, LOOP, or CASCADE.
4. To add an agent: create `agents/<id>.md` and append a row to `agents/router.md`.

## Books knowledge library (separate concern)
1. Check coverage: `/project:books-status`
2. Query the KB: `/project:query-knowledge <topic>`
3. Encode a local source: `/project:ingest-local-sources`
