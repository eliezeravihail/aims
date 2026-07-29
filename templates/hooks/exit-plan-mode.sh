#!/usr/bin/env bash
# aims PostToolUse hook on ExitPlanMode — bridges the harness-mode plan
# presentation into a Capsa plan record (.capsa/plans/NNNN-slug.md) so the
# close-out + consolidation pipelines can see it.
#
# Triggered only when matcher: "ExitPlanMode" is wired in settings.json.
# Reads the harness's tool_input.plan from stdin (JSON payload), persists it
# as a conforming Capsa plan (frontmatter id/title/kind/status/opened) with
# status: in_progress so the normal /plan close-out logic picks it up.
# Never blocks; exits 0 always.

set -u

PLAN_DIR="${AIMS_PLAN_DIR:-.capsa/plans}"

# Shared helpers (fm_get) if available — used to read existing plan ids.
for _d in .claude/memory templates/memory; do
  [ -r "$_d/_lib.sh" ] && { . "$_d/_lib.sh"; break; }
done
command -v fm_get >/dev/null 2>&1 || fm_get() {
  awk -v k="$2" 'NR==1&&/^---$/{f=1;next} f&&/^---$/{exit}
    f&&$0 ~ "^"k":"{sub("^"k":[ \t]*","");gsub(/^["'\''"]|["'\''"]$/,"");print;exit}' "$1"
}

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
# Strip a leading "Plan:" label if the harness heading carried one.
title=$(printf '%s' "$title" | sed -E 's/^[Pp]lan:[[:space:]]*//')

slug=$(printf '%s' "$title" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -e 's/[^a-z0-9]\+/-/g' -e 's/^-//' -e 's/-$//' \
  | awk -F'-' '{
      n = (NF > 6) ? 6 : NF
      for (i=1; i<=n; i++) printf "%s%s", $i, (i<n ? "-" : "")
      print ""
    }')
[ -z "$slug" ] && slug="exit-plan-mode"

# Next plan id = max existing frontmatter id + 1 (Capsa ids are integers).
max_id=-1
for f in "$PLAN_DIR"/*.md; do
  [ -e "$f" ] || continue
  pid=$(fm_get "$f" id)
  case "$pid" in ''|*[!0-9]*) continue ;; esac
  [ "$pid" -gt "$max_id" ] && max_id="$pid"
done
next_id=$((max_id + 1))
printf -v num '%04d' "$next_id"

date_stamp=$(date -u +%Y-%m-%d)
file="$PLAN_DIR/$num-$slug.md"

# If /plan already wrote a file with the same slug today, do not overwrite.
if [ -e "$file" ]; then
  printf '[aims-exit-plan-mode] %s already exists; not overwriting.\n' "$file" >&2
  exit 0
fi
# Guard: same slug already present under a different id → skip (avoid dupes).
if ls "$PLAN_DIR"/*-"$slug".md >/dev/null 2>&1; then
  printf '[aims-exit-plan-mode] a plan with slug "%s" already exists; not duplicating.\n' "$slug" >&2
  exit 0
fi

# If the harness body already opens with a frontmatter block, keep it verbatim
# (assume the author wrote a conforming record); else synthesize one.
case "$body" in
  '---'*)
    printf '%s\n' "$body" > "$file"
    ;;
  *)
    {
      printf -- '---\n'
      printf 'id: %s\n' "$next_id"
      printf 'title: "%s"\n' "$(printf '%s' "$title" | sed 's/"/\\"/g')"
      printf 'kind: initiative\n'
      printf 'status: in_progress\n'
      printf 'opened: %s\n' "$date_stamp"
      printf 'completed: null\n'
      printf 'priority: null\n'
      printf 'target_date: null\n'
      printf 'milestone: null\n'
      printf 'requirement_refs: []\n'
      printf 'decision_refs: []\n'
      printf -- '---\n\n'
      printf '%s\n' "$body"
    } > "$file"
    ;;
esac

printf '[aims-exit-plan-mode] Wrote %s\n' "$file" >&2
exit 0
