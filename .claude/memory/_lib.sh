#!/usr/bin/env bash
# Shared helpers for the aims memory tree scripts.
# Sourced (not executed) by mark.sh, find-dirty.sh, etc.
#
# All helpers operate on the leaf schema defined in ADR-0007:
#   - Frontmatter delimited by `---` at lines 1 and N.
#   - Required keys: node, kind, code.
#   - System-managed keys: dirty, last_touched, last_consolidated.
#
# POSIX-friendly: only features available in mawk/BSD awk.
# No `match(str, re, arr)` (that's gawk-only); we use match()+RSTART+RLENGTH.

set -u

MEMORY_DIR="${AIMS_MEMORY_DIR:-docs/memory}"
INBOX="${MEMORY_DIR}/_inbox.md"

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
      # Match a line like:  <indent><key><space>:<space><value>
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
# Lists may be inline (`code: [a, b]`) or block (`code:\n  - a\n  - b`).
# For block-form objects (`- { path: x, kind: y }`) we extract `path`.
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
          # Inline-object form: { path: <p>, ... }
          if (match(v, /path[ \t]*:[ \t]*[^,}]+/)) {
            obj = substr(v, RSTART, RLENGTH)
            sub(/^path[ \t]*:[ \t]*/, "", obj)
            v = trim_ws(obj)
          }
          v = trim_quotes(v)
          if (v != "") print v
          next
        }
        # End of block when we see a non-indented line that is not a list item.
        if ($0 !~ /^[ \t]/) in_block = 0
      }
      if (match($0, "^[ \t]*" k "[ \t]*:[ \t]*")) {
        rest = substr($0, RSTART + RLENGTH)
        rest = trim_ws(rest)
        if (rest == "" ) {
          in_block = 1
          next
        }
        # Inline list: [a, b, c]
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

# Now in ISO-8601 UTC.
now_iso() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }

# True if the haystack matches the needle (exact, or needle is a prefix
# before a `:lineRange`). Lets src/bar.py match a `code:` entry of
# src/bar.py:10-30.
path_matches() {
  local needle="$1" hay="$2"
  [ "$needle" = "$hay" ] && return 0
  case "$hay" in
    "$needle":*) return 0 ;;
  esac
  return 1
}

# Iterate all leaf files (regular .md under MEMORY_DIR,
# excluding README.md and _inbox.md). One path per line.
list_leaves() {
  [ -d "$MEMORY_DIR" ] || return
  find "$MEMORY_DIR" -type f -name '*.md' \
    ! -name 'README.md' ! -name '_inbox.md' 2>/dev/null | sort
}
