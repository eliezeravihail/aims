# Design history of the work just completed (unordered; nothing marks which items matter)

a. A design comparison must lead with the §0–§14 rubric scored from the code. Tests are a floor that
   earns nothing; behavioural change-proxies (reopened-owner count, edit locality) are gameable.
b. An earlier measurement change (decisions/0019) demoted the §0–§14 rubric beneath those proxies. It
   was itself a regression and has been superseded.
c. Two designs passing the identical test suite scored 43 vs 16 on the rubric, blind. Tests never
   separated them.
d. Six earlier record-layer experiments used records written by hand rather than filed by aims, and
   were retracted; their conclusions were withdrawn.
e. aims has two goals — correct design, and knowledge that does not belong to the code. They are served
   by different machinery and judged by different instruments, and merging them reports a false result.
f. A filed non-goal caught a change that contradicted it: 3 of 3 agents holding the records reconciled
   it; 0 of 3 with the code alone did, and none could.
g. On a ~300-line module six independent agents produced the same class hierarchy, differing only in a
   private base class's name. At that scale a strong model converges.
h. A record holds only what the code cannot. Anything a docstring, comment, name, signature or test
   could carry belongs there; a record that restates the design is duplicate state that goes stale on
   its own, and the anchor only flags the drift.
i. Measured: 62% of a companion filed before that gate existed was recoverable from the code. With the
   gate, an agent dropped 8/8 code-carried items and kept 6/6 the code cannot hold.
j. The same mistake was made three times during this work, in one shape: the thing aims actually
   optimizes was replaced by a proxy that was easier to observe — functional tests standing in for
   design quality, then the design rubric standing in for the record layer, then a structural-
   convergence result read as a verdict on records. Each substitution looked like rigour at the time.
k. Both defects found in the shipped guidance had the same form: the rule was present but not where it
   is read. "Most files never get a companion" sat in a parenthetical under a heading that said the
   opposite ("a companion beside each source file"), and the placement test sat as a clause in the last
   section. In both cases a reader followed the heading and the structure, not the qualifier.
l. A single combined discussions-and-decisions file at the project root was proposed as an alternative
   to per-file companions, on the grounds that cases needing a record at all are rare. It was tested
   (bp18) but the test was invalid — the records in it were hand-written, not filed by aims — and the
   conclusion was withdrawn. Its status now is considered-but-untested, not rejected.
m. The placement gate was validated on an agent that was handed the rejected alternatives in its input.
   An agent that must remember them from its own design work is untested.
n. The 3-of-3 record result partly measures instruction-following, since amending a record is behaviour
   the skill asks for. What it establishes is that the contradiction was detectable at all.
