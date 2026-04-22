from pathlib import Path

from harness.registry import Registry


ROOT = Path(__file__).parent.parent


def test_registry_loads_current_workers():
    reg = Registry.load(ROOT / "agents")
    names = sorted(reg.workers())
    assert names == ["debugger", "implementer", "test_strategist", "tester"]


def test_registry_exposes_infra_agents():
    reg = Registry.load(ROOT / "agents")
    # Lean Router (new default, used by /experts)
    assert reg.infra("_router").id == "_router"
    assert reg.infra("_router").model.startswith("claude-haiku")
    assert reg.infra("_router").tools == ()  # tools: [] — zero tools
    # Pipeline Router (used by /agents-experts)
    assert reg.infra("_router_pipeline").id == "_router_pipeline"
    assert reg.infra("_router_pipeline").model.startswith("claude-haiku")
    assert reg.infra("_planner").model.startswith("claude-opus")
    assert reg.infra("_validator").model.startswith("claude-sonnet")
    assert reg.has_infra("_baseline")


def test_registry_has_infra_helper():
    reg = Registry.load(ROOT / "agents")
    assert reg.has_infra("_router") is True
    assert reg.has_infra("_router_pipeline") is True
    assert reg.has_infra("_nonexistent") is False


def test_unknown_worker_raises():
    reg = Registry.load(ROOT / "agents")
    try:
        reg.worker("nonexistent")
    except KeyError as e:
        assert "nonexistent" in str(e)
    else:
        raise AssertionError("expected KeyError")
