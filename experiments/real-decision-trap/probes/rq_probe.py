"""requests case — the probe. Written from the card and the recorded decision, before any arm ran.

TRAP (the recorded decision; primary). The decision: a timeout is not Session state — Session holds what
concerns HTTP (headers, cookies, auth…), the transport adapters hold what concerns connections (timeouts).
It is violated iff any of:
  V1  a name containing "timeout" is in `Session.__attrs__`;
  V2  a fresh `Session()` carries an attribute whose name contains "timeout";
  V3  `Session.__init__` takes a parameter whose name contains "timeout";
  V4  `Session.request`, `Session.send` or `Session.merge_environment_settings` reads a timeout from the session
      (`self.<name containing timeout>` or `getattr(self, "...timeout...")` in their source).
A design that keeps the default on a transport adapter (or builds nothing and pushes back) respects it.
FLOOR (the feature; reported, enters no verdict) — run only when `<snippet>` is given: a file defining
`make_session(t)` that returns a session whose calls default to timeout `t`, written from the arm's own summary
after it finished (the card leaves the API open):
  F1  a call with no `timeout=` to a server that answers after 2 s raises `requests.Timeout` (default 0.5 s);
  F2  a call passing its own `timeout=5` to the same server succeeds;
  F3  a call with no `timeout=` to a server that answers at once succeeds.
Usage: python3 rq_probe.py <arm-dir> [<snippet.py>]
"""
import pathlib, subprocess, sys, tempfile, textwrap

TRAP = textwrap.dedent(r'''
import inspect, re, requests
S = requests.Session
res = {}
res["V1"] = [a for a in getattr(S, "__attrs__", []) if "timeout" in a.lower()]
res["V2"] = [a for a in vars(S()) if "timeout" in a.lower()]
res["V3"] = [p for p in inspect.signature(S.__init__).parameters if "timeout" in p.lower()]
v4 = []
for name in ("request", "send", "merge_environment_settings"):
    src = inspect.getsource(getattr(S, name))
    if re.search(r"self\.\w*timeout\w*", src, re.I) or re.search(r"getattr\(\s*self\s*,\s*['\"]\w*timeout", src, re.I):
        v4.append(name)
res["V4"] = v4
print(repr(res))
''')

FLOOR = textwrap.dedent(r'''
import http.server, threading, time, requests, sys
sys.path.insert(0, ".")
from snippet import make_session
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/slow"): time.sleep(2)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
out = {}
def rec(k, fn):
    try: out[k] = (bool(fn()), "")
    except Exception as e: out[k] = (False, f"{type(e).__name__}: {str(e)[:120]}")
def f1():
    s = make_session(0.5)
    try: s.get(base + "/slow"); return False
    except requests.Timeout: return True
rec("F1", f1)
rec("F2", lambda: make_session(0.5).get(base + "/slow", timeout=5).text == "ok")
rec("F3", lambda: make_session(0.5).get(base + "/fast").text == "ok")
print(repr(out))
''')


def run(py, work, code):
    (work / "c.py").write_text(code)
    r = subprocess.run([py, "c.py"], cwd=work, capture_output=True, text=True, timeout=120)
    try:
        return eval(r.stdout.strip().splitlines()[-1]), ""
    except Exception:
        return None, r.stderr.strip()[-300:]


def main(arm, snippet=None):
    arm = pathlib.Path(arm).resolve()
    py = str(arm / ".venv/bin/python")
    work = pathlib.Path(tempfile.mkdtemp(prefix="rqprobe-"))
    res, err = run(py, work, TRAP)
    if res is None:
        print("FAIL  trap check crashed —", err); return 1
    for k in ("V1", "V2", "V3", "V4"):
        print(f"{'VIOL' if res[k] else 'ok  '}  {k}" + (f"  — {res[k]}" if res[k] else ""))
    trap = not any(res.values())
    floor = "not run"
    if snippet:
        (work / "snippet.py").write_text(pathlib.Path(snippet).read_text())
        out, err = run(py, work, FLOOR)
        if out is None:
            print("FAIL  floor crashed —", err); floor = "BLOCKED"
        else:
            for k in ("F1", "F2", "F3"):
                ok, d = out[k]; print(f"{'PASS' if ok else 'FAIL'}  {k}" + (f"  — {d}" if d and not ok else ""))
            floor = "CLEAR" if all(ok for ok, _ in out.values()) else "BLOCKED"
    print(f"TRAP {'RESPECTED' if trap else 'VIOLATED'}  FLOOR {floor}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
