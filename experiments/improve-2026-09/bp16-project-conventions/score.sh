#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
for d in r1 r2 r3 n1 n2 n3; do
  echo "$d:"
  python3 "$HERE/probes/check.py" "$HERE/arms/$d" 2>&1 | sed 's/^/ /'
done
