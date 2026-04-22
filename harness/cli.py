"""Command-line entry point.

Usage:
    python -m harness.cli run "<request>" [--cwd <path>] [--trace <file>]
    python -m harness.cli validate <envelope.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import envelope as env
from .dispatcher import LiveDispatcher
from .executor import Executor
from .registry import Registry
from .tracer import Tracer


def _cmd_run(args: argparse.Namespace) -> int:
    registry = Registry.load(Path(args.cwd) / "agents")
    tracer = Tracer(sink=Path(args.trace) if args.trace else None)
    dispatcher = LiveDispatcher()
    executor = Executor(registry, dispatcher, tracer)
    state = executor.run(args.request, cwd=args.cwd)

    print(json.dumps({
        "outcome": state.outcome,
        "reason": state.outcome_reason,
        "summary": tracer.summary(),
        "steps": list(state.step_results),
    }, indent=2))
    return 0 if state.outcome == "accept" else 2


def _cmd_validate(args: argparse.Namespace) -> int:
    text = Path(args.path).read_text()
    try:
        envelope = env.parse(text)
    except env.EnvelopeError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"OK — signal={envelope.signal}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run a request end-to-end")
    run.add_argument("request")
    run.add_argument("--cwd", default=".")
    run.add_argument("--trace")
    run.set_defaults(func=_cmd_run)

    val = sub.add_parser("validate", help="validate an envelope file")
    val.add_argument("path")
    val.set_defaults(func=_cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
