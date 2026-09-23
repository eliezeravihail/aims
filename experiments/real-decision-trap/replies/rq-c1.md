# rq-c1 (C, requests) — final reply, summarized as handed back

Added `Session.timeout` (default `None`); applied in `Session.send()` when the call's timeout is missing or `None`;
pickled via `__attrs__`. `timeout=None` on a call still gets the session default; `(None, None)` waits forever.
14 tests (`TestSessionTimeout`); docs in advanced.rst, quickstart.rst, HISTORY.md. Asked nothing.
Usage: `s = requests.Session(); s.timeout = (3.05, 27); s.get(url)`.
