#!/usr/bin/env bash
# Build the inbox-classification prompt (no network call).
#
# Per ADR-0009, classification runs in-band: the Stop hook (or plan close-out)
# injects this prompt as additionalContext; the active Claude Code
# session classifies each entry and either Edits it into an existing
# insight's `code_globs`, scaffolds a new insight, or surfaces it via
# AskUserQuestion.
#
# The inbox lives OUTSIDE the capsule (.claude/, Capsa §1.5) — it is aims
# run-state, not a durable record.
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

Emits a prompt for in-band classification of the inbox entries. Pure
bash, no LLM call. Empty stdout if inbox is empty.
EOF
  exit 0
fi

[ -f "$INBOX" ] || exit 0
[ -s "$INBOX" ] || exit 0

leaves_summary=""
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  title=$(fm_get "$leaf" title)
  kind=$(fm_get "$leaf" kind)
  paths=$(insight_globs "$leaf" | tr '\n' ',' | sed 's/,$//')
  leaves_summary+="- ${leaf} (title=${title}, kind=${kind}, code_globs=[${paths}])"$'\n'
done < <(list_insights)

inbox_entries=$(cat "$INBOX")

cat <<EOF
=== INBOX CLASSIFICATION ===

Each bullet in INBOX below is a source path that was edited this
session but matched no existing insight's code_globs. For each, decide
one of:

  - existing-insight → the path clearly belongs to an existing insight.
                     Action: Edit that insight's frontmatter `code_globs`
                     to include the new path, then remove the bullet
                     from $INBOX.
  - new-insight    → the path is significant enough to deserve its
                     own insight. Action: ask the user via
                     AskUserQuestion before scaffolding; on approval
                     run new-insight.sh and remove the bullet.
  - uncertain      → not enough signal. Action: leave the bullet in
                     place; surface to the user via AskUserQuestion.

EXISTING INSIGHTS:
${leaves_summary:-(none)}

INBOX ($INBOX):
$inbox_entries

After applying any confident matches and asking the user about the
rest, the next run of this script (next session or plan close-out) will only
see whatever remains.
EOF
