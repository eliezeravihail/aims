## Usage
```
/project:query-knowledge <topic>
```

Examples:
```
/project:query-knowledge backpropagation
/project:query-knowledge RANSAC homography
/project:query-knowledge regularization dropout
```

## What it does
Queries the pre-built knowledge base in `skills/BOOKS/` and returns a deep,
book-sourced answer for the requested topic — including derivations, code examples,
and pitfalls that are specific to what the book says, not generic knowledge.

## Steps

1. **Identify the category** — read `skills/BOOKS/_index.md` to understand the available
   categories and which one best matches the topic.

2. **Pick the best book** — read `skills/BOOKS/<CATEGORY>/_meta.md` and select the entry
   with the highest `quality_score`. Skip any entry marked `stale: true`.

3. **Find the topic file** — read `skills/BOOKS/<CATEGORY>/<slug>/_index.md` and find the
   closest matching topic file name.
   - If an exact match exists: load it directly.
   - If no exact match: load the two closest topic files and synthesize an answer.

4. **Load and answer** — read the topic file and answer the user's question using its content.
   Always cite the source using the `Read more` line at the top of the topic file
   (book title + chapter reference).

5. **Multi-category queries** — if the topic spans multiple categories (e.g. "optimization"
   applies to both ANN and TRAINING_OPTIMIZATION), load the top book from each relevant
   category and note which source covers which angle.

## Output format
- Lead with a one-paragraph direct answer
- Then include the relevant sections from the topic file (Deep Dive, code, pitfalls)
- End with: `Source: <title> — <read_more_url>`
