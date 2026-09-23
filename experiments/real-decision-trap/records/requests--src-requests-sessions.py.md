---
title: "sessions.py"
date: 2026-09-23
hash: "sha256:3d2089736ced93b2b405624a943f866d22652b17df06a85eb010f86272fc3e7d"
---
## Decisions
- `Session` deliberately has no `timeout` default. Proxies, stream, verify and cert fall back to session
  defaults; `timeout` does not, and that is on purpose, not an oversight.
  It is set per call only. This rules out a `Session.timeout` attribute, an entry for it in `__attrs__`, and
  merging a session value into `request()`/`send()`. Maintainers have rejected it again and again: #1130
  (2013, the creator's own "explicit decision"), #2011 (2014), PR #2094, PR #4560 (2018, closed as
  "removed … with prejudice"), and PR #5230 (closed 2022-05-11). PR #5230 also proposed a session-level
  `allow_redirects`; its closing comment gave reasons only for `timeout`.
  - Rationale as the maintainers gave it: a Session holds state about HTTP itself (cookies, headers, auth).
    Connection behaviour such as sockets and timeouts belongs to the transport adapters, so a timeout is a
    property of sending a request, not of the session. Caveat for anyone relying on that rationale:
    `HTTPAdapter` stores no default timeout either. It receives `timeout` only as a `send()` argument, so
    "adapters own timeouts" describes where the value is applied, not a setting the adapter keeps.
  - Scope: the latest statement (#5230, 2022) limits the refusal to "this major version" (2.x). A new major
    version is the only point it was left open for, and nothing was promised even then. Within 2.x, a PR that adds a session-level
    timeout contradicts a standing decision; it is not a missing feature.

## Discussions
- Not verified: per the maintainers (#4560), an earlier version of the library *did* have session-level
  timeouts, and they were dropped because users expected "various different things" from them. The
  discussion does not say which conflicting expectations those were. This checkout does not confirm the
  history either: `HISTORY.md` 1.0.0 lists "Removal of all configuration" but does not name timeout.
  Treat it as the maintainers' account, not an established fact. It is still the only failure evidence
  on record against re-adding the feature.
