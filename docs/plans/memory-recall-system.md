# Plan: Memory-recall system implementation (ADR-0006)
Status: in-progress
Started: 2026-05-25

## Context

ADR-0006 (proposed, this branch) specifies a two-tier memory model:
SessionStart-time Tier-1 (project orientation, always injected) plus
event-driven Tier-2 (full recall + Haiku rerank, firing only on the
session's first prompt and on detected topic shifts). The ADR settles
the data model (markdown files in `docs/memories/` with a sidecar
embeddings cache in `.claude/embeddings/`), the embedding model
(`bge-small-en-v1.5` via local Ollama), the keyword-surrogate encoding
strategy (LLM-generated English title+keywords are embedded; the body
is stored raw and never embedded), and the relationship to git
(memories tracked by default, like ADRs).

Today aims has:
- Three hooks: `templates/hooks/session-start.sh`,
  `prompt-submit.sh`, `pre-write.sh`. Local copies under
  `.claude/hooks/`.
- Four discipline commands: `templates/commands/{plan,adr,grunt,
  done}.md`.
- `commands/init-workflow.md` bootstraps a target.
- `templates/settings.json.tmpl` wires the three existing hooks.
- No language toolchain beyond bash + jq.

Constraints:
- aims is "markdown + bash" by tradition (`CLAUDE.md`). Adding a
  language runtime is a deliberate deviation that needs an ADR.
- ADR-0002 forbids per-prompt LLM orchestration; event-driven Haiku
  rerank is the explicit exception, justified in ADR-0006.
- The plugin must remain idempotent under repeated `/init-workflow`
  on existing targets — same merge-aware behaviour as today.

## Goal

Ship a memory-recall pipeline such that, in a freshly-bootstrapped
target with Ollama + `bge-small-en-v1.5` + `ANTHROPIC_API_KEY`
present: (a) the first prompt of every session triggers a recall
that injects 0–5 memories tagged `[aims-recall]`; (b) topic shifts
mid-session trigger the same plus a `/clear` recommendation; (c)
new ADRs and plan-decisions written during a session are auto-
ingested as memories at session Stop; (d) `tests/recall.sh` passes
end-to-end.

## Options considered

- **A — sqlite-vec DB** (original ADR-0006 draft): rejected at
  v1 scale. See ADR-0006 "Alternatives".
- **B — pure bash + awk for all vector math, no Python**: chosen.
  Cosine over <500 floats per file is a one-line awk; sequential
  scan over 100 memory files finishes in <100ms. Preserves the
  "markdown + bash" boundary.
- **C — small Python helper for vector math**: rejected for v1.
  Would add a runtime dependency for negligible code reduction;
  awk handles all the arithmetic we need.

## Steps

Each step is independently verifiable. Order matters where the next
step needs the previous one's output; otherwise noted "any order".

### 1. Add the memory-layer scripts under `templates/memory/`

Create five small bash/awk helpers. Each has a `--help` and runs
under `bash -n` cleanly:

- `embed.sh <text>` → POST to Ollama `/api/embeddings`, return
  newline-separated floats on stdout. Configurable model via
  `AIMS_EMBED_MODEL` (default `bge-small-en-v1.5`).
- `cosine.awk` → reads two `.vec` files on argv, prints cosine
  similarity. One-liner.
- `recall.sh <query>` → embeds the query, iterates
  `.claude/embeddings/*.vec`, prints top-20 as TSV
  (`<sim>\t<id>\t<title>\t<source_path>`).
- `rerank.sh <query>` → reads top-K TSV on stdin, calls Anthropic
  Haiku via curl, returns selected memory IDs (0–5) with one-line
  reasons. Falls back to `head -5` if `ANTHROPIC_API_KEY` unset.
- `shift-detect.sh <prompt>` → embeds prompt, compares to
  `.claude/session-centroid.vec`, prints `shift=true|false
  distance=<n>`. Updates the centroid file in place.

Verify: `bash -n templates/memory/*.sh && awk -f templates/memory/
cosine.awk </dev/null` (parses without error).

### 2. Add the ingestion scripts under `templates/memory/`

- `ingest.sh <kind> <importance> <source_path>` → reads the memory
  body from stdin, calls Haiku (via curl) to generate a one-line
  English `title` and 5–10 space-separated English `keywords`,
  writes `docs/memories/NNNN-slug.md` with full frontmatter, and
  generates `.claude/embeddings/NNNN.vec`. Falls back gracefully if
  Haiku unavailable (uses first-line-as-title + grep-extracted
  identifier-like tokens as keywords).
- `index.sh` → walks `docs/memories/*.md`, regenerates
  `.claude/embeddings/*.vec` for any memory whose file is newer
  than its sidecar (or sidecar missing). Idempotent.

Verify: `bash -n templates/memory/{ingest,index}.sh`. Manual test:
pipe a known body into `ingest.sh decision 0.8 docs/adr/0006-...md`
and confirm the .md and .vec land.

### 3. Update `templates/hooks/session-start.sh`

Two additions (existing behaviour preserved):

- At the top, remove `.claude/session-centroid.vec` if it exists
  (new session = fresh topic centroid).
- After the existing in-progress-plans / recent-ADRs block, append
  the contents of `docs/project-overview.md` if it exists (capped
  at 2KB).

Verify: `bash -n templates/hooks/session-start.sh`. Smoke test:
create a fake project-overview.md, source the hook, confirm it
appears in stdout.

### 4. Update `templates/hooks/prompt-submit.sh`

Append a new section after the existing router logic. New flow:

1. After the router has decided whether to emit its
   `additionalContext` block, run `shift-detect.sh` on the prompt
   (always — this is the cheap per-prompt path).
2. Determine if this is the session's first prompt: check for a
   sentinel file `.claude/.session-recalled` — absent on
   SessionStart (the hook from step 3 removed the centroid; we'll
   also have it remove this sentinel), present after the first
   recall.
3. If first-prompt OR shift-detect says `shift=true`:
   a. Run `recall.sh "<prompt>" | rerank.sh "<prompt>"` to get the
      filtered top-N memory IDs.
   b. Build a `[aims-recall]` block listing the memories' titles +
      bodies (capped at 4KB total).
   c. On shift (not first-prompt), append the `/clear` suggestion.
   d. Emit the block as additional `hookSpecificOutput.
      additionalContext`. If the router already emitted one, the
      hook must merge — Claude Code accepts at most one
      additionalContext per hook invocation; concatenate with `\n
      ---\n` separator.
   e. Touch `.claude/.session-recalled`.
4. If neither trigger: emit nothing new (router output stands as-is).

Verify: `bash -n templates/hooks/prompt-submit.sh`. Trace-test with
`AIMS_RECALL_TRACE=1` and a seeded memory store.

### 5. Add `templates/hooks/session-stop.sh` (new)

Stop hook fires when the session ends. Logic:

- Read `.claude/last-stop.timestamp` (or default to 1970).
- For each `docs/adr/*.md` newer than the timestamp: extract the
  `## Decision` + `## Consequences` sections, pipe to `ingest.sh
  decision 0.9 <path>`.
- For each `docs/plans/*.md` newer than the timestamp: grep for
  lines starting with `Decided:`, `Avoid:`, `Gotcha:` (case-
  insensitive); each line → `ingest.sh deliberation 0.7 <path>`.
- Update `.claude/last-stop.timestamp` to now.

Always exits 0 (never blocks). Errors go to stderr.

Verify: `bash -n templates/hooks/session-stop.sh`. Smoke test:
touch a fake ADR with a Decision section, run the hook, confirm a
new `docs/memories/NNNN-...md` appears.

### 6. Add `templates/commands/remember.md` (new, Haiku)

Frontmatter pins the model to Haiku. Body: takes the user's
note from `$ARGUMENTS`, calls `ingest.sh gotcha 0.8 manual` with
the note as stdin. Reports the new memory's ID and title.

Verify: file exists at the right path with the Haiku frontmatter
matching the `/grunt` style.

### 7. Add `templates/commands/forget.md` (new, Haiku)

Frontmatter: Haiku. Body: lists candidate memories (those with
`access_count=0`, age > 180 days, importance < 0.5) by reading
the frontmatter of each `.md` file. Asks user to confirm
deletion via `AskUserQuestion`. On confirm, removes both the .md
and the .vec sidecar.

Verify: file exists, dry-run with no candidate matches reports
"nothing to forget".

### 8. Update `templates/settings.json.tmpl`

Add the Stop hook to the existing JSON:

```json
"Stop": [
  { "hooks": [
    { "type": "command", "command": "bash .claude/hooks/session-stop.sh" }
  ]}
]
```

Verify: `jq . templates/settings.json.tmpl` parses cleanly.

### 9. Update `commands/init-workflow.md`

Add to the bootstrap interview (after the existing questions):

- "Memory recall (Tier-2) requires Ollama + `bge-small-en-v1.5`
  + an Anthropic API key. Install now / explain commands / skip
  (Tier-1 only)?"

Idempotent install steps (additions only, no edits to existing
behaviour):
- `mkdir -p docs/memories .claude/embeddings`
- Copy `templates/memory/*.sh|*.awk` to `.claude/memory/`
- Copy `templates/commands/{remember,forget}.md` to
  `.claude/commands/`
- Copy `templates/hooks/session-stop.sh` to `.claude/hooks/`
- Append `.claude/embeddings/` and `.claude/session-centroid.vec`
  and `.claude/.session-recalled` and `.claude/last-stop.timestamp`
  to `.gitignore` (idempotent — check before append).
- Add a `## Memory recall` section to the target's `CLAUDE.md` if
  not present (merge-aware).

Verify: run `/init-workflow` against a fresh test project,
inspect the resulting tree.

### 10. Update `templates/CLAUDE.md.tmpl`

Add a `## Memory recall` section documenting:
- What gets remembered (decisions, plan deliberations, /remember
  notes).
- When recall fires (session start, topic shift).
- How to disable (unset envs, or remove the Stop hook).
- The git story (memories committed by default; how to make them
  private).

Verify: `markdownlint` (if available) or visual review.

### 11. Dogfood — copy templates into `.claude/`

Per the dogfooding rule in this repo's `CLAUDE.md`:
- Copy `templates/memory/*` → `.claude/memory/`
- Copy `templates/commands/{remember,forget}.md` → `.claude/commands/`
- Copy `templates/hooks/session-stop.sh` → `.claude/hooks/`
- Update `.claude/settings.json` to match.

Then seed the memory store with the existing ADRs and plans:
`for f in docs/adr/000[1-6]-*.md; do bash .claude/memory/ingest.sh
decision 0.9 "$f" < <(awk '/^## Decision/,/^## Consequences\b/' "$f"); done`

Verify: `ls docs/memories/` shows N memory files; `ls .claude/
embeddings/` shows matching .vec files.

### 12. Add `tests/recall.sh`

A small end-to-end smoke test:
- Creates a temp dir with mocked Ollama + Anthropic responses.
- Seeds three memories: one obviously relevant to a test query,
  one marginally related, one totally irrelevant.
- Runs `recall.sh "<query>" | rerank.sh "<query>"`.
- Asserts: the relevant memory is in the output, the irrelevant
  one is not, and the output count is ≤5.

Verify: `bash tests/recall.sh` exits 0.

### 13. Write the supporting ADRs

After implementation works end-to-end, write two follow-up ADRs:

- **ADR-0007** "Memory layer uses awk for vector math, not Python"
  — captures the deliberate choice to stay bash-family, and the
  N≤1000 ceiling at which it would need to be revisited.
- **ADR-0008** "Memories tracked in git by default"
  — captures the three-layer split (git / ADRs / memories) and
  the override path for private memories.

These are post-implementation because they record what we built;
the design rationale already lives in ADR-0006.

## Verification

End-to-end commands that prove the plan succeeded:

- `bash -n templates/memory/*.sh templates/hooks/*.sh .claude/memory/
  *.sh .claude/hooks/*.sh` — all shell scripts parse.
- `awk -f templates/memory/cosine.awk </dev/null; echo $?` — awk
  script syntactically valid.
- `bash tests/recall.sh` — end-to-end smoke test passes.
- Run a real Claude session against this repo: first prompt
  "what does aims do?" should produce a `[aims-recall]` block
  with at least the project-overview ADR-0001 memory. Then
  prompt "let's switch to talking about Ebbinghaus and decay" —
  expect a topic-shift recall block plus a `/clear` recommendation.
- `git status` after a session shows new files only under
  `docs/memories/` (the .md files); `.claude/embeddings/` changes
  are gitignored.

## Risks / unknowns

- **Ollama cold-start**: first call after the daemon idles can
  take ~2s. We accept this on the session's first prompt; if it
  becomes painful we can add a SessionStart-time warmup ping.
- **Haiku JSON robustness**: occasionally Haiku may return
  malformed JSON. The rerank wrapper must tolerate this — fall
  back to top-5 by composite score and log to stderr.
- **awk float precision**: awk uses double-precision, fine for
  cosine over 384-d vectors. Verified empirically against a
  Python reference for a few cases during step 12.
- **Hook output concatenation**: Claude Code accepts one
  `additionalContext` per UserPromptSubmit invocation. If the
  router already emitted one, our recall block must be
  concatenated, not a second emission. Spec is clear; need to
  verify behaviour in the smoke test.
- **Sentinel file races**: if a user opens two Claude Code
  sessions in the same checkout, `.session-recalled` can flip
  unexpectedly. We accept this — recall might fire twice or not
  fire on session 2's first prompt. Documented in the CLAUDE.md
  section.
- **First-time UX**: a user with no memories yet runs into recall
  blocks that say "nothing relevant". The block should suppress
  itself entirely on empty result, not say "[aims-recall] no
  memories found".

## ADRs to record after implementation

- [ ] ADR-0007 — Memory layer uses awk for vector math (not
      Python or a vector DB) at v1 scale.
- [ ] ADR-0008 — Memories tracked in git by default; the
      three-layer documentation split (git / ADRs / memories).
- [ ] Update ADR-0006 status to `accepted` once the
      implementation lands.
