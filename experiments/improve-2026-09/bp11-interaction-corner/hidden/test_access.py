"""BP11 hidden tests. THE INTERACTION CORNER is test_specific_allow_under_broad_deny:
a 'deny always wins' implementation returns DENY there and FAILS — the load-bearing case."""
import importlib, os
acc = importlib.import_module(os.environ.get("ACC_MOD", "access"))
AccessControl = acc.AccessControl
ALLOW, DENY = "ALLOW", "DENY"


def ev(rules, path):
    return AccessControl(rules).evaluate(path)


def test_no_rules_default_deny():
    assert ev([], "a/b") == DENY


def test_single_allow():
    assert ev([("a", ALLOW)], "a/b/c") == ALLOW


def test_single_deny():
    assert ev([("a", DENY)], "a/b/c") == DENY


def test_no_match_default_deny():
    assert ev([("x", ALLOW)], "a/b") == DENY


def test_more_specific_deny_beats_broad_allow():
    # broad ALLOW at "a", specific DENY at "a/b" -> for a/b/c the specific DENY wins
    assert ev([("a", ALLOW), ("a/b", DENY)], "a/b/c") == DENY


def test_specific_allow_under_broad_deny():
    # THE CORNER: broad DENY at "a", specific ALLOW at "a/b/c".
    # P1 (most specific wins) -> the ALLOW at a/b/c wins for a/b/c/d.
    # A 'deny always wins' impl returns DENY here and is WRONG.
    assert ev([("a", DENY), ("a/b/c", ALLOW)], "a/b/c/d") == ALLOW


def test_equal_specificity_deny_wins():
    # tie at the SAME most-specific scope "a/b": DENY beats ALLOW
    assert ev([("a/b", ALLOW), ("a/b", DENY)], "a/b/c") == DENY


def test_root_rule_matches_all():
    assert ev([("", ALLOW)], "anything/here") == ALLOW


def test_deeper_allow_over_deny_multi_level():
    rules = [("", DENY), ("a", DENY), ("a/b", DENY), ("a/b/c", ALLOW)]
    assert ev(rules, "a/b/c/d/e") == ALLOW      # most specific is the a/b/c ALLOW
    assert ev(rules, "a/b/x") == DENY           # most specific matching is a/b DENY


def test_exact_path_match():
    assert ev([("a/b", DENY), ("a/b/c", ALLOW)], "a/b/c") == ALLOW
