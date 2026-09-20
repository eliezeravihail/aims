"""Prefix-scoped access control with default-deny and DENY-wins tie-breaking."""


def _segments(path):
    """Split a path into its non-empty segments; the root "" yields ()."""
    if path == "":
        return ()
    return tuple(path.split("/"))


def _scope_matches(scope_segs, path_segs):
    """True when scope is the path itself or a segment-boundary prefix of it."""
    if len(scope_segs) > len(path_segs):
        return False
    return path_segs[: len(scope_segs)] == scope_segs


class AccessControl:
    def __init__(self, rules):
        # Precompute each rule's scope segments once.
        self._rules = [
            (_segments(scope), len(_segments(scope)), effect)
            for scope, effect in rules
        ]

    def evaluate(self, path):
        path_segs = _segments(path)

        best_len = None
        best_effect = None
        for scope_segs, scope_len, effect in self._rules:
            if not _scope_matches(scope_segs, path_segs):
                continue
            if best_len is None or scope_len > best_len:
                # Strictly more specific: it decides on its own for now.
                best_len = scope_len
                best_effect = effect
            elif scope_len == best_len:
                # Tie at the most-specific length: DENY wins.
                if effect == "DENY":
                    best_effect = "DENY"

        if best_effect is None:
            return "DENY"  # default deny: no rule matched
        return best_effect
