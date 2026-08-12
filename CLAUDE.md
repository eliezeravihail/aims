# aims

This repository **is** the `aims` plugin. Working on it = developing the plugin itself. The plugin is
also installed locally (under `.claude/`) so its hooks apply to its own development. Dogfooding.

aims is Balash's design method carried onto a capsa durable-knowledge layer. See `README.md` for the
overview; this file is the working guidance for developing aims itself.

## What is where

- `skills/aims-guide/` — the design method (SKILL + references + assets). The heart.
- `skills/aims-sharpen-prompt/` — the general-purpose "sharpen the task into a brief" companion.
- `commands/aims-*.md` — the design-method slash commands; `commands/install-on.md` — per-project install.
- `docs/format-profile.md` — the capsa subset aims writes + the `anchors:`/`shape:` fields.
- `vendor/capsa/` — the capsa format, **developed here now** (the standalone repo is retired). Editing
  the grammar is a reviewed act that bumps `vendor/capsa/VERSION`.
- `tools/aims_anchor.py` — stamps a record's staleness anchor at file time (never a hook).
- `hooks/staleness_read.py` — the one active mechanism: a Read advisory that flags drift; never blocks.
- `.capsa/` — aims' own design capsule (dogfood): its decisions, components, and insights as capsa records.

## How aims documents itself — use the capsule

Durable design knowledge for aims lives in the `.capsa/` capsule, not in scattered notes:

- A boundary/ownership/architecture decision → a `decisions/` ADR (append-only; supersede, never
  rewrite), placed at the component it governs or root if cross-cutting.
- A requirement / rule the plugin must honor → `requirements/`.
- The structure of a part → `components/<slug>/component.md`.
- An engineering lesson → `insights/dev/`; a note tied to specific code → `insights/code/`.

**Anchor every record on filing** with `python3 tools/aims_anchor.py` — `anchors:` for a record about
file content, `--shape` for one about structure. Never hash by hand. When you read a record and the
staleness hook flags it, re-verify against the current code before relying on it.

Read by placement: at a node, read the normative records on the walk to the capsule root plus in-scope
insights — not the whole capsule.

## Build & test

Markdown + bash + a little stdlib Python; no toolchain. Before declaring work complete, run:

```
bash tests/copies-identical.sh   # distribution surfaces stay byte-identical
bash tests/capsa-anchor.sh       # anchor stamping + staleness detection behavior
python3 -m py_compile tools/aims_anchor.py hooks/staleness_read.py
```

## Hooks — inform, never block

aims has exactly two hooks, and neither blocks:

- `SessionStart` (`session-start.sh`) — surfaces in-progress plans and the presence of the `.capsa/`
  capsule with the reading rule. Informational.
- `PostToolUse` on `Read` (`staleness_read.py`) — when a capsa record is read, re-hashes its anchor and,
  on drift, injects an advisory "re-verify" note. Advisory only, fail-open.

The plugin's distributable hook source lives under `templates/hooks/`; the locally-installed copy under
`.claude/hooks/` (dogfooding). Keep them byte-identical (guarded by `tests/copies-identical.sh`); refresh
via `/install-on .`.

## What was removed (and why)

The memory-tree subsystem (mark/consolidate/find-dirty/lint/doctor/check-refs/classify-inbox/new-node/
readme-sync) and its hooks were **cut**. capsa's placement-addressed, one-record-per-file grammar makes
relevance structural (a tree walk) rather than computed, so there is no mutable store to keep coherent —
the machinery was maintaining a problem the format does not create. The history of that subsystem lives
in `.capsa/` as superseded decisions.
