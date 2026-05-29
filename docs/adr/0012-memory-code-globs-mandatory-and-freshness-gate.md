# ADR-0012: Module nodes must carry code globs; install gates tree work on freshness
Status: proposed
Date: 2026-05-28
Supersedes: —
Superseded by: —

## Context

The ADR-0007 memory tree is maintained by a two-phase loop: `post-edit-marker`
flags a node `dirty` when an edited file matches one of the node's `code:`
globs, and the consolidation loop (ADR-0009) later fills the node body. The
whole mechanism is driven entirely by `code:` globs.

But `new-node.sh` hardcoded `code: []`, and the `/install-on` cold-start
(Phase 5A) created one node per module without ever filling `code:`. The
result: every freshly-bootstrapped node was **inert** — no glob ever matched,
so the marker never flagged it dirty, so consolidation never ran, so the body
stayed the empty six-section scaffold forever. A real install had a full
~9-node tree where all bodies were still empty weeks later, and nobody knew
because the failure is silent. Re-running `/install-on` did not help: the
augment path (Phase 5B) only *adds* nodes, it never backfilled the empty
`code:` of existing ones.

Separately, an idempotent re-install re-scanned/re-augmented the tree every
time even when it had just been curated, which is wasted work and risks
churn on an actively-maintained tree.

## Decision

1. **`code:` globs are mandatory for `module` nodes.**
   - `new-node.sh` accepts trailing glob arguments
     (`new-node.sh <path> <kind> [glob ...]`) and renders them as a YAML
     block list; with no globs it still emits `code: []`.
   - `/install-on` Phase 5A (cold-start) MUST pass ≥1 glob for every
     `module` node. `topic`/`decision`/`runbook` nodes may omit globs.
   - Phase 5B (re-install) MUST **backfill** `code:` into existing
     `module` nodes that have `code: []`, frontmatter-only (body untouched),
     so an old inert tree heals on re-install.
   - `lint.sh` and `doctor.sh` report any `module` node with `code: []` as
     an **inert node** — a first-class health signal.

2. **Install gates tree work on a 7-day freshness window.** A missing tree
   is always cold-started. An existing tree is audited/augmented only if its
   newest node `last_consolidated` is older than 7 days; within a week,
   `/install-on` skips all tree work and only refreshes the system layer.
   Freshness is read from frontmatter `last_consolidated`, never file mtime
   (a fresh `git clone` resets mtimes).

## Consequences

- ✅ A bootstrapped tree is live: edits flag nodes dirty, consolidation runs,
  bodies fill. The pipeline actually works end-to-end.
- ✅ Re-install heals a legacy inert tree instead of leaving it dead.
- ✅ `doctor`/`lint` make the silent failure visible (`inert nodes` count).
- ✅ Re-installing over a freshly-curated tree is cheap and non-disruptive.
- ⚠️ Cold-start globs and backfill globs are inferred by the model and may be
  imprecise. Mitigated: frontmatter-only edits (bodies never touched) and
  lint surfaces any node still left inert.
- ⚠️ The freshness probe relies on `last_consolidated` being honest. `mark.sh`
  owns that field, so it tracks real consolidation; acceptable.
- 🔒 Rules out `module` nodes with no code anchor — if a node tracks no code,
  it must be a `topic`/`decision`, not a `module`.

## Alternatives considered

- **Leave cold-start bodies empty and rely on the consolidation loop only.**
  Rejected — that is exactly today's broken state: with `code: []` the loop is
  never triggered.
- **Use file mtime for freshness.** Rejected — a `git clone` or a re-install
  copy resets mtimes, so the tree would falsely read as "just updated."

## Verification

- `new-node.sh <p> module a.py b.py` produces a block `code:` list;
  `new-node.sh <p> topic` produces `code: []`.
- `lint.sh` flags a `module` node with `code: []`; `doctor.sh` shows an
  `inert (code: [])` count.
- `commands/install-on.md` Phase 5 documents the freshness gate, the
  cold-start glob requirement, and the Phase 5B backfill step (and all three
  install-on.md copies are byte-identical).
