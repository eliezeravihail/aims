---
title: "staleness_hook.py"
date: 2026-08-12
hash: "sha256:e7452917d0d9bea295b2bf003d102c90e7dfe64d24aa096391a3ff53bf1e058b"
---
## Insights
- Identifying a companion needs no naming convention or path match: a record is anchored iff it carries
  a `hash:` field. Everything else (READMEs, system records) is silently ignored.
## Decisions
- Advisory only, fail-open: a missing import, unreadable source, or any error yields no block and at
  most a "possibly moved" note. The hook must never break a Read.
## Discussions
- Imports the derivation from anchor.py rather than duplicating it, so read-time and write-time can
  never diverge.
