"""Path-prefix access control.

Rules are (scope, effect) pairs. A scope is a slash-segmented prefix; the
empty string is the root and matches everything. For a given path, the
longest matching scope decides, DENY breaks ties, and an unmatched path is
denied by default.
"""

ALLOW = "ALLOW"
DENY = "DENY"


def _seg_count(scope):
    """Number of segments in a scope; the root scope '' counts as 0."""
    if not scope:
        return 0
    return scope.count("/") + 1


def _is_prefix(scope, path):
    """Whether `scope` matches `path` on segment boundaries."""
    if scope == "":
        return True
    if path == scope:
        return True
    return path.startswith(scope + "/")


class AccessControl:
    def __init__(self, rules):
        self._rules = list(rules)

    def evaluate(self, path):
        best_depth = -1
        decision = DENY  # default deny when nothing matches

        for scope, effect in self._rules:
            if not _is_prefix(scope, path):
                continue
            depth = _seg_count(scope)
            if depth > best_depth:
                best_depth = depth
                decision = effect
            elif depth == best_depth and effect == DENY:
                # Tie at the most specific depth -> DENY wins.
                decision = DENY

        return decision
