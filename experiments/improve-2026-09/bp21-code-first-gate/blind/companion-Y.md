---
title: "flags.py"
date: 2026-09-22
---
## Discussions
- An index from flag to the rules that mention it was considered for `Resolver` and dropped; every
  lookup scans every rule instead. Building the index would have made "a rule names exactly one flag"
  part of the `Rule` contract, where today it is a convenience of `_FlagRule` alone and a rule is free
  to abstain on whatever grounds it likes. The price paid is a linear scan per lookup, on rule sets
  assumed small — revisit if a real rule set ever grows large enough for that scan to show up in a
  profile, knowing the revisit spends the freedom to abstain for reasons other than the flag name.
