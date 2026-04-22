"""Structured observability for the executor.

Every meaningful event becomes one line of JSON. Re-readable by tools;
no narrative logs.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class TraceEvent:
    t: float
    kind: str                      # "dispatch" | "envelope" | "decision" | "cap" | "outcome"
    step: str | None = None        # step id (if applicable)
    agent: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    duration_ms: float | None = None
    envelope_valid: bool | None = None
    data: dict = field(default_factory=dict)


class Tracer:
    def __init__(self, sink: Path | None = None):
        self.events: list[TraceEvent] = []
        self._sink = sink
        self._t0 = time.time()
        if sink:
            sink.parent.mkdir(parents=True, exist_ok=True)
            sink.write_text("")  # truncate

    def emit(self, **kwargs) -> None:
        kwargs.setdefault("t", round(time.time() - self._t0, 4))
        event = TraceEvent(**kwargs)
        self.events.append(event)
        if self._sink:
            with self._sink.open("a") as f:
                f.write(json.dumps(asdict(event)) + "\n")

    def summary(self) -> dict:
        total_in  = sum(e.tokens_in  or 0 for e in self.events)
        total_out = sum(e.tokens_out or 0 for e in self.events)
        dispatches = [e for e in self.events if e.kind == "dispatch"]
        return {
            "events": len(self.events),
            "dispatches": len(dispatches),
            "total_tokens_in": total_in,
            "total_tokens_out": total_out,
            "outcome": next((e.data.get("outcome") for e in reversed(self.events)
                             if e.kind == "outcome"), None),
            "duration_s": round(
                (self.events[-1].t - self.events[0].t) if self.events else 0.0, 3
            ),
        }
