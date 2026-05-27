#!/usr/bin/env bash
# Build the inbox-classification prompt (no network call).
#
# Per ADR-0009, classification runs in-band: the Stop hook (or /done)
# injects this prompt as additionalContext; the active Claude Code
# session classifies each entry and either Edits it into an existing
# node, scaffolds a new one, or surfaces it via AskUserQuestion.
#
# Usage:  classify-inbox.sh
# Output: prompt text on stdout (empty if inbox is empty or absent).

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: classify-inbox.sh

Emits a prompt for in-band classification of docs/memory/_inbox.md
entries. Pure bash, no LLM call. Empty stdout if inbox is empty.
EOF
  exit 0
fi

[ -f "$INBOX" ] || exit 0
[ -s "$INBOX" ] || exit 0

leaves_summary=""
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  node=$(fm_get "$leaf" node)
  kind=$(fm_get "$leaf" kind)
  paths=$(fm_list "$leaf" code | tr '\n' ',' | sed 's/,$//')
  leaves_summary+="- ${leaf} (node=${node}, kind=${kind}, code=[${paths}])"$'\n'
done < <(list_leaves)

inbox_entries=$(cat "$INBOX")

cat <<EOF
=== INBOX CLASSIFICATION ===

Each bullet in INBOX below is a source path that was edited this
session but matched no existing node. For each, decide one of:

  - existing-node  → the path clearly belongs to an existing node.
                     Action: Edit that node's frontmatter `code:` list
                     to include the new path, then remove the bullet
                     from $INBOX.
  - new-node       → the path is significant enough to deserve its
                     own node. Action: ask the user via
                     AskUserQuestion before scaffolding; on approval
                     run new-node.sh and remove the bullet.
  - uncertain      → not enough signal. Action: leave the bullet in
                     place; surface to the user via AskUserQuestion.

EXISTING NODES:
${leaves_summary:-(none)}

INBOX ($INBOX):
$inbox_entries

After applying any confident matches and asking the user about the
rest, the next run of this script (next session or /done) will only
see whatever remains.
EOF
