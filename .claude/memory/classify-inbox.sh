#!/usr/bin/env bash
# Classify entries in docs/memory/_inbox.md.
# For each entry (a path that was edited but matched no leaf), ask the
# model to propose either an existing leaf or a new leaf path.
#
# Output (TSV, one row per entry):
#   <inbox-entry>\texisting-leaf\t<leaf-path>
#   <inbox-entry>\tnew-leaf\t<proposed-node-path>\t<proposed-kind>
#   <inbox-entry>\tuncertain\t<reason>
#
# Caller (Stop hook / /done) is responsible for applying confident
# proposals and surfacing uncertain ones to the user.
#
# Behaviour mirrors consolidate.sh: silent skip if no API key.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: classify-inbox.sh

Reads docs/memory/_inbox.md, asks the model to propose a leaf for
each entry. Prints TSV proposals to stdout.
EOF
  exit 0
fi

[ -f "$INBOX" ] || exit 0
[ -s "$INBOX" ] || exit 0

if [ -z "${ANTHROPIC_API_KEY:-}" ] \
   || ! command -v curl >/dev/null 2>&1 \
   || ! command -v jq >/dev/null 2>&1; then
  printf 'skipping inbox classification (no API key / curl / jq)\n' >&2
  exit 0
fi

MODEL="${AIMS_MEMORY_MODEL:-claude-sonnet-4-6}"
API_URL="${AIMS_ANTHROPIC_URL:-https://api.anthropic.com/v1/messages}"

# Build the list of existing leaves with their node + code paths, for context.
leaves_summary=""
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  node=$(fm_get "$leaf" node)
  kind=$(fm_get "$leaf" kind)
  paths=$(fm_list "$leaf" code | tr '\n' ',' | sed 's/,$//')
  leaves_summary+="- ${leaf} (node=${node}, kind=${kind}, code=[${paths}])"$'\n'
done < <(list_leaves)

inbox_entries=$(cat "$INBOX")

prompt=$(cat <<EOF
You are classifying unrecognised edited paths into the aims memory tree.

For EACH bullet in INBOX below, produce exactly ONE line of output in
this TSV format (no extra commentary):

  <entry>\texisting-leaf\t<leaf-path>
  <entry>\tnew-leaf\t<proposed-node-path>\t<module|decision|topic|runbook>
  <entry>\tuncertain\t<short-reason>

Use "existing-leaf" only if a leaf below clearly fits.
Use "new-leaf" only if the path is significant enough to deserve one.
Otherwise "uncertain".

EXISTING LEAVES:
${leaves_summary:-(none)}

INBOX:
$inbox_entries
EOF
)

req=$(jq -n \
  --arg model "$MODEL" \
  --arg prompt "$prompt" \
  '{model: $model, max_tokens: 2048, messages: [{role: "user", content: $prompt}]}')

resp=$(curl -sS -X POST "$API_URL" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "$req" 2>&1) || {
    printf 'inbox classification API call failed: %s\n' "$resp" >&2
    exit 0
  }

text=$(printf '%s' "$resp" | jq -r '.content[0].text // empty' 2>/dev/null)
[ -z "$text" ] && exit 0

# Pass through only well-formed TSV lines (contain at least one tab).
printf '%s\n' "$text" | awk -F'\t' 'NF >= 2 { print }'
