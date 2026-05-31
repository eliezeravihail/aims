#!/usr/bin/env bash
# aims PostToolUse hook on ExitPlanMode — bridges the harness-mode
# plan presentation into a docs/plans/ file so close-out + memory
# consolidation pipelines can see it.
#
# Triggered only when matcher: "ExitPlanMode" is wired in settings.json.
# Reads the harness's tool_input.plan from stdin (JSON payload), persists
# it as docs/plans/<UTC-date>-<slug>.md with Status: in-progress so the
# normal /plan close-out logic picks it up. Never blocks; exits 0 always.

set -u

PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"

payload=$(cat || true)
[ -z "$payload" ] && exit 0

if command -v jq >/dev/null 2>&1; then
  body=$(printf '%s' "$payload" | jq -r '.tool_input.plan // empty' 2>/dev/null || true)
else
  body=$(printf '%s' "$payload" | sed -n 's/.*"plan"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')
fi
[ -z "$body" ] && exit 0

mkdir -p "$PLAN_DIR" 2>/dev/null || exit 0

title=$(printf '%s\n' "$body" | awk '
  /^#[[:space:]]+/ { sub(/^#[[:space:]]+/, ""); print; exit }
  NF              { print; exit }
' | head -c 200)
[ -z "$title" ] && title="exit-plan-mode"

slug=$(printf '%s' "$title" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -e 's/[^a-z0-9]\+/-/g' -e 's/^-//' -e 's/-$//' \
  | awk -F'-' '{
      n = (NF > 6) ? 6 : NF
      for (i=1; i<=n; i++) printf "%s%s", $i, (i<n ? "-" : "")
      print ""
    }')
[ -z "$slug" ] && slug="exit-plan-mode"

date_stamp=$(date -u +%Y-%m-%d)
file="$PLAN_DIR/$date_stamp-$slug.md"

# If /plan already wrote a file with the same slug today, do not overwrite.
if [ -e "$file" ]; then
  printf '[aims-exit-plan-mode] %s already exists; not overwriting.\n' "$file" >&2
  exit 0
fi

# Prepend frontmatter only if body does not start with one already.
case "$body" in
  '# Plan:'*|'#Plan:'*) header="" ;;
  *)                    header="# Plan: $title"$'\n' ;;
esac

{
  printf '%s' "$header"
  printf 'Status: in-progress\n'
  printf 'Started: %s\n\n' "$date_stamp"
  printf '%s\n' "$body"
} > "$file"

printf '[aims-exit-plan-mode] Wrote %s\n' "$file" >&2
exit 0
