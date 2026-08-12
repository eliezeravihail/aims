# aims

**aims makes design the goal of coding-agent work — and makes the design knowledge durable.**

It is [Balash](https://github.com/eliezeravihail/balash)'s design method carried onto a
[capsa](https://github.com/eliezeravihail/capsa) knowledge layer. The method produces genuinely
well-designed software as a product grows; the capsa layer files the design knowledge it produces —
intent, the substrate, the architecture, the decisions and lessons behind them — as durable records
that survive across sessions and years, so a later **clean session reads the prior conclusions and
builds on them instead of re-deriving from scratch**.

## The three layers

1. **The design method (the brain).** A Guide holds the product vision and hands a capable Worker one
   *design/quality objective* at a time, with the feature as a constraint; then measures the result and
   chooses the next. Discovery, a feasibility gate, ownership/encapsulation, a subtractive pass, a
   review panel. Lives in [`skills/aims-guide/`](skills/aims-guide/SKILL.md).
2. **The durable knowledge layer.** The method files ADRs, requirements, components, and insights into
   the product's `.capsa/` capsule — **one record per fact, placed in a tree where placement is
   scope**, so a later session reads only what is in force where it is working, never one file that
   bloats. Mapping: [`skills/aims-guide/references/design-record.md`](skills/aims-guide/references/design-record.md);
   format: [`docs/format-profile.md`](docs/format-profile.md); vendored spec: [`vendor/capsa/`](vendor/capsa/).
3. **One advisory signal.** Each record is *anchored* to the code it describes when filed; a read-time
   hook re-hashes the anchor and, if the code drifted, flags *"re-verify"* when a later session reads
   the record. It **never blocks**. That replaces keeping docs true by hand.

## Commands

- `/aims-plan` — choose one design objective, file the durable records it commits to, draft the Worker
  handoff; stop for review.
- `/aims-build` — delegate the objective to a Worker (or run it inline); stop before evaluation.
- `/aims-review` — measure the result against the exit criteria with the review panel (also works
  standalone on any diff/branch/PR).
- `/aims-plan-and-build` — the full autonomous loop, pausing only for open product decisions.
- `/install-on <path>` — install aims' per-project pieces (the two hooks + capsule scaffolding) into a
  target project.

## The staleness model — the anchor follows the claim

| A record claims about… | Anchor | Drift = |
|---|---|---|
| **file content** | `anchors:` — whole-file content hash per file | the file changed |
| **arrangement / structure** | `shape:` — child-name fingerprint of a subtree (content-blind) | the shape changed (moved / renamed / merged) |
| **a content invariant** ("core stays pure") | just `anchors:` on the files that embody it | a governed file changed → re-verify |

The hook re-reads the *actual* file/tree, so it catches drift whether the change went through aims or
was made by hand or another tool.

## What aims deliberately does not have

No memory tree, no consolidation/doctor/lint machinery, no write hook, no planning lock. capsa's
passivity plus the method's documentation discipline keep design rationale current by construction; the
one read-time advisory is the whole of the active machinery. Content-invariant *enforcement* (a linter)
is an opt-in fitness-function emitting capsa `X-` findings — never part of the passive layer.

## Name

aims = AI Manager System, and "aims / goals": the design *aim* is what the system manages.

## License

MIT. capsa under `vendor/capsa/` is MIT (© eliezeravihail) and is developed here now.
