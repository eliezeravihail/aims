# rq-c2 (C, requests) — final reply, summarized as handed back

Added `Session.timeout` (default `None`), filled in inside `Session.send()` when the call's timeout is missing or
`None`; kept on pickling. `(None, None)` opts one call out. 21 tests (`TestSessionTimeout`); docs in advanced.rst,
quickstart.rst, HISTORY.md. Asked nothing.
Usage: `s = requests.Session(); s.timeout = (3.05, 27); s.get(url)`.
