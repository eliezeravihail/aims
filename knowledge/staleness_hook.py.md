---
title: "staleness_hook.py"
date: 2026-08-12
hash: "sha256:483d042616a77245de230a32b68c1d9f791aade9db3e6e21b1546c241c39337a"
---
## Insights
- Identifying a companion needs no naming convention or path match: a record is anchored iff it carries
  a `hash:` field. Everything else (READMEs, system records) is silently ignored.
## Decisions
- Advisory only, fail-open: a missing import, unreadable source, or any error yields no block and at
  most a "possibly moved" note. The hook must never break a Read.
- The hook holds **no** frontmatter parse or hash regex of its own: it imports `read_hash` from anchor.py,
  which owns the anchor-line format for read and write alike (2026-09-17).
## Discussions
- Imports the derivation from anchor.py rather than duplicating it, so read-time and write-time can
  never diverge.
