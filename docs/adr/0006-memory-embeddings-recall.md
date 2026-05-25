# ADR-0006: Two-tier project memory — core context plus embedding-based recall
Status: superseded
Date: 2026-05-25
Supersedes: —
Superseded by: ADR-0007 (tree-based memory with automatic build and maintenance)

> **Note on supersession.** This ADR explored an embedding-based recall
> design through three revisions (per-prompt → event-driven → keyword-
> surrogate). During the implementation step (three commits later
> reverted, never pushed), the user concluded that the runtime cost
> of an embedding model plus the rerank step was overkill for the
> realistic memory corpus size (<500 items per project). The decision
> was to pivot to a navigable hierarchical knowledge graph — see
> ADR-0007 for the chosen design.
>
> The full text below is preserved as the design conversation we ran
> through. Treat it as historical; do not implement.

---

## Context

aims's persistence today is artifact-based: `/plan` writes to
`docs/plans/`, `/adr` writes to `docs/adr/`, and the SessionStart hook
surfaces in-progress plans and recently-touched ADRs. That solves
"decisions survive compaction" but leaves a gap users hit in practice:

- When a session opens, the agent needs a **lightweight project
  orientation** — enough to act sensibly, not enough to overwhelm the
  context window. SessionStart already injects in-progress plans plus
  recent ADRs; this is the "core context" layer.
- When the user later **touches a specific topic** (a module, a past
  bug, a rejected design), the agent should recall the relevant
  *detailed* deliberations from prior sessions — not the entire
  history, just the slices that match the current concern.

Reading every ADR, plan, and design discussion into every session is
wrong on two counts. First, context rot: 2026 evidence (Chroma's
18-model study; Morph's context-rot survey) shows every frontier model
degrades as input grows, often before the advertised window is half
full. Second, distractor penalty: irrelevant retrieved context
measurably hurts answer quality (Liu et al. 2025 "Distracting Effect";
Anthropic's own just-in-time-retrieval guidance in the memory-tool
docs). The right pattern is two-tier: a small always-on core plus a
larger pool searched on demand.

The "search on demand" mechanism that best matches the user's framing
("recall topics related to what I'm now discussing, the way the brain
does") is embedding similarity, with refinements borrowed from
cognitive-memory models — recency decay and importance weighting on
top of relevance, in the spirit of Park et al.'s Generative Agents
(Stanford, 2023) and the Letta core/recall/archival split.

## Decision

aims adopts a **two-tier memory model**, both tiers injected via
existing hooks. No new runtime dependencies on the model — the
mechanism is deterministic shell + SQL + one embedding call.

### Tier 1 — Core context (always-on, SessionStart)

Extend `templates/hooks/session-start.sh` to also surface, if present:

- `docs/project-overview.md` (≤2KB) — human-curated one-pager:
  what this project is, top-level architecture, current focus.
- In-progress plans (existing behaviour, unchanged).
- Recently-touched ADRs (existing behaviour, unchanged).

Total injected at SessionStart: ≤4KB. Designed to sit well below the
context-rot inflection point observed across 2026 frontier models.

### Tier 2 — Recall memory (event-driven, not per-prompt)

Recall is **not** triggered on every UserPromptSubmit. It fires only
on two events: (a) the **first prompt of a new session**, (b) a
detected **topic shift** mid-session. This matches the user's actual
need (orientation up-front, refocus on transitions) and avoids the
per-prompt orchestration cost that ADR-0002 and ADR-0004 explicitly
rejected.

#### Shift detector (cheap, deterministic, per-prompt)

A lightweight component does run on every prompt. It maintains a
running session "topic centroid" — the decaying mean of recent prompt
embeddings, stored at `.claude/session-centroid.vec` (gitignored,
deleted on SessionStart). On each prompt:

1. Embed the prompt locally (~10ms on CPU with `bge-small-en-v1.5`).
2. Compute cosine distance to the centroid.
3. If `distance > 0.5` **and** at least 60s elapsed since the last
   recall event → topic shift detected.
4. Update the centroid with a 0.7 decay weight (recent prompts
   dominate).

No LLM call here. No retrieval. Just a small embedding + math.

#### Recall pipeline (fires only on shift or session-first-prompt)

When the detector triggers, or when this is the session's first
prompt, the full pipeline runs:

1. Embed the prompt (already done by the shift detector — reuse).
2. Score every memory by cosine similarity between the prompt
   embedding and the memory's stored title+keywords embedding. Drop
   anything below `sim < 0.35` (the distractor floor). Keep top-20.
3. Re-rank using a composite:
   `score = α·similarity + β·recency_decay + γ·importance`
   defaults `α=0.6, β=0.2, γ=0.2`. `recency_decay = exp(-Δdays / 14)`.
4. **Haiku rerank-and-filter** (Tier 2.5, see next): pass the
   surviving top-20 plus the prompt to Haiku, get back the filtered
   top-N (N≤5, sometimes 0). This is what catches the false
   positives that pure-embedding similarity misses.
5. Inject the survivors into `additionalContext`, tagged
   `[aims-recall]`. If this was a topic shift (not the first prompt),
   append: `Topic shift detected — consider /clear to drop accumulated
   context from the previous topic.`
6. Update `last_accessed_at` and `access_count` for surfaced memories.

#### Tier 2.5 — Haiku rerank-and-filter (event-driven, low frequency)

A small Anthropic API call to `claude-haiku-4-5` runs **only on
recall events** (~5–15 times per day at typical usage). Input: the
prompt + the 20 candidates (title, keywords, body, source_path).
Output: a JSON array of 0–5 chosen memories, each with a one-line
reason. Haiku is allowed to return an **empty array** — "no memory
is genuinely relevant right now, inject nothing." This is the killer
capability a cross-encoder reranker cannot provide.

Why Haiku is acceptable here (despite ADR-0002 and ADR-0004 rejecting
per-prompt LLM orchestration):

- **Frequency**: ~5–15 calls/day, not per-prompt. Three orders of
  magnitude below what ADR-0002 rejected.
- **Latency**: ~1–2s on shift moments — natural transition points
  where a brief pause is acceptable, even useful.
- **Cost**: ~$0.001/day per heavy user. Not a budget concern.
- **Quality**: catches body-vs-keyword false positives that cosine
  on keyword surrogates cannot. Also catches "context-aware"
  rejections that a cross-encoder cannot.
- **Disable path**: if no `ANTHROPIC_API_KEY` is configured, the
  pipeline falls back to top-5 by composite score (no LLM
  filtering). Tier 2 still works, just less precisely.

### Storage — files, not a DB

Memories live as markdown files in `docs/memories/NNNN-slug.md`, one
file per memory, with YAML frontmatter:

```yaml
---
id: 0042
kind: decision           # decision | deliberation | gotcha | episode
title: bge-small as the default embedding model
keywords: bge-small embedding ollama local cpu cross-lingual
importance: 0.8          # 0..1
created: 2026-05-25T12:34:56Z
source: docs/adr/0006-memory-embeddings-recall.md
last_accessed: null
access_count: 0
---
We chose bge-small-en-v1.5 because [body in any language] ...
```

Two reasons not to use sqlite-vec or any vector DB at v1:

- **Scale**: typical project ends up with tens to low-hundreds of
  memories. Sequential awk-cosine over 100 sidecar embedding files
  runs in well under 100ms — orders of magnitude below the
  Haiku-rerank step. A vector DB is unnecessary infrastructure.
- **Source-of-truth clarity**: when the .md file IS the memory,
  there is nothing to migrate, nothing to dump-restore, nothing
  to "rebuild the index" except recompute embeddings from text
  the user can already read.

The embeddings cache lives at `.claude/embeddings/NNNN.vec`
(newline-separated floats, gitignored). Regenerable from the .md
files at any time via the `index` script.

### Relationship to git

Memories are tracked in git **by default** because they are the
informal-knowledge counterpart of ADRs and plans:

| Layer | What it captures | Cadence | Formality |
|-------|------------------|---------|-----------|
| Git history | What changed, when, by whom | Per commit | Terse |
| ADRs / plans | Why a major decision was made | Event-driven | Formal, reviewed |
| **Memories** | Gotchas, dead-ends, mental models, contextual hints | Lightweight, ad-hoc | Informal |

This three-layer split fills the gap between "commit message" (too
terse) and "ADR" (too ceremonious for a passing observation). It is
**not** parallel documentation: each layer captures something the
others do not.

Users who want private (machine-local) memories can `.gitignore
docs/memories/` themselves. The default is share-by-commit, matching
how ADRs already work.

### When the embedding model can be tiny

The embedded surface is `title + " " + keywords` — an LLM-generated,
short, dense, English surrogate. The body is stored raw (any
language, any length) but **never embedded**; it is surfaced into
the prompt only after a successful match. This split (LLM compresses
meaning into English keywords at write-time; small embedding model
matches keyword strings at read-time) is what lets the embedding
model be tiny (`bge-small-en-v1.5`, 33M params) and English-only
without sacrificing recall on Hebrew or mixed prompts.

### Encoding (how memories get in)

Two complementary paths. Both share a final step: the LLM running in
the current session (whatever model is active — no separate
orchestrated call) produces a one-line **title** and 5–10 English
**keywords** for the memory, before it is written. Only those two
fields are concatenated and embedded; the body is stored raw.

- **Explicit** — `/remember <note>` (Haiku, new command in
  `templates/commands/remember.md`). User marks something worth
  remembering during a session. Stored with `importance=0.8`. The
  Haiku invocation generates the title + keywords as part of the
  same call that writes the row.
- **Implicit, end-of-session** — a `Stop` hook scans files changed
  under `docs/adr/` and `docs/plans/` since the previous Stop. For
  each new/modified ADR, extract `## Decision` + `## Consequences` as
  one memory body (`kind=decision`, `importance=0.9`). For each plan,
  extract bullets prefixed `Decided:`, `Avoid:`, `Gotcha:` as
  separate memory bodies. Each body is then passed to a Haiku
  one-shot for title + keyword generation before insertion.

The keyword-surrogate insight (the user's framing): meaning is
compressed *once* by an LLM at write-time, into a stable English
representation. From then on, retrieval is a cheap string-similarity
problem, not a semantic one. This is what lets the embedding model
shrink by an order of magnitude.

### Decay (the forgetting half)

`/forget` (manual, recommended monthly) removes memories where
`access_count = 0`, age > 180 days, and `importance < 0.5`. This is
the system's analogue of the Ebbinghaus forgetting curve combined
with access reinforcement: memories you never recall, that you didn't
flag as important, fade.

### Embedding model

Default: **`bge-small-en-v1.5` via local Ollama** (`ollama pull
bge-small-en-v1.5`; queried via `curl http://localhost:11434/api/
embeddings`). Rationale:

- 33M parameters, ~133MB on disk, embedding dim 384.
- MTEB ~62 — best quality-per-byte in the English small class
  (significantly above `all-MiniLM-L6-v2` at ~56), comparable to
  larger paid APIs on short-string matching tasks.
- <10ms per embedding on a modern laptop CPU. No network round-trip,
  no cost-per-call, no key management.
- Privacy: memory titles and keywords never leave the machine.
- English-only is acceptable because the **embedded surface is the
  English keyword surrogate**, not the original memory body. Hebrew
  prompts still match well in practice via the English identifiers
  they contain (function names, file names, library names); pure-
  Hebrew prompts simply produce low scores and recall does not fire.

Configurable in `.claude/memory.toml` to swap for: any other Ollama
embedding model (`nomic-embed-text`, `mxbai-embed-large`,
`embeddinggemma`), or a remote API (`text-embedding-3-small`,
Voyage 3-lite, Cohere embed-v4) by changing `provider` + `model`.

aims ships **no Ollama dependency check beyond a TCP probe at hook
load**. If `localhost:11434` is unreachable and no remote provider is
configured, the recall tier disables silently and Tier 1 continues
to function — recall is strictly additive.

## Consequences

- ✅ Two-tier matches the user's stated need: light orientation per
  session, deep recall when a specific topic surfaces.
- ✅ Recall is additive. Existing aims workflows (plans, ADRs, the
  router) are unchanged; recall makes them searchable across
  sessions without changing how they're written.
- ✅ Composite scoring mitigates pure-cosine failure modes: a stale,
  marginally-similar memory cannot crowd out a recent, highly-relevant
  one.
- ✅ Hard similarity floor (0.35) + N=5 cap respects the 2026
  distractor evidence: injecting nothing beats poisoning the context.
- ✅ Disabling path is zero-config: unset the API key and the system
  reverts to current behaviour exactly.
- ⚠️ Adds one external dependency: `sqlite-vec` (single-file
  extension; pip-installable or prebuilt binary). Acceptable — no
  server, no daemon, the DB is one file under `.claude/`.
- ⚠️ Adds one local embedding call **per prompt** for the shift
  detector (~10ms with `bge-small-en-v1.5`). The full recall +
  Haiku pipeline fires only on shift events (~5–15/day).
- ⚠️ Requires a running Ollama daemon (or equivalent) for the
  default embedding path. Per-user, not per-project; does not
  violate ADR-0005. Users who refuse Ollama can either set a
  remote-provider key or accept Tier 1-only.
- ⚠️ Requires `ANTHROPIC_API_KEY` for the Haiku rerank/filter step.
  If unset, the pipeline falls back to top-5 by composite score
  (no LLM filtering). Tier 2 still works, just less precisely.
- ⚠️ Memory files in `docs/memories/` are tracked in git by default.
  This is intentional (shareable with collaborators) but means
  users must be deliberate about what they write — same discipline
  as ADRs.
- 🔒 Closes the door on multi-step LLM retrieval (HyDE, query
  rewriting, LLM re-ranking). Same reasoning as ADR-0002 and
  ADR-0004: one deterministic shell+SQL hop, no orchestration. If
  recall quality proves insufficient, the next move is a better
  embedding model or a hybrid BM25+dense layer, not more LLM calls.

## Alternatives considered

- **Use Anthropic's official memory tool (`memory_20250818`) as the
  primary mechanism** — rejected for *this* problem. That tool is
  runtime-driven: the model decides when to invoke
  `view`/`create`/`str_replace` on a `/memories` directory. It
  solves "the model manages its own scratchpad across turns" —
  excellent for long single-task agents, weak for "the system
  surfaces relevant context **before** the model starts thinking."
  The two are complementary; a future bridge that exposes the recall
  DB through the memory-tool surface is plausible but unnecessary
  here.

- **Heavyweight memory framework (Letta/MemGPT, mem0, Zep, Cognee)**
  — rejected. Each ships a server, a graph layer, opinionated
  agents. aims is markdown + bash + one new SQL file; importing a
  framework breaks the value/complexity ratio set by ADR-0002. We
  borrow the *ideas* (core/recall split from Letta, importance and
  recency from Generative Agents, dynamic linking from A-MEM)
  without the runtime.

- **Full-text search (SQLite FTS5) alone, no embeddings** —
  rejected. FTS5 misses synonyms and paraphrases ("auth failures"
  vs "login broke"), which is exactly the brain-like recall the
  user is asking for. May be added later as a **hybrid retrieval**
  sibling (BM25 + dense, fused via Reciprocal Rank Fusion) if
  recall@5 proves weak in practice — 2026 hybrid-search evidence
  shows RRF typically beats either alone, especially for
  identifier-heavy queries (function names, file paths).

- **In-context summarization / compaction as the recall mechanism**
  — rejected. Compaction loses detail; preserving detail is the
  whole point of the user's complaint. Embedding recall lets
  details stay detailed and only fetches them when the current
  prompt asks.

- **Equal-weight Generative Agents scoring (`α=β=γ=⅓`)** —
  rejected as the default. In a coding context, relevance dominates
  much more than in the social-simulation context Park et al.
  studied. The 0.6/0.2/0.2 tilt is a starting point; tunable.

- **Embedding the memory body directly, with a large multilingual
  model** — rejected after the keyword-surrogate insight. The original
  draft of this ADR proposed `text-embedding-3-small` over the full
  memory body, which forces a 1536-d index, ~$0.02/1M token billing,
  network latency, and (for Hebrew prompts vs. English bodies) a
  multilingual model big enough to bridge the gap. Compressing
  meaning into LLM-generated English keywords at write-time
  collapses all four problems into one cheap, local, small-model
  step. Rejected variant kept for context.

- **Cloud API (`text-embedding-3-small`) as the default** — rejected
  after evaluating local options. Still offered as a configurable
  fallback. Reasons to keep it available: users who refuse Ollama,
  environments where local model downloads are blocked, or future
  CI environments where the embedding step needs to be reproducible
  without a daemon.

- **`sqlite-vec` as the storage backend** — initially proposed, then
  rejected. At v1 scale (tens to low-hundreds of memories per
  project), sequential cosine over per-memory `.vec` sidecar files
  finishes in under 100ms — far below the Haiku rerank step that
  dominates. A vector DB adds an extension dependency, a binary
  format, and a "rebuild the index" failure mode, for no observable
  win. If a project ever exceeds ~1,000 memories the trade-off
  flips; that is a follow-up problem, not a v1 problem.

- **Anthropic's `memory_20250818` tool as the primary mechanism** —
  rejected as primary (it is runtime-driven, not system-proactive),
  but explicitly kept compatible: the storage layout (markdown files
  in a directory with frontmatter) is intentionally similar to
  Anthropic's `/memories` convention, so a future bridge that
  exposes the same files through the official tool requires no
  migration.

- **Per-prompt recall (the original draft)** — superseded by the
  event-driven shift-detector design. Per-prompt recall meant an
  embedding call + rerank + injection on every turn, with all the
  associated context-rot and orchestration costs. Event-driven
  triggers (session start, topic shift) match how a person
  re-orients themselves around a topic, and reduce LLM rerank to a
  few calls a day — at which frequency Haiku becomes feasible.

## Verification

- `docs/memories/` exists and is tracked in git; `.claude/embeddings/`
  exists and is gitignored. Verify with `git check-ignore -v
  .claude/embeddings/0001.vec` (should report ignored) and
  `git ls-files docs/memories | head` (should list any committed
  memory files).
- `templates/hooks/prompt-submit.sh` makes at most one embedding
  call per prompt (shift detector). Full recall + Haiku rerank
  runs only on shift events; trace with `AIMS_RECALL_TRACE=1`.
- Injected `additionalContext` for recall is ≤4KB and prefixed
  `[aims-recall]` so it is visually distinct from `[aims-router]`
  in transcripts. On topic-shift events the injection includes a
  `/clear` recommendation in the same block.
- Ollama unreachable on `localhost:11434` AND no remote provider
  configured → SessionStart and the router behave identically to
  pre-ADR-0006; no recall block injected; no error on stderr.
- `ANTHROPIC_API_KEY` unset → Tier 2 still fires on shifts, but
  uses top-5 by composite score without LLM filtering. A breadcrumb
  on stderr notes the fallback.
- Distractor floor enforced: a unit test (`tests/recall.sh`) inserts
  a known-irrelevant memory, runs a query whose true top match is
  above the floor, asserts the irrelevant memory is filtered out
  before injection.
- README "Design principles" gains a fifth point referencing this
  ADR: "Memory is event-driven — light always-on at SessionStart,
  deep recall on topic-shift, with LLM filtering only at those
  inflection points."
