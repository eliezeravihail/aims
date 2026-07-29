#!/usr/bin/env bash
# Shared helpers for the aims tooling over a Capsa capsule (.capsa/).
# Sourced (not executed) by mark.sh, find-dirty.sh, the hooks, etc.
#
# aims is the ACTIVE self-maintenance layer; the capsule is PASSIVE data
# (Capsa 0.2.0). Durable truth lives in .capsa/ records; aims' own run-state
# (staleness cache, throttle, injection dedup) lives OUTSIDE the capsule under
# .claude/ (Capsa §1.5). "Stale" is COMPUTED from an insight's `updated:` date
# vs. git, never stored as a flag (Capsa §1.4).
#
# POSIX-friendly: only features available in mawk/BSD awk.

set -u

CAPSA_DIR="${AIMS_CAPSA_DIR:-.capsa}"
INSIGHTS_DIR="${AIMS_INSIGHTS_DIR:-$CAPSA_DIR/insights}"
PLANS_DIR="${AIMS_PLAN_DIR:-$CAPSA_DIR/plans}"
DECISIONS_DIR="${AIMS_DECISIONS_DIR:-$CAPSA_DIR/decisions}"
# Back-compat alias — some callers still guard on MEMORY_DIR.
MEMORY_DIR="$INSIGHTS_DIR"
# aims run-state (never inside the capsule).
STATE_DIR="${AIMS_STATE_DIR:-.claude/aims-state}"
INBOX="${AIMS_INBOX:-$STATE_DIR/inbox.md}"

# Strip surrounding whitespace and a single layer of matching ' or ".
_strip_quotes_ws() {
  awk '{
    sub(/^[ \t]+/, ""); sub(/[ \t]+$/, "");
    if ((substr($0,1,1) == "\"" && substr($0,length($0),1) == "\"") ||
        (substr($0,1,1) == "'\''" && substr($0,length($0),1) == "'\''")) {
      $0 = substr($0, 2, length($0)-2);
    }
    print
  }'
}

# Print the line number where the closing `---` of the frontmatter sits.
# Prints "0" if the file has no frontmatter.
fm_end_line() {
  local f="$1"
  [ -r "$f" ] || { printf '0\n'; return; }
  awk '
    NR==1 && /^---$/ { in_fm=1; next }
    in_fm && /^---$/ { print NR; found=1; exit }
    END { if (!found) print 0 }
  ' "$f"
}

# Extract one frontmatter scalar value.
# Usage: fm_get <file> <key>  →  stdout: value (no quotes) or empty.
fm_get() {
  local f="$1" key="$2" end raw
  end=$(fm_end_line "$f")
  [ "$end" -le 1 ] && return
  raw=$(awk -v k="$key" -v end="$end" '
    NR>1 && NR<end {
      if (match($0, "^[ \t]*" k "[ \t]*:[ \t]*")) {
        v = substr($0, RSTART + RLENGTH)
        print v
        exit
      }
    }
  ' "$f")
  printf '%s' "$raw" | _strip_quotes_ws
}

# Set or insert a scalar frontmatter key. In-place via tempfile.
# Usage: fm_set <file> <key> <value>
fm_set() {
  local f="$1" key="$2" val="$3" end tmp
  end=$(fm_end_line "$f")
  [ "$end" -le 1 ] && return 1
  tmp=$(mktemp)
  chmod --reference="$f" "$tmp" 2>/dev/null \
    || { mode=$(stat -f '%Lp' "$f" 2>/dev/null); [ -n "$mode" ] && chmod "$mode" "$tmp" 2>/dev/null; } \
    || true
  awk -v k="$key" -v v="$val" -v end="$end" '
    BEGIN { set=0 }
    {
      if (NR>1 && NR<end && !set && match($0, "^[ \t]*" k "[ \t]*:")) {
        print k ": " v
        set=1
        next
      }
      if (NR==end && !set) {
        print k ": " v
      }
      print
    }
  ' "$f" > "$tmp" && mv "$tmp" "$f"
}

# Iterate paths in a frontmatter list key (one path per line).
# Handles inline (`code_globs: ["a", "b"]`) and block (`key:\n  - a`) lists,
# and block-object form (`- { path: x }`).
# Usage: fm_list <file> <key>
fm_list() {
  local f="$1" key="$2" end
  end=$(fm_end_line "$f")
  [ "$end" -le 1 ] && return
  awk -v k="$key" -v end="$end" '
    function trim_quotes(v,    c1, c2, L) {
      L = length(v)
      if (L < 2) return v
      c1 = substr(v, 1, 1); c2 = substr(v, L, 1)
      if ((c1 == "\"" && c2 == "\"") || (c1 == "'\''" && c2 == "'\''")) {
        return substr(v, 2, L-2)
      }
      return v
    }
    function trim_ws(v) {
      sub(/^[ \t]+/, "", v); sub(/[ \t]+$/, "", v); return v
    }
    NR>1 && NR<end {
      if (in_block) {
        if (match($0, /^[ \t]+-[ \t]+/)) {
          v = substr($0, RSTART + RLENGTH)
          v = trim_ws(v)
          if (match(v, /path[ \t]*:[ \t]*[^,}]+/)) {
            obj = substr(v, RSTART, RLENGTH)
            sub(/^path[ \t]*:[ \t]*/, "", obj)
            v = trim_ws(obj)
          }
          v = trim_quotes(v)
          if (v != "") print v
          next
        }
        if ($0 !~ /^[ \t]/) in_block = 0
      }
      if (match($0, "^[ \t]*" k "[ \t]*:[ \t]*")) {
        rest = substr($0, RSTART + RLENGTH)
        rest = trim_ws(rest)
        if (rest == "" ) {
          in_block = 1
          next
        }
        if (substr(rest, 1, 1) == "[" && substr(rest, length(rest), 1) == "]") {
          inner = substr(rest, 2, length(rest)-2)
          n = split(inner, parts, ",")
          for (i=1; i<=n; i++) {
            v = trim_ws(parts[i])
            v = trim_quotes(v)
            if (v != "") print v
          }
          in_block = 0
        }
      }
    }
  ' "$f"
}

# Now in ISO-8601 UTC / date-only.
now_iso() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
today()   { date -u +'%Y-%m-%d'; }

# True if the haystack glob matches the needle path (fnmatch; ADR-0014).
path_matches() {
  local needle="$1" hay="$2"
  local hay_path="${hay%%:*}"
  [ "$needle" = "$hay" ] && return 0
  case "$hay" in "$needle":*) return 0 ;; esac
  # shellcheck disable=SC2254
  case "$needle" in $hay_path) return 0 ;; esac
  case "$needle" in
    /*)
      local root rel
      root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
      case "$needle" in
        "$root"/*)
          rel="${needle#$root/}"
          [ "$rel" = "$hay" ] && return 0
          case "$hay" in "$rel":*) return 0 ;; esac
          # shellcheck disable=SC2254
          case "$rel" in $hay_path) return 0 ;; esac
          ;;
      esac
      ;;
  esac
  return 1
}

# Escape a string for embedding inside a JSON string literal (ADR-0025).
json_escape() {
  printf '%s' "$1" | awk '
    BEGIN { for (i=0; i<256; i++) ord[sprintf("%c", i)] = i; first = 1 }
    {
      if (!first) printf "\\n"
      first = 0
      for (i = 1; i <= length($0); i++) {
        c = substr($0, i, 1); n = ord[c]
        if      (c == "\\") printf "\\\\"
        else if (c == "\"") printf "\\\""
        else if (n == 8)    printf "\\b"
        else if (n == 9)    printf "\\t"
        else if (n == 10)   printf "\\n"
        else if (n == 12)   printf "\\f"
        else if (n == 13)   printf "\\r"
        else if (n < 32)    printf "\\u%04x", n
        else                printf "%s", c
      }
    }
  '
}

# ── Capsa insight helpers ────────────────────────────────────────────────

# Iterate every insight record (insights/{code,dev,design}/*.md). One per line.
list_insights() {
  [ -d "$INSIGHTS_DIR" ] || return
  local sub
  for sub in code dev design; do
    [ -d "$INSIGHTS_DIR/$sub" ] || continue
    find "$INSIGHTS_DIR/$sub" -type f -name '*.md' 2>/dev/null
  done | sort
}
# Back-compat alias.
list_leaves() { list_insights; }

# The code_globs of an insight (empty for dev/design).
insight_globs() { fm_list "$1" code_globs; }

# Parse an insight's freshness anchor (`updated:` else `created:`) to epoch
# seconds. 0 if unparseable.
insight_updated_epoch() {
  local f="$1" d
  d=$(fm_get "$f" updated)
  if [ -z "$d" ] || [ "$d" = "null" ]; then d=$(fm_get "$f" created); fi
  d="${d:0:10}"
  [ -n "$d" ] || { printf '0\n'; return; }
  date -u -d "$d" +%s 2>/dev/null \
    || date -u -j -f '%Y-%m-%d' "$d" +%s 2>/dev/null \
    || printf '0\n'
}

# COMPUTED staleness (no stored flag; Capsa §1.4). An insight is stale iff one
# of its code_globs has a committed change newer than `updated:`, or an
# uncommitted change, or (no git) a file mtime newer than `updated:`.
# Exit 0 = stale, 1 = fresh. dev/design insights (no globs) are never stale.
insight_stale() {
  local f="$1" up g last in_git=0 p m
  up=$(insight_updated_epoch "$f")
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 && in_git=1
  while IFS= read -r g; do
    [ -z "$g" ] && continue
    g="${g%%:*}"
    if [ "$in_git" -eq 1 ]; then
      if [ -n "$(git status --porcelain -- "$g" 2>/dev/null)" ]; then
        return 0
      fi
      last=$(git log -1 --format=%ct -- "$g" 2>/dev/null || echo 0)
      case "$last" in ''|*[!0-9]*) last=0 ;; esac
      [ "$last" -gt "$up" ] && return 0
    else
      for p in $g; do
        [ -e "$p" ] || continue
        m=$(stat -c %Y "$p" 2>/dev/null || stat -f %m "$p" 2>/dev/null || echo 0)
        [ "$m" -gt "$up" ] && return 0
      done
    fi
  done < <(insight_globs "$f")
  return 1
}

# ── Plan helpers (Capsa plans: `status:` is a frontmatter field) ─────────

# The status of a plan record, from frontmatter.
plan_status() { fm_get "$1" status; }

# Print plan files whose frontmatter status == $2, from directory $1.
plans_with_status() {
  local d="$1" want="$2" f
  [ -d "$d" ] || return
  for f in "$d"/*.md; do
    [ -e "$f" ] || continue
    [ "$(fm_get "$f" status)" = "$want" ] && printf '%s\n' "$f"
  done
}
