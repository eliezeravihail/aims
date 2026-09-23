"""access.py — evaluate ALLOW/DENY for paths against prefix-scoped rules."""


def _split(path):
    """Return the list of segments in a path. Root "" has zero segments."""
    return [] if path == "" else path.split("/")


def _matches(scope, path):
    """A scope matches a path if it equals the path or is a boundary prefix."""
    s = _split(scope)
    p = _split(path)
    if len(s) > len(p):
        return False
    return s == p[: len(s)]


def _specificity(scope):
    """How specific a scope is: its number of path segments (root == 0)."""
    return len(_split(scope))


class AccessControl:
    """Decide access for a path from a list of (scope, effect) rules."""

    def __init__(self, rules):
        self.rules = list(rules)

    def evaluate(self, path):
        matching = [
            (_specificity(scope), effect)
            for scope, effect in self.rules
            if _matches(scope, path)
        ]

        if not matching:
            return "DENY"

        top = max(spec for spec, _ in matching)
        winners = [effect for spec, effect in matching if spec == top]

        # Among the most specific rules, any DENY overrides ALLOW.
        return "DENY" if "DENY" in winners else "ALLOW"
