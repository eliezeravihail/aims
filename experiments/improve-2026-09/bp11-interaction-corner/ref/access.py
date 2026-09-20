"""Reference for BP11 — validates hidden tests only; not shown to arms.

The interaction corner: two stated principles that CONFLICT on a corner —
  (P1) most-specific (longest matching prefix) rule wins;
  (P2) at equal specificity, DENY beats ALLOW.
A naive 'deny always wins' implementation satisfies P2 but VIOLATES P1 when a
specific ALLOW sits under a broader DENY. The correct resolution is P1 first,
P2 only as the tie-break at the single most-specific scope."""

from typing import List, Tuple, Optional

ALLOW = "ALLOW"
DENY = "DENY"


def _matches(scope: str, path: str) -> bool:
    # scope is a prefix of path on '/'-segment boundaries; "" matches everything (root)
    if scope == "":
        return True
    s = scope.split("/")
    p = path.split("/")
    return len(s) <= len(p) and p[:len(s)] == s


class AccessControl:
    def __init__(self, rules: List[Tuple[str, str]]) -> None:
        # rules: list of (scope, effect); effect in {ALLOW, DENY}
        self._rules = list(rules)

    def evaluate(self, path: str) -> str:
        matching = [(scope, effect) for (scope, effect) in self._rules if _matches(scope, path)]
        if not matching:
            return DENY  # default deny
        # P1: most specific = longest scope in segments
        best = max(len(scope.split("/")) if scope != "" else 0 for (scope, _) in matching)
        winners = [effect for (scope, effect) in matching
                   if (len(scope.split("/")) if scope != "" else 0) == best]
        # P2: at the most-specific scope, DENY beats ALLOW
        return DENY if DENY in winners else ALLOW
