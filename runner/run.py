"""
runner/run.py — GitHub Actions entrypoint for knowledge-library-agents.

All LLM calls go through GitHub Models (OpenAI-compatible endpoint).
GITHUB_TOKEN is the only credential needed — no ANTHROPIC_API_KEY required.

Free models used (verify availability at github.com/marketplace/models):
  gpt-4o-mini                  — OpenAI, free tier, fast
  Meta-Llama-3.1-70B-Instruct  — Meta, free tier, high quality

Agent routing by issue label:
  find-book    → Agent 4 (Book Finder)  — gpt-4o-mini (fast structured ranking)
  encode-book  → Agent 5 (Book Encoder) — Meta-Llama-3.1-70B-Instruct
  books-status → Agent 5               — Meta-Llama-3.1-70B-Instruct
  books-audit  → Agent 5               — Meta-Llama-3.1-70B-Instruct
  books-init   → Agent 5 (queue run)   — Meta-Llama-3.1-70B-Instruct
"""

from __future__ import annotations

import os
import subprocess
import sys

import yaml
from openai import OpenAI

# ── GitHub Models client ────────────────────────────────────────────────────

GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"
SONNET_MODEL  = "gpt-4o-mini"  # Free tier — confirmed ID
MINI_MODEL    = "gpt-4o-mini"        # Fast free model for lightweight ranking

_client = OpenAI(
    base_url=GITHUB_MODELS_BASE_URL,
    api_key=os.environ["GITHUB_TOKEN"],
)


def call_llm(system_prompt: str, user_message: str, model: str) -> str:
    response = _client.chat.completions.create(
        model=model,
        max_tokens=8192,
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
    path = f"agents/prompts/versions/agent_{agent_num}_{version}.md"
    with open(path) as f:
        return f.read()


# ── GitHub comment ──────────────────────────────────────────────────────────

def post_comment(body: str) -> None:
    subprocess.run(
        ["gh", "issue", "comment", ISSUE_NUMBER, "--body", body, "--repo", REPO],
        check=True,
        env={**os.environ, "GH_TOKEN": os.environ["GH_TOKEN"]},
    )


# ── Routing table ───────────────────────────────────────────────────────────

# label → (agent_number, model)
ROUTES: dict[str, tuple[str, str]] = {
    "find-book":    ("4", MINI_MODEL),    # gpt-4o-mini — fast structured ranking
    "encode-book":  ("5", SONNET_MODEL),
    "books-status": ("5", SONNET_MODEL),
    "books-audit":  ("5", SONNET_MODEL),
    "books-init":   ("5", SONNET_MODEL),
}


def run_books_init() -> str:
    """Encodes each pending book in books-init-queue.yaml one by one."""
    with open("books-init-queue.yaml") as f:
        queue = yaml.safe_load(f)

    with open(".claude/books_checkpoint.json") as f:
        import json
        checkpoint = json.load(f)

    completed = set(checkpoint.get("completed", []))
    system_prompt = load_agent_prompt("5")
    results = []

    for book in queue:
        slug = book["slug"]
        if slug in completed:
            results.append(f"- `{slug}` — skipped (already encoded)")
            continue

        post_comment(f"**books-init** — encoding `{slug}`...")
        user_msg = (
            f"slug: {book['slug']}\n"
            f"title: {book['title']}\n"
            f"authors: {book['authors']}\n"
            f"category: {book['category']}\n"
            f"free_url: {book.get('free_url', 'null')}\n"
            f"topics_to_encode: {book['topics_to_encode']}"
        )
        response = call_llm(system_prompt, user_msg, SONNET_MODEL)
        results.append(f"### `{slug}`\n{response}")

        completed.add(slug)
        checkpoint["completed"] = list(completed)
        with open(".claude/books_checkpoint.json", "w") as f:
            json.dump(checkpoint, f, indent=2)

    return "## books-init complete\n\n" + "\n\n---\n\n".join(results)


# ── Main ────────────────────────────────────────────────────────────────────

LABEL = os.environ["AGENT_LABEL"]
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO = os.environ["GITHUB_REPOSITORY"]

try:
    if LABEL == "books-init":
        result = run_books_init()
        model_used = SONNET_MODEL
    elif LABEL in ROUTES:
        agent_num, model = ROUTES[LABEL]
        result = call_llm(load_agent_prompt(agent_num), ISSUE_BODY, model)
        result = f"## Agent {agent_num} — `{LABEL}`\n\n{result}"
        model_used = model
    else:
        post_comment(f"Unknown label `{LABEL}`. Supported: {', '.join(ROUTES)}")
        sys.exit(0)

    footer = f"\n\n---\n*Model: `{model_used}` via GitHub Models · Label: `{LABEL}`*"
    post_comment(result + footer)

except Exception as exc:
    post_comment(f"**Agent error** (`{LABEL}`):\n```\n{exc}\n```")
    sys.exit(1)
