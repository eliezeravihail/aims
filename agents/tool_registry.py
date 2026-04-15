"""
agents/tool_registry.py
========================
Typed tool definitions — every Tool has a strict input/output schema.
Tools are registered centrally and injected into agents that need them.
Agents never instantiate tools directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pydantic import BaseModel


# ─────────────────────────────────────────────
# Tool Base
# ─────────────────────────────────────────────

class ToolInput(BaseModel):
    pass

class ToolOutput(BaseModel):
    pass

class BaseTool(ABC):
    name: str

    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        ...


# ─────────────────────────────────────────────
# Books Loader Tool
# ─────────────────────────────────────────────

class BooksLoaderInput(ToolInput):
    category: str
    book_slug: str
    topic_file: str

class BooksLoaderOutput(ToolOutput):
    content: str        # raw markdown of the topic file
    found: bool

class BooksLoaderTool(BaseTool):
    name = "books_loader"

    def __init__(self, books_root: str):
        self.books_root = books_root

    async def execute(self, input_data: BooksLoaderInput) -> BooksLoaderOutput:
        import aiofiles
        import os
        path = os.path.join(
            self.books_root,
            input_data.category,
            input_data.book_slug,
            input_data.topic_file,
        )
        if not os.path.exists(path):
            return BooksLoaderOutput(content="", found=False)
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        return BooksLoaderOutput(content=content, found=True)


# ─────────────────────────────────────────────
# LLM Caller Tool
# ─────────────────────────────────────────────

class LLMCallInput(ToolInput):
    system_prompt: str
    user_message: str
    model: str
    max_tokens: int = 8192

class LLMCallOutput(ToolOutput):
    content: str
    input_tokens: int
    output_tokens: int
    model: str

class LLMCallerTool(BaseTool):
    name = "llm_caller"

    def __init__(self, client):
        self.client = client    # anthropic.AsyncAnthropic or similar

    async def execute(self, input_data: LLMCallInput) -> LLMCallOutput:
        response = await self.client.messages.create(
            model=input_data.model,
            max_tokens=input_data.max_tokens,
            system=input_data.system_prompt,
            messages=[{"role": "user", "content": input_data.user_message}],
        )
        return LLMCallOutput(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
        )


# ─────────────────────────────────────────────
# Web Search Tool (Agent 4)
# ─────────────────────────────────────────────

class WebSearchInput(ToolInput):
    query: str
    max_results: int = 5

class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class WebSearchOutput(ToolOutput):
    results: list[WebSearchResult]

class WebSearchTool(BaseTool):
    name = "web_search"

    def __init__(self, search_client):
        self.search_client = search_client

    async def execute(self, input_data: WebSearchInput) -> WebSearchOutput:
        raw = await self.search_client.search(input_data.query, n=input_data.max_results)
        results = [
            WebSearchResult(title=r["title"], url=r["url"], snippet=r["snippet"])
            for r in raw
        ]
        return WebSearchOutput(results=results)
