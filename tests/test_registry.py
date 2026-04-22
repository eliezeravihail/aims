from pathlib import Path

from harness.registry import Registry


ROOT = Path(__file__).parent.parent


def test_registry_loads_current_workers():
    reg = Registry.load(ROOT / "agents")
    names = sorted(reg.workers())
    assert names == ["debugger", "implementer", "test_strategist", "tester"]


def test_registry_exposes_infra_agents():
    reg = Registry.load(ROOT / "agents")
    assert reg.infra("_router").id == "_router"
    assert reg.infra("_planner").model.startswith("claude-opus")
    assert reg.infra("_validator").model.startswith("claude-sonnet")


def test_unknown_worker_raises():
    reg = Registry.load(ROOT / "agents")
    try:
        reg.worker("nonexistent")
    except KeyError as e:
        assert "nonexistent" in str(e)
    else:
        raise AssertionError("expected KeyError")
