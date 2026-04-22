---
description: "Expert router — parse a request and invoke the right agent(s) in single, cascade, or loop mode"
allowed-tools: Read, Write, WebSearch, Bash
argument-hint: "<request>"
---

# /project:experts

Natural-language front door to the agent library. Parses `$ARGUMENTS`, chooses a
mode (single / cascade / loop), loads the agent files listed in `agents/router.md`,
and executes them.

## Usage
```
/project:experts find a book on reinforcement learning
/project:experts encode sutton_barto_rl
/project:experts build the library for graph neural networks
/project:experts refresh stale books in NLP
```

## Step 1 — Load registry
Read `agents/router.md`. This is the authoritative list of available agents and their files.

## Step 2 — Parse intent
Classify `$ARGUMENTS` into exactly one intent by matching in order (first match wins):

| Intent   | Trigger phrases (case-insensitive)                                     |
|----------|-------------------------------------------------------------------------|
| BUILD    | "build", "grow the library", "find and encode", "full pipeline", "ingest pipeline" |
| REFRESH  | "refresh", "update stale", "update the library", "audit and update"     |
| ENCODE   | "encode", "add book", or explicit `slug` token (lowercase_underscored)  |
| FIND     | "find", "recommend", "which book", "best book"                          |
| default  | (no match) → FIND                                                       |

## Step 3 — Choose mode & pipeline

| Intent   | Mode     | Pipeline                                   | Max loops |
|----------|----------|--------------------------------------------|-----------|
| FIND     | SINGLE   | book_finder                                | 1         |
| ENCODE   | LOOP     | book_encoder                               | 3         |
| BUILD    | CASCADE  | book_finder → book_encoder                 | 3 on encoder |
| REFRESH  | CASCADE  | book_finder (per stale slug) → book_encoder | 3 on encoder |

## Step 4 — Load the agent files
For every agent id in the chosen pipeline, read `agents/<id>.md`. Respect:
- `model` in frontmatter — invoke with this exact model
- `tools` in frontmatter — use only these tools
- `inputs` / `outputs` — this is the contract the router binds against

## Step 5 — Execute

### SINGLE
1. Bind inputs from `$ARGUMENTS` to the agent's `inputs` list.
2. Invoke the agent with its declared model.
3. Emit the agent's output verbatim + a one-line summary.

### LOOP (encode, max 3)
1. Bind inputs. Initial `retry_hint = null`.
2. Invoke `book_encoder`.
3. If output starts with `STATUS: RETRY <reason>` AND attempt < max:
   - Set `retry_hint = <reason>`, increment attempt, go to step 2.
4. Stop when the agent returns its normal output contract OR attempt == max.
5. Emit final status: success + `quality_score`, OR failure with all retry reasons.

### CASCADE (find → encode)
Maintain a `state` dict keyed by output field names.
1. **Step 1 — book_finder.** Bind `domain` from `$ARGUMENTS`. Invoke.
   - On `STATUS: RETRY` from finder: one retry, then abort the cascade.
   - Write the BOOK_RECOMMENDATION fields into `state` (slug, title, authors, category, free_url, topics_to_encode, source_tier).
2. **Step 2 — book_encoder.** Bind its `inputs` from `state`. Run inside the LOOP mode above (max 3 retries).
3. Emit a cascade report: per-step status, final artifact paths, total loops consumed.

### REFRESH (specialisation of CASCADE)
1. Read every `skills/BOOKS/<category>/_meta.md` that matches the filter (category or "all stale").
2. For each entry flagged `stale=true` OR older than 18 months:
   - Run the find → encode cascade with `domain` = the book's original topic cluster.
3. Emit a per-book refresh report.

## Step 6 — Report
Always end with a compact summary block:

```
Mode: <SINGLE|LOOP|CASCADE|REFRESH>
Agents: <list>
Steps: <per-step pass/fail + loop count>
Artifacts: <created / updated file paths>
Retries: <reasons, if any>
```

## Input parsing notes
- Strip leading "please ", "can you ", "i want to ".
- For FIND: everything after the trigger phrase is `domain`.
- For ENCODE: the first `lowercase_underscored` token is `slug`; remaining queue fields (title, authors, category, free_url, topics_to_encode) are pulled from `books-init-queue.yaml` if present, otherwise prompt for them.
- For BUILD: domain is the free text after the trigger phrase.
- For REFRESH: optional category filter after the trigger phrase; otherwise all categories.
