# ADR-0007: Tree-based project memory with automatic build and maintenance
Status: accepted (partially superseded by ADR-0009)
Date: 2026-05-25

> **Partially superseded by [ADR-0009](0009-in-band-memory-consolidation.md).**
> The "Stop hook calls Sonnet via curl" mechanism and the ⚠️
> `ANTHROPIC_API_KEY` consequence below no longer apply. Consolidation now
> runs in-band: the Stop hook injects the prompt as `additionalContext`
> and the active session executes the Edits. Everything else in this ADR
> (tree shape, Phase A marker, throttle thresholds, commands) is unchanged.
Supersedes: ADR-0006 (embedding-based recall)
Superseded by: —

Implemented in commits a0f4913, 2d967a8, 47977ae and the dogfood/test
commit that follows this ADR's status flip. Tests under `tests/marker.sh`
and `tests/consolidate.sh` cover the marker-flips-dirty path and the
throttled-consolidation path (with a mocked Anthropic endpoint).

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

### Leaf content schema

Each leaf carries fixed-shape frontmatter and five named body sections.
The shape is rigid enough that hooks and the model can navigate it
mechanically, and loose enough that any section may be empty.

**Frontmatter** (machine-readable; the contract the hooks rely on):

```yaml
---
node: interface/auth/oauth-callback
kind: module                    # module | decision | topic | runbook
code:                           # source files this leaf documents
  - src/auth/callback.py
  - src/auth/handlers.py:42-90
commits: [a1b2c3d, e4f5g6h]     # only seminal/anchor SHAs (~5-10 max);
                                # the git log holds the rest
sessions:                       # plans/ADRs that fed this leaf
  - docs/plans/oauth-callback-2026-04.md
  - docs/adr/0012-pkce-required.md
related:                        # cross-refs to other leaves
  - network/http-client/auth-headers

# Pointers to memory that lives OUTSIDE the tree.
# These are read-only references; the tree never overwrites them.
claude_md_refs:                 # sections in project or user CLAUDE.md
  - "Models policy"
  - "Hooks"
external_refs:                  # other files holding relevant memory
  - { path: ~/.claude/memory/auth-notes.md, kind: user-memory,
      why: "cross-project auth conventions" }
  - { path: docs/adr/0012-pkce-required.md, kind: adr,
      why: "established PKCE invariant" }

owners: [ema]                   # optional — who knows this best
dirty: false                    # system: flipped by post-edit marker
last_touched: 2026-05-25T12:34:56Z       # system
last_consolidated: 2026-05-20T09:00:00Z  # system
---
```

`code:` is a list of paths (optionally `:start-end`). It is what lets
the edit-marker hook find which leaves a changed source file touches.

`commits:` is a **curated, append-only list of anchor SHAs**, not a
mirror of `git log`. A SHA goes in when it is the commit you would
point a newcomer to in order to explain how this leaf came to be —
the introduction of a feature, a bug-fix that established an
invariant, a rollback that closed a door. The git log holds the rest;
duplicating it here would just decay.

`kind:` hints which body section is the centre of the leaf — it does
not change the schema:

| kind       | centre of attention                              |
|------------|--------------------------------------------------|
| `module`   | Editing considerations + Logical rules           |
| `decision` | Deliberations & history                          |
| `topic`    | Logical rules & invariants                       |
| `runbook`  | Editing considerations (as step-by-step actions) |

**Body — five named sections, fixed names, all optional:**

```markdown
# OAuth callback handling

## Purpose
One or two lines: what this leaf documents. Filled at cold-start by
the LLM scan; refined by hand if the scan's summary is off.

## Logical rules & invariants
Things that MUST hold, whether or not they are enforced in code.
Business rules, security invariants, contracts with callers.
  - "state param MUST be a nonce with TTL ≤ 5 min."
  - "redirect_uri MUST match the whitelist exactly — substring
    matching is unsafe (CVE-2026-1234)."

## Editing considerations
What to check before touching the referenced code. The section that
saves the next session from re-discovering past mistakes.
  - "Changing verify_state() requires re-running tests/integration/
    test_csrf.py — unit tests don't cover all paths."
  - "Token shape changes propagate to migrations/0042_*.sql."
  - "Making the callback async requires updating the timeout in
    src/auth/middleware.py."

## Deliberations & history
Why it is the way it is. What was considered and rejected. The
referenced commits (and ADRs/plans) reappear here as narrative:
  - "Considered JWT vs server-side session cookies (ADR-0012).
    Chose cookies because the mobile client could not store JWT
    securely at the time."
  - "Tried refresh-token rotation in 2026-03 (commit a1b2c3d);
    rolled back in e4f5g6h after mobile races caused logouts."

## Open questions
What we do not yet know but probably should:
  - "Is the current refresh policy SOC2-compliant?"
  - "Should callback success emit to the event bus?"

`/done` will surface these for periodic review.
```

No size cap. A leaf is as big as the topic justifies; if a section
grows long enough that the model fails to use it well, splitting
into sub-leaves is a deliberate edit, not a rule the linter enforces.

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

**Phase B — Consolidation (deferred, LLM-driven, throttled).**

`Stop` is the chosen trigger because real users often leave Claude
Code open for days without ever firing `SessionEnd`. But `Stop` fires
after **every** Claude turn, so an unconditional LLM call there would
mean ~30 LLM calls per active session. Throttle in bash before
calling the LLM:

```
Stop hook fires:
  ↓
bash check:  N_DIRTY = count of leaves with dirty: true
             T_LAST  = mtime of .claude/memory/.last-consolidated
  ↓
  if  N_DIRTY ≥ 5   OR
      (now - T_LAST > 30 min  AND  N_DIRTY > 0)  →  run consolidation
  else                                            →  exit 0 (≈5ms, invisible)
```

When the threshold trips, the consolidation pass does:

1. Find every leaf with `dirty: true`.
2. For each, build a Sonnet/Opus call: "Here is the leaf's current
   body + the diffs to its referenced source files since
   `last_touched`. Update the leaf's content to reflect what
   changed; preserve voice; do not invent."
3. **Check `external_refs` and `claude_md_refs`** for mtime/hash
   changes since `last_consolidated`; for each changed reference,
   append a one-line breadcrumb in the leaf's `## Deliberations &
   history` section: `"<path> updated <date>, review for impact"`.
   **Never overwrites the referenced file.**
4. Write back, set `dirty: false`, update `last_touched` and
   `last_consolidated`.
5. Also process `_inbox.md`: ask the LLM to classify each pending
   path into an existing leaf (or propose a new leaf). Apply
   confident matches; leave ambiguous ones for `/done`.

Default thresholds: `N_DIRTY_MAX=5`, `T_INTERVAL=30min`. Configurable
per project via `.claude/memory/throttle.conf`.

`/done` runs the same consolidation **unconditionally** (ignores the
throttle); it is the explicit trigger when you want everything
caught up right now.

`SessionEnd` (when it does fire) also runs the consolidation as a
safety net — cheap when no dirty leaves, ensures nothing waits if
you actually do close the CLI.

This satisfies the "must be automatic" requirement without per-
prompt orchestration: the per-edit cost is bash+sed (~30ms); the
per-Stop cost is bash-only (~5ms) until threshold; the LLM call
happens only at natural pause points.

### Cross-cutting concepts — tree plus front-matter cross-refs

A concept that spans two domains (OAuth concerns both `interface/auth`
and `network/http-client`) lives in **one canonical leaf** with a
`related:` cross-reference in the other leaf's frontmatter. The
canonical placement avoids drift; the cross-ref keeps the graph
navigable from either side. No bidirectional sync — `related:` is
declared, not derived.

### Relationship to existing Claude Code memory mechanisms

aims's tree does NOT replace or duplicate Claude Code's native
memory. The tree is a **navigator over multiple memory sources**;
each piece of information has exactly one home, and the tree points
to it.

| Mechanism                       | Owner             | aims tree's role                                                                 |
|---------------------------------|-------------------|----------------------------------------------------------------------------------|
| `CLAUDE.md` (project/user)      | Claude Code       | Unchanged. Leaves reference relevant sections via `claude_md_refs:`.            |
| `/memory` slash command         | Claude Code       | Unchanged. Output goes to `CLAUDE.md`; tree picks it up at next consolidation. |
| `memory_20250818` tool          | Claude Code (when exposed) | When the tool is available, configure it to target `docs/memory/` (via symlink `/memories → docs/memory` if the path prefix is fixed). The tree's file layout works with Read/Glob regardless. |
| `docs/adr/`, `docs/plans/`      | aims (existing)   | Formal records. Leaves reference via `sessions:` and prose in `## Deliberations & history`. |
| `docs/memory/` (this ADR)       | aims (new)        | The map. Owns per-topic Logic/Editing/Deliberations/Open questions; points to everything else. |

**No content migration at install.** CLAUDE.md keeps its current
contents (build/test commands, workflow, hook config, plugin notes).
The cold-start `/memory-init` reads CLAUDE.md and seeds
`claude_md_refs:` in the relevant leaves; it does **not** copy
content into the tree.

**The `/memory` slash command keeps working as Claude Code defines
it** — appends to CLAUDE.md. The next consolidation pass detects the
CLAUDE.md change, identifies which leaf (if any) should reference
the new section, and adds a `claude_md_refs:` entry. If no leaf
fits, the change goes to `_inbox.md` for classification at the next
`/done`. The user never has to choose between `/memory` and
`/remember`; both feed the same map.

**The tree's update never modifies CLAUDE.md or user-memory files.**
External references are read-only. This is the **non-duplication
invariant**.

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
