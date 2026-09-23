#!/usr/bin/env bash
# Usage: run-hidden.sh <arm-dir> <stage:1|2>
# Copies the arm's promo.py to a scratch dir and runs the matching hidden tests
# against it (arm never sees the tests). Prints "N passed"/failures.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ARM="$1"; STAGE="$2"
SCR="$(mktemp -d)"
cp "$HERE/$ARM/promo.py" "$SCR/promo.py"
if [ "$STAGE" = "1" ]; then
  cp "$HERE/hidden/test_stage1.py" "$SCR/"
  ( cd "$SCR" && PROMO_MOD=promo python3 -m pytest test_stage1.py -q )
else
  cp "$HERE/hidden/test_stage1.py" "$SCR/"   # stage 2 must keep stage-1 green too
  cp "$HERE/hidden/test_stage2.py" "$SCR/"
  ( cd "$SCR" && PROMO_MOD=promo python3 -m pytest test_stage1.py test_stage2.py -q )
fi
rm -rf "$SCR"
