# Agent Registry

The router (`/project:experts`) reads this file to know which agents exist and what each one does.
Agents are behavior wrappers — the domain playbook lives in the project skills, not here.
To add a new agent: create `agents/<name>.md` and append one row to the table below.

| id            | file                      | one-line capability                                                        |
|---------------|---------------------------|----------------------------------------------------------------------------|
| book_finder   | agents/book_finder.md     | Produces a `BOOK_RECOMMENDATION` for a given domain.                       |
| book_encoder  | agents/book_encoder.md    | Encodes a `BOOK_RECOMMENDATION` into the knowledge base.                   |

# Conventions
- `model` and `tools` for each agent are declared in the agent file's frontmatter.
- Each agent's `outputs` contract is authoritative — the router binds those fields 1:1 to the next agent's `inputs` in a cascade.
- An agent signals an unacceptable result with a single line `STATUS: RETRY <reason>`. The router feeds the reason back as `retry_hint` on the next loop iteration. Max 3 retries per stage.
