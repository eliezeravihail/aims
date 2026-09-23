# rq-a1 (A, requests) — final reply, summarized as handed back

Kept `Session` unchanged; `HTTPAdapter(timeout=...)` holds a default applied in `HTTPAdapter.send` when the call's
timeout is `None`; validated at construction; pickled. 30 tests (`tests/test_adapters.py`); docs, HISTORY.md, the
adapter docstring; filed `src/requests/adapters.py.md`, updated `sessions.py.md` ("reaffirmed"). Asked once — named the
recorded decision, got the maintainers' answer.
Usage: `s.mount("https://", HTTPAdapter(timeout=(3.05, 27)))` (and "http://").
