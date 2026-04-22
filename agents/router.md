# Agent Registry

The router (`/project:experts`) reads this file to know which agents exist and what each one does.
To add a new agent: create `agents/<name>.md` and add one row here.

| id            | file                      | one-line capability                                                        |
|---------------|---------------------------|----------------------------------------------------------------------------|
| book_finder   | agents/book_finder.md     | Given a technical domain, return the single best foundational book as structured YAML. |
| book_encoder  | agents/book_encoder.md    | Given a book recommendation, encode its topics into `skills/BOOKS/<category>/<slug>/`. |

# Conventions
- The `model` and `tools` for each agent are declared in the agent file's frontmatter.
- Each agent's output contract is authoritative — router maps its fields 1:1 to the next agent's inputs during a cascade.
- An agent signals that its result is unacceptable by returning a line beginning with `STATUS: RETRY`. The router feeds the reason back as `retry_hint` on the next loop iteration.
