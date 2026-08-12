# aims

This repository **is** the `aims` plugin. Working on it = developing the plugin itself. The plugin is
also installed locally (under `.claude/`) so its hooks apply to its own development. Dogfooding.

aims makes design the goal, and keeps the design knowledge co-located with the code. See `README.md`
for the overview; this file is the working guidance for developing aims itself.

## What is where

- `skills/aims-guide/` — the design method (SKILL + references + assets). The heart.
- `skills/aims-sharpen-prompt/` — the general-purpose "sharpen the task into a brief" companion.
- `commands/aims-*.md` — the design-method slash commands; `commands/install-on.md` — per-project install.
- `knowledge/` — the durable-knowledge layer: `format.md` (the record format), `anchor.py` (write-time
  stamper), `staleness_hook.py` (read-time advisory).
- Design records are **co-located in this repo's own code tree** (dogfood): `charter.md` and root
  `decisions/` at the root; a `component.md` in each code directory (`skills/aims-guide/component.md`,
  `knowledge/component.md`, …) with its `decisions/`/`insights/` beside it.

## How aims documents itself — co-located records

Durable design knowledge for aims lives **next to the code it describes**, not in a separate folder:

- A boundary/ownership/architecture decision → a `decisions/` record beside the code (append-only;
  supersede, never rewrite), or at the root if cross-cutting.
- The structure of a part → a `component.md` **inside that part's directory**.
- An engineering lesson → `insights/{dev,design,code}/` in the relevant directory (or root).
- A project-wide norm → a root `decisions/` record (no anchor).

**Anchor every record on filing** with `python3 knowledge/anchor.py <record>` — it derives the target
from the record's location (shape for a `component.md`, content for a decision/insight, none for a root
record) and stamps the single `hash:`/`shape:` line. Never hash by hand. When you read a record and the
staleness hook flags it, re-verify against the current code before relying on it.

Read by location: at a directory, read its `component.md` and local `decisions/`/`insights/`, then walk
up to the root — not the whole tree.

## Build & test

Markdown + bash + a little stdlib Python; no toolchain. Before declaring work complete, run:

```
bash tests/copies-identical.sh   # distribution surfaces stay byte-identical
bash tests/anchor.sh             # anchor stamping + staleness detection behavior
python3 -m py_compile knowledge/anchor.py knowledge/staleness_hook.py
```

## Hooks — inform, never block

aims has exactly two hooks, and neither blocks:

- `SessionStart` (`session-start.sh`) — surfaces in-progress plans and points at the co-located design
  records with the reading rule. Informational.
- `PostToolUse` on `Read` (`knowledge/staleness_hook.py`) — when an anchored record is read, re-derives
  its anchor from location and, on drift, injects an advisory "re-verify" note. Advisory only, fail-open.

The plugin's distributable hook source lives under `templates/hooks/`; the locally-installed copy under
`.claude/hooks/` (dogfooding). Keep them byte-identical (guarded by `tests/copies-identical.sh`); refresh
via `/install-on .`.

## What was removed (and why)

The memory-tree subsystem (mark/consolidate/find-dirty/lint/doctor/…) and its hooks were **cut**.
Relevance is now structural — a walk of the co-located record tree — so there is no mutable store to
keep coherent. The history of that subsystem lives in `docs/adr/` (frozen) and in the superseding
records here.
