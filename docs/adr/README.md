# Architecture Decision Records

This directory holds the project's architecture decisions. Each file captures
one decision: its context, the choice made, and the consequences accepted.

## How we use ADRs

- **One decision per file.** Numbered monotonically: `NNNN-slug.md`.
- **Append-only log.** Past records are not edited. If a decision changes,
  a new ADR supersedes the old one.
- **Lifecycle:** `proposed → accepted → (later) superseded | deprecated`.
- **Pithy.** One to two pages max. Link out for longer design notes.
- **Inverted pyramid.** Decision and consequences first; alternatives later.

## How to write one

```
/adr <title>
```

This drafts a record from `_template.md`, picks the next number, and adds
it to the index below.

## Index

| #    | Title                                          | Status   | Date       |
|------|------------------------------------------------|----------|-----------|
| 0001 | Record architecture decisions                  | accepted | 2026-05-06 |
| 0002 | Single-dispatch over multi-agent orchestration | accepted | 2026-05-06 |
| 0003 | Hooks default to nudge, lock always blocks     | accepted | 2026-05-06 |
| 0004 | Router via hook-injected context, not orchestration | accepted | 2026-05-06 |
| 0005 | Two install paths; only /init-workflow ever goes global | accepted | 2026-05-06 |
