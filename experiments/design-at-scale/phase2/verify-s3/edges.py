"""Blind check of the simplicity judge's §1 edge findings, on every design."""
import base64, pathlib, re, shutil, subprocess, sys, os
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
L, udu = sys.argv[1], sys.argv[2] == "1"
root = pathlib.Path(f"/tmp/claude-0/phase2/verify-s3/edge-{L}-{int(udu)}"); shutil.rmtree(root, ignore_errors=True)
files = {
 "mkdocs.yml": "site_name: S\nlanguages:\n  default: en\n  others: [fr]\n" + ("" if udu else "use_directory_urls: false\n"),
 "docs/en/index.md": "# Home\n\nHOMEBODY [to deep](sub/index.md) [dir link](sub/)\n",
 "docs/en/qa.md": "# Q & A\n\nQABODY\n",
 "docs/en/art.md": '# Art\n\n<svg width="10" height="10"><defs><linearGradient id="g"><stop offset="0"/></linearGradient></defs><rect width="10" height="10" fill="url(#g)"/></svg>\n\n<style>.bg { background: url(img/pic.png); }</style>\n\n<img src="img/pic.png" srcset="img/pic.png 2x" alt="p">\n',
 "docs/en/sub/index.md": "# Deep\n\nDEEPBODY\n",
 "docs/fr/index.md": "# Accueil\n\nFRHOME\n",
}
for rel, t in files.items():
    p = root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
for lang in ("en", "fr"):
    (root/f"docs/{lang}/img").mkdir(parents=True, exist_ok=True); (root/f"docs/{lang}/img/pic.png").write_bytes(PNG)
env = dict(os.environ, PYTHONPATH=f"/tmp/claude-0/phase2/judge-s3/design-{L}")
r = subprocess.run(["/tmp/claude-0/phase0/pristine/.venv/bin/python", "-m", "mkdocs", "export"], cwd=root, env=env, capture_output=True, text=True)
outs = [p for p in root.rglob("*.html") if "docs" not in p.relative_to(root).parts]
en = next((p.read_text() for p in outs if "HOMEBODY" in p.read_text()), None)
if en is None: print(L, int(udu), "no en export; rc", r.returncode, r.stderr.strip().splitlines()[-1:] ); sys.exit()
ids = set(re.findall(r'\bid="([^"]+)"', en)) | set(re.findall(r"\bid='([^']+)'", en))
dbl = "&amp;amp;" in en
svg_refs = re.findall(r'url\(#([^)]+)\)', en); svg_bad = [x for x in svg_refs if x not in ids]
style_rel = bool(re.search(r'url\((?!data:|#|https?:)[^)]*pic\.png', en))
srcset = re.findall(r'srcset="([^"]*)"', en); srcset_rel = any("pic.png" in s and "data:" not in s for s in srcset)
dir_links = [h for h, t in re.findall(r'<a [^>]*href="([^"]*)"[^>]*>([^<]*)</a>', en) if t.strip() == "dir link"]
dir_ok = bool(dir_links) and dir_links[0].startswith("#") and dir_links[0][1:] in ids
print(f"{L} udu={int(udu)} | title escaped twice: {dbl} | SVG url(#) to a missing id: {svg_bad[:2] or 'no'} | <style> url() left relative: {style_rel} | srcset left relative: {srcset_rel} | dir link resolved: {dir_ok} {dir_links[:1]}")
