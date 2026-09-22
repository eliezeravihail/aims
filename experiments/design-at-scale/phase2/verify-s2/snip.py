"""Blind check: a Markdown extension that includes another file; edit that file under `mkdocs serve --dirty`."""
import pathlib, shutil, socket, subprocess, sys, time, urllib.request, os
L = sys.argv[1]; D = pathlib.Path(f"/tmp/claude-0/phase2/judge-s2/design-{L}")
PY = "/tmp/claude-0/phase0/pristine/.venv/bin/python"
proj = pathlib.Path(f"/tmp/claude-0/phase2/verify-s2/snip-{L}"); shutil.rmtree(proj, ignore_errors=True)
(proj/"docs/en").mkdir(parents=True); (proj/"docs/fr").mkdir(parents=True)
(proj/"incl.py").write_text('''
import re, pathlib
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
class P(Preprocessor):
    def run(self, lines):
        out = []
        for l in lines:
            m = re.match(r"\\{\\{include:(.+)\\}\\}", l.strip())
            out.append(pathlib.Path("docs", m.group(1)).read_text().strip() if m else l)
        return out
class IncludeExtension(Extension):
    def extendMarkdown(self, md): md.preprocessors.register(P(md), "incl", 30)
def makeExtension(**kw): return IncludeExtension(**kw)
''')
(proj/"mkdocs.yml").write_text("site_name: S\nlanguages:\n  default: en\n  others: [fr]\nmarkdown_extensions:\n  - incl\n")
(proj/"docs/en/index.md").write_text("# Home\n\n{{include:en/snip.txt}}\n")
(proj/"docs/en/guide.md").write_text("# Guide\n\nG.\n")
(proj/"docs/fr/index.md").write_text("# Accueil\n\nFR.\n")
(proj/"docs/en/snip.txt").write_text("SNIPVONE\n")
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
env = dict(os.environ, PYTHONPATH=f"{D}:{proj}")
proc = subprocess.Popen([PY, "-m", "mkdocs", "serve", "--dirty", "-a", f"127.0.0.1:{port}"], cwd=proj, env=env,
                        stdout=subprocess.DEVNULL, stderr=open(proj/"serve.log", "w"))
def get(p):
    try: return urllib.request.urlopen(f"http://127.0.0.1:{port}{p}", timeout=3).read().decode()
    except Exception: return None
res = "server never answered"
try:
    for _ in range(80):
        time.sleep(0.5); b = get("/en/")
        if b and "SNIPVONE" in b: break
    if b and "SNIPVONE" in b:
        time.sleep(1.5); (proj/"docs/en/snip.txt").write_text("SNIPVTWO\n")
        res = "STALE after 30 s (page still shows the old include)"
        for _ in range(60):
            time.sleep(0.5); b = get("/en/")
            if b and "SNIPVTWO" in b: res = "updated"; break
finally:
    proc.terminate()
    try: proc.wait(timeout=10)
    except Exception: proc.kill()
print(L, "->", res)
