import pytest

from harness.state import Caps, CapsUsed, ExecutionState, resolve_binding


def test_caps_defaults():
    c = Caps()
    assert (c.retries_per_step, c.reroutes, c.replans) == (3, 3, 2)


def test_caps_used_bump():
    u = CapsUsed()
    assert u.bump_retry("s1") == 1
    assert u.bump_retry("s1") == 2
    assert u.retries_for("s2") == 0


def test_resolve_binding_literal_passthrough():
    s = ExecutionState(request="r", cwd="/tmp")
    assert resolve_binding("plain", s) == "plain"
    assert resolve_binding(42, s) == 42
    assert resolve_binding([1, 2], s) == [1, 2]


def test_resolve_binding_simple():
    s = ExecutionState(request="r", cwd="/tmp")
    s.step_results["s1"] = {"ok": True, "outputs": {"x": 7, "y": [1, 2]}}
    assert resolve_binding("${s1.outputs.x}", s) == 7
    assert resolve_binding("${s1.outputs.y}", s) == [1, 2]


def test_resolve_binding_nested_dict():
    s = ExecutionState(request="r", cwd="/tmp")
    s.step_results["s1"] = {"ok": True, "outputs": {"gaps": [{"id": 1}]}}
    resolved = resolve_binding({"targets": "${s1.outputs.gaps}", "lit": "x"}, s)
    assert resolved == {"targets": [{"id": 1}], "lit": "x"}


def test_resolve_binding_missing_step():
    s = ExecutionState(request="r", cwd="/tmp")
    with pytest.raises(KeyError, match="not run"):
        resolve_binding("${s9.outputs.x}", s)


def test_resolve_binding_missing_port():
    s = ExecutionState(request="r", cwd="/tmp")
    s.step_results["s1"] = {"ok": True, "outputs": {"x": 1}}
    with pytest.raises(KeyError, match="not in outputs"):
        resolve_binding("${s1.outputs.missing}", s)
