"""Deterministic executor for the tiered agent routing system.

The markdown at ``.claude/commands/experts.md`` describes this state machine
in prose; this file implements it. Hand-waving is not allowed here —
anything ambiguous in the spec becomes a hard decision in code.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import envelope as env
from .dispatcher import Dispatcher, DispatchResult
from .frontmatter import AgentSpec
from .registry import Registry
from .state import Caps, CapsUsed, ExecutionState, resolve_binding
from .tracer import Tracer


PROJECT_CONTEXT_FILE = ".claude.md"


class ExecutorError(RuntimeError):
    pass


class Executor:
    def __init__(
        self,
        registry: Registry,
        dispatcher: Dispatcher,
        tracer: Optional[Tracer] = None,
    ):
        self.registry = registry
        self.dispatcher = dispatcher
        self.tracer = tracer or Tracer()

    # ---- public entrypoint ---------------------------------------------

    def run(self, request: str, cwd: str) -> ExecutionState:
        state = ExecutionState(request=request, cwd=cwd)
        self.tracer.emit(kind="dispatch", data={"phase": "start", "request": request})

        # Step 0 — project-context preflight
        self._preflight_context(state)

        # Step 1 — Router (pre-exec)
        decision = self._invoke_infra("_router", {"request": request}, state)
        action = decision.get("action")
        scope = decision.get("scope")

        if action == "dispatch-trivial":
            self._run_single(decision["target_agent"], state, validate=False)
        elif action == "dispatch-simple":
            self._run_single(decision["target_agent"], state, validate=True)
        elif action == "dispatch-baseline":
            self._run_baseline(state)
        elif action == "dispatch-planner":
            self._run_planned(state)
        else:
            raise ExecutorError(f"Router returned invalid pre-exec action: {action!r}")

        self.tracer.emit(kind="outcome", data={"outcome": state.outcome or "accept"})
        return state

    # ---- step 0 --------------------------------------------------------

    def _preflight_context(self, state: ExecutionState) -> None:
        path = Path(state.cwd) / PROJECT_CONTEXT_FILE
        if path.exists():
            return
        self.tracer.emit(kind="decision", data={"preflight": "bootstrap"})
        # In a live session, the Executor would dispatch a subagent with the
        # project-context skill loaded. Here we record the advisory and let
        # the caller decide whether to inline or delegate.
        # For determinism, the harness writes a minimal stub the workers can
        # read; real bootstrapping remains the LLM's job via skills/.
        path.write_text(_stub_context(state.cwd))

    # ---- step 1–5 ------------------------------------------------------

    def _run_baseline(self, state: ExecutionState) -> None:
        """Holistic path: dispatch `_baseline` (Opus) with the raw request,
        no Planner, no Validator. Exists because pilot data showed decomposition
        hurts correctness on self-contained feature builds."""
        step_id = "s1"
        try:
            spec = self.registry.infra("_baseline")
        except KeyError:
            state.outcome = "abort"
            state.outcome_reason = "_baseline infra agent not registered"
            return
        envelope_dict = self._dispatch_worker(spec, {"request": state.request}, step_id)
        state.step_results[step_id] = envelope_dict
        if not envelope_dict["ok"]:
            state.outcome = "abort"
            state.outcome_reason = (envelope_dict.get("abort") or envelope_dict.get("retry"))["reason"]
            return
        state.outcome = "accept"

    def _run_single(self, agent_id: str, state: ExecutionState, *, validate: bool) -> None:
        step_id = "s1"
        entry = self.registry.worker(agent_id)
        inputs = _infer_inputs_from_request(state.request, entry.spec)
        envelope_dict = self._dispatch_worker(entry.spec, inputs, step_id)
        state.step_results[step_id] = envelope_dict
        if not envelope_dict["ok"]:
            state.outcome = "abort"
            state.outcome_reason = (envelope_dict.get("abort") or envelope_dict.get("retry"))["reason"]
            return
        if validate:
            self._validate_and_route(step_id, entry.spec, inputs, state)
        else:
            state.outcome = "accept"

    def _run_planned(self, state: ExecutionState) -> None:
        plan_env = self._invoke_infra("_planner", {"request": state.request}, state)
        # Plan is the 'plan' output, or the plan envelope's outputs itself
        plan = plan_env.get("plan") or plan_env
        state.plan = plan
        state.caps = Caps(**plan.get("caps", {}))

        for step in plan["steps"]:
            self._run_plan_step(step, state)
            if state.outcome in {"abort"}:
                return
        state.outcome = state.outcome or "accept"

    def _run_plan_step(self, step: dict, state: ExecutionState) -> None:
        step_id = step["id"]
        agent_id = step["agent"]
        entry = self.registry.worker(agent_id)
        raw_inputs = step.get("inputs", {})
        inputs = resolve_binding(raw_inputs, state)

        envelope_dict = self._dispatch_worker(entry.spec, inputs, step_id)
        state.step_results[step_id] = envelope_dict

        if not envelope_dict["ok"] and envelope_dict.get("retry"):
            if state.caps_used.bump_retry(step_id) <= state.caps.retries_per_step:
                inputs_with_hint = {**inputs, "retry_hint": envelope_dict["retry"]["reason"]}
                envelope_dict = self._dispatch_worker(entry.spec, inputs_with_hint, step_id)
                state.step_results[step_id] = envelope_dict
            else:
                state.outcome = "abort"
                state.outcome_reason = "retries_per_step exceeded"
                return

        if not envelope_dict["ok"] and envelope_dict.get("abort"):
            state.outcome = "abort"
            state.outcome_reason = envelope_dict["abort"]["reason"]
            return

        if step.get("validate"):
            self._validate_and_route(step_id, entry.spec, inputs, state)

    # ---- validation + router post-exec --------------------------------

    def _validate_and_route(
        self, step_id: str, spec: AgentSpec, inputs: dict, state: ExecutionState
    ) -> None:
        verdict = self._invoke_infra(
            "_validator",
            {
                "artifact": state.step_results[step_id],
                "agent_id": spec.id,
                "step_goal": state.plan["goal"] if state.plan else state.request,
                "step_inputs": inputs,
            },
            state,
        )
        state.verdicts[step_id] = verdict

        decision = self._invoke_infra(
            "_router",
            {
                "verdict": verdict,
                "state": {
                    "caps_used": {
                        "retries_per_step": state.caps_used.retries_for(step_id),
                        "reroutes": state.caps_used.reroutes,
                        "replans": state.caps_used.replans,
                    },
                    "current_step": step_id,
                },
            },
            state,
        )
        action = decision.get("action")
        self.tracer.emit(kind="decision", step=step_id,
                         data={"post_exec_action": action, "verdict_score": verdict.get("score")})

        if action == "accept":
            state.outcome = "accept"
            return
        if action == "retry":
            state.caps_used.bump_retry(step_id)
            if state.caps_used.retries_for(step_id) > state.caps.retries_per_step:
                state.outcome = "abort"
                state.outcome_reason = "retries_per_step exceeded after post-exec"
                return
            # re-dispatch with hint from verdict
            hint = (verdict["issues"][0]["suggestion"] if verdict.get("issues") else "")
            new_env = self._dispatch_worker(spec, {**inputs, "retry_hint": hint}, step_id)
            state.step_results[step_id] = new_env
            if new_env["ok"]:
                return self._validate_and_route(step_id, spec, inputs, state)
            state.outcome = "abort"
            state.outcome_reason = "retry did not produce a successful envelope"
            return
        if action == "abort":
            state.outcome = "abort"
            state.outcome_reason = decision.get("rationale", "router aborted")
            return
        # re-route / replan handling left as TODO; emit abort with a precise reason
        # so the caller knows the harness didn't silently succeed.
        state.outcome = "abort"
        state.outcome_reason = f"post-exec action {action!r} not yet implemented in harness"

    # ---- dispatch helpers ----------------------------------------------

    def _invoke_infra(self, role: str, inputs: dict, state: ExecutionState) -> dict:
        spec = self.registry.infra(role)
        result = self.dispatcher.dispatch(spec, inputs)
        envelope = env.parse(result.text)
        self.tracer.emit(
            kind="envelope", step=role, agent=spec.id, model=spec.model,
            tokens_in=result.tokens_in, tokens_out=result.tokens_out,
            duration_ms=result.duration_ms, envelope_valid=True,
            data={"signal": envelope.signal, "outputs": envelope.outputs},
        )
        # Infra agents return an envelope whose `outputs` contains one typed
        # payload (decision / plan / verdict). Flatten to that payload.
        outputs = envelope.outputs or {}
        if role == "_router":
            return outputs.get("decision", outputs)
        if role == "_planner":
            return outputs.get("plan", outputs)
        if role == "_validator":
            return outputs.get("verdict", outputs)
        return outputs

    def _dispatch_worker(self, spec: AgentSpec, inputs: dict, step_id: str) -> dict:
        self.tracer.emit(kind="dispatch", step=step_id, agent=spec.id, model=spec.model)
        result = self.dispatcher.dispatch(spec, inputs)
        try:
            envelope = env.parse(result.text)
            valid = True
        except env.EnvelopeError as e:
            self.tracer.emit(
                kind="envelope", step=step_id, agent=spec.id, model=spec.model,
                tokens_in=result.tokens_in, tokens_out=result.tokens_out,
                envelope_valid=False, data={"error": str(e), "raw_head": result.text[:200]},
            )
            # malformed envelope → synthesize an abort so the state machine stays honest
            return env.abort(f"malformed envelope from {spec.id}: {e}")
        self.tracer.emit(
            kind="envelope", step=step_id, agent=spec.id, model=spec.model,
            tokens_in=result.tokens_in, tokens_out=result.tokens_out,
            duration_ms=result.duration_ms, envelope_valid=True,
            data={"signal": envelope.signal, "advisory": envelope.advisory},
        )
        return envelope.raw


# -- helpers ----------------------------------------------------------------


def _infer_inputs_from_request(request: str, spec: AgentSpec) -> dict:
    """Lightweight fallback when the Router returns only a target_agent.

    Maps the raw request onto the first string-typed required input.
    Real-world use will pass explicit inputs from the Router's decision.
    """
    inputs: dict = {}
    for port, type_hint in spec.inputs.items():
        if port.endswith("?"):
            continue
        if "string" in (type_hint or "").lower() and port not in inputs:
            inputs[port] = request
    return inputs


def _stub_context(cwd: str) -> str:
    import datetime as _dt
    ts = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return (
        "# Project Context\n"
        f"<!-- Generated: {ts} | Source of truth: harness-stub | Root: {cwd} -->\n\n"
        "## Layout\nHarness-generated stub. Run `python -m harness.cli refresh-context` to replace with the real map.\n\n"
        "## Modules\n(empty — stub)\n\n"
        "## Test layout\n- Framework: unknown\n\n"
        "## Conventions\n(none recorded)\n\n"
        "## Known invariants\n(none recorded)\n\n"
        "## Sources consulted\n- harness stub (filesystem not walked)\n"
    )
