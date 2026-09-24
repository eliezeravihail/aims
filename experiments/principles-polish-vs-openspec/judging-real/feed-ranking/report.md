# Feed ranking — blind design judgment (X vs Y)

Instrument: `rubric/assessment-form.md` rows, sub-check-derived, using the severity, ceiling and weight table in `rubric/measurement.md`. That file names itself the canonical instrument, so the **reported grade is the uncapped weighted list plus the S4 gate**. The form's older graded caps are shown next to it for reference.

**How the rubric pieces fit together.**
- The form numbers its rows 1–17. `design-principles.md` numbers its chapters §0–§14. I scored the form's 17 rows and used the principle text behind each one:
  - row 13 = principles §1;
  - row 9 = the §5 one-owner rule;
  - row 7 = §0/§5 seams and errors;
  - row 14 = §4/§11;
  - rows 15–17 = §12–§14.
- Severity follows `measurement.md`. A failed precondition item (row 13; the §5 one-owner rule in row 9) is S4. A quality item is S1–S3, depending on how pervasive the failure is.
- Row score = min(round(10 × passed/applicable), ceiling). Weight: ×1 for none or S1, ×2 for S2, ×4 for S3, ×8 for S4.
- **N/A for all four documents, so every arm has the same applicable set:**
  - row 15, testability: code-leaning, and N/A on a pure design document;
  - row 16, performance: the oracle says no performance requirement is stated;
  - row 17, security: single process, no trust boundary.

## Step 0 (pinned from `product/`, not from either design)

- **R (rules):**
  - R1: score is a weighted sum of recency, affinity and popularity.
  - R2: order by score, highest first.
  - R3: ties break by a stable item id.
  - R4: weights are per-deployment configuration, changed by an operator with no code change.
  - R5: every signal is in 0..1.
  - Stage 2 adds R6: an item from a blocked author or on a muted topic is absent from the output.
  - Stage 2 adds R7: never more than 2 same-author items in a row. The rule is hard (oracle). A would-be third item is deferred, and score order is otherwise kept as much as possible.
  - R1–R4 stay unchanged in stage 2.
- **X (change axes):**
  - X1: the weight values.
  - X2: the kind of operation that decides an item's place in the feed. This is the plausible unstated variant, and stage 2 realizes it.
- **C (cases):**
  - Stage 1: empty list; one candidate; many candidates; equal scores ordered by id; an operator retune changes the order; input order does not affect output.
  - Stage 2: all candidates blocked or muted gives an empty feed; a muted item does not count toward a run; the third same-author item is deferred; a single author dominates the eligible set.
  - Implied interaction X1 × R3: under the configured weights, two scores that are mathematically equal must tie.

Checked by execution:
- With the product's own example weights (0.5/0.3/0.2), float arithmetic gives `0.08000000000000002` vs `0.08`, so `==` is False.
- `nan < 0` is False, so a NaN weight passes a guard of the form "reject if any weight < 0".
- X's stage-2 greedy algorithm applied to score order `a1,b1,a2,a3,a4` yields `a1,b1,a2,a3,a4`. That is three A items in a row, although `a1,a2,b1,a3,a4` is valid.

---

## 1. D1: first-round design (stage 1)

### X-stage-1

| § | principle | applies | score | sev | sub-checks → finding + citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | 2/2: the service calls only its immediate collaborators, `self._scorer.score(c.signals, w)` and `self._ordering.order(scored)`. No chains. |
| 2 | Interface, calibration, concept-fit | Y | 10 | — | 4/4:<br>• Seams carry domain types (`RankRequest`, `ScoredCandidate`).<br>• The config source sits behind `WeightsProvider(Protocol)`.<br>• Weights are modelled as independent coefficients: "not normalized (ADR 0002)".<br>• The ordered output is a domain type, `list[Candidate]`. |
| 3 | Interface Segregation | Y | 10 | — | 1/1: the port has one method, `current() -> SignalWeights`. |
| 4 | Primitive obsession | Y | 10 | — | 4/4:<br>• The range rule has a type: `UnitInterval` "raises ValueError if not 0.0 <= value <= 1.0".<br>• `ItemId` and `SignalVector` are typed.<br>• `SignalWeights` is typed.<br>• A named type, `ScoredCandidate`, crosses the seam. |
| 5 | Anemic domain model | Y | 10 | — | 2/2: value objects enforce their own invariants (`SignalWeights` "raises if any < 0 or all == 0"). Each rule has a named owner. |
| 6 | Cohesion/coupling/OCP | Y | 10 | — | 4/4:<br>• A formula change stays inside `FeedScorer`.<br>• The domain does not depend on the config source.<br>• There are no cycles.<br>• Each part is cohesive. |
| 7 | Leaky abstractions / errors | Y | 5 | S2 | 1/2. Passes: seams speak domain types. **Fails:** no error vocabulary is defined at any public seam. The only failures named are raw `ValueError`s from constructors. There is no request-error vs config-error distinction, and nothing says what `WeightsProvider.current()` does on a missing or invalid config (seam: config → domain, R4). |
| 8 | SRP / God object | Y | 10 | — | 1/1: `FeedRankingService` does "orchestration only … No rule of its own". |
| 9 | One owner per rule | Y | 10 | — | 6/6: R1 → `FeedScorer`. R2+R3 → `OrderingPolicy`. R4 validity → `SignalWeights`. R4 sourcing → `WeightsProvider`. R5 → `UnitInterval`. Id uniqueness → `TransportAdapter`, the intended single path in ("Validation … happens here"). |
| 10 | DRY | Y | 10 | — | 1/1: one range check "shared by all three signals". |
| 11 | Naming and failure | Y | 10 | — | 2/2: names reveal intent. Failure messages are unspecified, but that is the row-7 defect, referenced here and not deducted again. |
| 12 | YAGNI / subtractive | Y | 7 | S1 | 2/3. **Fails:** `Score` owns no rule, so deleting it (a float inside `ScoredCandidate`) damages no ownership. The design itself calls it "thin". Passes: no speculative framework; no unrequested feature. |
| 13 | Functional correctness | Y | **2** | **S4** | 4/6. Passes: listed cases; contracts INV1–5; fail fast at the boundary; defensive at the edge.<br>**Fail (X1×R3 trace):** scores are `float` (`Score: value: float`). With the product's own weights 0.5/0.3/0.2, the equal sums (0,0,0.4) and (0,0.2,0.1) do not tie, so the float noise, not the id, decides the order and R3 is violated.<br>**Fail (edges):** the weight guard "raises if any < 0 or all == 0" accepts NaN and ±inf. A NaN weight makes every score NaN and the sort order undefined (R2). |
| 14 | State / immutability | Y | 10 | — | 1/1: frozen dataclasses. `current()` is read once per request (`w = self._weights.current()`), so one request uses one weight set. |
| 15–17 | Testability / perf / security | N/A | — | — | See the N/A note at the top. |

**Profile X-1:** weighted average **6.50**; worst 2; (#S3,#S4) = (0,1); gate **BLOCKED**. Form-cap view: 5.0.

### Y-stage-1

| § | principle | applies | score | sev | sub-checks → finding + citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | 2/2: "`FeedService.rank` calls `weights.snapshot()` once, then `parse_request(raw)`, then `rank(snapshot, …)`". No chains. |
| 2 | Interface, calibration, concept-fit | Y | 8 | S1 | 3/4. Passes: domain types cross seams; output is a named `RankedItem`; concept fit ("Weights are used as given, not normalized").<br>**Fails:** the service depends on the concrete, file-bound class `WeightsProvider.__init__(self, path: Path)` rather than on a port. S1 because a duck-typed stub already substitutes for it. |
| 3 | Interface Segregation | Y | 10 | — | 1/1: FeedService calls only `snapshot()`. The unused `reload()` on the concrete class is part of the row-2 defect, not deducted again. |
| 4 | Primitive obsession | Y | 7 | S2 | 3/4. Passes: `Weights` is typed; seams carry the named `RankedItem`; `item_id: str` is acceptable because its spec'd order is str code-point order.<br>**Fails:** signals are a string-keyed map, `signals: Mapping[str, Decimal]`, so the R5 range rule and the "all three present" rule are carried by no type. |
| 5 | Anemic domain model | Y | 5 | S2 | 1/2. Passes: each rule has a named owner.<br>**Fails:** `Weights: values: Mapping[str, Decimal]` and `Candidate` are frozen data bags. Their invariants live only in the separate `parse_weights` and `parse_request` functions, so a directly built `Weights` can hold a negative value. |
| 6 | Cohesion/coupling/OCP | Y | 10 | — | 4/4: the core "does no I/O"; the "file loader never scores anything"; `SIGNALS` is the single point for adding a signal; no cycles. |
| 7 | Leaky abstractions / errors | Y | 10 | — | 2/2: domain types at seams. Separate error types, `ValidationError` and `ConfigError`, each "names the offending item and field or key". CLI exits 2 for a request error and 3 for a config error. |
| 8 | SRP / God object | Y | 10 | — | 1/1: component table with owns and does-not-know-about columns. `FeedService` does "per-request orchestration" only. |
| 9 | One owner per rule | Y | 10 | — | 7/7: the formula is in `score`; the order key `(-score, item_id)` is in `rank`; weight validity is in `parse_weights`; candidate validity and uniqueness are in `parse_request`; the config lifecycle is in `WeightsProvider`; the one-snapshot rule is in `FeedService`. The funnel `FeedService.rank(raw_request)` always parses, which is a small one-line funnel that carries weight. |
| 10 | DRY | Y | 10 | — | 1/1: "One definition of the signal set", `SIGNALS`, shared by both models. |
| 11 | Naming and failure | Y | 10 | — | 2/2: names are clear, and errors name the item and field. |
| 12 | YAGNI / subtractive | Y | 7 | S1 | 2/3. **Fails:** "An environment variable such as `FEED_RANKING_CONFIG` can supply the path as a fallback" is an unrequested second path to the config. Passes: every type owns a rule; the CLI is a permitted entry point. |
| 13 | Functional correctness | Y | 10 | — | 6/6:<br>• Exact `Decimal` ties; the float failure is traced explicitly in D2.<br>• Rejects "booleans, NaN and infinities" in signals.<br>• Requires weights to be "finite, ≥ 0, at least one > 0".<br>• Rejects duplicate ids.<br>• Empty list returns an empty feed.<br>• An input-order-independent key. |
| 14 | State / immutability | Y | 10 | — | 1/1: `Weights` is frozen. Reload is "validate first, then swap the reference", and there is one snapshot per request. |
| 15–17 | Testability / perf / security | N/A | — | — | See the N/A note at the top. |

**Profile Y-1:** weighted average **8.69**; worst 5; (#S3,#S4) = (0,0); gate **CLEAR**. Form-cap view: 8.5.

**D1 winner: no clear advantage, and Y ahead only on the correctness gate.**
- As scored, Y leads 8.69 to 6.50, and Y is CLEAR while X is BLOCKED.
- That whole margin comes from X's row 13. Both of its failures can be fixed locally: make `Score` and the signals exact (Decimal), and add a finiteness guard to `SignalWeights`.
- If I remove that row, X scores 9.13 and Y 8.69, and both cap to 8.5 in the form view.
- **Structure:** X has stronger domain typing (rows 4 and 5). Y specifies the config and error seam fully (row 7). These roughly cancel.
- Because a removable local blemish must not flip the verdict, I don't call a structural winner. **Y is the only stage-1 design that is correct as written.**

---

## 2. D2: change absorption

### Component and seam classification

**X (stage 1 → stage 2)**

| element | verdict | evidence |
|---|---|---|
| `UnitInterval`, `SignalVector`, `ItemId`, `Score`, `ScoredCandidate` | survived | "Unchanged stage-1 components: …" |
| `SignalWeights`, `WeightsProvider` (config seam) | survived | unchanged |
| `FeedScorer` (R1) | survived | "the scorer still reads only `signals`" |
| `OrderingPolicy` (R2+R3) | survived | "`ordered = self._ordering.order(scored)  # unchanged`" |
| `Candidate` | extended | "gains `author: Author` + `topics: frozenset[Topic]`, additively" |
| `RankRequest` | extended | gains `blocked_authors`, `muted_topics` |
| `TransportAdapter` | extended | "now parses author/topics … still owns boundary validation" |
| `FeedRankingService` | extended | "gained two pipeline stages (first + last); still owns no rule" |
| seam scorer → orderer | survived | — |
| seam transport → domain | extended | new fields on the same types |
| **INV5 (output is a permutation of the input)** | **reopened** | "INV5' (supersedes INV5): output is a permutation of the **eligible** subset". X records this reopening. |
| **INV3 / R2 (the returned order is score desc, id asc)** | **reopened, unacknowledged** | Stage 1: "INV3: the returned order is the unique total order (score desc, id asc)". Stage 2 returns `self._diversity.arrange(ordered)`, yet claims "INV1–INV4 (stage 1) hold **unchanged**". The service's output contract changed, and X's survival table omits it. |

**X reopened + discarded = 2** (INV5, INV3). Both are forced by the product. Discarded: 0.

**Y (stage 1 → stage 2)**

| element | verdict | evidence |
|---|---|---|
| `SIGNALS` | survived | — |
| `Weights`, `parse_weights`, `WeightsProvider`, `ranking-config` capability | survived | "`ranking-config` is not affected" |
| `score(w, c)` and the order key `(-score, item_id)` | survived | "without changing the formula or sort key" |
| `Candidate`, `RankRequest`, `parse_request` | extended | "+author, +topic", "+exclusions: Exclusions" |
| `FeedService` | extended | "Composition order: parse, then filter, then rank, then arrange, then project" |
| CLI | extended | "input JSON gains … output format is unchanged" |
| `RankedItem` | survived, as the final projection | — |
| **`rank()` core output boundary** | **reopened** | Stage 1: "`rank(weights, candidates) -> list[RankedItem]`". Stage 2: "**The only change is that it returns `Scored(candidate, score)` so later stages can still see `author`**". Task 3.1 has to adapt the stage-1 tests. |
| **Requirement: rank request contract (completeness)** | **reopened** | "**BREAKING (completeness):** … Stage 1 promised 'every candidate exactly once'. Stage 2 promises 'each eligible candidate at most once'". |
| **Requirement: order by score descending** | **reopened** | "MODIFIED … highest first, subject only to the same-author run limit". |

**Y reopened + discarded = 3.** Two are the same forced contract changes X has. The third, the core's output type, is not forced: stage 1's core returned a projection (`item_id, score`) that dropped the item, so a later stage could not see `author`. Discarded: 0.

**D2 winner on survival: X, narrowly.**
- The count is 2 vs 3.
- The deciding item is X's stage-1 order stage, `OrderingPolicy.order(...) -> list[Candidate]`. It already emitted the full domain item, so diversity slotted in with no boundary change.
- Y's core boundary had to change.
- By `measurement.md` this is weak corroboration, not a lead signal.

### Stage-2 forms

**X-stage-2.** Rows 1, 3, 4, 5, 6, 8, 9, 10, 11 and 14 are unchanged at 10:
- row 4 gains `Author` and `Topic` value objects;
- row 9: R6 is owned by `EligibilityPolicy` and R7 by `DiversityPolicy`;
- row 5: diversity has "distinct owners, distinct signatures (`filter -> subset`, `arrange -> permutation`)".

The changed or carried rows:

| § | score | sev | sub-checks → finding + citation |
|---|---|---|---|
| 2 | 10 | — | 4/4:<br>• Eligibility is a filter that "runs first, before scoring".<br>• Diversity is a sequencing stage, not a score term.<br>• Types at seams.<br>• The port is kept. |
| 7 | 5 | S2 | 1/2. Carried from stage 1: no error vocabulary, and the new-field failures are unspecified ("now parses/validates the new fields"). |
| 12 | 7 | S1 | 2/3. `Score` is carried. Passes: X cut the wrappers ("`BlockList`/`MuteList` wrapper types **cut**"). |
| 13 | **2** | **S4** | 3/7. Passes: the eligibility cases ("keep c iff c.author not in blocked_authors and c.topics.isdisjoint(muted_topics)"); all blocked gives an empty feed; muted items are excluded from runs ("diversity operates only on the eligible subset").<br>**Fail (R7 hard limit):** "If none admissible … emit the rest in rank order. Never drops." With score order `a1,b1,a2,a3,a4` this greedy emits `a2,a3,a4` in a row even though `a1,a2,b1,a3,a4` is valid. So X's own "INV7: no author runs 3-in-a-row whenever satisfiable" is false, and when the input is unsatisfiable the hard rule is broken on purpose.<br>**Fail (contract):** the placement rule is stated two incompatible ways. "whose author != the last two emitted authors" would bar `a2` after `a1,b1`, while "blocked by a 2-in-a-row" would not.<br>**Fail (X1×R3):** float ties, carried from stage 1.<br>**Fail (edges):** NaN/inf weights, carried from stage 1. |

**Profile X-2:** weighted average **6.50**; worst 2; (#S3,#S4) = (0,1); gate **BLOCKED**. Form-cap view: 5.0. Even without the stage-1 carry-overs, the R7 failure keeps row 13 at S4. It sits in the core algorithm of a new rule, so it is not a removable blemish.

**Y-stage-2.** Rows 1, 3, 6, 7, 8, 9, 10, 11 and 14 are unchanged at 10:
- row 9: R6 is owned by `is_eligible` and R7 by `arrange` with `MAX_SAME_AUTHOR_RUN = 2`;
- row 10: the feasibility check is one predicate, reused for the trim;
- row 7: new-field errors "name the field and the offending position".

The changed or carried rows:

| § | score | sev | sub-checks → finding + citation |
|---|---|---|---|
| 2 | 8 | S1 | 3/4. Passes: filter before scoring ("a score of −∞ or 0 … Rejected"); diversity is "a post-order rearrangement over an opaque key", generic `arrange(ordered: Sequence[T], author_of)`. **Fails:** the concrete `WeightsProvider` from stage 1 is carried. |
| 4 | 7 | S2 | 3/4. Carried: `signals: Mapping[str, Decimal]`. `author: str` and `topic: str` pass under the same standard as `item_id` (exact equality is their only rule, "Matching is exact string equality"). |
| 5 | 5 | S2 | 1/2. Carried: `Candidate`, `Weights` and the new `Exclusions` are bags whose validity lives in `parse_request`. |
| 12 | 7 | S1 | 2/3. The env-var fallback is carried. The lookahead is not over-build, because the hard rule forces it. |
| 13 | 10 | — | 7/7:<br>• Hard limit with a feasibility lookahead: "`count_R(X) <= 2 * (\|R\| - count_R(X)) + 2 - (r if X == L else 0)`". I checked it by hand: `a1,b1,a2,a3,a4 → a1,a2,b1,a3,a4`, and `a1..a5,b1` keeps 2(k+1) = 4 items.<br>• Identical to plain greedy whenever plain greedy succeeds.<br>• When unsatisfiable, omits the minimal lowest-ranked surplus.<br>• Excluded items "neither separate nor extend a run".<br>• Excluded candidates are still validated.<br>• Duplicate ids are checked across all candidates.<br>• Decimal ties carried. |

**Profile Y-2:** weighted average **8.69**; worst 5; (#S3,#S4) = (0,0); gate **CLEAR**. Form-cap view: 8.5.

**D2 winner on the stage-2 form: Y, clearly.**
- 8.69 CLEAR vs 6.50 BLOCKED.
- X's gap is not a local blemish: its diversity stage does not guarantee the product's hard rule, even on satisfiable input.
- Y's remaining deductions are typing and anemia, the same as in stage 1.

---

## 3. Correctness traps (`spec-and-oracle.md`)

| trap | X | Y |
|---|---|---|
| 1. Blocked item modelled as a weight | **Avoided.** "drop any candidate whose author is blocked … runs first, before scoring (INV6)". | **Avoided.** "(a) a score of −∞ or 0 for excluded items. Rejected: they would still be present". |
| 2. Diversity modelled as a score penalty | **Penalty avoided**, since diversity is a sequencing step: "`DiversityPolicy.arrange(ordered)` … reorder only". But the sequencing step still **does not guarantee** the rule: "If none admissible … emit the rest in rank order". It lets 3 in a row through on the satisfiable input `a1,b1,a2,a3,a4`. So X avoids the penalty but misses what the trap protects. | **Avoided.** "fold diversity into the sort key. Rejected: a run limit depends on neighbors". The limit is guaranteed: "The same-author run limit is hard and SHALL never be broken". |
| 3. Pipeline ownership (filter → score/sort → diversify, one owner each) | **Avoided, already in stage 1.** "eligibility filter → score → order by score → diversify". The stage-1 scorer→orderer seam over `ScoredCandidate`/`Candidate` meant no reopen. | **Reached in stage 2** ("1. eligibility … 2. ranking core (unchanged) … 3. diversity"), with scoring rules untouched. Getting there needed a **boundary change**: "it returns `Scored(candidate, score)` so later stages can still see `author`". This is not the oracle's "scoring component changed to carry filtering or ordering rules", but it is a reopen of the core's output type. |

---

## 4. Residual tells and controls

- **Method guess and rubric vocabulary.** I guessed X = aims and Y = OpenSpec, and this rubric is aims' own instrument. X recites its vocabulary: "§5", "subtractive pass", "concept-fit pass", "F1–F5". The risk was capture in X's favour. Controls:
  - I credited no self-description.
  - I checked X's claims instead of accepting them. Two were false: "INV1–INV4 (stage 1) hold unchanged" and "INV7 … whenever satisfiable". Its "reopened on purpose … isolated to one ADR" undercounts, because INV3 was reopened too.
  - X's review-round sections and cost section earned nothing.
- **Length and style.** Y is about 2.3× longer and specifies more, which could both earn credit and draw nitpicks. Controls:
  - The same sub-check list was applied to all four documents.
  - X lost points only where it specifies nothing (the error and config-failure seam). I did not deduct for brevity.
  - Y lost points for typed-model gaps that are visible in its own signatures (`Mapping[str, Decimal]`, parse-only validity).
  - I did not treat Y's spec scenarios as evidence of structure. Every Y credit above is also stated in `design.md`: Decimal (D2), validation lists (component table), feasibility (D4/D5).
  - One exception: I used `tasks.md` 6.1 (the stub provider) to set Y's row-2 severity at S1. At S2, Y-1 would drop by about 0.2.
- **Rubric inconsistencies.** The form's graded caps conflict with `measurement.md` ("no global cap"). I report both and lead with `measurement.md`, which the form names as canonical. The form's §1–§17 numbering differs from the principles' §0–§14; the mapping is stated at the top.
- **"Removable blemish" rule.** X's stage-1 row 13 decides the whole D1 gap, so I reported D1 as no clear advantage rather than letting it flip the verdict. I did not apply the same exemption to X's stage-2 R7 failure: that sits in the core algorithm of a new rule, and X's own invariant is contradicted by X's own algorithm.
- **Oracle leakage.** The hard-limit oracle answer was not visible to either designer. X's "degrade, never drop" was a stated assumption. Even setting the unsatisfiable case aside, X still fails the satisfiable `a1,b1,a2,a3,a4` case against its own INV7, so the D2 verdict does not rest on the unseen oracle.
