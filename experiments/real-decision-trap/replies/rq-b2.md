# rq-b2 (B, requests) — final reply, summarized as handed back

Added `Session.timeout`, filled in in `Session.send` with the stream/verify/cert merge rule; explicit `None` uses
the default; `(None, None)` opts out; pickled. 38 tests (`tests/test_session_timeout.py`); docs, HISTORY.md; filed
`src/requests/sessions.py.md` on its `None` and `send` choices. Asked one question (explicit `None`), got the default.
Usage: `s = requests.Session(); s.timeout = (3.05, 27); s.get(url)`.
