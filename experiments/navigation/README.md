# Navigation test — can an agent find the needed knowledge without reading the whole project?

## The question

The companion model claims that a session finds the design knowledge it needs by **navigating the
structure** — open a file's companion, read the root records — rather than reading the whole project.
This tests that on a real task with a fresh agent.

## Design

**The product (`product/`)** — a small maze-site builder with four source files, each with a companion,
plus root `goals.md` and `architecture.md`:

- `src/render.py` + `render.py.md` — the companion carries a **non-obvious, load-bearing constraint**:
  an earlier version made `to_svg` async with an internal frame cache and it silently served the wrong
  maze under concurrency, so `to_svg` **must stay a pure synchronous function, new options as plain
  parameters, no cache/async/state**.
- `src/store.py` + `store.py.md` — a **distractor**: its companion says storage keeps a module-level
  cache that callers must clear after a write. This rule is real but **specific to storage** — applying
  it to the renderer would be exactly wrong.
- `src/generator.py`, `architecture.md`, `goals.md` — context, mostly irrelevant to the task.

**The task** (given to a fresh, no-history agent, told only *how* aims navigation works — not the
answer): *"Add a `theme` parameter to `src/render.py` so mazes can be drawn in different color themes."*
The framing ("make it themeable") is a mild temptation toward stateful/cached drawing — the trap
`render.py.md` warns against.

## What is measured

1. **Navigation** — did the agent read only the relevant files (`render.py` + its companion, and the
   root records for context), or did it read the whole project? Which files did it correctly skip?
2. **Constraint found** — did it discover `render.py.md`'s purity constraint by navigating to it?
3. **Constraint honored** — did it add `theme` as a plain parameter and keep `to_svg` pure/synchronous,
   *without* pulling in the distractor's caching rule?

Success = the agent navigated to the one relevant companion, found the constraint, honored it, and did
not need to read the whole project (in particular, did not read or apply `store.py.md`).

## Results

<!-- filled in from the agent's return; see results.md -->

See [`results.md`](results.md).

## Honest limits

n = 1, one task, a constraint the companion states explicitly. Directional. A subtler constraint, or a
task spanning several files, would be a harder test.
