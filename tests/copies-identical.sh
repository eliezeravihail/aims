#!/usr/bin/env bash
# Assert that aims's three distribution surfaces stay byte-identical:
#   templates/<dir>/*  ←→  .claude/<dir>/*  (dogfood install)
#   templates/commands/*  ←→  commands/*    (marketplace install)
#
# Why: the marketplace `commands/` copy is loaded by users who install
# aims as a plugin; the dogfooded `.claude/` copy is what the project
# itself runs. A drift between any pair means /install-on missed a
# refresh — the exact failure mode that produced audit finding M6
# (commands/install-on.md was missing the summary-language feature).

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
      printf '  MISSING: %s\n' "$g" >&2
      fail=$((fail + 1))
      continue
    fi
    if ! diff -q "$f" "$g" >/dev/null; then
      printf '  DIFFER:  %s vs %s\n' "$f" "$g" >&2
      diff -u "$f" "$g" | head -40 >&2
      fail=$((fail + 1))
    fi
  done
}

# Pair 1: hooks (templates/.claude dogfood)
check_pair templates/hooks   .claude/hooks   sh

# Pair 2: memory helpers
check_pair templates/memory  .claude/memory  sh

# Pair 3: slash commands — both dogfood (.claude/) and marketplace (commands/).
check_pair templates/commands .claude/commands md
for f in templates/commands/install-on.md templates/commands/plan.md; do
  g="commands/$(basename "$f")"
  if [ ! -f "$g" ]; then
    printf '  MISSING: %s\n' "$g" >&2
    fail=$((fail + 1))
    continue
  fi
  if ! diff -q "$f" "$g" >/dev/null; then
    printf '  DIFFER:  %s vs %s (marketplace copy)\n' "$f" "$g" >&2
    diff -u "$f" "$g" | head -20 >&2
    fail=$((fail + 1))
  fi
done

if [ "$fail" -eq 0 ]; then
  printf '[PASS] all paired copies identical\n'
  exit 0
fi
printf '[FAIL] %d divergence(s)\n' "$fail" >&2
exit 1
