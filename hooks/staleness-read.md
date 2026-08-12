# Staleness read hook — the one active mechanism

A single hook, firing when the agent **reads a capsa record**. It recomputes the record's anchor
against the *current* source and, on mismatch, injects an **advisory** note. It is the only thing in
aims that runs automatically, and it only reads.

## What it does

1. When a read touches a file under `.capsa/`, parse the record's frontmatter.
2. Recompute its anchor:
   - `anchors:` present → re-hash each `path` and compare to the stored hash.
   - `shape:` present → re-hash the child-name set under `root` (to `depth`) and compare.
   - neither → nothing to check.
3. On any mismatch, append an advisory line to the read result, e.g.:

   > ⚠ aims: `src/tiling/cache.py` changed since this record was written — re-verify before relying
   > on it. (This flags *possible* staleness, not proven falsehood.)

## Hard constraints

- **Advisory only.** It **never blocks** the read, **never edits** the record, **never
  auto-invalidates** it. A change is possible-staleness, not proof the record is wrong.
- **Reads actual state.** Because it re-hashes the real file/tree, it catches drift regardless of
  whether the change went through aims or was made by hand or another tool.
- **Right granularity by construction.** `anchors:` reports *which file* drifted; `shape:` fires only
  on a structural change (move/rename/merge) and stays silent on content edits under a structural
  record — no false-positive storm.
- **No write side.** It does not stamp anchors (that is `aims anchor`, called explicitly at write
  time) and maintains no state of its own.
- **Fail-open.** If a source path is missing or unreadable, report it as *possibly moved/renamed —
  re-verify* rather than erroring; a broken anchor must never break a read.

## Wiring

Registered as a read-time hook (e.g. a `PreToolUse`/`PostToolUse` hook on `Read` matching
`**/.capsa/**`). It calls the same hashing as [`../tools/aims_anchor.py`](../tools/aims_anchor.py)
so write-time and read-time hashes are computed identically. Reference stub:
[`staleness_read.py`](staleness_read.py).

## Content invariants — detected here, enforced elsewhere

A content invariant ("nothing under `core/` does I/O") is a record that anchors (via `anchors:`) to
the files carrying the rule, so this hook *does* flag it when one of those files changes — "re-verify
against the rule". What this hook does **not** do is decide automatically whether the change actually
broke the rule; that verdict needs code re-analysis and is an opt-in fitness-function emitting capsa
`X-` findings — a separate tool, wired only if a specific invariant earns it. Detection is here;
automatic enforcement is the door left open.
