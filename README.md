# knowledge-library-agents

A Claude Code plugin that builds and maintains a structured technical knowledge base from books.
An AI agent can query this knowledge base instead of relying solely on its training data — getting
dense, curated, up-to-date information on demand.

**Created by [Eliezer Avihail](https://www.linkedin.com/in/eliezer-avihail/) · MIT License**

## How it works

```
find-book <domain>          →  discovers the best foundational book for a topic
                                (searches the web, evaluates quality, returns a recommendation)

encode-book / books-init    →  reads the book from its free URL and distills it into
                                a hierarchy of skill files under skills/BOOKS/

query-knowledge <topic>     →  reads _meta.md to pick the best book,
                                reads _index.md to see available topics (cheap),
                                loads only the specific topic file it needs (lazy)
```

## Agents

| Agent | Role | Model | How it works |
|-------|------|-------|--------------|
| **book_finder** | Finds the best foundational book for a given domain | Haiku | Searches the web, compares editions and quality, returns a ranked recommendation with a free URL if available |
| **book_encoder** | Distills a book into queryable skill files | Sonnet | Fetches the book from its free URL, extracts key topics, writes a `_index.md` (topic list) and one `<topic>.md` per topic |

## Using the knowledge base

Query any topic directly from the pre-built KB:

```
/project:query-knowledge backpropagation
/project:query-knowledge RANSAC homography
/project:query-knowledge regularization dropout
```

The agent reads `_meta.md` to select the highest-quality book for the topic, then loads only
the specific topic file needed — keeping token usage low even as the KB grows.

### Knowledge structure

Each encoded book lives in a folder:

```
skills/BOOKS/<CATEGORY>/<slug>/
  _index.md        ← topic list (one line per topic — load this first)
  backprop.md      ← condensed, actionable content for this topic
  optimization.md
  ...
```

## Adding a book

### Encode a specific book (simple path)

If you know which book you want to add:

```
/project:encode-book
```

The command is interactive — it will prompt for the book URL, title, and topics to encode.

For books without a free URL, download the PDF and use:
```
/project:ingest-local-sources ./my-book.pdf --category ANN --slug my_book
```

### Encode from a queue (batch)

Add books to `books-init-queue.yaml`:

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

Then run:
```
/project:books-init          # encodes first 20 pending books
/project:books-init --count 1
```

## Discovering books (advanced)

If you don't have a specific book in mind, use `find-book` to search the web for the
best foundational book on a topic:

```
/project:find-book deep learning
/project:find-book computer vision
```

Returns a ranked recommendation with a free URL (when available) and suggested topics to encode.
The output can be pasted directly into `books-init-queue.yaml`.

## Maintenance

| Command | What it does |
|---------|-------------|
| `/project:books-status` | Coverage and quality report across all categories |
| `/project:books-update` | Find newer editions and refresh stale books |
| `/project:books-audit` | Knowledge hygiene: deduplicate, re-rank, decay old entries |

## Install

1. Clone this repo into your Claude Code plugins folder
2. Open the folder in Claude Code
3. Run `/project:query-knowledge <topic>` to use the pre-built KB immediately
4. Add books with `/project:encode-book` or edit `books-init-queue.yaml` + `/project:books-init`

## Knowledge categories

`ANN` · `CNN` · `VISION` · `OBJECT_DETECTION` · `REFACTORING` · `ALGORITHMS` · `NLP` · `RL` · `TRAINING_OPTIMIZATION` · `DISTRIBUTED_SYSTEMS`
