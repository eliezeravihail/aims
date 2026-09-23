# Tasks

## 1. Scaffolding

- [ ] 1.1 Create the `feed_ranking` package (stdlib only, Python 3.11+) with a `unittest` test directory, and verify `python -m unittest` runs with zero tests and no errors

## 2. Signals and weights model

- [ ] 2.1 Define the shared `SIGNALS` tuple and verify with a unit test that it is exactly `("recency", "affinity", "popularity")`
- [ ] 2.2 Implement the frozen `Weights` value and `parse_weights` (all signals present, no unknown keys, finite, ≥ 0, at least one > 0, Decimal values, no normalization; unknown top-level keys rejected), and verify tests covering each `ranking-config` "Weight validation" scenario pass

## 3. Request model

- [ ] 3.1 Implement the frozen `Candidate` and `RankRequest` and `parse_request` (non-empty user; non-empty, unique string `item_id`; each signal present, real, not bool/NaN/inf, in [0,1]; converted to Decimal via `str`), and verify tests for every `feed-ranking` "Candidate validation" and "User is carried but not scored" scenario pass, including errors that name the item and field

## 4. Ranking core

- [ ] 4.1 Implement pure `score` (weighted sum over `SIGNALS`) and `rank` (sort key `(-score, item_id)`, returning `RankedItem` values), and verify tests pass for the 0.65 example, the exact 0.08 tie, tie-by-id, score descending, empty input, and permuted input giving identical output

## 5. Configuration lifecycle

- [ ] 5.1 Implement `WeightsProvider` (load JSON from an explicit path with an env-var fallback, parse with `parse_float=Decimal`, fail fast when the path is missing, invalid or unreadable, and `snapshot()`), and verify tests using temp files for the load and "No configuration supplied" scenarios
- [ ] 5.2 Implement `reload()` (validate first, then swap the reference; keep the last good weights and raise on failure; serialize reloaders with a lock), and verify tests for "Reload applies new weights" and "Bad edit does not break ranking"

## 6. Service facade

- [ ] 6.1 Implement `FeedService.rank` (one `snapshot()` per request, then `parse_request`, then `rank`), and verify with a test using a provider stub that swaps weights mid-request that all candidates in one request use one weight set
- [ ] 6.2 Document the library API and the config file format (including the operator workflow: edit the file, then reload or re-run) in the package README, and verify the README examples match the tested behavior

## 7. CLI adapter

- [ ] 7.1 Implement the `feed-rank --config PATH [REQUEST_FILE|-]` CLI that prints ranked JSON with string scores and exits 0 on success, 2 on a request error and 3 on a config error, and verify subprocess tests for each exit code
- [ ] 7.2 Add CLI usage to the README and verify the documented command runs as written against a sample config and request

## 8. Integration check

- [ ] 8.1 End to end: run the CLI with weights 0.5/0.3/0.2, edit the file to change the weights, re-run, and verify the order changes as predicted with no code change
