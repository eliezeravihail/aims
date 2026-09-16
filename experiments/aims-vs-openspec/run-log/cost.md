# Cost log

**How to read these.** The harness reports `subagent_tokens` on every hand-back. Within a single agent the
figure rises monotonically across its rounds (plain stage 1: 60,581 → 91,058 → 102,313; OpenSpec stage 3:
232,248 → 275,537), so I read it as **cumulative for that agent's whole life**, not per-round. The totals
below are therefore each agent's final reported figure. If that reading is wrong the numbers are
over-counted in the same direction for every arm, so the comparison holds even if the absolute values do
not. Stated because it is an interpretation, not a measurement.

| Stage | aims | OpenSpec | plain |
|---|---|---|---|
| 1 | 153,086 | 160,232 | 102,313 |
| 2 | 221,680 | 196,164 | 145,840 |
| 3 | *(pending)* | 275,537 | 209,658 |

| Stage | aims | OpenSpec | plain |
|---|---|---|---|
| tool uses, stage 1 | 33 | 40 | 28 |
| tool uses, stage 2 | 15 | 12 | 23 |
| tool uses, stage 3 | 34+ | 72 | 11 |
| wall-clock s, stage 3 | 1,251+ | 1,871 | 434 |

## What the cost reading already shows, before any judge runs

1. **The plain arm is consistently the cheapest**, by roughly 1.3-1.5x against either method, at every
   stage. That is the expected direction and it is real.
2. **It is nothing like the gap the experiment package implied.** README §4 called the method arms' extra
   reasoning "the treatment"; in practice all three arms spend the same order of magnitude, because the
   dominant cost is thinking about pricing, not running a method.
3. **The two methods cost about the same as each other.** Nothing here separates them on cost.
4. **The plain arm produced the longest documents while spending the fewest tokens** (stage 3: 2,009 lines
   on 209,658 tokens vs OpenSpec's 1,251 lines on 275,537). Output length and cost are not the same axis,
   which is worth remembering when reading the "length is not merit" instruction to the Q1 judges.

## Discarded run
The first aims stage-3 session (killed at the contamination described in observations.md) is excluded: it
wrote nothing and its tokens are not counted for or against the arm.
