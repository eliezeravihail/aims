"""access.py -- prefix-scoped ALLOW/DENY rule evaluation.

A rule (scope, effect) applies to a path when its scope is a segment-boundary
prefix of the path. The applicable rule with the longest scope decides; ties go
to DENY; no applicable rule means DENY.
"""

ALLOW = "ALLOW"
DENY = "DENY"


def _matches(scope, path):
    """Return True if `scope` matches `path` on segment boundaries."""
    if not scope:
        return True  # root scope matches everything
    scope_segs = scope.split("/")
    path_segs = path.split("/")
    if len(scope_segs) > len(path_segs):
        return False
    return path_segs[: len(scope_segs)] == scope_segs


class AccessControl:
    """Evaluate access decisions against an ordered list of rules."""

    def __init__(self, rules):
        self._rules = list(rules)

    def evaluate(self, path):
        applicable = [(scope, effect) for scope, effect in self._rules if _matches(scope, path)]
        if not applicable:
            return DENY

        # Longest scope (most segments) is most specific.
        def specificity(scope):
            return 0 if scope == "" else len(scope.split("/"))

        best = max(specificity(scope) for scope, _ in applicable)
        effects = {effect for scope, effect in applicable if specificity(scope) == best}

        return DENY if DENY in effects else ALLOW
