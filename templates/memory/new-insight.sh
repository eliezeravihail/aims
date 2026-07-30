#!/usr/bin/env bash
# Scaffold a new Capsa insight record under .capsa/insights/{code,dev,design}/.
#
# Usage:  new-insight.sh <kind> <slug> "<title>" [code-glob ...]
#   <kind>       code | dev | design
#   <slug>       filename stem (no .md); e.g. hooks-session-start
#   <title>      human title (quote it)
#   [code-glob]  repo-relative paths/globs for `code_globs:`. REQUIRED
#                (>=1) when kind=code — a code insight with no globs can
#                never be flagged stale, so it never consolidates (and the
#                Capsa validator rejects it). Ignored for dev/design.
#
# Idempotent: refuses if the record already exists. "Stale" is computed from
# `updated:` vs git (Capsa §1.4); a fresh record gets updated: = created:.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 3 ]; then
  cat <<'EOF'
usage: new-insight.sh <kind> <slug> "<title>" [code-glob ...]

  <kind>   one of: code | dev | design
  <slug>   filename stem under .capsa/insights/<kind>/, no .md
  <title>  human title (quote it)
  globs    zero or more code_globs (>=1 required for kind=code)
EOF
  exit 0
fi

kind="$1"
slug="$2"
title="$3"
shift 3 2>/dev/null || shift "$#"
code_globs=("$@")

case "$kind" in
  code|dev|design) ;;
  *)
    printf 'error: kind must be one of code|dev|design (got %q)\n' "$kind" >&2
    exit 1 ;;
esac

if [ "$kind" = "code" ] && [ "${#code_globs[@]}" -eq 0 ]; then
  printf 'error: kind=code requires at least one code-glob (else it never consolidates)\n' >&2
  exit 1
fi

slug="${slug%.md}"
leaf="$INSIGHTS_DIR/$kind/$slug.md"
if [ -e "$leaf" ]; then
  printf 'error: insight already exists: %s\n' "$leaf" >&2
  exit 1
fi

# Build the code_globs frontmatter line (inline JSON-ish array, per migrated
# records). Only emit the key when non-empty (Capsa: absent is fine for
# dev/design; required non-empty only for kind=code).
GLOBS_FM=""
if [ "${#code_globs[@]}" -gt 0 ]; then
  inner=""
  for g in "${code_globs[@]}"; do
    [ -n "$inner" ] && inner+=", "
    inner+="\"$g\""
  done
  GLOBS_FM="code_globs: [$inner]"
fi

mkdir -p "$(dirname "$leaf")"
TODAY=$(today)

{
  printf -- '---\n'
  printf 'kind: %s\n' "$kind"
  printf 'title: "%s"\n' "$(printf '%s' "$title" | sed 's/"/\\"/g')"
  printf 'created: %s\n' "$TODAY"
  printf 'updated: %s\n' "$TODAY"
  [ -n "$GLOBS_FM" ] && printf '%s\n' "$GLOBS_FM"
  printf 'tags: []\n'
  printf -- '---\n'
  cat <<'BODY'

## Purpose

(One short paragraph: what this code does.)

## Invariants & gotchas

(What must not break when editing. Concise bullets.
Open design questions as `- open: …` bullets.)

## Pointers

(- ADR-NNNN — why it matters here)
(- .capsa/plans/NNNN-<slug>.md — plan that shaped this)
(- <SHA> — one-line  (anchor commits only))
(- External: <URL> — one-line  (issues, third-party docs))

## Deltas

(Appended by consolidation, newest last — ADR-0028:
- <commit-date>: <what changed and why it matters> — <SHA|ADR|plan-slug>)
BODY
} > "$leaf"

printf 'created: %s\n' "$leaf"
