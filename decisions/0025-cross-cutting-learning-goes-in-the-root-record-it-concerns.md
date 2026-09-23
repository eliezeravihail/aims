---
title: "cross-cutting learning goes in the root record it concerns; there is no missing record kind"
date: 2026-09-22
supersedes: 0024 (the claimed root-level Insights gap)
---

**Context.** `0024` claimed the format had a hole: a companion has Insights / Decisions / Discussions, the
root records do not, so cross-cutting learning with no decision attached had nowhere to go. It recorded
the gap and deferred a fix.

**There is no gap.** An insight that concerns the whole project belongs in the **root record it concerns**:
what the project is for and what its evidence supports → `goals.md`; the system's shape → `architecture.md`;
a decision, correction or finding of record → an ADR. The two items `0024` called "smuggled" into `goals.md`
— the measurement-error pattern, and the instruction-following caveat — were not smuggled. They are
statements about what this project's evidence does and does not support, which is what `goals.md` holds.

**Where the mistake came from.** The companion's three headings were read as a shape the root level must
mirror, so a root record without an "Insights" heading looked incomplete. It is not: those headings describe
how *a companion* is laid out, because a companion is everything known about one file and needs internal
divisions. A root record is already scoped by its subject — that is what makes it a root record — and
learning about that subject goes in it, under whatever heading fits.

**Decision.** `design-record.md` states it plainly: cross-cutting learning goes in the root record it
concerns, and there is no separate root Insights record. `0024` is marked superseded. Nothing else changes:
no new record kind, and `0023`'s single-root-file question stays open and untouched, since this removes the
only reason anyone had to prejudge it.

**Consequence.** The dogfood run's finding #1 is withdrawn (`experiments/improve-2026-09/bp22-gate-on-itself/`).
The other four findings from that run stand — they were real and are fixed.
