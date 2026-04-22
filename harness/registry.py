"""Load the agent registry (agents/registry.md) and provide lookups.

The registry is the authoritative list of worker agents the Router and
Planner may choose from. Infrastructure agents (_router, _planner,
_validator) are always present and loaded separately.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .frontmatter import AgentSpec, load as load_spec


_ROW = re.compile(r"^\|\s*([A-Za-z_][A-Za-z0-9_]*)\s*\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*$")


@dataclass(frozen=True)
class RegistryEntry:
    id: str
    file: Path
    capability: str
    spec: AgentSpec


class Registry:
    def __init__(self, entries: dict[str, RegistryEntry], infra: dict[str, AgentSpec]):
        self._entries = entries
        self._infra = infra

    @classmethod
    def load(cls, agents_dir: str | Path) -> "Registry":
        agents_dir = Path(agents_dir)
        registry_file = agents_dir / "registry.md"
        if not registry_file.exists():
            raise FileNotFoundError(registry_file)

        entries: dict[str, RegistryEntry] = {}
        for line in registry_file.read_text().splitlines():
            if line.startswith("| id ") or line.startswith("|--"):
                continue
            m = _ROW.match(line)
            if not m:
                continue
            agent_id, rel, cap = m.group(1), m.group(2), m.group(3)
            # rel is typically "agents/debugger.md" — resolve relative to repo root
            file = (agents_dir.parent / rel).resolve()
            if not file.exists():
                file = (agents_dir / Path(rel).name).resolve()
            spec = load_spec(file)
            if spec.id != agent_id:
                raise ValueError(
                    f"{file}: frontmatter name '{spec.id}' != registry id '{agent_id}'"
                )
            entries[agent_id] = RegistryEntry(agent_id, file, cap, spec)

        infra: dict[str, AgentSpec] = {}
        for infra_id in ("_router", "_planner", "_validator"):
            infra_file = agents_dir / f"{infra_id}.md"
            if infra_file.exists():
                infra[infra_id] = load_spec(infra_file)

        return cls(entries, infra)

    # ---- lookups -------------------------------------------------------

    def worker(self, agent_id: str) -> RegistryEntry:
        if agent_id not in self._entries:
            raise KeyError(f"unknown worker: {agent_id} (known: {sorted(self._entries)})")
        return self._entries[agent_id]

    def infra(self, role: str) -> AgentSpec:
        if role not in self._infra:
            raise KeyError(f"missing infrastructure agent: {role}")
        return self._infra[role]

    def workers(self) -> dict[str, RegistryEntry]:
        return dict(self._entries)

    def has_worker(self, agent_id: str) -> bool:
        return agent_id in self._entries
