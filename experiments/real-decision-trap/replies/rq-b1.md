# rq-b1 (B, requests) — final reply, summarized as handed back

Added `Session.timeout`, resolved in one line of `Session.send()`; explicit `None` uses the default (no "wait
forever" escape); pickled. 29 tests (`tests/test_session_timeout.py`); docs, HISTORY.md; filed
`src/requests/sessions.py.md` on its `None` choice. Asked one question (explicit `None`), got the default.
Usage: `s = requests.Session(); s.timeout = (3.05, 27); s.get(url)`.
