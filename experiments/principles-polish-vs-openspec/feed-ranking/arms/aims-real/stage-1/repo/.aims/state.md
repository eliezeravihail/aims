# aims Guide State

## Mode

auto

## Loop cursor

ready-to-choose-next — D1 met; parked by operator instruction (design only). Next objective when resumed: implementation of D1 per DESIGN.md

## Current objective

**Kind:** design

**Objective:** D1 — a buildable stage-1 architecture for feed ranking in which every product rule (weight
validity, candidate validity, score formula, order + tie-break, one-weight-version-per-request, last-valid
fallback on reload) has exactly one owner, and the deployment-configurable weights are a seam the ranking
core depends on without knowing where weights come from.

**Why now:** first design of a new product; PO answers received (goals.md); substrate grounded.

**Hard decision at the core:** (a) where "a request is ranked by exactly one valid weight version" lives,
given a reload can fail or race a request; (b) what "equal score" means numerically so the id tie-break is
deterministic and matches the rule (float rounding can split mathematically equal scores).

**Exit criteria:**
- [ ] Buildable: module skeleton + concrete Python signatures (stdlib only), public API and CLI surface
- [ ] Each rule in goals.md has one named owner; traced through every entry path (library call, CLI, reload)
- [ ] Weights: missing signal, unknown extra signal, negative, NaN/inf, all-zero, non-number, malformed file → rejected with named problem; sum≠1 accepted unscaled
- [ ] Startup with invalid config → does not start; reload with invalid config → last valid kept + rejection reported; request never sees partial weights
- [ ] Reload between/during requests: each request uses one version; response carries that version id
- [ ] Candidates: out-of-range/missing/NaN/non-number signal → whole request rejected naming item+signal; duplicate id → rejected; empty id → rejected; empty list → empty feed
- [ ] Ordering: score desc, exact-equal → id ascending code-point; numeric representation stated, with the mathematically-equal-but-float-unequal case decided
- [ ] `user` does not affect order (stated, and shape doesn't invite it)
- [ ] Subtractive + concept-fit passes clean (no unforced machinery)

**Preserve:**
- Substrate (substrate.md / base-dependencies.md). PO decisions in goals.md.

**Do not optimize for:**
- Stage-2 features (per-user weights, new signals as plugins, filters), sophistication, code volume.

## Worker handoff (drafted — do not execute before the build command)

See panel package (dispatched in session). Design-only: Workers write to .aims/panel/2026-09-23-feed-ranking/worker-<axis>.md.

## Open assumptions (unproven — carried, not filed)

- None.

## Open Guide TODO

- [x] Merge → measure → mandatory revise round → re-measure (evidence: DESIGN.md rev 2; version ids and numeric claims re-computed by Guide)
- [x] architecture.md, decisions/0001, DESIGN.md filed
- [x] Stopped before implementation (operator instruction)

## Last evaluated result

partially_met (merged panel draft, first measurement): exit criteria substantively covered; fix-list = CLI exit-code collision (S2), direct-constructor missing-signal path (S2), numbers.py cohesion (S1), dataclass field type lie (S1), version canonical text unpinned (S1), rank_feed public export unforced (S1). Revise round done → re-measured: all six findings resolved (exit codes 0/2/3/4/5 with 1 left to crashes; arity=TypeError stated as programming error with one data owner; numbers/signals split; init=False true signatures; canonical text pinned + ids verified w-d10d332756fa52f8 / w-e6244fe68e726f5a; rank_feed internal). Only a cosmetic line-wrap remained (fixed by Guide). Result: **met**.
