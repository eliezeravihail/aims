# knowledge-library-agents

A Claude Code plugin that builds and maintains a structured technical knowledge base from books.
An AI agent can query this knowledge base instead of relying solely on its training data — getting
dense, curated, up-to-date information on demand.

**Created by [Eliezer Avihail](https://www.linkedin.com/in/eliezer-avihail/) · MIT License**

## How it works

One slash command — `/project:experts` — routes a natural-language request to the right agent(s).
Two agents do the actual work:

```
/project:experts find a book on <domain>
    → book_finder: searches the web, ranks by tier, returns a BOOK_RECOMMENDATION

/project:experts encode <slug>                    (loop, retries on quality failure)
/project:experts build the library for <domain>   (cascade: find → encode)
    → book_encoder: distils the book into skills/BOOKS/<CATEGORY>/<slug>/

/project:query-knowledge <topic>
    → reads _meta.md to pick the best book, loads only the specific topic file it needs
```

## Agents

Agent definitions live in `agents/<name>.md`. Each file has the model + tools in its frontmatter
and the full behavior spec in the body. To add an agent: create `agents/<name>.md` and add a row
to `agents/router.md`.

| Agent | File | Model | What it does |
|-------|------|-------|--------------|
| **book_finder**  | `agents/book_finder.md`  | Haiku  | Finds the best foundational book for a given domain, returns ranked YAML |
| **book_encoder** | `agents/book_encoder.md` | Sonnet | Fetches the book, writes `_index.md` + one `<topic>.md` per topic |

## Router modes

`/project:experts` picks one of four modes based on the request:

| Intent  | Mode    | Pipeline                                 |
|---------|---------|------------------------------------------|
| FIND    | SINGLE  | book_finder                              |
| ENCODE  | LOOP    | book_encoder, up to 3 retries on `STATUS: RETRY` |
| BUILD   | CASCADE | book_finder → book_encoder               |
| REFRESH | CASCADE | book_finder → book_encoder per stale slug |

An agent signals an unacceptable result by returning `STATUS: RETRY <reason>` instead of its
normal output contract. The router feeds the reason back as `retry_hint` on the next loop.

## Using the knowledge base

```
/project:query-knowledge backpropagation
/project:query-knowledge RANSAC homography
/project:query-knowledge regularization dropout
```

The agent reads `_meta.md` to select the highest-quality book for the topic, then loads only
the specific topic file needed.

### Knowledge structure

```
skills/BOOKS/<CATEGORY>/<slug>/
  _index.md        ← topic list (one line per topic — load this first)
  backprop.md      ← condensed, actionable content for this topic
  optimization.md
  ...
```

## Adding a book

### Encode a single book
```
/project:experts encode <slug>
```
Pulls the queue entry from `books-init-queue.yaml` and loops on quality failure.

### Build from a domain name (find + encode)
```
/project:experts build the library for reinforcement learning
```

### Encode from a queue
Add entries to `books-init-queue.yaml`:

```yaml
- slug: your_book_slug
  title: "Book Title"
  authors: [Author]
  category: ANN          # see categories below
  free_url: "https://..."  # must be a verifiable free source; null = local ingest only
  source_tier: tier_1a
  topics_to_encode:
    - topic_one
    - topic_two
```

Then:
```
/project:experts encode your_book_slug
```

### Local PDFs or text
For books without a free URL:
```
/project:ingest-local-sources ./my-book.pdf --category ANN --slug my_book
```

## Install

1. Clone this repo into your Claude Code plugins folder
2. Open the folder in Claude Code
3. Run `/project:query-knowledge <topic>` to use the pre-built KB immediately
4. Add books with `/project:experts build the library for <domain>` or edit the queue + `/project:experts encode <slug>`

## Knowledge categories

`ANN` · `CNN` · `VISION` · `OBJECT_DETECTION` · `REFACTORING` · `ALGORITHMS` · `NLP` · `RL` · `TRAINING_OPTIMIZATION` · `DISTRIBUTED_SYSTEMS`
