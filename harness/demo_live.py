"""Demo: feed a REAL LLM envelope (captured from a live dispatch) through
the harness parser. Proves the plumbing between a live subagent and the
deterministic executor.

Invocation:
    python -m harness.demo_live
"""
from __future__ import annotations

import json

from . import envelope as env


# Verbatim output from a live Haiku dispatch for the request:
#   "fix src/calc.py add() — add('3','4') returns '34' instead of 7; cover with tests"
# Captured in the project conversation as a real Agent-tool invocation.
LIVE_ROUTER_OUTPUT = '''```json
{
  "schema_version": 1,
  "ok": true,
  "outputs": {
    "decision": {
      "action": "dispatch-planner",
      "scope": "complex",
      "target_agent": null,
      "rationale": "Bug fix requires debugger to isolate root cause, then tester to add coverage. Multi-worker pipeline."
    }
  }
}
```'''


def main() -> int:
    print("Live LLM output (raw, 400 chars):")
    print("  " + LIVE_ROUTER_OUTPUT[:400].replace("\n", "\n  "))
    print()

    print("Parsing with harness.envelope.parse() ...")
    try:
        e = env.parse(LIVE_ROUTER_OUTPUT)
    except env.EnvelopeError as exc:
        print(f"  FAILED: {exc}")
        return 1

    print(f"  ✓ signal          = {e.signal}")
    print(f"  ✓ schema_version  = {e.raw['schema_version']}")
    print(f"  ✓ fence stripped  = yes")
    print()

    decision = e.outputs["decision"]
    print("Decision extracted:")
    print(f"  action        = {decision['action']}")
    print(f"  scope         = {decision['scope']}")
    print(f"  target_agent  = {decision['target_agent']}")
    print(f"  rationale     = {decision['rationale']}")
    print()

    # Prove the executor would route this correctly:
    valid_pre_exec = {"dispatch-trivial", "dispatch-simple", "dispatch-planner"}
    if decision["action"] in valid_pre_exec:
        print(f"Executor routing: {decision['action']} → Step 2b (Planner).")
    else:
        print(f"INVALID pre-exec action: {decision['action']!r}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
