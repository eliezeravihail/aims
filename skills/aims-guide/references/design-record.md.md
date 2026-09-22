---
title: "design-record.md"
date: 2026-09-22
hash: "sha256:e2054922e9dfb62546ca3d430965da2bbd6894c60ab87ba911a3fffbe0c1419f"
---
## Insights
- Both defects this file has shipped had the **same form: the rule was present, but not where it is
  read.** "Most files never get a companion" sat as a parenthetical under a heading that asserted the
  opposite ("a companion beside each source file"); the placement test — does the code carry this
  already — sat as a clause in the last section. In both cases readers followed the heading and the
  section order and never reached the qualifier, so a correct rule in the wrong position read as its own
  negation. The symptom to watch for here is a rule whose *position* contradicts it, not a rule that is
  missing — for this file, deciding where a rule goes costs as much as writing it.
