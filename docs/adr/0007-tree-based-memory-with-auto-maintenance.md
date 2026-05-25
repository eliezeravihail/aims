# ADR-0007: Tree-based project memory with automatic build and maintenance
Status: proposed
Date: 2026-05-25
Supersedes: ADR-0006 (embedding-based recall)
Superseded by: —

## Context

The memory system needs to give a session orientation on the right
topic without forcing the agent to load everything every time. The
prior design (ADR-0006) attempted this via embedding similarity over
LLM-generated keyword surrogates, with Haiku rerank on shift events.
That design is technically sound but **pays for infrastructure the
scale does not justify**:

- Realistic per-project memory corpus: tens to a few hundred items.
  Embedding shines at >10K corpora; below 500 it is over-engineered.
- An always-on Ollama daemon, a `bge-small-en-v1.5` model download,
  per-prompt embedding for shift detection, and an Anthropic API key
  for the Haiku rerank — all to navigate a corpus a person could
  scan with `ls` and `grep`.
- Embedding-based retrieval is **opaque when it errs**: cosine on
  keywords surfaces something irrelevant, you have no good way to
  see why.

The user's reframe: memory should be a **navigable structure**, not
a similarity bag. A hierarchy where:

- The top level is a small list of project-domain tags (interface,
  network, implementation, documentation, …).
- Each level down is more specific, until the leaves hold the
  detailed content (code references, relevant commits, prior
  sessions, instructions, gotchas).
- The model navigates this structure intentionally — it reads the
  top, picks the relevant subtree, drills down — rather than having
  the system push pre-selected items into its context.

This is essentially **a wiki with curated taxonomy**, well-understood
since 2003. The Anthropic `memory_20250818` tool is the official
primitive for exactly this access pattern (the model invokes
`view` to browse a `/memories` directory, then drills in). Two of
our requirements then collapse into the platform primitive.

The remaining hard requirement — and the one the prior design did
NOT solve — is **build and maintenance must be automatic**. Wikis
die when they require manual upkeep. aims's choice is meaningful only
if the user never has to remember to update the tree.

## Decision

aims adopts a **tree-based memory** stored as a hierarchy of markdown
files under `docs/memory/`. The structure is built once at project
init by an LLM scan, navigated by the model on demand via the official
memory tool (or Read/Glob as a transparent fallback), and maintained
automatically by hooks. No embeddings. No vector DB. No rerank.

### Storage layout

```
docs/memory/
├── README.md                          ← top-level tag list + nav guide
├── interface/
│   ├── README.md                      ← subsystem overview
│   ├── auth/
│   │   ├── README.md
│   │   ├── oauth-callback.md          ← leaf: code refs, commits, sessions
│   │   └── refresh-tokens.md
│   └── ui/
├── network/
├── implementation/
└── documentation/
```

Each leaf `.md` carries YAML frontmatter:

```yaml
---
node: interface/auth/oauth-callback
related: [network/http-client/auth-headers]
code:
  - src/auth/callback.py
  - src/auth/handlers.py:42-90
commits: [a1b2c3d, e4f5g6h]
sessions: [docs/plans/oauth-callback-2026-04.md]
dirty: false                  # flipped by the edit-marker hook
last_touched: 2026-05-25T12:34:56Z
---

# OAuth callback handling

## What this is
…

## Gotchas
…

## Instructions for working here
…
```

`code:` is a list of paths (optionally `:start-end`). It is what
lets the edit hook find which nodes a changed source file touches.

### Cold start — LLM proposes, user refines (one-time, at /init-workflow)

A new command `/memory-init` (Sonnet) runs once per target project:

1. Walks the codebase (Glob + Read), classifies modules into
   coarse domain tags (5–10).
2. Drafts the top-level structure (`docs/memory/README.md` + per-tag
   `README.md` files + leaf stubs for the most prominent modules,
   each with the `code:` frontmatter populated by the walk).
3. Presents the proposed tree via diff preview; the user approves
   in full or by-section.
4. Writes the approved tree to `docs/memory/`. Commits in a single
   `git add docs/memory/` step (committed by default — see ADR-0008
   carry-over).

This is intelligent at one moment (cold start) and silent thereafter.

### Navigation — `memory_20250818` (primary), Read/Glob (fallback)

The model is encouraged to use the official memory tool when
exposed:

- Session start: read `docs/memory/README.md` (always; via Tier-1
  injection or via the model's first `view` call).
- During the session: when the user introduces a topic, the model
  calls `view docs/memory/<tag>/` then `view docs/memory/<tag>/<leaf>.md`
  to load only what is relevant.

If `memory_20250818` is not exposed in the current Claude Code
runtime, the model uses Read/Glob — the file layout is identical
either way, and the navigation behaviour is the same. The choice of
tool affects only audit/traversal hardening, not retrieval semantics.

### Automatic maintenance — two-phase, by design

Maintenance has to be automatic but cannot afford an LLM call on
every Edit/Write. We split it:

**Phase A — Marking (every edit, cheap, deterministic, no LLM).**
A `PostToolUse` hook on `Edit|Write|MultiEdit|NotebookEdit`:

1. Extracts the changed file path from the tool input.
2. Greps `docs/memory/**/*.md` for that path in any `code:` list.
3. For each matching leaf: sets `dirty: true` and updates
   `last_touched` in the frontmatter (sed-level edit; no LLM, no
   network, ~20-40ms total).
4. If no matching leaf exists, records the changed path in
   `docs/memory/_inbox.md` (a flat append-only file) for later
   classification.

The hook never blocks edits. It is fire-and-forget bookkeeping.

**Phase B — Consolidation (deferred, LLM-driven, automatic).**
The `Stop` hook (session end) and the `/done` command both invoke
the consolidation pass:

1. Find every leaf with `dirty: true`.
2. For each, build a Sonnet/Opus call: "Here is the leaf's current
   body + the diffs to its referenced source files since
   `last_touched`. Update the leaf's content to reflect what
   changed; preserve voice; do not invent."
3. Write back, set `dirty: false`, update `last_touched`.
4. Also process `_inbox.md`: ask the LLM to classify each pending
   path into an existing leaf (or propose a new leaf), one round
   per session.

Stop is the strongest natural trigger because the session is already
ending — even a multi-second consolidation pass is invisible to the
user. `/done` is the redundant explicit trigger for users who run
long sessions and want consolidation mid-stream.

This split satisfies the user's "must be automatic" requirement
**without** introducing per-prompt orchestration: the per-edit
cost is bash+sed; the per-session cost is one LLM call.

### Cross-cutting concepts — tree plus front-matter cross-refs

A concept that spans two domains (OAuth concerns both `interface/auth`
and `network/http-client`) lives in **one canonical leaf** with a
`related:` cross-reference in the other leaf's frontmatter. The
canonical placement avoids drift; the cross-ref keeps the graph
navigable from either side. No bidirectional sync — `related:` is
declared, not derived.

### Commands

- `/memory-init` (Sonnet, new) — cold-start scan and tree proposal.
- `/remember <note>` (Haiku, new) — append a note to the right leaf;
  the model picks the leaf (or creates a new one) based on the note's
  content.
- `/done` (Opus, existing) — extended to invoke the consolidation
  pass before printing its existing report.

No `/forget` in v1. Pruning is manual file deletion; revisit if
memory bloat becomes a real problem.

## Consequences

- ✅ Zero runtime dependencies beyond aims's existing bash + jq.
  No Ollama, no embedding model, no Anthropic API key required at
  edit time (only at session end / `/done` / `/remember`).
- ✅ Retrieval is intentional and inspectable. When the model loads
  the wrong leaf, you can see exactly which `view` call it made.
- ✅ Aligns with the official `memory_20250818` primitive; if/when
  Claude Code exposes it explicitly, no migration.
- ✅ The cold-start LLM scan is a one-time cost paid at
  `/memory-init`; the per-session cost is one LLM call at Stop.
  Together far cheaper than the ADR-0006 design's per-prompt
  embedding + per-shift Haiku.
- ✅ The hook-marker mechanism gives the user a real "what touched
  what this session" audit trail at `docs/memory/_inbox.md`, even
  before consolidation runs.
- ⚠️ Wiki rot is the well-known failure mode of all curated-taxonomy
  systems. We bet the automatic maintenance hooks prevent it; if
  they don't, the user notices when `dirty:` leaves accumulate
  faster than they consolidate. Visible failure mode = catchable.
- ⚠️ The Stop-hook consolidation pass needs `ANTHROPIC_API_KEY` to
  succeed. If unset: dirty markers remain, _inbox.md keeps growing,
  consolidation can be run later by re-triggering. Tree remains
  usable for navigation (read-only) even without the key.
- ⚠️ A node's `code:` list must be kept current for the edit-marker
  to find it. The cold-start scan seeds this; consolidation can
  refresh it. A stale `code:` list means the marker silently misses
  a real touch. Mitigation: `/done` also reports leaves whose
  `code:` paths no longer exist, prompting cleanup.
- 🔒 Closes the door on embedding-based recall (ADR-0006) and on
  any per-prompt LLM orchestration for memory selection. The
  embedding code, had we shipped it, would be unwired now.

## Alternatives considered

- **Embedding-based recall (ADR-0006)** — superseded. The design
  conversation in ADR-0006 is preserved as historical record; the
  short version is "right idea, wrong scale". Tree navigation gives
  the same orientation effect at a tenth of the moving parts.

- **Manual tree maintenance** (no hooks) — rejected. Wiki rot
  guaranteed within months. The user explicitly required
  "automatically, without a doubt."

- **Synchronous LLM update on every edit** — rejected as expensive
  and slow. Every Edit/Write tool call would gain ~1-2 seconds and
  ~$0.0001. The two-phase split (cheap marker + batched
  consolidation) gets the same end-state automation without the
  per-edit tax.

- **Anthropic `memory_20250818` as the only access path** —
  rejected as the sole mechanism. The tool may not be exposed in
  every Claude Code runtime, and the file layout works identically
  through Read/Glob. We design for the tool but do not require it.

- **Pure tree, no cross-references** — rejected. Real concepts span
  multiple taxonomy branches; forcing a single home creates either
  duplication or stranded knowledge. `related:` in frontmatter
  costs one line and fixes the problem.

- **Graph database (Neo4j, kuzu) for cross-references** — rejected
  as 10× the infrastructure for 1.1× the expressive power at this
  scale. Markdown frontmatter is enough.

## Verification

- `docs/memory/` exists after `/memory-init` and contains `README.md`
  plus at least one tag subdirectory. Verified via `find docs/memory
  -name README.md | head`.
- The PostToolUse marker hook runs in <100ms on a 500-file `docs/memory/`
  tree (one `grep -l` plus one `sed -i` per matched leaf). Trace with
  `AIMS_MARKER_TRACE=1`.
- Editing a source file referenced in a leaf's `code:` flips the
  leaf's `dirty: true`. Verified by `tests/marker.sh`.
- Stop-hook consolidation reads every `dirty: true` leaf, calls the
  LLM, writes back, sets `dirty: false`. Verified by `tests/consolidate.sh`
  with a mocked Anthropic endpoint.
- `docs/memory/_inbox.md` accumulates source paths that touch no
  known leaf; `/done` empties it by proposing classifications.
- The `code:` reference in every leaf points to an existing path
  (or is flagged). Verified by `bash .claude/memory/lint.sh`.
- README "Design principles" gains a fifth point: "Memory is a
  navigable tree, automatically maintained — no embedding, no
  similarity search, no per-prompt LLM cost."
