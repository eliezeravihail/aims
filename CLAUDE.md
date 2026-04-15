# Dev Agent System v2

## Always-active rules
- Every agent runs in an isolated subprocess via `claude --print`.
- Always read `agents/prompts/prompt_versions.yaml` before invoking any agent, then load the exact versioned prompt file listed there.
- Validation uses three channels: static analysis + semantic validation + confidence scoring.
- Refactor changes are gated by `refactor_mode` (auto / review / blocked).
- BOOKS knowledge is loaded by `quality_score` descending; skip `stale=true` entries.

## Primary entrypoints
- `/project:dev-cycle`              — full adaptive pipeline
- `/project:books-init`             — encode book queue
- `/project:ingest-local-sources`   — encode a local folder of PDFs or text files
- `/project:books-status`           — coverage and quality report
- `/project:books-audit`            — knowledge hygiene

## Agent map
| Agent | Role | Model |
|-------|------|-------|
| Agent 1 | Refactoring + Guardrails | Sonnet |
| Agent 2 | Validation + Scoring | Sonnet, temp=0 |
| Agent 3 | Testing + Coverage | Sonnet |
| Agent 4 | Book Finder | Haiku |
| Agent 5 | Book Encoder | Sonnet |
