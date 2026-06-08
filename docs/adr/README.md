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

ADRs are proposed automatically during plan close-out — the implementation
session decides per a confidence rule (see `/plan` Phase 4 in
`.claude/commands/plan.md`). For ad-hoc decisions outside a plan, copy
`_template.md` to `NNNN-<slug>.md` (next number, status `proposed`) and
add a row to the index below.

## Index

| #    | Title                                          | Status   | Date       |
|------|------------------------------------------------|----------|-----------|
| 0001 | Record architecture decisions                  | accepted | 2026-05-06 |
| 0002 | Single-dispatch over multi-agent orchestration | accepted | 2026-05-06 |
| 0003 | Hooks default to nudge, lock always blocks     | superseded by 0020 | 2026-05-06 |
| 0004 | Router via hook-injected context, not orchestration | superseded by 0015 | 2026-05-06 |
| 0005 | Two install paths; only /init-workflow ever goes global | accepted | 2026-05-06 |
| 0006 | Two-tier project memory — core context plus embedding-based recall | superseded by 0007 | 2026-05-25 |
| 0007 | Tree-based project memory with automatic build and maintenance | accepted (partial 0009) | 2026-05-25 |
| 0008 | Node as primary context interface                 | accepted | 2026-05-27 |
| 0009 | Memory consolidation runs in-band via hook-injected instructions | accepted | 2026-05-27 |
| 0010 | Two-command surface; idempotent install; auto plan close-out | proposed (partial 0011) | 2026-05-27 |
| 0011 | Re-install refreshes aims scaffolding and prunes stale system files | proposed | 2026-05-28 |
| 0012 | Module nodes must carry code globs; install gates tree work on freshness | proposed | 2026-05-28 |
| 0013 | Plan template — configurable summary language and explicit Open design questions | proposed | 2026-05-31 |
| 0014 | `code:` entries are matched as fnmatch globs                | proposed | 2026-05-31 |
| 0015 | `/plan` auto-engages on edit intents and writes a draft to disk before approval | proposed | 2026-05-31 |
| 0016 | Per-prompt memory node auto-injection                       | proposed | 2026-05-31 |
| 0017 | `pre-write` carves out plan drafts during the planning lock | superseded by 0020 | 2026-05-31 |
| 0018 | Multi-session-safe consolidation via in-frontmatter claims  | superseded by 0019 | 2026-06-01 |
| 0019 | Sidecar `.lock` files for memory nodes (supersedes 0018)    | proposed (repurposed by 0020) | 2026-06-01 |
| 0020 | Hooks inform, they never block (no planning lock; factual injection; advisory node marker) | proposed | 2026-06-02 |
| 0021 | Per-node requirements are user-sourced and surfaced at edit time | proposed | 2026-06-08 |
