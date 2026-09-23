# rq-c3 (C, requests) — final reply, summarized as handed back

Added `Session.timeout` (default `None`), applied in `Session.send`; `timeout=None` on a call falls back to the
default, `(None, None)` waits forever; survives pickling. 22 tests (`TestSessionTimeout`); docs in advanced.rst,
HISTORY.md. Asked nothing.
Usage: `s = requests.Session(); s.timeout = (3.05, 27); s.get(url)`.
