#!/usr/bin/env bash
# Lint the memory tree.
# For every leaf, verify that:
#   - each path in `code:` exists on disk
#   - each path in `external_refs:` exists on disk
#   - each `claude_md_refs:` heading exists in CLAUDE.md
# Reports orphans to stdout, one per line.  Exit code 0 (informational).
#
# Usage:  lint.sh

set -u

# L4: lint.sh uses mapfile and declare -A. bash 3.2 lacks both.
if (( BASH_VERSINFO[0] < 4 )); then
  printf '[aims] lint.sh: bash >= 4 required; current is %s. Skipping.\n' \
    "$BASH_VERSION" >&2
  exit 0
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: lint.sh

Walks every leaf under docs/memory/ and reports references that do
not resolve on disk. Always exits 0.
EOF
  exit 0
fi

CLAUDE_MD="${AIMS_CLAUDE_MD:-CLAUDE.md}"

# Derive this repo's URL prefix (host/org/repo) so we can flag pointers
# that round-trip through a host instead of staying repo-relative.
REPO_URL_PREFIX=""
if command -v git >/dev/null 2>&1 \
   && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  origin=$(git remote get-url origin 2>/dev/null || true)
  case "$origin" in
    git@*:*)         # SSH form: git@github.com:org/repo.git
      host="${origin#git@}"; host="${host%%:*}"
      path="${origin#*:}"; path="${path%.git}"
      REPO_URL_PREFIX="${host}/${path}"
      ;;
    https://*|http://*)
      stripped="${origin%.git}"
      REPO_URL_PREFIX="${stripped#http*://}"
      ;;
  esac
fi

# Collect CLAUDE.md headings (without leading #s).
declare -A CLAUDE_HEADINGS=()
if [ -r "$CLAUDE_MD" ]; then
  while IFS= read -r h; do
    [ -z "$h" ] && continue
    CLAUDE_HEADINGS["$h"]=1
  done < <(awk '/^#+ /{ sub(/^#+ +/, ""); print }' "$CLAUDE_MD")
fi

issues=0

while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue

  # code: paths
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="${p%%:*}"   # strip :start-end if present
    if ! [ -e "$base" ]; then
      printf '%s: code path missing: %s\n' "$leaf" "$p"
      issues=$((issues + 1))
    fi
  done < <(fm_list "$leaf" code)

  # Inert-node check: a `module` node with no code: globs can never be
  # flagged dirty by post-edit-marker, so it never consolidates.
  if [ "$(fm_get "$leaf" kind)" = "module" ] && [ -z "$(fm_list "$leaf" code)" ]; then
    printf '%s: inert node — code: [] (module not tracked by post-edit-marker)\n' "$leaf"
    issues=$((issues + 1))
  fi

  # external_refs: paths (already reduced to just the path by fm_list)
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    # Expand ~ for files under the user's home.
    case "$p" in
      "~/"*) p="${HOME}/${p#~/}" ;;
      "~") p="${HOME}" ;;
    esac
    if ! [ -e "$p" ]; then
      printf '%s: external_ref missing: %s\n' "$leaf" "$p"
      issues=$((issues + 1))
    fi
  done < <(fm_list "$leaf" external_refs)

  # claude_md_refs: headings
  while IFS= read -r h; do
    [ -z "$h" ] && continue
    if [ -z "${CLAUDE_HEADINGS[$h]+x}" ]; then
      printf '%s: claude_md_ref missing in %s: %s\n' "$leaf" "$CLAUDE_MD" "$h"
      issues=$((issues + 1))
    fi
  done < <(fm_list "$leaf" claude_md_refs)

  # parents: / children: must resolve on disk (repo-relative).
  for field in parents children; do
    while IFS= read -r p; do
      [ -z "$p" ] && continue
      if ! [ -e "$p" ]; then
        printf '%s: %s entry missing: %s\n' "$leaf" "$field" "$p"
        issues=$((issues + 1))
      fi
    done < <(fm_list "$leaf" "$field")
  done

  # ADR-0008 section checks: exactly six body sections in order.
  EXPECTED='## Purpose|## Design rationale|## Invariants & gotchas|## Known issues|## Pointers|## Open questions|'
  actual=$(grep -E '^## ' "$leaf" | tr '\n' '|')
  if [ "$actual" != "$EXPECTED" ]; then
    printf '%s: section headings/order wrong (got: %s)\n' "$leaf" "$actual"
    issues=$((issues + 1))
  fi

  # ADR-0008 portability: no absolute paths under ## Pointers / ## Known issues.
  bad=$(awk '
    /^## Pointers/      { in_section=1; next }
    /^## Known issues/  { in_section=1; next }
    /^## /              { in_section=0 }
    in_section && /(^|[[:space:]])(\/|~\/)[A-Za-z0-9._-]/ { print NR": "$0 }
  ' "$leaf")
  if [ -n "$bad" ]; then
    while IFS= read -r line; do
      printf '%s: non-portable pointer: %s\n' "$leaf" "$line"
      issues=$((issues + 1))
    done <<<"$bad"
  fi

  # ADR-0008 portability: no URL pointing back into this repo's own remote.
  if [ -n "${REPO_URL_PREFIX:-}" ]; then
    bad_url=$(awk -v pre="$REPO_URL_PREFIX" '
      /^## Pointers/      { in_section=1; next }
      /^## Known issues/  { in_section=1; next }
      /^## /              { in_section=0 }
      in_section && index($0, pre) > 0 { print NR": "$0 }
    ' "$leaf")
    if [ -n "$bad_url" ]; then
      while IFS= read -r line; do
        printf '%s: host-bound URL to same repo: %s\n' "$leaf" "$line"
        issues=$((issues + 1))
      done <<<"$bad_url"
    fi
  fi

  # ADR-0008 known-issues commit validity: every fixed-bug SHA must be a
  # real commit that touches at least one path from this node's `code:`.
  if command -v git >/dev/null 2>&1 \
     && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # Gather node's code paths once (strip :line ranges).
    mapfile -t NODE_CODE < <(fm_list "$leaf" code | sed 's/:.*//')
    # L1: process substitution instead of a pipeline so `issues` updates
    # land in the parent shell. Also: the missing-commit branch now
    # actually increments issues (previously fell through silently).
    while IFS= read -r sha; do
      [ -z "$sha" ] && continue
      if ! git cat-file -e "$sha" 2>/dev/null; then
        printf '%s: fixed-bug commit not in git: %s (shallow clone?)\n' "$leaf" "$sha"
        issues=$((issues + 1))
        continue
      fi
      touched=$(git show --name-only --format= "$sha" 2>/dev/null)
      hit=0
      for c in "${NODE_CODE[@]}"; do
        [ -z "$c" ] && continue
        if printf '%s\n' "$touched" | grep -qxF -- "$c"; then
          hit=1; break
        fi
      done
      if [ "$hit" -eq 0 ]; then
        printf '%s: fixed-bug commit %s does not touch any code: path\n' "$leaf" "$sha"
        issues=$((issues + 1))
      fi
    done < <(awk '
      /^## Known issues/ { in_section=1; next }
      /^## /             { in_section=0 }
      in_section && /^- *fixed:/ { print }
    ' "$leaf" | grep -oE '[0-9a-f]{7,40}' | sort -u)
  fi

  # Size cap (inspired by project-bedrock's memory-compaction skill —
  # https://github.com/robotaitai/project-bedrock). Bedrock warns at ~150
  # body lines (excluding frontmatter) and treats >200 as CRITICAL. Both
  # are informational; the model decides whether to split or extract.
  end=$(fm_end_line "$leaf")
  body_lines=$(awk -v e="$end" 'NR>e' "$leaf" | wc -l | tr -d ' ')
  if [ "$body_lines" -gt 200 ]; then
    printf '%s: CRITICAL: body is %d lines (>200) — split or extract subtopics\n' "$leaf" "$body_lines"
    issues=$((issues + 1))
  elif [ "$body_lines" -gt 150 ]; then
    printf '%s: warning: body is %d lines (>150) — consider splitting at next consolidation\n' "$leaf" "$body_lines"
  fi
done < <(list_leaves)

# DAG acyclicity: follow parents: upward from each node; if we revisit
# a node, report a cycle. O(N^2) worst case — fine for hundreds of nodes.
while IFS= read -r start; do
  [ -z "$start" ] && continue
  declare -A seen=()
  seen["$start"]=1
  frontier=("$start")
  while [ "${#frontier[@]}" -gt 0 ]; do
    next=()
    for n in "${frontier[@]}"; do
      while IFS= read -r p; do
        [ -z "$p" ] && continue
        # Only follow parents that are themselves memory nodes (in docs/memory).
        case "$p" in
          docs/memory/*) ;;
          *) continue ;;
        esac
        if [ -n "${seen[$p]+x}" ]; then
          printf '%s: parent cycle through %s\n' "$start" "$p"
          issues=$((issues + 1))
          break 3
        fi
        seen["$p"]=1
        next+=("$p")
      done < <(fm_list "$n" parents 2>/dev/null)
    done
    frontier=("${next[@]}")
  done
  unset seen
done < <(list_leaves)

if [ "$issues" -eq 0 ]; then
  printf '[aims-memory] lint: clean (%d nodes)\n' "$(list_leaves | wc -l)" >&2
fi

exit 0
