---
title: "Stage-1 architecture: exact decimals, valid-by-construction weights, snapshot-per-request"
date: 2026-09-23
---
**Context.** Opening design round for feed ranking (goals.md). It was produced by three independent axis
Workers (clean code, encapsulation, genericity) and merged. The full architecture is in DESIGN.md.

**Decision.**
- Signals, weights and scores are `Decimal`. Every input is canonicalized to the shortest decimal of its
  double, arithmetic is exact in a module-owned context, and "equal" means value equality.
- `Weights` is valid by construction and immutable. It owns the formula and derives its version id from
  its content.
- `FeedService` reads the current weights once per request and reloads by building first, then swapping.
- The core is pure. The weights seam is `Callable[[], Weights]`.

**Strengths harvested per axis.**
- *Clean code*: the fewest moving parts. It gave the `Callable` seam over a Protocol, two error types with
  no base, and `unittest` so there are no dev dependencies. Its `from_mapping` idiom does shape checks
  only and delegates every value rule to the constructor.
- *Encapsulation*: it found that unary `-score` rounds to the ambient context (verified). That led to
  `copy_negate` in the sort key and to explicit `EXACT` arithmetic that ignores the host's decimal
  context. It also found that parsing text exactly makes exact arithmetic unbounded (`1e-999999999`),
  which is why every number is canonicalized through the double. Its "refuses to start" is the absence
  of an object, and it reports problems first-found in a fixed order.
- *Genericity*: it tied every seam to a named change axis and made the list of what is deliberately not
  an axis explicit. It chose TOML (stdlib, and it rejects duplicate keys natively). It showed that
  `Decimal(float)` brings the trap back and that the default precision of 28 silently makes false ties.
  It keeps `rank_feed` taking weights *by value*, and it excludes `FeedService.from_file` because policy
  must not depend on the file adapter.

**Axis splits and how each was resolved.**
- *Number parsing* (clean and genericity: `parse_float=Decimal`, exact text; encapsulation: go through the
  double). **Harmonized.** Canonicalizing through the double gives the clean axis fewer parser hooks and
  gives the encapsulation axis bounded exactness plus one meaning of "0.1" on every path. The mechanism:
  shortest-repr is injective on doubles and reproduces what people write.
- *Owner of duplicate ids* (encapsulation: `rank`; the other two: `FeedRequest`). **Chose `FeedRequest`
  over `rank`** because the rule is about the request as a whole. A valid-request type lets `rank_feed`
  trust its input ("defensive at the edge, trusting inside").
- *Reload lock* (clean: none; the other two: reload-only lock). **Chose the lock** because two
  overlapping reloads can otherwise install the older file last. It costs nothing on the request path.
- *Error base class* (encapsulation: yes). **Cut**, because no handler catches either error the same way.
- *Echoing `user` in `Feed`* (encapsulation and genericity: yes). **Cut**, because it is not in the
  required response and nothing consumes it.
- *Unknown keys on a candidate* (clean: ignore; the other two: reject). **Chose reject**, to be
  consistent with weights and to fail fast on misspelled signals.
- *Weights seam* (encapsulation: `WeightSource` Protocol). **Chose the `Callable` alias**, because it is
  complete for its one consumer and a named interface would be decorative.
- *Config format* (clean and encapsulation: JSON with a duplicate-key hook; genericity: TOML). **Chose
  TOML**, because it rejects duplicate keys with no hook and is easier for operators to edit.

**Consequences.** Numbers written with more than about 17 significant digits are read as their nearest
double. An exact score is bounded at about 960 digits.
