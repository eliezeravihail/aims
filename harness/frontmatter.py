"""Parse an agent markdown file into its behavioural contract.

Frontmatter shape (per agents/_schema.md):
    ---
    name: <id>
    model: <exact model id>
    tools: [<tool>, ...]
    capabilities: [<tag>, ...]
    inputs:
      - <name>: <type>
    outputs:
      - <name>: <type>
    effects: [read-fs | write-fs | web | external-api]
    idempotent: <bool>
    strategy:
      max_retries: <int>
      on_failure: abort | retry | escalate
    ---
    <body>
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)", re.DOTALL)


@dataclass(frozen=True)
class AgentSpec:
    id: str
    model: str
    tools: tuple[str, ...]
    capabilities: tuple[str, ...]
    inputs: dict[str, str]
    outputs: dict[str, str]
    effects: tuple[str, ...]
    idempotent: bool
    max_retries: int
    on_failure: str
    body: str
    path: Path

    def required_input_ports(self) -> set[str]:
        """Input ports without a trailing '?' are required."""
        return {n for n in self.inputs if not n.endswith("?")}


def _port_list(raw: Any) -> dict[str, str]:
    """Inputs/outputs are a YAML list of single-key mappings; flatten to dict."""
    out: dict[str, str] = {}
    if not raw:
        return out
    for item in raw:
        if isinstance(item, dict) and len(item) == 1:
            k, v = next(iter(item.items()))
            out[k] = str(v) if v is not None else ""
        elif isinstance(item, str):
            # tolerate bare "name" without type annotation
            out[item] = ""
    return out


def load(path: str | Path) -> AgentSpec:
    """Load and parse an agent markdown file."""
    path = Path(path)
    text = path.read_text()
    match = _FRONTMATTER.match(text)
    if not match:
        raise ValueError(f"{path}: no YAML frontmatter")
    fm = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)

    missing = {"name", "model"} - set(fm)
    if missing:
        raise ValueError(f"{path}: frontmatter missing required fields: {missing}")

    strategy = fm.get("strategy") or {}
    return AgentSpec(
        id=fm["name"],
        model=fm["model"],
        tools=tuple(fm.get("tools") or ()),
        capabilities=tuple(fm.get("capabilities") or ()),
        inputs=_port_list(fm.get("inputs")),
        outputs=_port_list(fm.get("outputs")),
        effects=tuple(fm.get("effects") or ()),
        idempotent=bool(fm.get("idempotent", False)),
        max_retries=int(strategy.get("max_retries", 1)),
        on_failure=str(strategy.get("on_failure", "abort")),
        body=body,
        path=path,
    )
