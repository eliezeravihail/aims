---
title: "A record X.md anchors to a same-named source file X; system records carry no anchor"
date: 2026-08-12
---

Records are lean (title + date + body; a companion's body is Insights/Decisions/Discussions). The
anchor is one derivation with no `code:` field and no stored path: a record `X.md` anchors to a sibling
file named `X` (its name with `.md` removed) when that file exists — a content `hash:` stamped by
`knowledge/anchor.py`. A record with no same-named source file (`goals.md`, `architecture.md`) is a
system record and carries no anchor. The read hook re-hashes the source and advises on drift. Supersedes
the earlier {path,hash}-list, code:+hash, and shape/component designs.
