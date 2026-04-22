"""End-to-end test of the executor with a mock dispatcher.

Covers the main pathways: trivial dispatch, simple + Validator accept,
complex Plan → workers → Validator → Router → accept, and the retry path.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from harness import envelope as env
from harness.dispatcher import MockDispatcher
from harness.executor import Executor
from harness.registry import Registry
from harness.tracer import Tracer


ROOT = Path(__file__).parent.parent


# -- shared fixtures -----------------------------------------------------


@pytest.fixture
def registry():
    return Registry.load(ROOT / "agents")


@pytest.fixture
def tmp_cwd(tmp_path: Path) -> Path:
    """A temp dir where .claude.md is bootstrapped by the executor."""
    return tmp_path


# -- helpers -------------------------------------------------------------


def router_decision(action, **extra):
    return env.ok({"decision": {"action": action, "rationale": "test", **extra}})


def verdict(**kwargs):
    default = {
        "schema_version": 1,
        "passed": True,
        "score": 0.9,
        "issues": [],
        "suggested_action": "accept",
    }
    default.update(kwargs)
    return env.ok({"verdict": default})


def plan(*steps, goal="test goal", caps=None):
    return env.ok({
        "plan": {
            "schema_version": 1,
            "plan_id": "plan_test",
            "goal": goal,
            "steps": list(steps),
            "caps": caps or {"retries_per_step": 3, "reroutes": 3, "replans": 2},
        }
    })


# -- tests ---------------------------------------------------------------


def test_trivial_dispatch_skips_validator(registry, tmp_cwd):
    """scope=trivial: Router → worker, no Validator."""
    responses = {
        "_router_pipeline": lambda inp: router_decision(
            "dispatch-trivial", scope="trivial", target_agent="debugger"
        ),
        "debugger": lambda inp: env.ok({
            "root_cause": "typo",
            "fix": {"files": ["a.py"], "summary": "fixed typo"},
            "verification": "pytest -q",
            "test_gaps": [],
        }),
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("rename variable", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert "s1" in state.step_results
    assert state.verdicts == {}  # Validator never invoked


def test_simple_dispatch_invokes_validator(registry, tmp_cwd):
    responses = {
        "_router_pipeline": _twoway_router("dispatch-simple", "debugger"),
        "_validator": lambda inp: verdict(score=0.85),
        "debugger": lambda inp: env.ok({
            "root_cause": "off-by-one in loop bound",
            "fix": {"files": ["src/loop.py"], "summary": "use len()-1"},
            "verification": "pytest tests/test_loop.py",
            "test_gaps": [],
        }),
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("fix off-by-one in src/loop.py", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert state.verdicts["s1"]["passed"] is True


def test_complex_plan_cascade(registry, tmp_cwd):
    """Debugger emits test_gaps → Planner binds them into tester inputs."""
    captured_tester_inputs = {}

    def capture_tester(inputs):
        captured_tester_inputs.update(inputs)
        return env.ok({
            "tests_added": {
                "files": ["tests/test_regression.py"],
                "count": 2,
                "summary": "closed the two gaps",
            },
            "verification": "pytest tests/test_regression.py",
        })

    gaps = [
        {"test_type": "unit", "target": "src/a.py", "scenario": "empty list",
         "origin": "bug-driven", "priority": "high", "rationale": "triggers the bug"},
    ]

    responses = {
        "_router_pipeline": _twoway_router("dispatch-planner"),
        "_planner": lambda inp: plan(
            {"id": "s1", "agent": "debugger",
             "inputs": {"bug_description": "${input}"},
             "validate": True, "depends_on": []},
            {"id": "s2", "agent": "tester",
             "inputs": {"targets": "${s1.outputs.test_gaps}"},
             "validate": True, "depends_on": []},
            goal="fix bug X and close its gaps",
        ),
        "_validator": lambda inp: verdict(),
        "debugger": lambda inp: env.ok({
            "root_cause": "null deref on empty list",
            "fix": {"files": ["src/a.py"], "summary": "guard with if not xs"},
            "verification": "pytest",
            "test_gaps": gaps,
        }),
        "tester": capture_tester,
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("fix bug X", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert set(state.step_results) == {"s1", "s2"}
    # The critical assertion: gap binding from s1 actually reached tester
    assert captured_tester_inputs["targets"] == gaps


def test_retry_path_when_validator_asks(registry, tmp_cwd):
    """Validator says retry → executor re-dispatches with a hint, then accepts."""
    call_log: list[dict] = []

    def debugger(inputs):
        call_log.append(inputs)
        if "retry_hint" in inputs:
            # second call: produce a good envelope
            return env.ok({
                "root_cause": "off-by-one",
                "fix": {"files": ["a.py"], "summary": "fix"},
                "verification": "pytest",
                "test_gaps": [],
            })
        # first call: output is missing verification
        return env.ok({
            "root_cause": "off-by-one",
            "fix": {"files": ["a.py"], "summary": "fix"},
            "verification": "",
            "test_gaps": [],
        })

    verdicts_iter = iter([
        verdict(
            passed=False, score=0.4,
            issues=[{"severity": "high", "location": "verification",
                     "reason": "empty", "suggestion": "populate verification"}],
            suggested_action="retry",
        ),
        verdict(),  # second pass: accept
    ])
    router_decisions = iter([
        router_decision("dispatch-simple", scope="simple", target_agent="debugger"),
        router_decision("retry"),    # post-exec, first round
        router_decision("accept"),   # post-exec, second round
    ])

    responses = {
        "_router_pipeline": lambda inp: next(router_decisions),
        "_validator": lambda inp: next(verdicts_iter),
        "debugger": debugger,
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("fix off-by-one", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert len(call_log) == 2
    assert "retry_hint" in call_log[1]


def test_retry_in_plan_step_feeds_hint_back(registry, tmp_cwd):
    """Plan-step retry path: worker returns retry envelope, executor feeds hint,
    worker succeeds on the second attempt. Mirrors the cookiecutter pilot's
    intended recovery flow if the debugger had produced an incomplete fix."""
    call_log: list[dict] = []

    def debugger(inputs):
        call_log.append(dict(inputs))
        if "retry_hint" in inputs:
            return env.ok({
                "root_cause": "null-deref on empty list",
                "fix": {"files": ["a.py"], "summary": "guard with len check"},
                "verification": "pytest -q",
                "test_gaps": [],
            })
        return env.retry(
            "reproduction not established",
            hint="call with an empty list to reproduce",
        )

    responses = {
        "_router_pipeline": _twoway_router("dispatch-planner"),
        "_planner": lambda inp: env.ok({"plan": {
            "schema_version": 1,
            "plan_id": "retry_pilot",
            "goal": "fix null-deref",
            "steps": [{
                "id": "s1", "agent": "debugger",
                "inputs": {"bug_description": "null deref on empty list"},
                "validate": False, "depends_on": [],
            }],
            "caps": {"retries_per_step": 3, "reroutes": 3, "replans": 2},
        }}),
        "debugger": debugger,
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("fix null-deref", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert len(call_log) == 2
    assert "retry_hint" not in call_log[0]
    assert call_log[1]["retry_hint"] == "reproduction not established"
    assert state.caps_used.retries_for("s1") == 1


def test_lying_artifact_is_rejected_on_objective_check(registry, tmp_cwd):
    """Simulates the medium-pilot stretch goal: worker claims success but
    verdict's objective_checks show tests did not pass. Router should NOT
    accept — here we simulate via validator returning passed=false."""
    def debugger(inputs):
        # Worker lies: claims success but the code doesn't actually pass tests.
        return env.ok({
            "root_cause": "wrong exception type raised",
            "fix": {"files": ["hooks.py"], "summary": "raise exception"},
            "verification": "pytest (claimed)",
            "test_gaps": [],
        })

    def validator(_inputs):
        # Validator runs objective_checks and discovers the lie.
        v = {
            "schema_version": 1,
            "passed": False, "score": 0.15,
            "issues": [{
                "severity": "critical", "location": "cookiecutter/hooks.py:74",
                "reason": "Raises ValueError, not FailedHookException; regression test fails",
                "suggestion": "Replace ValueError with FailedHookException",
            }],
            "suggested_action": "retry",
            "objective_checks": {"tests_passed": False, "fix_matches_claim": False},
        }
        return env.ok({"verdict": v})

    retry_decisions = iter([
        router_decision("dispatch-simple", scope="simple", target_agent="debugger"),
        router_decision("abort", rationale="objective_checks contradict claim"),
    ])
    responses = {
        "_router_pipeline": lambda inp: next(retry_decisions),
        "_validator": validator,
        "debugger": debugger,
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("fix the bug", cwd=str(tmp_cwd))

    assert state.outcome == "abort"
    assert "objective_checks" in (state.outcome_reason or "").lower() or \
           "contradict" in (state.outcome_reason or "").lower()
    # verdict was recorded
    assert state.verdicts["s1"]["passed"] is False
    assert state.verdicts["s1"]["objective_checks"]["tests_passed"] is False


def test_malformed_envelope_becomes_abort(registry, tmp_cwd):
    """A worker that returns non-JSON must not crash the executor."""
    from harness.dispatcher import DispatchResult

    class MalformedDispatcher(MockDispatcher):
        def dispatch(self, spec, inputs):
            if spec.id == "debugger":
                self.calls.append((spec.id, inputs))
                return DispatchResult(
                    text="Sure! Here is my answer: the bug is in line 42.",
                    tokens_in=10, tokens_out=20, model=spec.model,
                )
            return super().dispatch(spec, inputs)

    responses = {
        "_router_pipeline": lambda inp: router_decision(
            "dispatch-trivial", scope="trivial", target_agent="debugger"
        ),
    }
    ex = Executor(registry, MalformedDispatcher(responses), Tracer())
    state = ex.run("fix typo", cwd=str(tmp_cwd))

    assert state.outcome == "abort"
    assert "malformed" in state.outcome_reason


def test_tracer_records_dispatches(registry, tmp_cwd):
    tracer = Tracer()
    responses = {
        "_router_pipeline": lambda inp: router_decision(
            "dispatch-trivial", scope="trivial", target_agent="debugger"
        ),
        "debugger": lambda inp: env.ok({
            "root_cause": "x", "fix": {"files": [], "summary": "y"},
            "verification": "pytest", "test_gaps": [],
        }),
    }
    ex = Executor(registry, MockDispatcher(responses), tracer)
    ex.run("do it", cwd=str(tmp_cwd))
    summary = tracer.summary()
    assert summary["dispatches"] >= 2
    assert summary["outcome"] == "accept"


def test_baseline_dispatch_skips_planner_and_validator(registry, tmp_cwd):
    """scope=holistic: Router → _baseline → done. No Planner, no Validator.
    The holistic path is the architecture's escape hatch from decomposition,
    motivated by pilot data showing a single Opus dispatch outperforms a
    decomposed pipeline on self-contained feature builds."""
    responses = {
        "_router_pipeline": lambda inp: router_decision(
            "dispatch-baseline", scope="holistic", target_agent=None
        ),
        "_baseline": lambda inp: env.ok({
            "summary": "built TODO CLI end-to-end in one dispatch",
            "created_files": ["todo.py", "test_todo.py"],
            "verification": "python -m pytest test_todo.py -q",
        }),
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    state = ex.run("build a terminal TODO CLI with plain-text persistence",
                   cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert "s1" in state.step_results
    assert state.verdicts == {}                     # no Validator ran
    assert state.plan is None                       # no Planner ran
    envelope = state.step_results["s1"]
    assert envelope["outputs"]["summary"].startswith("built TODO CLI")


def test_baseline_missing_infra_agent_aborts_gracefully(tmp_cwd):
    """If `_baseline` is not registered, the executor must abort with a
    clear reason — not raise."""
    from harness.registry import Registry

    class RegistryWithoutBaseline(Registry):
        def infra(self, role):
            if role == "_baseline":
                raise KeyError("_baseline missing")
            return super().infra(role)

    reg = RegistryWithoutBaseline.load(ROOT / "agents")
    # Shim out: intentionally force the KeyError path.
    orig_infra = reg.infra
    reg.infra = lambda r: (_ for _ in ()).throw(KeyError("_baseline missing")) if r == "_baseline" else orig_infra(r)

    responses = {
        "_router_pipeline": lambda inp: router_decision(
            "dispatch-baseline", scope="holistic", target_agent=None
        ),
    }
    ex = Executor(reg, MockDispatcher(responses), Tracer())
    state = ex.run("build X", cwd=str(tmp_cwd))
    assert state.outcome == "abort"
    assert "_baseline" in state.outcome_reason


# -- lean-mode tests (run_lean) -----------------------------------------


def test_lean_dispatch_single_worker_with_skills(registry, tmp_cwd):
    """Lean Router → single worker on chosen model with skills loaded.
    No Planner, no Validator invoked (worker outputs have no write-effect ports)."""
    captured_worker_inputs = {}

    def capture_worker(inputs):
        captured_worker_inputs.update(inputs)
        return env.ok({
            "summary": "explained it in one dispatch",
            "answer": "42",
        })

    responses = {
        "_router": lambda inp: env.ok({"decision": {
            "action": "dispatch-lean",
            "model": "claude-sonnet-4-6",
            "skills_to_load": ["project-context"],
            "rationale": "read-only explanation",
        }}),
    }
    # Route the synthetic lean worker — MockDispatcher matches by spec.id
    # prefix since the id is f"_lean_worker({model})".
    class LeanMock(MockDispatcher):
        def dispatch(self, spec, inputs):
            if spec.id.startswith("_lean_worker"):
                self.calls.append((spec.id, inputs))
                envelope = capture_worker(inputs)
                import json
                return __import__("harness.dispatcher", fromlist=["DispatchResult"]).DispatchResult(
                    text=json.dumps(envelope),
                    tokens_in=len(json.dumps(inputs)) // 4,
                    tokens_out=len(json.dumps(envelope)) // 4,
                    duration_ms=1.0, model=spec.model,
                )
            return super().dispatch(spec, inputs)

    ex = Executor(registry, LeanMock(responses), Tracer())
    state = ex.run_lean("explain the project", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert "s1" in state.step_results
    assert state.verdicts == {}   # no Validator — no write effects claimed
    assert captured_worker_inputs == {"request": "explain the project"}


def test_lean_dispatch_triggers_validator_on_write_effects(registry, tmp_cwd):
    """When the lean worker's envelope has write-effect ports (created_files,
    fix, or tests_added), the Validator must run as a terminal check."""
    def worker(inputs):
        return env.ok({
            "created_files": ["new.py"],
            "summary": "wrote a file",
            "verification": "python new.py",
        })

    verdicts_iter = iter([verdict(score=0.9)])

    responses = {
        "_router": lambda inp: env.ok({"decision": {
            "action": "dispatch-lean",
            "model": "claude-sonnet-4-6",
            "skills_to_load": ["feature-build"],
            "rationale": "feature build",
        }}),
        "_validator": lambda inp: next(verdicts_iter),
    }

    class LeanMock(MockDispatcher):
        def dispatch(self, spec, inputs):
            if spec.id.startswith("_lean_worker"):
                import json
                envelope = worker(inputs)
                return __import__("harness.dispatcher", fromlist=["DispatchResult"]).DispatchResult(
                    text=json.dumps(envelope),
                    tokens_in=10, tokens_out=10, duration_ms=1.0, model=spec.model,
                )
            return super().dispatch(spec, inputs)

    ex = Executor(registry, LeanMock(responses), Tracer())
    state = ex.run_lean("build a CLI", cwd=str(tmp_cwd))

    assert state.outcome == "accept"
    assert state.verdicts["s1"]["passed"] is True


def test_lean_rejects_non_lean_router_action(registry, tmp_cwd):
    """The lean Router must emit action='dispatch-lean'. Anything else is
    a protocol violation."""
    responses = {
        "_router": lambda inp: env.ok({"decision": {
            "action": "dispatch-planner",   # wrong mode — lean path must reject
            "rationale": "oops",
        }}),
    }
    ex = Executor(registry, MockDispatcher(responses), Tracer())
    import pytest
    with pytest.raises(Exception, match="Lean router returned invalid action"):
        ex.run_lean("do it", cwd=str(tmp_cwd))


# -- helpers -------------------------------------------------------------


def _twoway_router(action, target_agent=None):
    """Return a stateful router-response callable: first call pre-exec,
    subsequent calls post-exec return 'accept'."""
    state = {"calls": 0}

    def handler(_inputs):
        state["calls"] += 1
        if state["calls"] == 1:
            return router_decision(action, scope="simple", target_agent=target_agent)
        return router_decision("accept")

    return handler
