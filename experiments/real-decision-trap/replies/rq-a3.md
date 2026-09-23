# rq-a3 (A, requests) — final reply, summarized as handed back

Kept `Session` unchanged; `HTTPAdapter(timeout=...)` validated and stored; a private method picks the call's timeout
or the default; pickled. 29 tests (`tests/test_adapters.py`); docs, HISTORY.md; filed `src/requests/adapters.py.md`,
appended to `sessions.py.md` (decision kept, not superseded). Asked once — named the recorded decision, got the
maintainers' answer.
Usage: `s.mount("https://", HTTPAdapter(timeout=(3.05, 27)))` (and "http://").
