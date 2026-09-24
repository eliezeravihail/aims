# Tasks

## 1. Request model

- [ ] 1.1 Add required `author` and `topic` (non-empty strings) to `Candidate` and its parsing, and verify tests for "Missing author rejected", "Topic list instead of string rejected", and that errors name the item and field
- [ ] 1.2 Add the frozen `Exclusions` value (`blocked_authors`, `muted_topics` as `frozenset[str]`, default empty) to `RankRequest` and `parse_request`, rejecting non-list values and entries that are not non-empty strings, and verify tests for "Block and mute lists omitted" and "Malformed block list rejected"
- [ ] 1.3 Confirm validation covers every candidate regardless of exclusions, and verify the "Malformed excluded candidate still rejects the request" test and a test that duplicate ids across an excluded and an eligible item are rejected

## 2. Eligibility

- [ ] 2.1 Implement pure `is_eligible` / `filter_eligible` in a new eligibility module (exact, case-sensitive author/topic membership), and verify tests for "Blocked author excluded despite top score", "Muted topic excluded", "Matching is case-sensitive" and "All candidates excluded"

## 3. Diversity

- [ ] 3.1 Change `rank` to return `Scored(candidate, score)` in score order without changing the formula or sort key, and verify all stage-1 ranking tests still pass after adapting them to the new return type
- [ ] 3.2 Implement the feasibility predicate from design D4 as a standalone function, and verify with a test comparing it to brute-force permutation search over all author multisets of up to 7 items, 3 authors and every tail state
- [ ] 3.3 Implement `arrange(ordered, author_of)` with `MAX_SAME_AUTHOR_RUN = 2`: minimal lowest-ranked surplus trim (D5), then greedy placement with lookahead (D4). Verify tests for every scenario in "No more than two consecutive items from the same author" and "Unplaceable same-author surplus is omitted", plus a property test over random sequences that the output never has 3 in a row, is a subsequence-preserving permutation of the kept items, drops only the minimal surplus, and equals plain skip-the-third greedy whenever that greedy places everything

## 4. Service and CLI

- [ ] 4.1 Compose `FeedService.rank` as parse, filter, rank, arrange, then project to `RankedItem` (one weights snapshot per request, as before), and verify tests for "Excluded item does not separate a run", "Diversity does not reorder when not needed", "All candidates returned once" and "Input order still does not affect output" with same-author candidates
- [ ] 4.2 Extend the CLI input handling to the new fields (output and exit codes unchanged), and verify subprocess tests: a blocked item is absent, a same-author triple is deferred, and a missing `author` exits 2
- [ ] 4.3 Update the README request format (new fields, exact matching, the run limit, the surplus-omission rule), and verify its example request runs through the CLI and produces the documented output

## 5. Integration check

- [ ] 5.1 End to end with weights 0.5/0.3/0.2: run the CLI on a request mixing blocked, muted and same-author items, and verify the output matches a hand-computed expectation; then edit the weights file, re-run, and verify the order changes as predicted and diversity and eligibility still hold
