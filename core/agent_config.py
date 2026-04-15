from __future__ import annotations

from pydantic import BaseModel
from core.models import AgentRole


class AgentModelConfig(BaseModel):
    model: str
    max_tokens: int
    temperature: float
    prompt_version: str
    rationale: str


MODEL_REGISTRY: dict[AgentRole, AgentModelConfig] = {
    AgentRole.BOOK_FINDER: AgentModelConfig(
        model='claude-haiku-4-5-20251001',
        max_tokens=2048,
        temperature=0.2,
        prompt_version='v1.0',
        rationale='Structured ranking and filtering, cost-sensitive.',
    ),
    AgentRole.BOOK_ENCODER: AgentModelConfig(
        model='claude-sonnet-4-6',
        max_tokens=16384,
        temperature=0.2,
        prompt_version='v1.1',
        rationale='Knowledge distillation quality compounds across the whole system.',
    ),
}


def get_config(role: AgentRole) -> AgentModelConfig:
    return MODEL_REGISTRY[role]
