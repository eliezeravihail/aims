from pathlib import Path

import pytest

from harness.frontmatter import load


ROOT = Path(__file__).parent.parent
AGENTS = ROOT / "agents"


@pytest.mark.parametrize("name", [
    "_router", "_planner", "_validator", "debugger", "tester", "test_strategist",
])
def test_existing_agents_parse(name):
    spec = load(AGENTS / f"{name}.md")
    assert spec.id == name
    assert spec.model.startswith("claude-")
    assert spec.max_retries >= 0


def test_debugger_has_expected_ports():
    spec = load(AGENTS / "debugger.md")
    assert "bug_description" in spec.inputs
    assert "test_gaps" in spec.outputs
    assert "read-fs" in spec.effects
    assert "write-fs" in spec.effects


def test_port_optional_marker_detected():
    spec = load(AGENTS / "tester.md")
    required = spec.required_input_ports()
    assert "targets" in required
    assert "retry_hint?" not in required  # optional ports stay suffixed
