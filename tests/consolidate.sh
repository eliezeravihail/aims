#!/usr/bin/env bash
# Smoke test for the Stop-hook consolidation path, using a tiny
# Python http.server as a mock Anthropic endpoint.
#
# Exits 0 on success, non-zero on first failure.

set -eu

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"; [ -n "${MOCK_PID:-}" ] && kill "$MOCK_PID" 2>/dev/null || true' EXIT

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

export AIMS_MEMORY_DIR="$TMP/memory"
export AIMS_MEMORY_STATE_FILE="$TMP/.last-consolidated"
export ANTHROPIC_API_KEY="dummy-test-key"

if ! command -v python3 >/dev/null 2>&1; then
  printf '[SKIP] python3 not available; skipping consolidate smoke test\n'
  exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
  printf '[SKIP] jq not available; skipping consolidate smoke test\n'
  exit 0
fi

# Start a mock Anthropic endpoint. It accepts a POST, reads the prompt,
# and echoes back a leaf whose `## Purpose` section reads "UPDATED BY
# MOCK". The mock just returns the original leaf body with that
# replacement so the frontmatter stays valid.
MOCK_LOG="$TMP/mock.log"
PORT=$((10000 + RANDOM % 50000))
python3 - "$PORT" "$MOCK_LOG" <<'PY' &
import sys, json, http.server, socketserver, re
PORT = int(sys.argv[1]); LOG = sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        with open(LOG, 'a') as f: f.write((fmt % args) + '\n')
    def do_POST(self):
        n = int(self.headers.get('content-length', 0))
        body = self.rfile.read(n).decode('utf-8', 'replace')
        try:
            req = json.loads(body)
            prompt = req['messages'][0]['content']
        except Exception:
            prompt = ''
        # Find the leaf body inside the prompt (between "CURRENT LEAF:" and
        # "DIFFS").  Fall back to a minimal valid leaf if not found.
        m = re.search(r'CURRENT LEAF:\n(.*?)\n\nDIFFS', prompt, re.S)
        leaf = m.group(1) if m else "---\nnode: x\nkind: module\n---\n## Purpose\n"
        # Mark the leaf body to prove the mock was used.
        leaf = leaf.replace("(One paragraph: what this leaf documents and why it deserves a home.)",
                            "UPDATED BY MOCK")
        out = {"content":[{"type":"text","text": leaf}]}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header('content-type','application/json')
        self.send_header('content-length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
with socketserver.TCPServer(('127.0.0.1', PORT), H) as srv:
    srv.serve_forever()
PY
MOCK_PID=$!
# Wait for the mock to be ready.
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s "http://127.0.0.1:$PORT" -o /dev/null; then break; fi
  sleep 0.1
done

export AIMS_ANTHROPIC_URL="http://127.0.0.1:$PORT/v1/messages"

# Seed a dirty leaf.
bash "$ROOT/templates/memory/new-leaf.sh" interface/foo module >/dev/null
LEAF="$AIMS_MEMORY_DIR/interface/foo.md"
python3 -c "
p='$LEAF'
s=open(p).read()
s=s.replace('code: []', 'code:\n  - src/foo.py')
s=s.replace('dirty: false', 'dirty: true', 1)
open(p,'w').write(s)
"

# Run the Stop hook with --force so the throttle is bypassed.
bash "$ROOT/templates/hooks/stop-consolidate.sh" --force 2>"$TMP/stop.err"

. "$ROOT/templates/memory/_lib.sh"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "false" ] || { cat "$TMP/stop.err"; fail "expected dirty=false after consolidate, got '$v'"; }
grep -q "UPDATED BY MOCK" "$LEAF" || { cat "$LEAF"; fail "leaf body was not updated by the mock"; }
pass "stop-consolidate.sh --force: dirty leaf consolidated via mock"

# Verify state file was written.
[ -r "$AIMS_MEMORY_STATE_FILE" ] || fail "state file not written"
pass "state file (.last-consolidated) updated"

# Run again with no dirty leaves — should exit fast, no API call.
mock_calls_before=$(wc -l < "$MOCK_LOG" 2>/dev/null || echo 0)
bash "$ROOT/templates/hooks/stop-consolidate.sh" --force
mock_calls_after=$(wc -l < "$MOCK_LOG" 2>/dev/null || echo 0)
[ "$mock_calls_before" = "$mock_calls_after" ] || \
  fail "stop hook called the API even though there were no dirty leaves"
pass "stop-consolidate.sh: no-op when N_DIRTY=0 (no API call)"

# Verify the throttle: 1 dirty leaf, default DIRTY_MAX=5, recent state
# file → should NOT consolidate.
python3 -c "
p='$LEAF'
s=open(p).read()
s=s.replace('dirty: false', 'dirty: true', 1)
open(p,'w').write(s)
"
mock_calls_before=$(wc -l < "$MOCK_LOG" 2>/dev/null || echo 0)
# state file mtime is fresh from the previous --force run.
AIMS_MEMORY_DIRTY_MAX=5 AIMS_MEMORY_INTERVAL_SEC=99999 \
  bash "$ROOT/templates/hooks/stop-consolidate.sh"
mock_calls_after=$(wc -l < "$MOCK_LOG" 2>/dev/null || echo 0)
[ "$mock_calls_before" = "$mock_calls_after" ] || \
  fail "stop hook called API despite throttle (1 dirty < 5, interval not elapsed)"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "true" ] || fail "leaf should still be dirty after throttled run, got '$v'"
pass "throttle blocks consolidation when N_DIRTY < threshold and interval recent"

printf '\nAll consolidate tests passed.\n'
