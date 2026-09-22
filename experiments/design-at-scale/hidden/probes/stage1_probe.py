"""Stage-1 acceptance probes — the floor. Written from cards/stage-1.md alone, black-box on built output.

Passing earns nothing (decisions/0021); a failure marks the arm-stage BLOCKED. Probes test only what the card
states. Behaviour the card leaves open (URLs of the search index, the notice's wording) is not probed.

Usage: python3 stage1_probe.py <arm-dir> <pristine-dir>
Each dir is an mkdocs checkout with its own .venv. Prints one line per probe and a summary.
"""
import json, os, pathlib, re, shutil, socket, subprocess, sys, tempfile, time, urllib.parse, urllib.request

BASELINE_FAILURES = {
    "test_merge_translations", "test_translations_found", "test_jinja_extension_installed",
    "test_no_translations_found", "test_draft_docs_with_comments_from_user_guide",
}

ML_FILES = {
    "mkdocs.yml": "site_name: Probe\nlanguages:\n  default: en\n  others: [fr, he]\n",
    "docs/en/index.md": "# Home\n\nENHOME body.\n",
    "docs/en/guide.md": "# User Guide\n\nENGUIDE body text.\n",
    "docs/en/about.md": "# About\n\nENABOUT body text.\n",
    "docs/fr/index.md": "# Accueil\n\nFRHOME corps.\n",
    "docs/fr/guide.md": "# Guide Utilisateur\n\nFRGUIDE corps.\n",
    "docs/he/index.md": "# Bayit\n\nHEHOME guf.\n",
}
PLAIN_FILES = {
    "mkdocs.yml": "site_name: Plain\n",
    "docs/index.md": "# Home\n\nPLAINHOME body.\n",
    "docs/guide.md": "# Guide\n\nPLAINGUIDE body.\n",
    "docs/sub/deep.md": "# Deep\n\nPLAINDEEP body, [back](../index.md).\n",
}


def write(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def build(arm, project):
    py = str(pathlib.Path(arm) / ".venv/bin/python")
    r = subprocess.run([py, "-m", "mkdocs", "build", "-q"], cwd=project, capture_output=True, text=True, timeout=300)
    return r.returncode, r.stderr[-2000:]


def read(site, rel):
    p = site / rel
    return p.read_text(errors="replace") if p.exists() else None


def hrefs_resolved(html, page_url):
    out = set()
    for h in re.findall(r'href="([^"#?]+)', html):
        if h.startswith(("http:", "https:", "mailto:")):
            continue
        u = urllib.parse.urljoin("http://x" + page_url, h)
        path = urllib.parse.urlparse(u).path
        if path.endswith("index.html"):
            path = path[: -len("index.html")]
        out.add(path)
    return out


def search_text(site, lang_dir):
    blobs = []
    for p in (site / lang_dir).rglob("search_index.json"):
        blobs.append(p.read_text(errors="replace"))
    return blobs


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port


def main(arm, pristine):
    arm, pristine = pathlib.Path(arm).resolve(), pathlib.Path(pristine).resolve()
    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    work = pathlib.Path(tempfile.mkdtemp(prefix="probe1-"))
    ml = work / "ml"; write(ml, ML_FILES)
    rc, err = build(arm, ml)
    check("P1 multi-language site builds", rc == 0, err.strip().splitlines()[-1] if rc and err.strip() else "")
    site = ml / "site"

    en_guide, fr_guide, he_guide = read(site, "en/guide/index.html"), read(site, "fr/guide/index.html"), read(site, "he/guide/index.html")
    fr_about, root_guide = read(site, "fr/about/index.html"), read(site, "guide/index.html")
    fr_index, en_index = read(site, "fr/index.html"), read(site, "en/index.html")

    check("P2 every page exists in every language", all(x is not None for x in (en_guide, fr_guide, he_guide, fr_about)))
    check("P3 default language also served at the root", root_guide is not None and "ENGUIDE" in root_guide)
    check("P4 a translation is used where it exists", fr_guide is not None and "FRGUIDE" in fr_guide and "ENGUIDE" not in fr_guide)
    check("P5 an untranslated page falls back to the default text",
          fr_about is not None and "ENABOUT" in fr_about and he_guide is not None and "ENGUIDE" in he_guide)
    check("P6 a fallback page carries that language's navigation", fr_about is not None and "Guide Utilisateur" in fr_about)
    check("P7 each language's navigation uses its own titles",
          fr_index is not None and "Guide Utilisateur" in fr_index and en_index is not None
          and "User Guide" in en_index and "Guide Utilisateur" not in en_index)

    def links_to(html, page_url, lang):
        targets = {f"/{lang}/guide/"} | ({"/guide/"} if lang == "en" else set())
        return html is not None and bool(hrefs_resolved(html, page_url) & targets)
    check("P8 every page links to the same page in each other language",
          links_to(fr_guide, "/fr/guide/", "en") and links_to(fr_guide, "/fr/guide/", "he")
          and links_to(en_guide, "/en/guide/", "fr") and links_to(he_guide, "/he/guide/", "fr"))

    fr_idx, he_idx = search_text(site, "fr"), search_text(site, "he")
    check("P9 each language has its own search index, holding what its reader sees",
          fr_idx and any("FRGUIDE" in b for b in fr_idx) and not any("ENGUIDE" in b for b in fr_idx)
          and he_idx and any("HEHOME" in b for b in he_idx) and any("ENGUIDE" in b for b in he_idx))

    # P10 — a site with no `languages` builds exactly as the pristine commit builds it
    outs = {}
    for label, d in (("arm", arm), ("pristine", pristine)):
        p = work / f"plain-{label}"; write(p, PLAIN_FILES); build(d, p); outs[label] = p / "site"
    def snapshot(s):
        # Two builds of identical input differ only in the theme's "Build Date UTC" stamp (verified by
        # diffing two pristine builds) and in sitemap dates; mask exactly those, compare everything else.
        snap = {}
        for f in sorted(s.rglob("*")):
            if f.is_file() and not f.name.startswith("sitemap.xml"):
                data = f.read_bytes()
                if f.suffix == ".html":
                    data = re.sub(rb"Build Date UTC : [^\n]*", b"Build Date UTC : <masked>", data)
                snap[str(f.relative_to(s))] = data
        return snap
    a, b = snapshot(outs["arm"]), snapshot(outs["pristine"])
    diff = sorted(set(a) ^ set(b)) + sorted(k for k in set(a) & set(b) if a[k] != b[k])
    check("P10 a site with no languages builds exactly as before", not diff, ", ".join(diff[:4]))

    # P11 — `mkdocs serve` serves the multi-language site
    port = free_port()
    py = str(arm / ".venv/bin/python")
    proc = subprocess.Popen([py, "-m", "mkdocs", "serve", "-a", f"127.0.0.1:{port}", "--no-livereload"],
                            cwd=ml, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    served = False
    try:
        for _ in range(60):
            time.sleep(0.5)
            try:
                body = urllib.request.urlopen(f"http://127.0.0.1:{port}/fr/guide/", timeout=3).read().decode(errors="replace")
                served = "FRGUIDE" in body
                break
            except Exception:
                continue
    finally:
        proc.terminate()
        try: proc.wait(timeout=10)
        except Exception: proc.kill()
    check("P11 mkdocs serve serves the multi-language site", served)

    # P12 — no test that passed at baseline now fails
    r = subprocess.run([py, "-m", "unittest", "discover", "-s", "mkdocs/tests", "-p", "*tests.py", "-t", "."],
                       cwd=arm, capture_output=True, text=True, timeout=600)
    failing = set(re.findall(r"^(?:FAIL|ERROR): (\w+)", r.stderr, re.M))
    new = sorted(failing - BASELINE_FAILURES)
    ran = re.search(r"^Ran (\d+) tests", r.stderr, re.M)
    check("P12 no baseline-green test now fails", not new, (", ".join(new[:5]) + f" (ran {ran.group(1) if ran else '?'})"))

    shutil.rmtree(work, ignore_errors=True)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
    passed = sum(ok for _, ok, _ in results)
    print(f"{passed}/{len(results)} probes pass — floor {'CLEAR' if passed == len(results) else 'BLOCKED'}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
