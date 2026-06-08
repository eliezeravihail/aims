#!/usr/bin/env bash
# Scaffold a new memory leaf.
#
# Usage:  new-node.sh <node-path> <kind> [code-glob ...]
#   <node-path>  e.g. interface/auth/oauth-callback (NO .md suffix)
#   <kind>       module | decision | topic | runbook
#   [code-glob]  zero or more repo-relative paths/globs for `code:`.
#                A `module` node should ALWAYS get >=1 — without it the
#                post-edit-marker can never flag the node dirty, so it
#                never consolidates.
#
# Idempotent: refuses if the leaf already exists.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 2 ]; then
  cat <<'EOF'
usage: new-node.sh <node-path> <kind>

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

shift 2 2>/dev/null || shift "$#"   # remaining args = code: globs
code_globs=("$@")

if [ "${#code_globs[@]}" -eq 0 ]; then
  CODE_FM="code: []"
else
  CODE_FM=$(printf 'code:\n'; printf '  - %s\n' "${code_globs[@]}")
fi

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
$CODE_FM
commits: []
sessions: []
parents: []
children: []
related: []
claude_md_refs: []
external_refs: []
owners: []
dirty: false
last_touched: $NOW
last_consolidated: $NOW
---

## Purpose

(One paragraph: what this code does.)

## Design rationale

(2–4 bullets: why it is shaped this way. Each bullet may end with a
repo-relative pointer — ADR-NNNN, commit SHA, plan slug.)

## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

(Invariants/gotchas — what must not break when editing. Concise.)

## Known issues

(- open:  one-line — pointer: commit SHA / repo-relative file:line / external URL)
(- fixed: one-line: what broke and why — commit SHA)

## Pointers

(- ADRs:     ADR-NNNN)
(- Plans:    docs/plans/<slug>.md (in-progress | done))
(- Commits:  <SHA> — one-line  (anchor commits only))
(- External: <URL> — one-line  (Slack threads, issues, third-party docs))

## Open questions

(Design questions not yet decided. Distinct from bugs.)
EOF

printf 'created: %s\n' "$leaf"
