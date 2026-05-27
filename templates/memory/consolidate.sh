#!/usr/bin/env bash
# Consolidate a single dirty leaf: ask Sonnet/Opus to update the leaf body
# based on (a) the current body and (b) diffs of the leaf's referenced
# source files since `last_touched`. Append breadcrumbs for any
# external_refs that changed since `last_consolidated`.
#
# Usage:  consolidate.sh <leaf_path>
#
# Behaviour:
#   - Reads ANTHROPIC_API_KEY from env. If missing, prints
#     "skipping consolidation (no API key)" to stderr and exits 0;
#     the leaf remains dirty so a later run can catch up.
#   - On success: writes the updated body in place, sets dirty: false,
#     bumps last_touched + last_consolidated.
#   - On API failure: prints to stderr and exits 0 (non-blocking).
#
# Model: ${AIMS_MEMORY_MODEL:-claude-sonnet-4-6}

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 1 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: consolidate.sh <leaf_path>

Consolidates a dirty leaf via the Anthropic API. Requires
ANTHROPIC_API_KEY in the environment; exits 0 silently if absent.
EOF
  exit 0
fi

leaf="$1"
if ! [ -f "$leaf" ]; then
  printf 'error: not a file: %s\n' "$leaf" >&2
  exit 1
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  printf 'skipping consolidation (no ANTHROPIC_API_KEY): %s\n' "$leaf" >&2
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  printf 'skipping consolidation (curl not found): %s\n' "$leaf" >&2
  exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
  printf 'skipping consolidation (jq not found): %s\n' "$leaf" >&2
  exit 0
fi

MODEL="${AIMS_MEMORY_MODEL:-claude-sonnet-4-6}"
API_URL="${AIMS_ANTHROPIC_URL:-https://api.anthropic.com/v1/messages}"

# Build the per-source diffs since last_touched. If a source isn't in git,
# include just its current content (truncated).
LAST_TOUCHED=$(fm_get "$leaf" last_touched)
diffs=""
while IFS= read -r p; do
  [ -z "$p" ] && continue
  base="${p%%:*}"
  [ -e "$base" ] || continue
  if git -C . rev-parse --is-inside-work-tree >/dev/null 2>&1 && [ -n "$LAST_TOUCHED" ]; then
    d=$(git -C . log --since="$LAST_TOUCHED" --no-merges -p -- "$base" 2>/dev/null | head -c 8000)
  else
    d=""
  fi
  if [ -n "$d" ]; then
    diffs+=$'\n\n=== diff: '"$p"$' ===\n'"$d"
  fi
done < <(fm_list "$leaf" code)

# Collect changed external refs (breadcrumb input).
changed_refs=$(bash "$SCRIPT_DIR/check-refs.sh" "$leaf" || true)

# URLs harvested from the session transcript by the Stop hook
# (newline-separated). Filtered downstream by the LLM.
transcript_urls="${AIMS_TRANSCRIPT_URLS:-}"

# Optional extra context (typically plan / ADR bodies, injected by
# /done's propagation step). The LLM is asked to mine this for
# invariants, design rationale, and fixed-bug entries — but ONLY to
# add content that is clearly about this node's code.
extra_context="${AIMS_EXTRA_CONTEXT:-}"

# Build the prompt.
node_body=$(cat "$leaf")
prompt=$(cat <<EOF
You are updating an aims memory NODE (per ADR-0008). A node is the
primary read interface for a slice of the codebase; it may itself
have parent nodes and child nodes (the memory structure is a DAG,
not a strict tree). It has six fixed body sections, in this order:

  ## Purpose            — one paragraph: what this code does.
  ## Design rationale   — 2–4 bullets: why it is shaped this way;
                          each bullet may end with a repo-relative
                          pointer (ADR-NNNN, commit SHA, plan slug).
  ## Invariants & gotchas — what must not break when editing. Concise.
  ## Known issues       — open: one-line — pointer
                          fixed: one-line: what broke and why — SHA
  ## Pointers           — ADRs / Plans / Commits (anchors only) / External.
  ## Open questions     — design questions not yet decided.
                          (Distinct from Known issues, which are bugs.)

RULES:
- Preserve all frontmatter (the YAML between --- markers) EXACTLY.
  Do not invent or change frontmatter values; the caller manages
  dirty/last_touched/last_consolidated. Frontmatter includes
  parents:/children:/related: DAG edges — leave them alone.
- Keep the six section headings verbatim and in order.
- Target ~1–2 KB total. If the node would bulge past ~4 KB, do NOT
  pack everything in — instead add an Open question bullet
  ("Should this node split into …?" or "Should X be extracted to an
  ADR?"). The user reviews at /done.
- ALL in-project pointers MUST be repo-relative. Forbidden:
    * absolute filesystem paths (leading "/" or "~/")
    * URLs to this repo's host pointing back into the same repo
      (e.g. github.com/<org>/<repo>/blob/...)
  Use "docs/adr/NNNN-slug.md", "src/foo.py:42", "ADR-0008", etc.
  Commit SHAs are fine. External URLs to OTHER systems (Slack,
  third-party docs, issue trackers) are fine.
- Do NOT invent facts. If a diff is ambiguous, prefer adding an
  Open questions bullet to fabricating a rule or a fixed-bug entry.
- "Known issues > fixed" entries MUST cite a real commit SHA from the
  diffs below.
- Preserve the existing voice. Concise, declarative.
- Output the COMPLETE node file (frontmatter + body) — nothing else.

CURRENT NODE:
$node_body

DIFFS OF REFERENCED SOURCES SINCE last_touched:
${diffs:-(no diffs available)}

CHANGED EXTERNAL REFS (for each, append one-line breadcrumb under
"## Pointers" formatted as:
"- External: <path> updated since last consolidation — review for impact"):
${changed_refs:-(none)}

URLS CITED IN SESSION TRANSCRIPT (consider for "## Pointers > External".
ONLY add a URL if it is clearly about this node's code; otherwise
drop it. Format: "- External: <URL> — <one-line context>"):
${transcript_urls:-(none)}

ADDITIONAL CONTEXT (plan / ADR text driving this consolidation, if any).
Mine for invariants (→ "## Invariants & gotchas"), design rationale
(→ "## Design rationale"), fixed bugs (→ "## Known issues > fixed",
ONLY if a commit SHA from the diffs above can be cited), and open
design questions (→ "## Open questions"). DO NOT add content unless
the connection between this context and this node's code is clear.
If the connection is weak, leave sections empty:
${extra_context:-(none)}
EOF
)

# Call the API.
req=$(jq -n \
  --arg model "$MODEL" \
  --arg prompt "$prompt" \
  '{model: $model, max_tokens: 4096, messages: [{role: "user", content: $prompt}]}')

resp=$(curl -sS -X POST "$API_URL" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "$req" 2>&1) || {
    printf 'consolidation API call failed for %s: %s\n' "$leaf" "$resp" >&2
    exit 0
  }

new_body=$(printf '%s' "$resp" | jq -r '.content[0].text // empty' 2>/dev/null)
if [ -z "$new_body" ]; then
  printf 'consolidation returned empty for %s; leaving dirty.\n' "$leaf" >&2
  printf 'response was: %s\n' "$resp" >&2
  exit 0
fi

# Sanity: response must still start with `---` (frontmatter preserved).
case "$new_body" in
  '---'*) ;;
  *)
    printf 'consolidation lost frontmatter for %s; leaving dirty.\n' "$leaf" >&2
    exit 0 ;;
esac

# Write atomically.
tmp=$(mktemp)
printf '%s\n' "$new_body" > "$tmp"
mv "$tmp" "$leaf"

NOW=$(now_iso)
fm_set "$leaf" dirty false
fm_set "$leaf" last_touched "$NOW"
fm_set "$leaf" last_consolidated "$NOW"

printf '[aims-memory] consolidated %s\n' "$leaf" >&2
