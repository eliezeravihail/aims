"""Demo: run the executor on the sample buggy-calc project with
handcrafted responses that match what real LLMs produce.

Invocation:
    python -m harness.demo

Produces:
    tests/fixtures/sample_project/.claude.md   (stub, bootstrapped)
    demo.trace.jsonl                           (per-step JSONL trace)
    stdout                                     (human summary)
"""
from __future__ import annotations

import json
from pathlib import Path

from . import envelope as env
from .dispatcher import MockDispatcher
from .executor import Executor
from .registry import Registry
from .tracer import Tracer


ROOT = Path(__file__).parent.parent
SAMPLE = ROOT / "tests" / "fixtures" / "sample_project"


# -- Realistic LLM responses for the scenario "fix calc.add, add tests" -----

def _router_responses():
    """Router called twice per validated step: once pre-exec, once post-exec."""
    calls = {"n": 0}

    def handler(_inputs):
        calls["n"] += 1
        if calls["n"] == 1:  # pre-exec: classify
            return env.ok({"decision": {
                "action": "dispatch-planner",
                "scope": "complex",
                "target_agent": None,
                "rationale": "bug-fix with test-gap analysis → debugger + tester",
            }})
        # every post-exec round: accept (validator already passed)
        return env.ok({"decision": {
            "action": "accept",
            "scope": None,
            "target_agent": None,
            "rationale": "verdict score above threshold",
        }})

    return handler


def _planner(_inputs):
    return env.ok({"plan": {
        "schema_version": 1,
        "plan_id": "plan_calc_fix",
        "goal": "fix src/calc.add coercion bug and close its test gap",
        "steps": [
            {
                "id": "s1", "agent": "debugger",
                "inputs": {
                    "bug_description": "src/calc.add returns '34' for add('3','4'); expected 7",
                    "codebase_hint": "src/calc.py",
                },
                "validate": True, "depends_on": [],
            },
            {
                "id": "s2", "agent": "tester",
                "inputs": {
                    "targets":     "${s1.outputs.test_gaps}",
                    "fix_summary": "${s1.outputs.fix.summary}",
                    "codebase_hint": "tests/",
                },
                "validate": True, "depends_on": [],
            },
        ],
        "caps": {"retries_per_step": 3, "reroutes": 3, "replans": 2},
    }})


def _debugger(_inputs):
    return env.ok({
        "root_cause": (
            "add() uses Python's '+' operator without type coercion. "
            "When given strings like '3' and '4', it concatenates to '34' "
            "instead of numerically summing."
        ),
        "fix": {
            "files": ["src/calc.py"],
            "summary": "Coerce numeric-looking inputs to numbers before '+' in add().",
        },
        "verification": "pytest tests/test_calc.py -v",
        "test_gaps": [
            {
                "test_type": "unit",
                "target": "src.calc.add",
                "scenario": "both inputs are numeric strings ('3', '4')",
                "origin": "bug-driven",
                "priority": "high",
                "rationale": "original bug surface — concatenation vs sum",
            },
            {
                "test_type": "unit",
                "target": "src.calc.add",
                "scenario": "one int and one numeric string ('3', 4)",
                "origin": "bug-driven",
                "priority": "high",
                "rationale": "mixed-type coercion",
            },
        ],
    })


def _tester(inputs):
    # Sanity: the Planner must have resolved the binding, so inputs['targets']
    # is a list of TestTarget dicts — not a literal string.
    assert isinstance(inputs.get("targets"), list), \
        f"binding failed: targets={inputs.get('targets')!r}"
    return env.ok({
        "tests_added": {
            "files": ["tests/test_calc_regression.py"],
            "count": 2,
            "summary": (
                "Two tests added: add_with_two_numeric_strings_returns_sum and "
                "add_with_mixed_int_and_numeric_string_returns_sum."
            ),
        },
        "verification": "pytest tests/test_calc_regression.py -v",
    })


def _validator(inputs):
    # Pretend the artifact under review looks good; score above 0.75 → pass.
    agent = inputs.get("agent_id", "")
    score = 0.88 if agent == "debugger" else 0.82
    return env.ok({"verdict": {
        "schema_version": 1,
        "passed": True,
        "score": score,
        "issues": [],
        "suggested_action": "accept",
    }})


def main() -> int:
    # Use the sample project as cwd so the preflight bootstraps .claude.md there.
    registry = Registry.load(ROOT / "agents")
    trace_file = ROOT / "demo.trace.jsonl"
    tracer = Tracer(sink=trace_file)
    dispatcher = MockDispatcher({
        "_router":    _router_responses(),
        "_planner":   _planner,
        "_validator": _validator,
        "debugger":   _debugger,
        "tester":     _tester,
    })
    ex = Executor(registry, dispatcher, tracer)
    state = ex.run(
        "fix src/calc.py add() — add('3','4') returns '34' instead of 7; cover with tests",
        cwd=str(SAMPLE),
    )

    # ---- human-readable summary ---------------------------------------
    print("=" * 72)
    print("DEMO RUN — sample buggy-calc project")
    print("=" * 72)
    print(f"outcome: {state.outcome}")
    if state.outcome_reason:
        print(f"reason : {state.outcome_reason}")
    print()
    print("Plan:")
    for step in state.plan["steps"]:
        verdict = state.verdicts.get(step["id"], {})
        env_sig = "ok" if state.step_results[step["id"]].get("ok") else "fail"
        score = verdict.get("score", "—")
        print(f"  {step['id']}  agent={step['agent']:<15} envelope={env_sig:<4}  "
              f"score={score}")
    print()
    print("Bindings resolved:")
    tester_inputs = next(i for a, i in dispatcher.calls if a == "tester")
    print(f"  tester.inputs.targets = {len(tester_inputs['targets'])} TestTargets")
    for t in tester_inputs["targets"]:
        print(f"    - [{t['priority']}] {t['target']}: {t['scenario']}")
    print()
    print("Summary metrics:")
    print(json.dumps(tracer.summary(), indent=2))
    print()
    print(f"Full trace written to: {trace_file}")
    return 0 if state.outcome == "accept" else 2


if __name__ == "__main__":
    raise SystemExit(main())
