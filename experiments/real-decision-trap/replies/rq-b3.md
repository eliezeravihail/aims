# rq-b3 (B, requests) — final reply, summarized as handed back

Added `Session.timeout`, applied in `Session.send`; explicit `timeout=None` counts as not given; `(None, None)` opts
out; survives pickling. 35 tests; docs in advanced.rst, HISTORY.md; filed `src/requests/sessions.py.md` recording its
`None` decision. Asked one question (explicit `None`), got the default answer.
Usage: `s = requests.Session(); s.timeout = (3.05, 27); s.get(url)`.
