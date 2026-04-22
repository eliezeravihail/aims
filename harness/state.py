"""Execution state with caps tracking."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Caps:
    retries_per_step: int = 3
    reroutes: int = 3
    replans: int = 2


@dataclass
class CapsUsed:
    retries_per_step: dict[str, int] = field(default_factory=dict)
    reroutes: int = 0
    replans: int = 0

    def retries_for(self, step_id: str) -> int:
        return self.retries_per_step.get(step_id, 0)

    def bump_retry(self, step_id: str) -> int:
        self.retries_per_step[step_id] = self.retries_for(step_id) + 1
        return self.retries_per_step[step_id]


@dataclass
class ExecutionState:
    request: str
    cwd: str
    plan: dict | None = None
    step_results: dict[str, dict] = field(default_factory=dict)   # step_id -> envelope
    verdicts: dict[str, dict] = field(default_factory=dict)       # step_id -> verdict
    caps: Caps = field(default_factory=Caps)
    caps_used: CapsUsed = field(default_factory=CapsUsed)
    outcome: str | None = None
    outcome_reason: str | None = None


def resolve_binding(value, state: ExecutionState):
    """Resolve a ${sN.outputs.<port>} reference against the current state.

    Literals are returned unchanged. Only strings of the exact form
    '${sN.outputs.<port>}' are substituted.
    """
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        inner = value[2:-1]          # e.g. "s1.outputs.test_gaps"
        parts = inner.split(".")
        if len(parts) == 3 and parts[1] == "outputs":
            step_id, port = parts[0], parts[2]
            env = state.step_results.get(step_id)
            if env is None:
                raise KeyError(f"unresolved binding {value!r}: step {step_id} not run")
            outputs = env.get("outputs") or {}
            if port not in outputs:
                raise KeyError(f"unresolved binding {value!r}: port {port!r} not in outputs")
            return outputs[port]
    if isinstance(value, list):
        return [resolve_binding(v, state) for v in value]
    if isinstance(value, dict):
        return {k: resolve_binding(v, state) for k, v in value.items()}
    return value
