"""Path-prefix access control with most-specific-wins, DENY-breaks-ties, default-deny."""


def _scope_matches(scope, path):
    """True when scope equals path or is a segment-boundary prefix of it."""
    if scope == "":
        return True
    if scope == path:
        return True
    return path.startswith(scope + "/")


def _segment_count(scope):
    """Specificity of a scope, measured in path segments; root '' is 0."""
    if scope == "":
        return 0
    return len(scope.split("/"))


class AccessControl:
    def __init__(self, rules):
        # Each rule is a (scope, effect) pair.
        self.rules = list(rules)

    def evaluate(self, path):
        matching = [
            (scope, effect)
            for scope, effect in self.rules
            if _scope_matches(scope, path)
        ]
        if not matching:
            return "DENY"

        best = max(_segment_count(scope) for scope, _ in matching)
        winners = [effect for scope, effect in matching if _segment_count(scope) == best]

        # Tie-break: DENY wins over ALLOW at the most-specific level.
        if "DENY" in winners:
            return "DENY"
        return "ALLOW"
