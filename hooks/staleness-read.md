# Staleness read hook — the one active mechanism

A PostToolUse hook on `Read`. When the read touches a capsa record carrying an anchor (`hash:` or
`shape:`) over the code it declares in `code:`, it recomputes that anchor against the **current** source
and, on drift, injects an advisory note as `additionalContext`:

> ⚠ [aims] The record `<path>` may be stale: the code under `<code>` changed since it was written.
> Re-verify before relying on it.

## Hard constraints

- **Advisory only.** Never blocks the read, never edits the record, never auto-invalidates it — a change
  is *possible* staleness, not proven falsehood.
- **Reads actual state.** It re-hashes the real file/tree, so it catches drift whether the change went
  through aims or was made by hand or another tool.
- **Right granularity.** `hash:` reports the concerned code changed; `shape:` fires only on a structural
  change (move/rename/merge) and stays silent on ordinary edits inside the subtree.
- **Fail-open.** Missing/unreadable source, an unimportable tool, or any internal error yields no block
  and (where it matters) a "possibly moved — re-verify" note, never an exception.

## Wiring

Registered as `PostToolUse` on `Read` (matching `.capsa/` records). It reuses the hashing in
[`../tools/aims_anchor.py`](../tools/aims_anchor.py), found in either layout (dogfood `hooks/` +
`../tools/`, or installed together under `.aims/`, or `$AIMS_HOME`), so read-time and write-time hashes
always agree. Reference implementation: [`staleness_read.py`](staleness_read.py).

## Out of scope — enforcement

Deciding *automatically* whether a change broke a content invariant needs code analysis; that is an
opt-in fitness-function emitting capsa `X-` findings, never part of this passive layer.
