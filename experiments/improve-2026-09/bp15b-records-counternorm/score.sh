#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
for d in r1 r2 r3 n1 n2 n3; do
  [ -f "$HERE/arms/$d/payouts.py" ] || { echo "$d: (missing)"; continue; }
  w=$(mktemp -d); cp "$HERE/arms/$d/payouts.py" "$w/payouts.py"; cp "$HERE/probes/probe_decisions.py" "$w/"
  out=$( cd "$w" && PAY_MOD=payouts python3 probe_decisions.py 2>&1 )
  echo "$d: $(echo "$out" | grep -o 'SURVIVED [0-9]*/[0-9]*')"
  echo "$out" | grep '^FAIL' | sed 's/^FAIL /   x /'
  rm -rf "$w"
done
