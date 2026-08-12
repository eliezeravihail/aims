#!/usr/bin/env bash
# Assert that aims's distribution surfaces stay byte-identical:
#   templates/hooks/*      ←→  .claude/hooks/*        (dogfood install)
#   templates/commands/install-on.md ←→ .claude/commands/install-on.md ←→ commands/install-on.md
#
# The design-method slash commands (commands/aims-*.md) are plugin-marketplace commands loaded when
# aims is enabled as a plugin; they are not per-project installed, so they are not paired here. The
# memory subsystem this test used to check is gone (replaced by the capsa capsule + staleness hook).

set -u
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
fail=0

check_pair() {
  local src="$1" dst="$2" ext="$3"
  for f in "$src"/*."$ext"; do
    [ -f "$f" ] || continue
    g="$dst/$(basename "$f")"
    if [ ! -f "$g" ]; then
      printf '  MISSING: %s\n' "$g" >&2; fail=$((fail + 1)); continue
    fi
    if ! diff -q "$f" "$g" >/dev/null; then
      printf '  DIFFER:  %s vs %s\n' "$f" "$g" >&2
      diff -u "$f" "$g" | head -40 >&2
      fail=$((fail + 1))
    fi
  done
}

# Pair 1: hooks (templates ↔ dogfood .claude)
check_pair templates/hooks .claude/hooks sh

# Pair 2: install-on across template, dogfood, and marketplace copies.
for pair in "templates/commands/install-on.md:.claude/commands/install-on.md" \
            "templates/commands/install-on.md:commands/install-on.md"; do
  f="${pair%%:*}"; g="${pair##*:}"
  if [ ! -f "$g" ]; then
    printf '  MISSING: %s\n' "$g" >&2; fail=$((fail + 1)); continue
  fi
  if ! diff -q "$f" "$g" >/dev/null; then
    printf '  DIFFER:  %s vs %s\n' "$f" "$g" >&2
    diff -u "$f" "$g" | head -20 >&2
    fail=$((fail + 1))
  fi
done

if [ "$fail" -eq 0 ]; then
  printf '[PASS] all paired copies identical\n'; exit 0
fi
printf '[FAIL] %d divergence(s)\n' "$fail" >&2
exit 1
