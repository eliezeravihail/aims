"""
agents/base_agent.py
====================
Abstract base for all agent implementations.
Every agent receives its AgentModelConfig at construction —
it never decides which model to call on its own.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from core.models import AgentRole
from core.agent_config import AgentModelConfig, get_config

TInput  = TypeVar("TInput",  bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class BaseAgent(ABC, Generic[TInput, TOutput]):
    """
    Contract:
    - config is injected at __init__ — never retrieved inside run()
    - run() is the only public method
    - Agents are stateless between calls
    - Agents do NOT hold references to WorkflowState
    """

    def __init__(self, config: AgentModelConfig | None = None):
        # If no config injected, fall back to registry default for this role
        self.config: AgentModelConfig = config or get_config(self.role)

    @abstractmethod
    async def run(self, input_data: TInput) -> TOutput:
        ...

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        ...
