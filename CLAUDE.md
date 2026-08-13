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
- Design records are **co-located in this repo's own code tree** (dogfood): root `goals.md`,
  `architecture.md`, and `decisions/` (system ADRs); a companion beside each source file
  (`knowledge/anchor.py.md`, `knowledge/staleness_hook.py.md`, …).

## How aims documents itself — companions + root records

Durable design knowledge for aims lives **next to the code it describes**, in two homes:

- Knowledge about one source file → its **companion** `<file>.md` beside it, under the sections
  Insights / Decisions / Discussions (Decisions are append-only — supersede in place, never rewrite).
- Cross-cutting knowledge → a root record: `goals.md`, `architecture.md`, `base-dependencies.md`,
  `dependencies.md`, or a `decisions/` ADR.

**Anchor every companion on filing** with `python3 knowledge/anchor.py <companion>` — it hashes the
same-named source file and stamps the single `hash:` line (a system record with no same-named source
file gets none). Never hash by hand. When you read a companion and the staleness hook flags it,
re-verify against the current code before relying on it.

Read by navigating: to understand a file, open its companion; for system context, read the root records
— not the whole tree.

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

There is no background maintenance machinery — no memory store, no consolidation, no doctor. Relevance
is structural (navigate the co-located records), so nothing needs to be kept coherent between turns.
