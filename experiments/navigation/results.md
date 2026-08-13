# Results — navigation test

A fresh, no-history agent, told only *how* aims navigation works (not the answer), was asked to add a
`theme` parameter to `src/render.py`. Verified against the actual code, not the self-report.

## What the agent did

| Measure | Result |
|---|---|
| **Files opened** | exactly two: `src/render.py` and `src/render.py.md` |
| **Read the whole project?** | **No.** It skipped `store.py`/`store.py.md` (the distractor), `generator.py`/its companion, and even `goals.md`/`architecture.md` — judging them irrelevant to a file-local change |
| **Constraint found?** | **Yes** — navigated straight to `render.py.md` and read its Insights + Decisions: `to_svg` must stay a pure, synchronous function, no async, no I/O, no cache; new options as plain parameters |
| **Constraint honored?** | **Yes** — added `theme="light"` as a plain parameter reading a **read-only module constant** `THEMES`; `to_svg` stayed pure and synchronous. No async, no per-call cache, no mutable state |
| **Distractor avoided?** | **Yes** — never opened `store.py.md`, so its storage-specific caching rule could not leak into the renderer |
| mtime check | only `render.py` was modified; every other file untouched |

## Reading

The agent found the exact, non-obvious constraint it needed and honored it, by **navigating to the one
relevant companion** — two files read, not eight. It did not read the whole project, and it correctly
ignored a real-but-irrelevant rule sitting in a sibling file's companion. This is the property the
companion model is for: the directory structure is the index, so relevant design knowledge is reached
by walking to the file (or the root record), not by loading everything.

The load-bearing detail: the constraint that saved the change from the "make it themeable → add a
cache" trap was **not in the code** — `render.py` is a one-line stub. It lived only in the companion,
and the agent got it because the companion sits right beside the file and is named for it.

## Honest limits

n = 1, one task, a constraint the companion states explicitly (the agent still had to *find and apply*
it, which is the point). A subtler constraint, or a task genuinely spanning several files (where the
right move is a root `architecture.md` record, not many companions), would be a harder test. One
verification wrinkle recorded for honesty: an automated grep for "cache" first flagged the result, but
it had matched the word "cached" in the new docstring, not any caching code — the implementation is
clean.
