#!/usr/bin/env bash
# Lint the aims layer over a Capsa capsule (.capsa/).
#
# Two tiers:
#   1. SCHEMA conformance — delegated to the vendored Capsa validator
#      (validator/validate.py). This is the source of truth for record
#      structure (frontmatter fields, enums, required code_globs, etc.).
#   2. aims BODY conventions the validator does not model, checked over
#      code insights only:
#        - literal code_globs entries resolve on disk
#        - ADR-0028 four-section schema (## Purpose / ## Invariants & gotchas
#          / ## Pointers / ## Deltas) in order
#        - delta compaction due (>= AIMS_MEMORY_DELTA_MAX)
#        - no non-portable (absolute / same-repo-URL) pointers
#        - every SHA cited in a delta is a real commit touching a code_glob
#        - body size caps (ADR-0008)
#
# Reports issues to stdout, one per line. Exit code 0 (informational).
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

Runs the Capsa validator over .capsa/ (schema conformance) and then checks
the aims body conventions over code insights. Always exits 0.
EOF
  exit 0
fi

issues=0

# ── Tier 1: Capsa schema conformance (delegated) ─────────────────────────
VALIDATOR="${AIMS_VALIDATOR:-validator/validate.py}"
if [ -r "$VALIDATOR" ] && command -v python3 >/dev/null 2>&1; then
  vout=$(python3 "$VALIDATOR" "$CAPSA_DIR" 2>&1 || true)
  case "$vout" in
    *"conforming capsule"*) : ;;   # ✔
    *)
      while IFS= read -r line; do
        [ -z "$line" ] && continue
        printf 'capsule schema: %s\n' "$line"
        issues=$((issues + 1))
      done <<< "$vout"
      ;;
  esac
fi

# Derive this repo's URL prefix so we can flag pointers that round-trip
# through a host instead of staying repo-relative.
REPO_URL_PREFIX=""
if command -v git >/dev/null 2>&1 \
   && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  origin=$(git remote get-url origin 2>/dev/null || true)
  case "$origin" in
    git@*:*)
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

# ── Tier 2: aims body conventions over code insights ─────────────────────
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  [ "$(fm_get "$leaf" kind)" = "code" ] || continue

  # code_globs: literal entries must resolve; glob patterns are skipped
  # (they legitimately may match nothing at a given moment).
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="${p%%:*}"   # strip :start-end if present
    case "$base" in
      *'*'*|*'?'*|*'['*) continue ;;   # glob pattern — don't existence-check
    esac
    if ! [ -e "$base" ]; then
      printf '%s: code_globs path missing: %s\n' "$leaf" "$p"
      issues=$((issues + 1))
    fi
  done < <(insight_globs "$leaf")

  # ADR-0028 section checks: exactly four body sections in order.
  EXPECTED='## Purpose|## Invariants & gotchas|## Pointers|## Deltas|'
  actual=$(grep -E '^## ' "$leaf" | tr '\n' '|')
  if [ "$actual" != "$EXPECTED" ]; then
    printf '%s: section headings/order wrong (got: %s)\n' "$leaf" "$actual"
    issues=$((issues + 1))
  fi

  # ADR-0028 compaction due: informational.
  DELTA_MAX="${AIMS_MEMORY_DELTA_MAX:-12}"
  n_deltas=$(awk '/^## Deltas/{d=1;next} /^## /{d=0} d && /^- /{n++} END{print n+0}' "$leaf")
  if [ "$n_deltas" -ge "$DELTA_MAX" ]; then
    printf '%s: warning: %d delta lines (>= %d) — compaction due at next consolidation\n' \
      "$leaf" "$n_deltas" "$DELTA_MAX"
  fi

  # ADR-0028 portability: no absolute paths under ## Pointers / ## Deltas.
  bad=$(awk '
    /^## Pointers/      { in_section=1; next }
    /^## Deltas/        { in_section=1; next }
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
      /^## Deltas/        { in_section=1; next }
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

  # ADR-0028 delta commit validity: every SHA cited in a delta line must be
  # a real commit that touches at least one literal path from code_globs.
  if command -v git >/dev/null 2>&1 \
     && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    mapfile -t NODE_CODE < <(insight_globs "$leaf" | sed 's/:.*//')
    while IFS= read -r sha; do
      [ -z "$sha" ] && continue
      if ! git cat-file -e "$sha" 2>/dev/null; then
        printf '%s: delta commit not in git: %s (shallow clone?)\n' "$leaf" "$sha"
        issues=$((issues + 1))
        continue
      fi
      touched=$(git show --name-only --format= "$sha" 2>/dev/null)
      hit=0
      for c in "${NODE_CODE[@]}"; do
        [ -z "$c" ] && continue
        case "$c" in *'*'*|*'?'*|*'['*) continue ;; esac
        if printf '%s\n' "$touched" | grep -qxF -- "$c"; then
          hit=1; break
        fi
      done
      if [ "$hit" -eq 0 ]; then
        printf '%s: delta commit %s does not touch any code_globs path\n' "$leaf" "$sha"
        issues=$((issues + 1))
      fi
    done < <(awk '
      /^## Deltas/ { in_section=1; next }
      /^## /       { in_section=0 }
      in_section && /^- / { print }
    ' "$leaf" | grep -oE '\b[0-9a-f]{7,40}\b' | sort -u)
  fi

  # Size cap (ADR-0008). Informational.
  end=$(fm_end_line "$leaf")
  body_lines=$(awk -v e="$end" 'NR>e' "$leaf" | wc -l | tr -d ' ')
  if [ "$body_lines" -gt 200 ]; then
    printf '%s: CRITICAL: body is %d lines (>200) — split or extract subtopics\n' "$leaf" "$body_lines"
    issues=$((issues + 1))
  elif [ "$body_lines" -gt 150 ]; then
    printf '%s: warning: body is %d lines (>150) — consider splitting at next consolidation\n' "$leaf" "$body_lines"
  fi
done < <(list_insights)

if [ "$issues" -eq 0 ]; then
  printf '[aims-memory] lint: clean (%d insights)\n' "$(list_insights | wc -l)" >&2
fi

exit 0
