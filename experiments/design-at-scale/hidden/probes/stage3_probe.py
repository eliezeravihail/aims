"""Stage-3 acceptance probes — the floor. Written from hidden/stage-3.md alone, black-box on the exported files,
before any stage-3 arm ran.

The card leaves the export's location and file names open, so the probe runs `mkdocs export` with no arguments in
a project directory and takes every HTML file the command created or changed there (outside `docs/`) as the export.
Each file's language is recognised by the marker text of that language's own home page.

"Opens in the reader's own language" is the goal-2 trap (DESIGN §5): it is **not** probed. Whether an export
contains browser-language detection is reported as INFO for the goal-2 record only.

Usage: python3 stage3_probe.py <arm-dir> <same-arm-stage-2-dir> <pristine-dir>
"""
import base64, html.parser, pathlib, re, shutil, subprocess, sys, tempfile

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
ML_FILES = {
    "mkdocs.yml": "site_name: Probe\nlanguages:\n  default: en\n  others: [fr, he]\n",
    "docs/en/index.md": "# Home\n\nENHOME body. See [the guide](guide.md).\n",
    "docs/en/guide.md": "# User Guide\n\nENGUIDE body text.\n\n![pic](img/pic.png)\n",
    "docs/en/about.md": "# About\n\nENABOUT body text.\n",
    "docs/fr/index.md": "# Accueil\n\nFRHOME corps. Voir [le guide](guide.md).\n",
    "docs/fr/guide.md": "# Guide Utilisateur\n\nFRGUIDE corps.\n\n![pic](img/pic.png)\n",
    "docs/he/index.md": "# Bayit\n\nHEHOME guf.\n",
}
IMAGES = ["docs/en/img/pic.png", "docs/fr/img/pic.png", "docs/he/img/pic.png"]
PLAIN_FILES = {
    "mkdocs.yml": "site_name: Plain\n",
    "docs/index.md": "# Home\n\nPLAINHOME body, [guide](guide.md).\n",
    "docs/guide.md": "# Guide\n\nPLAINGUIDE body.\n",
    "docs/sub/deep.md": "# Deep\n\nPLAINDEEP body, [back](../index.md).\n",
}
LANG_MARK = {"en": "ENHOME", "fr": "FRHOME", "he": "HEHOME"}
PAGES = {"en": ["ENHOME", "ENGUIDE", "ENABOUT"], "fr": ["FRHOME", "FRGUIDE", "ENABOUT"], "he": ["HEHOME", "ENGUIDE", "ENABOUT"]}


def write(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def project(root, files, images=()):
    write(root, files)
    for rel in images:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(PNG)


def mkdocs(arm, proj, *args):
    py = str(pathlib.Path(arm) / ".venv/bin/python")
    r = subprocess.run([py, "-m", "mkdocs", *args], cwd=proj, capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stderr or r.stdout)[-1500:]


def state(proj):
    return {p: p.stat().st_mtime_ns for p in proj.rglob("*.html") if "docs" not in p.relative_to(proj).parts}


def export(arm, proj):
    before = state(proj)
    rc, err = mkdocs(arm, proj, "export")
    after = state(proj)
    return rc, err, sorted(p for p in after if before.get(p) != after[p])


class Refs(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.refs, self.ids, self.anchors, self.text = [], set(), [], []
        self._a = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag == "a" and "name" in a: self.ids.add(a["name"])
        if tag == "img" and a.get("src"): self.refs.append(("img", a["src"]))
        if tag == "script" and a.get("src"): self.refs.append(("script", a["src"]))
        if tag == "link" and a.get("href") and "stylesheet" in (a.get("rel") or ""): self.refs.append(("css", a["href"]))
        if tag == "a" and a.get("href") is not None:
            self._a = [a["href"], ""]; self.anchors.append(self._a)
    def handle_endtag(self, tag):
        if tag == "a": self._a = None
    def handle_data(self, d):
        self.text.append(d)
        if self._a is not None: self._a[1] += d


def parse(text):
    p = Refs(); p.feed(text); return p


def text_nodes(page_html):
    return {t.strip() for t in parse(page_html).text if len(t.strip()) >= 8}


def masked_site(site):
    out = {}
    for f in sorted(site.rglob("*")):
        if f.is_file() and not f.name.startswith("sitemap.xml") and f.name != "messages.pot":
            d = f.read_bytes()
            if f.suffix == ".html":
                d = re.sub(rb"Build Date UTC : [^\n]*", b"Build Date UTC : <masked>", d)
            out[str(f.relative_to(site))] = d
    return out


def main(arm, prev, pristine):
    arm, prev, pristine = (pathlib.Path(x).resolve() for x in (arm, prev, pristine))
    work = pathlib.Path(tempfile.mkdtemp(prefix="probe3-"))
    results, info = [], []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    ml = work / "ml"; project(ml, ML_FILES, IMAGES)
    rc, err, files = export(arm, ml)
    by_lang, texts = {}, {}
    for f in files:
        t = f.read_text(errors="replace"); texts[f] = t
        langs = [l for l, m in LANG_MARK.items() if m in t]
        if len(langs) == 1:
            by_lang.setdefault(langs[0], []).append(f)
    one_each = rc == 0 and len(files) == 3 and all(len(by_lang.get(l, [])) == 1 for l in LANG_MARK)
    check("E1 `mkdocs export` writes one HTML file per language", one_each,
          (err.strip().splitlines() or [""])[-1] if rc else f"{len(files)} files: {[str(f.relative_to(ml)) for f in files][:5]}")
    doc = {l: texts[v[0]] for l, v in by_lang.items() if len(v) == 1}

    check("E2 each file holds every page of that language's site",
          len(doc) == 3 and all(all(m in doc[l] for m in PAGES[l]) for l in PAGES),
          "; ".join(f"{l} lacks {[m for m in PAGES[l] if m not in doc.get(l, '')]}" for l in PAGES
                    if any(m not in doc.get(l, "") for m in PAGES[l])))

    # A link to another language's exported file is allowed (the reader chooses the file); any other local link must
    # be an anchor that exists in the same file.
    siblings = {f.name for f in files}
    def internal_ok(t):
        p = parse(t)
        local = [(h, s) for h, s in p.anchors if h and not h.startswith(("http:", "https:", "mailto:"))
                 and h.split("#")[0].rsplit("/", 1)[-1] not in siblings]
        bad = [h for h, _ in local if not h.startswith("#") or h[1:] not in p.ids]
        toc = any(h.startswith("#") and "Guide" in s for h, s in local)
        return local and not bad and toc, bad
    oks = {l: internal_ok(doc[l]) for l in doc}
    check("E3 navigation is a table of contents; page links are anchors inside the file",
          len(doc) == 3 and all(ok for ok, _ in oks.values()),
          "; ".join(f"{l}: {bad[:3]}" for l, (ok, bad) in oks.items() if not ok))

    def embedded(t):
        p = parse(t)
        rel = [(k, s) for k, s in p.refs if not s.startswith(("data:", "http:", "https:", "//"))]
        net = [(k, s) for k, s in p.refs if s.startswith(("http:", "https:", "//"))]
        return rel, net, "data:image" in t
    emb = {l: embedded(doc[l]) for l in doc}
    check("E4 images and stylesheets are embedded; the file needs no file beside it",
          len(doc) == 3 and all(not rel and img for rel, _, img in emb.values()),
          "; ".join(f"{l}: {'no embedded image; ' if not img else ''}{rel[:3]}" for l, (rel, _, img) in emb.items()
                    if rel or not img))
    for l, (_, net, _) in emb.items():
        if net:
            info.append(f"E4: the {l} file loads {len(net)} resource(s) from the network, e.g. {net[0][1][:80]}")

    # E5 — an untranslated page appears as on the site: the default text, with the notice.
    rcb, _ = mkdocs(arm, ml, "build", "-q", "-d", str(work / "mlsite"))
    notice_ok, detail5 = False, "site build failed"
    if rcb == 0:
        s = work / "mlsite"
        fa, fg, ea = (s / "fr/about/index.html", s / "fr/guide/index.html", s / "en/about/index.html")
        if fa.exists() and fg.exists() and ea.exists():
            cands = text_nodes(fa.read_text()) - text_nodes(fg.read_text()) - text_nodes(ea.read_text())
            cands = {c for c in cands if "ENABOUT" not in c and "About" not in c}
            notice_ok = "fr" in doc and "ENABOUT" in doc["fr"] and any(c in doc["fr"] for c in cands)
            detail5 = "" if notice_ok else f"notice text seen on the site ({sorted(cands)[:2]}) not in the fr file"
        else:
            detail5 = "site pages missing"
    check("E5 an untranslated page appears as on the site: default text with the notice", notice_ok, detail5)

    plain = work / "plain"; project(plain, PLAIN_FILES)
    rcp, errp, pf = export(arm, plain)
    ok6 = rcp == 0 and len(pf) == 1 and all(m in pf[0].read_text(errors="replace") for m in ("PLAINHOME", "PLAINGUIDE", "PLAINDEEP"))
    check("E6 a site with no languages exports a single file", ok6,
          (errp.strip().splitlines() or [""])[-1] if rcp else f"{len(pf)} files")

    # E7 — `mkdocs build` is unchanged by stage 3: the same projects build identically with the stage-2 tree.
    same = True; where = ""
    for name, files_, imgs in (("ml", ML_FILES, IMAGES), ("plain", PLAIN_FILES, ())):
        outs = []
        for d in (arm, prev):
            p = work / f"b7-{name}-{d.name}"; project(p, files_, imgs)
            mkdocs(d, p, "build", "-q"); outs.append(masked_site(p / "site"))
        if outs[0] != outs[1]:
            same = False
            diff = sorted(set(outs[0]) ^ set(outs[1])) + sorted(k for k in set(outs[0]) & set(outs[1]) if outs[0][k] != outs[1][k])
            where += f"{name}: {diff[:3]} "
    check("E7 `mkdocs build` output is unchanged by the export", same, where)

    detect = [l for l, t in doc.items() if re.search(r"navigator\.(languages?|userLanguage)|Accept-Language", t)]
    info.append("goal-2: browser-language detection in the export files: " + (", ".join(detect) if detect else "none"))

    shutil.rmtree(work, ignore_errors=True)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
    for line in info:
        print(f"INFO  {line}")
    passed = sum(ok for _, ok, _ in results)
    print(f"{passed}/{len(results)} probes pass — floor {'CLEAR' if passed == len(results) else 'BLOCKED'}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
