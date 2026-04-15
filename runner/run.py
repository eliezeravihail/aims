"""
runner/run.py — GitHub Actions entrypoint for knowledge-library-agents.

All LLM calls go through GitHub Models (OpenAI-compatible endpoint).
GITHUB_TOKEN is the only credential needed — no ANTHROPIC_API_KEY required.

Agent routing by issue label:
  find-book    → Agent 4 (Book Finder)  — gpt-4o-mini
  encode-book  → Agent 5 (Book Encoder) — gpt-4o-mini
  books-status → Agent 5               — gpt-4o-mini
  books-audit  → Agent 5               — gpt-4o-mini
  books-init   → writes skill files to skills/BOOKS/ — gpt-4o-mini per topic
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import yaml
from openai import OpenAI

# ── GitHub Models client ────────────────────────────────────────────────────

GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"
MODEL = "gpt-4o-mini"

_client = OpenAI(
    base_url=GITHUB_MODELS_BASE_URL,
    api_key=os.environ["GITHUB_TOKEN"],
)


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
    response = _client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    return response.choices[0].message.content


# ── Prompt loading ──────────────────────────────────────────────────────────

def load_agent_prompt(agent_num: str) -> str:
    with open("agents/prompts/prompt_versions.yaml") as f:
        versions = yaml.safe_load(f)
    version = versions["active"][f"agent_{agent_num}"]
    with open(f"agents/prompts/versions/agent_{agent_num}_{version}.md") as f:
        return f.read()


# ── GitHub comment ──────────────────────────────────────────────────────────

def post_comment(body: str) -> None:
    subprocess.run(
        ["gh", "issue", "comment", ISSUE_NUMBER, "--body", body, "--repo", REPO],
        check=True,
        env={**os.environ, "GH_TOKEN": os.environ["GH_TOKEN"]},
    )


# ── Skill file writer ───────────────────────────────────────────────────────

TOPIC_SYSTEM_PROMPT = """\
You are a technical knowledge encoder. Given a book and a specific topic,
write a concise skill file in Markdown that a coding agent can use directly.

Structure:
## Key Definitions
## Core Algorithms / Patterns
## Code Example (one focused example)
## Common Pitfalls
## Connections to Other Topics

Be precise and actionable. No summaries — write knowledge an agent can apply immediately.
"""


def encode_topic(book: dict, topic: str) -> str:
    """Call LLM for one topic and return the markdown content."""
    user_msg = (
        f"Book: {book['title']} by {book['authors']}\n"
        f"Category: {book['category']}\n"
        f"Topic to encode: {topic}\n"
        f"Free URL: {book.get('free_url', 'not available')}\n\n"
        f"Write the skill file for this topic."
    )
    return call_llm(TOPIC_SYSTEM_PROMPT, user_msg, max_tokens=2048)


def write_skill_file(category: str, slug: str, topic: str, content: str) -> str:
    """Write content to skills/BOOKS/<CATEGORY>/<slug>_<topic>.md and return the path."""
    dir_path = f"skills/BOOKS/{category}"
    os.makedirs(dir_path, exist_ok=True)
    file_path = f"{dir_path}/{slug}_{topic}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {topic.replace('_', ' ').title()}\n\n")
        f.write(f"*Source: {slug}*\n\n")
        f.write(content)
    return file_path


def update_meta(category: str, slug: str, title: str, quality_score: float = 0.85) -> None:
    """Append a row to skills/BOOKS/<CATEGORY>/_meta.md."""
    from datetime import date
    meta_path = f"skills/BOOKS/{category}/_meta.md"
    today = date.today().isoformat()
    row = f"| {slug} | {title} | local_v1 | {quality_score} | {today} | false | — |\n"

    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Remove existing row for this slug if present (re-encode)
        lines = [l for l in content.splitlines(keepends=True) if f"| {slug} |" not in l]
        with open(meta_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
            f.write(row)
    else:
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("| slug | title | version | quality_score | date | stale | notes |\n")
            f.write("|------|-------|---------|---------------|------|-------|-------|\n")
            f.write(row)


# ── books-init ──────────────────────────────────────────────────────────────

def run_books_init() -> str:
    with open("books-init-queue.yaml") as f:
        queue = yaml.safe_load(f)

    with open(".claude/books_checkpoint.json") as f:
        checkpoint = json.load(f)

    completed = set(checkpoint.get("completed", []))
    summary_lines = []

    for book in queue:
        slug = book["slug"]
        category = book["category"]
        topics = book["topics_to_encode"]

        if slug in completed:
            summary_lines.append(f"- `{slug}` — skipped (already encoded)")
            continue

        # Skip books with no verified free source — encoding without a real
        # source produces hallucinated content that cannot be trusted.
        if not book.get("free_url"):
            summary_lines.append(
                f"- `{slug}` — **skipped** (no free URL)\n"
                f"  To encode this book, download it and run:\n"
                f"  `/project:ingest-local-sources <path> --category {category} --slug {slug}`"
            )
            continue

        post_comment(f"**books-init** — encoding `{slug}` ({len(topics)} topics)...")
        created_files = []

        for topic in topics:
            content = encode_topic(book, topic)
            path = write_skill_file(category, slug, topic, content)
            created_files.append(path)

        update_meta(category, slug, book["title"])

        completed.add(slug)
        checkpoint["completed"] = list(completed)
        with open(".claude/books_checkpoint.json", "w") as f:
            json.dump(checkpoint, f, indent=2)

        files_list = "\n".join(f"  - `{p}`" for p in created_files)
        summary_lines.append(f"- `{slug}` — {len(created_files)} files written:\n{files_list}")

    return "## books-init complete\n\n" + "\n".join(summary_lines)


# ── Main ────────────────────────────────────────────────────────────────────

LABEL = os.environ["AGENT_LABEL"]
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO = os.environ["GITHUB_REPOSITORY"]

ROUTES: dict[str, str] = {
    "find-book":    "4",
    "encode-book":  "5",
    "books-status": "5",
    "books-audit":  "5",
}

try:
    if LABEL == "books-init":
        result = run_books_init()
    elif LABEL in ROUTES:
        agent_num = ROUTES[LABEL]
        result = call_llm(load_agent_prompt(agent_num), ISSUE_BODY)
        result = f"## Agent {agent_num} — `{LABEL}`\n\n{result}"
    else:
        post_comment(f"Unknown label `{LABEL}`. Supported: {', '.join(ROUTES)}, books-init")
        sys.exit(0)

    footer = f"\n\n---\n*Model: `{MODEL}` via GitHub Models · Label: `{LABEL}`*"
    post_comment(result + footer)

except Exception as exc:
    post_comment(f"**Agent error** (`{LABEL}`):\n```\n{exc}\n```")
    sys.exit(1)
