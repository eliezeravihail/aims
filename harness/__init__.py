"""Deterministic executor for the agent routing system.

The markdown files under ``agents/`` and ``.claude/commands/experts.md`` are
the *specification*. This package is the *implementation*: it parses those
files, dispatches subagents, validates envelopes, and manages state.
"""

__version__ = "0.1.0"
SCHEMA_VERSION = 1
