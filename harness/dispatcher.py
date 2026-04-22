"""Adapter between the executor and whatever actually runs an agent.

Two implementations:

- ``MockDispatcher``  — used in tests; returns pre-canned envelopes.
- ``LiveDispatcher``  — talks to Anthropic SDK when available. If the SDK
  is not installed or ``ANTHROPIC_API_KEY`` is absent, it raises clearly
  on dispatch so the caller knows to pick a different backend.

A third option in Claude Code sessions is the Agent/Task tool, but that's
orchestration-level and is documented in the Executor markdown; here we
provide the programmatic path that keeps tests deterministic.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Protocol

from .frontmatter import AgentSpec


@dataclass(frozen=True)
class DispatchResult:
    """What a dispatcher returns. ``text`` is the raw model output."""
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: float = 0.0
    model: str = ""


class Dispatcher(Protocol):
    def dispatch(self, spec: AgentSpec, inputs: dict) -> DispatchResult: ...


class MockDispatcher:
    """Deterministic dispatcher for tests.

    ``responses`` maps agent id → callable(inputs) → envelope dict.
    """
    def __init__(self, responses: dict[str, Callable[[dict], dict]]):
        self._responses = responses
        self.calls: list[tuple[str, dict]] = []

    def dispatch(self, spec: AgentSpec, inputs: dict) -> DispatchResult:
        self.calls.append((spec.id, inputs))
        fn = self._responses.get(spec.id)
        if fn is None:
            raise KeyError(f"MockDispatcher: no response registered for {spec.id}")
        envelope = fn(inputs)
        import json
        return DispatchResult(
            text=json.dumps(envelope),
            tokens_in=len(json.dumps(inputs)) // 4,
            tokens_out=len(json.dumps(envelope)) // 4,
            duration_ms=1.0,
            model=spec.model,
        )


class LiveDispatcher:
    """Real Anthropic-SDK dispatcher.

    Kept intentionally minimal. The spec's body is used as the system
    prompt; ``inputs`` is serialised into the user turn as JSON. The
    model is expected to return an envelope (possibly fenced).
    """
    def __init__(self):
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "LiveDispatcher requires the 'anthropic' package"
            ) from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

    def dispatch(self, spec: AgentSpec, inputs: dict) -> DispatchResult:  # pragma: no cover
        import json
        import time
        import anthropic
        client = anthropic.Anthropic()
        system = (
            f"You are agent {spec.id}. Follow the specification below strictly. "
            f"Return ONE JSON envelope conforming to schemas/envelope.v1.json. "
            f"Do not wrap the envelope in prose.\n\n"
            f"--- AGENT SPEC ---\n{spec.body}"
        )
        user = f"Inputs:\n```json\n{json.dumps(inputs, indent=2)}\n```"
        t0 = time.time()
        msg = client.messages.create(
            model=spec.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        duration_ms = (time.time() - t0) * 1000
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        return DispatchResult(
            text=text,
            tokens_in=msg.usage.input_tokens,
            tokens_out=msg.usage.output_tokens,
            duration_ms=duration_ms,
            model=spec.model,
        )
