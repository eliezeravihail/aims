ROLE
You are a design Worker — a senior engineer as capable as the Guide. The design is the deliverable. This is a
DESIGN-ONLY task: write no implementation code and create no source files. Type signatures, interface
sketches and a few illustrative lines are welcome where they make a boundary concrete. If evidence
invalidates the objective, report it instead of expanding scope. Do not read other files in
.aims/panel/ (other Workers' drafts) — your work must be independent.

DESIGN GOAL
A buildable stage-1 architecture for a feed-ranking service in which every product rule has exactly one
owner, and the deployment-configurable weights are a seam the ranking core depends on without knowing
where weights come from. "Buildable" means a capable engineer could start the first sprint from it:
module skeleton, concrete Python signatures for the public API, the CLI surface, the types that cross each
seam, and the error vocabulary.

The hard decisions at its core (decide them, with reasons):
(a) where "a request is ranked by exactly one valid weight version" lives, given a reload can fail, or can
    happen while requests are being served;
(b) what "equal score" means numerically so the id tie-break is deterministic and honest. Example of the
    trap: weights r=0.1, a=0.2, p=0; item x (r=0.3, a=0) and item y (r=0, a=0.15) are mathematically both
    0.03, but in binary floats 0.1*0.3 = 0.030000000000000002 and 0.2*0.15 = 0.03. Decide what the service
    does and why; state the numeric representation of signals, weights and scores.

BEHAVIOR IT MUST SATISFY (constraint — grounded product decisions; see goals.md in the repo root)
- Input per request: a `user` and a list of candidate items; each candidate has an id and three signals
  `recency`, `affinity`, `popularity`.
- score = w_r·recency + w_a·affinity + w_p·popularity. Nothing else enters the score.
- Output: candidates ordered by score, highest first; each with its computed score; plus the id/version of
  the weight config used. Empty candidate list → empty feed (not an error).
- Ties: exactly equal scores → item id ascending, plain code-point string order ("10" before "9").
- Weights are deployment config read from a config file; an operator changes them without code change.
  Valid weights: exactly the three named signals (missing or unknown extra name → invalid), each a finite
  number ≥ 0, at least one > 0; need not sum to 1; never rescaled.
- Invalid config → rejected with an error naming the problem. At startup: the service refuses to start.
  On reload: keeps serving with the last valid weights and reports the rejection. A request is never
  ranked with partial or invalid weights.
- A weight change takes effect after an explicit reload (process restart or an explicit reload call). No
  file watching. Each request is ranked entirely with one weight version, never a mix.
- Signal contract: all three signals present, each a finite number in [0, 1]. A request violating it is
  rejected whole, with an error naming the item and the signal — never clamped, zero-filled, or dropped.
- Item id: non-empty string. Duplicate id in one request → request rejected. Empty id → rejected.
- `user` is carried for identity only; it does not affect score or order in stage 1.

WHY NOW
First design of a new product; product decisions and substrate are settled.

WHAT "GOOD" AIMS AT
The standard is .claude/skills/aims-guide/references/design-principles.md (read it) — the target, not a
checklist. Where a principle doesn't apply at this scale, don't force it; say why.

SUBSTRATE (fixed; do not revisit)
Python 3.11+, standard library only (decimal, datetime, zoneinfo available, none required). Single process.
No UI, network, database, persistence. Entry point: a library with an optional small CLI, or a local
function API — your call. A new runtime dependency must be argued for.

TESTING (to include in the design, not to run)
Say how the design is verified test-first: which decisions get which tests, including the adversarial
edges (empty/one/many, duplicate, NaN/inf, negative, all-zero weights, unknown key, reload failure,
reload between requests, float-equality tie).

NON-GOALS
Per-user/segment weights, new signals as plugins, learned/non-linear ranking, decay, filters/diversity,
pagination, file watching, persistence, network serving. Do not build for a stage not revealed. The
modules, classes and interfaces are YOURS to choose.

BEFORE RETURNING
Run a subtractive pass: for every type, guard, wrapper or abstraction you introduced, name the present
product force that requires it; delete what fails. Run a concept-fit pass: is each element the kind of
thing it is?

RETURN
Write your full design to the file given below (markdown). It must contain: module skeleton; public
signatures; the types crossing each seam; error vocabulary; the owner of each rule (a table: rule → owner →
every entry path that reaches it); the two hard decisions with reasons and rejected alternatives; the test
plan; what you cut in the subtractive pass. Then reply with a 10-line summary.
