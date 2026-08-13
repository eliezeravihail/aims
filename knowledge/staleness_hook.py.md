---
title: "staleness_hook.py"
date: 2026-08-12
hash: "sha256:cada8bdbb266ef6d09754a9e0023da8c164ea8a7f380e9940e724c4b608b8709"
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
