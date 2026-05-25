#!/usr/bin/env bash
# Scaffold a new memory leaf.
#
# Usage:  new-leaf.sh <node-path> <kind>
#   <node-path>  e.g. interface/auth/oauth-callback (NO .md suffix)
#   <kind>       module | decision | topic | runbook
#
# Idempotent: refuses if the leaf already exists.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 2 ]; then
  cat <<'EOF'
usage: new-leaf.sh <node-path> <kind>

  <node-path>  dotted/slash path under docs/memory/, no .md suffix
               e.g.  interface/auth/oauth-callback
  <kind>       one of: module | decision | topic | runbook
EOF
  exit 0
fi

node="$1"
kind="$2"

case "$kind" in
  module|decision|topic|runbook) ;;
  *)
    printf 'error: kind must be one of module|decision|topic|runbook (got %q)\n' "$kind" >&2
    exit 1 ;;
esac

# Strip any leading docs/memory/ and any .md the caller mistakenly added.
node="${node#"$MEMORY_DIR"/}"
node="${node%.md}"

leaf="$MEMORY_DIR/$node.md"
if [ -e "$leaf" ]; then
  printf 'error: leaf already exists: %s\n' "$leaf" >&2
  exit 1
fi

mkdir -p "$(dirname "$leaf")"
NOW=$(now_iso)

cat > "$leaf" <<EOF
---
node: $node
kind: $kind
code: []
commits: []
sessions: []
related: []
claude_md_refs: []
external_refs: []
owners: []
dirty: false
last_touched: $NOW
last_consolidated: $NOW
---

## Purpose

(One paragraph: what this leaf documents and why it deserves a home.)

## Logical rules & invariants

(What must always hold here? Constraints the code is built around.)

## Editing considerations

(What surprises a contributor editing the referenced code? Gotchas,
ordering requirements, things-not-to-do.)

## Deliberations & history

(Why is it like this? Choices made, alternatives rejected, links to
ADRs / plans / pivotal commits.)

## Open questions

(Things we deferred or don't know yet.)
EOF

printf 'created: %s\n' "$leaf"
