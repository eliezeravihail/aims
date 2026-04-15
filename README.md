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

Agent using the knowledge   →  reads _meta.md to pick the best book,
                                reads _index.md to see available topics (cheap),
                                loads only the specific topic file it needs (lazy)
```

## Agents

| Agent | Role | Model | How it works |
|-------|------|-------|--------------|
| **book_finder** | Finds the best foundational book for a given domain | Haiku | Searches the web, compares editions and quality, returns a ranked recommendation with a free URL if available |
| **book_encoder** | Distills a book into queryable skill files | Sonnet | Fetches the book from its free URL, extracts key topics, writes a `_index.md` (topic list) and one `<topic>.md` per topic |

## Commands

| Command | What it does |
|---------|-------------|
| `/project:find-book <domain>` | Search the web for the best foundational book on a domain and return a recommendation |
| `/project:encode-book` | Encode a single book (interactive — prompts for slug, URL, topics) |
| `/project:books-init [--count N]` | Encode the first N pending books from `books-init-queue.yaml` (default: 20) |
| `/project:ingest-local-sources <folder>` | Encode local PDFs or text files into the knowledge base |
| `/project:books-status` | Coverage and quality report across all categories |
| `/project:books-update` | Find newer editions and refresh stale books |
| `/project:books-audit` | Knowledge hygiene: deduplicate, re-rank, decay old entries |

## Knowledge structure

Each encoded book lives in a folder:

```
skills/BOOKS/<CATEGORY>/<slug>/
  _index.md        ← topic list (one line per topic — load this first)
  backprop.md      ← condensed, actionable content for this topic
  optimization.md
  ...
```

The agent loads `_index.md` to decide relevance, then only opens the specific topic file it needs.
This keeps token usage low even for large knowledge bases.

## Install

1. Clone this repo into your Claude Code plugins folder
2. Open the folder in Claude Code
3. Add books to `books-init-queue.yaml` (or use `/project:find-book` to discover them)
4. Run `/project:books-init` to encode the queue

## Add a book manually

Edit `books-init-queue.yaml`:

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

Then run `/project:books-init --count 1`.

For books without a free URL, download the PDF and use:
```
/project:ingest-local-sources ./my-book.pdf --category ANN --slug my_book
```

## Ingest local sources

```
/project:ingest-local-sources ./papers/yolo --category OBJECT_DETECTION --slug yolo_papers
/project:ingest-local-sources ./notes/pytorch --category TRAINING_OPTIMIZATION
```

Supports: `.pdf`, `.txt`, `.md`

## Knowledge categories

`ANN` · `CNN` · `VISION` · `OBJECT_DETECTION` · `REFACTORING` · `ALGORITHMS` · `NLP` · `RL` · `TRAINING_OPTIMIZATION` · `DISTRIBUTED_SYSTEMS`
