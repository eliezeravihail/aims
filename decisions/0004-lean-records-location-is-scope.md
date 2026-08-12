---
title: "Records are lean: title + date + body; kind and anchor derived from location, no code: field"
date: 2026-08-12
---

A record is `title` + `date` + a prose body; the kind comes from its location (component.md /
decisions/ / insights/ / root charter). It carries no `code:` field — the record's own directory is its
subject. The anchor is derived from location and stamped by knowledge/anchor.py: a `component.md` gets a
`shape:` of its directory; a decision/insight gets a `hash:` of the component's code; a cross-cutting
root record gets none. Design records are excluded from the hash, so editing knowledge never trips its
own anchor. Supersedes the earlier {path,hash}-list and code:+hash designs.
