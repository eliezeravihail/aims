# rq-a2 (A, requests) — final reply, summarized as handed back

Kept `Session` unchanged (`sessions.py` not modified); `HTTPAdapter(timeout=...)` holds a default used by
`HTTPAdapter.send` when the call gives none; validated at construction; pickled; class-level `timeout = None` for
subclasses. 32 tests (`tests/test_adapters.py`); docs, HISTORY.md; filed `src/requests/adapters.py.md`, dated entry in
`sessions.py.md`. Asked once — named the recorded decision, got the maintainers' answer.
Usage: `s.mount("https://", HTTPAdapter(timeout=(3.05, 27)))` (and "http://").
