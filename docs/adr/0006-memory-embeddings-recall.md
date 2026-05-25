# ADR-0006: Two-tier project memory — core context plus embedding-based recall
Status: proposed
Date: 2026-05-25
Supersedes: —
Superseded by: —

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

### Tier 2 — Recall memory (on-demand, UserPromptSubmit)

A new path inside `templates/hooks/prompt-submit.sh`, gated on
`OPENAI_API_KEY` (or alternative provider env var) being set. On each
non-suppressed prompt:

1. Embed the user's prompt via the configured provider (default:
   OpenAI `text-embedding-3-small`, 1536-d).
2. Query `.claude/memory.db` for top-K=20 by cosine similarity using
   `sqlite-vec`.
3. Re-rank with a Generative-Agents-style composite:
   `score = α·similarity + β·recency_decay + γ·importance`
   defaults `α=0.6, β=0.2, γ=0.2` (tunable in `.claude/memory.toml`).
   `recency_decay = exp(-Δdays / S)` with `S=14` days
   (Ebbinghaus-style; configurable).
4. Drop everything below a similarity floor (`sim < 0.35`). This is
   non-negotiable — empty injection is strictly better than a poisoned
   one.
5. Inject the surviving top-N (N=5, ≤4KB total) into
   `additionalContext`, tagged `[aims-recall]` so the model knows
   these are recalled detail-memories, not directives, and so the
   tag is visible in transcripts (parallel to `[aims-router]`).
6. Update `last_accessed_at` and `access_count` for the surfaced
   rows (access reinforcement).

Schema:

```sql
CREATE TABLE memories (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,           -- decision|deliberation|gotcha|episode
  source_path TEXT,             -- e.g. docs/adr/0004-...md
  text TEXT NOT NULL,           -- the memory itself, 1–10 sentences
  importance REAL DEFAULT 0.5,  -- 0..1, set at ingest
  created_at INTEGER NOT NULL,
  last_accessed_at INTEGER,
  access_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE memories_vec USING vec0(embedding FLOAT[1536]);
```

### Encoding (how memories get in)

Two complementary paths:

- **Explicit** — `/remember <note>` (Haiku, new command in
  `templates/commands/remember.md`). User marks something worth
  remembering during a session. Stored with `importance=0.8`.
- **Implicit, end-of-session** — a `Stop` hook scans files changed
  under `docs/adr/` and `docs/plans/` since the previous Stop. For
  each new/modified ADR, extract `## Decision` + `## Consequences` as
  one memory (`kind=decision`, `importance=0.9`). For each plan,
  extract bullets prefixed `Decided:`, `Avoid:`, `Gotcha:` as
  separate memories.

### Decay (the forgetting half)

`/forget` (manual, recommended monthly) removes memories where
`access_count = 0`, age > 180 days, and `importance < 0.5`. This is
the system's analogue of the Ebbinghaus forgetting curve combined
with access reinforcement: memories you never recall, that you didn't
flag as important, fade.

### Embedding provider

Default: **OpenAI `text-embedding-3-small`**. Rationale: cheapest
credible quality ($0.02 / 1M tokens; a typical 200-token prompt costs
~$0.000004 to embed), one `curl` call from bash, no Python dependency.
Configurable in `.claude/memory.toml` to swap for Voyage 3-lite,
Cohere embed-v4, or a local Ollama endpoint (`nomic-embed-text`,
`bge-m3`).

aims ships **no default API key**. The user provides one via the
provider's standard env var. If unset, the recall tier disables
silently and Tier 1 continues to function — recall is strictly
additive.

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
- ⚠️ Adds one outbound embedding call per non-suppressed prompt
  (~50–150ms typical latency). The user must accept this when recall
  is enabled.
- ⚠️ `.claude/memory.db` is gitignored by default. Memory does not
  sync across machines or collaborators without an opt-in mechanism;
  a `/memory sync` command is out of scope for this ADR.
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

## Verification

- `.claude/memory.db` exists after first ingest and contains the
  schema above (`sqlite3 .claude/memory.db .schema | grep -E
  'memories|vec0'`).
- `templates/hooks/prompt-submit.sh` makes at most one embedding
  call and one SQL query per non-suppressed prompt; tracing via
  `AIMS_RECALL_TRACE=1` prints the scored top-K plus the chosen
  top-N to stderr.
- Injected `additionalContext` for recall is ≤4KB and prefixed
  `[aims-recall]` so it is visually distinct from `[aims-router]`
  in transcripts.
- `OPENAI_API_KEY` unset → SessionStart and the router behave
  identically to pre-ADR-0006; no recall block injected; no error
  on stderr.
- Distractor floor enforced: a unit test (`tests/recall.sh`) inserts
  a known-irrelevant memory, runs a query whose true top match is
  above the floor, asserts the irrelevant memory is filtered out
  before injection.
- README "Design principles" gains a fifth point referencing this
  ADR: "Memory is two-tier — light always-on, deep on-demand —
  to respect context-rot and distractor evidence."
