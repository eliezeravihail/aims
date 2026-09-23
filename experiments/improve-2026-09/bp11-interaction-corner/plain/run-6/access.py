"""Access control by hierarchical path scopes.

Scopes are '/'-segmented prefixes. For a given path, the matching scope with the
greatest depth wins; at equal depth DENY overrides ALLOW; and if nothing matches
the decision defaults to DENY.
"""

from typing import Iterable, List, Tuple


class AccessControl:
    def __init__(self, rules: Iterable[Tuple[str, str]]):
        self._rules: List[Tuple[str, str]] = list(rules)

    @staticmethod
    def _depth(scope: str) -> int:
        # Number of path segments; the root scope "" has depth 0.
        return 0 if scope == "" else scope.count("/") + 1

    @staticmethod
    def _matches(scope: str, path: str) -> bool:
        if scope == "":
            return True
        if scope == path:
            return True
        return path.startswith(scope + "/")

    def evaluate(self, path: str) -> str:
        best_depth = -1
        decision = "DENY"  # default deny when nothing matches

        for scope, effect in self._rules:
            if not self._matches(scope, path):
                continue
            depth = self._depth(scope)
            if depth > best_depth:
                best_depth = depth
                decision = effect
            elif depth == best_depth and effect == "DENY":
                # Tie at the most specific depth: DENY wins.
                decision = "DENY"

        return decision
