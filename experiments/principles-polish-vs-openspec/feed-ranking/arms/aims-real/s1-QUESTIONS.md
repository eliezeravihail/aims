# Feed ranking, stage 1: questions for the product owner

The design is paused on these. Each one changes what the service visibly does, so under the aims-guide
method it's a product decision for you, not something the designer should guess. The substrate (Python 3.11+,
stdlib only, single process, library + optional small CLI) is already set in `substrate.md` and isn't asked
again.

Each question has a **proposed default**. Reply "defaults OK" to accept them all, or answer only the ones
you want to change.

---

### Q1. How are the signals combined?
The brief says "combines the signals into a single score" and gives per-signal weights.
**Proposed default:** a weighted linear sum, `score = w_r·recency + w_a·affinity + w_p·popularity`. Nothing
else goes into the score: no decay, no per-user term, no normalization of the result.

### Q2. What counts as valid weights, and must they sum to 1?
Can a weight be negative? Can one be zero? What if they sum to 0.9 or 3?
**Proposed default:** every weight must be a finite number ≥ 0 and at least one must be > 0. The weights
don't have to sum to 1 and are **not** rescaled; they're used as given. (Ordering is the same either way,
but the score is only comparable across configs if you tell us to normalize.) Any other weights make the
config invalid.

### Q3. What happens when the operator loads an invalid weight config?
This covers a malformed file, a missing signal weight, an extra unknown signal name, or a weight that breaks
Q2.
**Proposed default:** the invalid config is rejected with an error that names the problem. At startup,
the service refuses to start. On a later change, the service **keeps serving with the last valid weights**
and reports the rejection. A request is never ranked with partial or invalid weights.

### Q4. When does a weight change take effect?
"An operator changes the weights without a code change." Should a running process pick up the change, or
is a restart enough?
**Proposed default:** the weights are read from a config file. A change takes effect on the **next request
after the service reloads**, and reloading means restarting the process or calling an explicit reload. The
service doesn't watch the file. Each request is ranked entirely with one version of the weights, never a
mix.

### Q5. What happens with a candidate whose signals are out of range or missing?
For example, `recency = 1.3`, `affinity = -0.2`, `popularity` absent, or NaN.
**Proposed default:** the **whole request is rejected** with an error that names the item and the signal.
The service doesn't clamp values, doesn't fill in 0, and doesn't silently drop the item. (The alternatives
are clamping the value into [0, 1], or dropping only the bad item and ranking the rest.)

### Q6. What is the item id, and which way does the tie-break go?
**Proposed default:** the item id is a non-empty string. When two items have equal scores, they're ordered
by id **ascending**, using plain lexicographic string order: `"10"` sorts before `"9"`. Equal means
exactly equal as computed, with no epsilon.

### Q7. What if the same item id appears twice in one request?
**Proposed default:** the request is rejected as invalid. The alternatives are keeping the first
occurrence, or keeping the one with the higher score.

### Q8. What does the response contain?
**Proposed default:** the ordered list of candidates, each with its computed `score`, and the version or id
of the weight config that was used. An empty candidate list returns an empty feed and isn't an error.

### Q9. Does the `user` affect ranking in stage 1?
Affinity already arrives computed on each candidate.
**Proposed default:** no. In stage 1 the `user` is carried for identity only and doesn't change the score or
the order. There are no per-user or per-segment weights. Weights are set per deployment only.
