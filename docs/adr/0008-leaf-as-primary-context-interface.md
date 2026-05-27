# ADR-0008: Node as primary context interface

Status: proposed
Date: 2026-05-27
Supersedes: —
Superseded by: —

## Context

ADR-0007 established the tree-based memory subsystem, but framed each
node as a "navigator over other memory sources". In practice the
maintenance pass populated only `Purpose`, leaving the other four
sections empty. A session that loads a node today gets a one-line
summary plus a pile of pointers — not a working brief.

The user's intent is sharper than ADR-0007 captured:

- The node is the **primary read interface** for memory. The session
  loads it and that gives most of what is needed for the code at hand.
- Backing stores (ADRs, plans, git log, Slack/issues, CLAUDE.md) hold
  the full detail. The node points to them; the session follows
  pointers only when it needs to deepen.
- aims is host-neutral. Bugs do not live in GitHub Issues from aims's
  point of view — they live wherever the project keeps them (or
  nowhere, with the commit log as the trail).
- The memory tree must travel with the project. Cloning the repo to a
  different host, or copying the working tree to another path, must
  not break a single reference inside `docs/memory/`.

Two gaps in ADR-0007's node schema surface from this:

1. **Bugs have no first-class section.** Open ones (warn next session)
   and closed ones (don't redo the failed approach) currently bleed
   into "Deliberations & history" or get lost. They are a distinct
   content class.
2. **No tightness target.** "No size cap" was correct as a safety
   valve but wrong as a guideline; without a target, leaves either
   stay empty (today) or risk becoming dumps. The session needs to
   scan a node in seconds.

## Decision

Refine the ADR-0007 node body to make it a working brief. Six sections,
target ~1–2 KB:

```markdown
## Purpose
One paragraph: what this code does.

## Design rationale
2–4 bullets: why it is shaped this way. Each bullet may end with a
pointer (ADR-NNNN, commit SHA, plan slug).

## Invariants & gotchas
What must not break when editing. Concise.

## Known issues
- open:  <one-line> — <pointer: commit / repo-relative path / URL>
- fixed: <one-line: what broke and why> — <commit SHA>

## Pointers
- ADRs:     ADR-NNNN
- Plans:    docs/plans/<slug>.md (in-progress | done)
- Commits:  <SHA> — one-line  (anchor commits only)
- External: <URL> — one-line  (Slack, issues, docs)

## Open questions
Design questions not yet decided. Distinct from bugs.
```

**All in-project references are repo-relative.** Pointers to ADRs,
plans, CLAUDE.md sections, code files, and other leaves use paths
relative to the repository root (e.g. `docs/adr/0007-...md`,
`src/auth/callback.py:42`). No absolute filesystem paths. No
host-bound URLs (no `https://github.com/<org>/<repo>/blob/...` for
content the repo already contains). Commit SHAs are inherently
repo-local and fine. External URLs (Slack threads, third-party docs,
issue trackers if the project uses one) are unavoidable and stay as
URLs — they refer to content that lives outside the repo. The result:
cloning the repo to a new host or path leaves every in-project
pointer intact.

The ~1–2 KB target is a soft norm carried by the consolidation prompt,
not enforced by the linter. If a node bulges past it: a coherent
sub-topic → extract a sibling node; a discrete decision → extract an
ADR, replace the prose with a pointer.

ADRs and other backing stores remain **append-only stores**. The node
cites them by ID/path. The node is the only file the session is
expected to read first; everything else is fetched on demand.

Bugs are host-neutral: one-line description + whichever pointer is
available (commit SHA always; repo-relative path / URL only when
applicable).

`stop-consolidate` is updated to populate all six sections from
CLAUDE.md, ADRs, git log on `code:` files, plans that touched those
files, and URLs cited in the session transcript (for
`Pointers > External`). `/memory-init` is updated to seed the same
sections from the same sources at cold-start.

### Terminology and hierarchy: nodes, not leaves; DAG, not tree

ADR-0007 used "leaf" interchangeably with "node file", which conflated
two concepts: a *leaf* (by graph definition: no children) and a *node*
(any vertex in the structure). A node file under `docs/memory/` may
itself summarise many child nodes. **The canonical term is "node".**
"Leaf" is reserved for nodes that genuinely have no children.

The memory structure is also **not a strict tree**: a single
implementation node may have several semantic parents — e.g. the plan
that scoped it, the ADR that constrains it, and the higher-level code
module that calls it. The structure is a directed acyclic graph (DAG).
The directory layout under `docs/memory/` continues to provide a
default filesystem placement, but the semantic edges are recorded in
frontmatter:

```yaml
parents:                        # zero or more — heterogeneous
  - docs/memory/installer/README.md       # parent node
  - docs/adr/0005-clone-and-bootstrap-install.md   # parent ADR
  - docs/plans/2026-05-27-leaf-as-primary-context.md  # parent plan
children:                       # zero or more — node paths only
  - docs/memory/installer/templates.md
```

`parents:` may reference any in-project document that conceptually
defines this node (other nodes, ADRs, plans, source files).
`children:` lists node paths only — children live in the memory tree.
Both lists are repo-relative paths. `related:` (from ADR-0007) is
retained for sideways cross-references; it is not a parent/child
edge.

**Discovery vs. content are two separate concerns.** Discovery is
filesystem-based and cheap: a session that touches `src/foo/bar.py`
finds the relevant node via the `code:` reverse-lookup that
`mark.sh` already implements (or by reading the README at the
matching subdirectory). The directory layout under `docs/memory/`
exists for this discovery step. Once the node is loaded, its
*content* — `parents:`, `children:`, `related:`, body `Pointers` —
forms a semantic DAG that need not align with the directory
hierarchy at all. A node may have parents in unrelated tags, ADRs,
plans, or source modules.

This **refines** ADR-0007's node schema; storage layout, two-phase
maintenance, and navigation are unchanged.

## Consequences

- ✅ A loaded node is a working brief, not a one-liner + pointers.
- ✅ Bugs (open + fixed) become durable institutional memory at the
  place the next session will actually look.
- ✅ aims stays host-neutral. No coupling to any specific tracker, no
  hardcoded host URLs for in-project content.
- ✅ The memory tree is portable: re-cloning, mirroring, or moving the
  working tree never invalidates an in-project pointer.
- ✅ Backing stores stay clean: ADRs append-only, plans
  immutable-once-done. The node carries pointers only.
- ⚠️ The ~1–2 KB target is soft. Drift possible; `/done` flags leaves
  over 4 KB so the user can decide to split or extract.
- ⚠️ Consolidation prompt grows (six structured sections vs. one).
  One LLM call per dirty node; throttling already amortizes.
- ⚠️ URL capture requires the consolidation pass to receive the
  session transcript (or extracted URLs). New input to the prompt.
- 🔒 Closes the ADR-0007 framing of "node as navigator". The node is
  the primary interface; navigation is a side-effect.

## Alternatives considered

- **Two-tier node** (`<node>.md` + `<node>.history.md`) — rejected.
  Stay one file; tail growth signals a sibling node or an ADR.
- **Auto-extract URLs without review** — rejected. Session
  transcripts contain incidental URLs; LLM filters during
  consolidation.
- **Couple "Known issues" to a specific tracker** — rejected. aims is
  host-neutral; plain text + commit SHA + optional URL is enough.
- **Allow absolute paths or host-bound URLs for convenience** —
  rejected. Breaks the moment the repo is cloned to a new path or
  pushed to a new host. Repo-relative is mandatory.
- **Fix only the consolidation prompt, leave the schema alone** —
  rejected. The schema gap (no Known issues, no size norm) is real;
  prompt cannot create sections the schema lacks.

## Verification

- A node updated by consolidation contains all six body sections
  (populated or explicitly empty, never silently omitted). Verified by
  an extension to `bash .claude/memory/lint.sh`.
- `Known issues > fixed` entries point to commits that exist in
  `git log` for a file in `code:`. Verified by lint.
- `Pointers > ADRs` entries reference ADRs that exist in `docs/adr/`.
  Verified by lint.
- No in-project pointer is absolute (no leading `/` or `~`) and no
  in-project pointer is a host-bound URL pointing back into the same
  repo. Verified by lint (regex over `docs/memory/**/*.md`).
- Every `parents:` and `children:` entry resolves to a file that
  exists on disk. Verified by lint.
- The DAG is acyclic: following `parents:` upward from any node
  reaches a fixed point in finite steps. Verified by lint.
- A node's serialized size stays under 4 KB in `/done`'s health
  report; the 1–2 KB target is informational.
- `docs/memory/installer/init-workflow.md` shows all six sections
  populated after one consolidation pass following implementation.
