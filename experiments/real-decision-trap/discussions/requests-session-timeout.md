# GitHub discussion about `requests.Session` and timeouts

Collected from psf/requests. Quotes from #1130 and #2011 were read raw through the GitHub API; those from #4560 and
#5230 as rendered by a page-fetch tool on 2026-09-23 — wording may differ in small ways from the original.

## Issue #1130 (2013) — kennethreitz (creator of requests)

"Timeout is a parameter of the act of sending a request now. Basically, session-level timeouts down't make sense when
we have connection adapters."

"this was an explicit decision I made recently."

## Issue #2011 (2014) — "Feature Request: Add timeout to session"

ctheiss (reporter): the optional parameters of `send()` are settable on the Session object (like `verify` and
`stream`), but `timeout` is an exception; please merge it from the session like the other arguments.

Lukasa (maintainer): "I don't think we'll be adding `timeout` to the `Session`."

Lukasa: "`Session` objects strictly should manage things about the session that about how HTTP itself works:
cookies, headers etc. The transport adapters manage things that are about how network connections work: sockets,
timeouts etc."

## PR #2094 — a session timeout; rejected by Lukasa.

## PR #4560 (2018) — "Session timeout / Added the ability to set a default session timeout"

sigmavirus24 (maintainer), closing it: "In the past this library supported session-level timeouts but this proved to
be unintuitive to most users as they expected various different things. We intentionally removed the feature, with
prejudice. Adding it back at this time is unlikely."

## PR #5230 (closed 2022-05-11) — "#3070 Defaults on session level" (session-level `timeout=None`, `allow_redirects`)

nateprewitt (maintainer): "I don't believe we'll be able to accept this. `timeout` was intentionally omitted from the
Session class in Requests 2.x and we don't intend to add it within this major version."
