---
title: "0003 — the frontend mirrors coords.py rather than sharing one file via a build step"
date: 2026-08-13
status: accepted
---

## Context
Both the tested Python backend and the browser runtime need the same image↔viewport transform math.
Sharing a single source file would require a JS build/transpile step. `base-dependencies.md` deliberately
forbids a frontend build step (vanilla JS, no npm framework).

## Decision
`app/coords.py` is the single **authoritative, tested** owner of the transform. `app/static/coords.js` is
a thin, faithful mirror of it for the browser — small, pure (no DOM/fetch), and matched to the Python by
the same viewport model documented in both files.

## Consequences
- No build step; the mirror is small enough to keep in sync by reading both.
- Risk accepted: the two can drift. Mitigation is their smallness and the fact that the authoritative math
  is the tested Python; if drift is ever suspected, reconcile `coords.js` to `coords.py`.
</content>
