"""Stage-2 acceptance probes — the floor. Written from hidden/stage-2.md alone, black-box on built output,
before any stage-2 arm ran.

The card: after any single edit, a `--dirty` build (and `mkdocs serve --dirty`) must leave on disk exactly what a
full build produces, and must not rebuild pages the edit cannot affect.

What is compared, fixed before any run: every HTML file, byte for byte, with the theme's "Build Date UTC" line
masked. The search index is **reported, not gated**: pristine mkdocs' own `--dirty` build already writes a search
index holding only the rebuilt pages, on a single-language site (verified on the pinned commit), so a difference
there is not introduced by the multi-language change. `sitemap.xml*` carry dates and are skipped. Pristine rewrites
`404.html` on every build, so "rebuilt" counts page files only (`*/index.html`, `index.html`).

Found while validating on the pinned commit, before any stage-2 arm ran: pristine's own `--dirty` build writes
"None" in the navigation for every page it did not re-render (a page's title comes from rendering its file), on a
single-language site too. The card's equality therefore includes that: a page's navigation depends on other pages'
files — exactly the assumption stage 2 breaks. D7 (single-language `--dirty` unchanged from pristine) is therefore
**reported, not gated**: an arm that fixes the pristine bug for every site would otherwise fail it.

Usage: python3 stage2_probe.py <arm-dir> <pristine-dir>
"""
import pathlib, re, shutil, socket, subprocess, sys, tempfile, time, urllib.request

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
TICK = 1.2  # seconds between a build and an edit, so file mtimes differ
DATE_ONLY = {}  # scenario -> pages rewritten only to carry a new build date (not counted; reported)


def write(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def mk(arm, project, *args):
    py = str(pathlib.Path(arm) / ".venv/bin/python")
    r = subprocess.run([py, "-m", "mkdocs", "build", "-q", *args], cwd=project, capture_output=True, text=True, timeout=300)
    return r.returncode, r.stderr[-1500:]


def pages(site):
    return {str(p.relative_to(site)): p for p in site.rglob("*.html")}


def snap(site):
    out = {}
    for rel, p in pages(site).items():
        out[rel] = re.sub(rb"Build Date UTC : [^\n]*", b"Build Date UTC : <masked>", p.read_bytes())
    return out


def mtimes(site):
    return {rel: p.stat().st_mtime_ns for rel, p in pages(site).items() if rel.endswith("index.html")}


def search_blobs(site):
    return {str(p.relative_to(site)): p.read_bytes() for p in site.rglob("search_index.json")}


def scenario(arm, work, name, files, edit):
    """Full build, edit, --dirty build; then a clean full build of the edited project elsewhere.
    Returns (ok_equal, differing_pages, rewritten_pages, search_differs, error)."""
    proj = work / name
    write(proj, files)
    rc, err = mk(arm, proj)
    if rc:
        return False, [], set(), False, "initial build failed: " + (err.strip().splitlines() or [""])[-1]
    before = mtimes(proj / "site")
    raw_before = {rel: p.read_bytes() for rel, p in pages(proj / "site").items()}
    time.sleep(TICK)
    edit(proj)
    time.sleep(TICK)
    rc, err = mk(arm, proj, "--dirty")
    if rc:
        return False, [], set(), False, "--dirty build failed: " + (err.strip().splitlines() or [""])[-1]
    after = mtimes(proj / "site")
    # Correction made after the first stage-2 results (floor-notes.md): a page rewritten only to carry the new
    # "Build Date UTC" line is not counted as rebuilt — equality masks that line, so the rebuild count must too.
    # A page rewritten with identical bytes still counts.
    def date_only(rel):
        old, new = raw_before.get(rel), (proj / "site" / rel).read_bytes()
        mask = lambda b: re.sub(rb"Build Date UTC : [^\n]*", b"", b)
        return old is not None and old != new and mask(old) == mask(new)
    touched = {k for k in after if before.get(k) != after[k]}
    rewritten = {k for k in touched if not date_only(k)}
    if touched - rewritten:
        DATE_ONLY.setdefault(name, sorted(touched - rewritten))
    rc, err = mk(arm, proj, "-d", "full")
    if rc:
        return False, [], rewritten, False, "full build failed"
    a, b = snap(proj / "site"), snap(proj / "full")
    diff = sorted(set(a) ^ set(b)) + sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return not diff, diff, rewritten, search_blobs(proj / "site") != search_blobs(proj / "full"), ""


def replace(rel, old, new):
    def f(proj):
        p = proj / rel
        p.write_text(p.read_text().replace(old, new))
    return f


def create(rel, text):
    return lambda proj: write(proj, {rel: text})


def delete(rel):
    return lambda proj: (proj / rel).unlink()


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port


def fetch(port, path):
    try:
        return urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3).read().decode(errors="replace")
    except Exception:
        return None


def main(arm, pristine):
    arm, pristine = pathlib.Path(arm).resolve(), pathlib.Path(pristine).resolve()
    work = pathlib.Path(tempfile.mkdtemp(prefix="probe2-"))
    results, info = [], []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    def run(code, title, edit, allowed=None, must=None):
        ok, diff, rewritten, sdiff, err = scenario(arm, work, code, ML_FILES, edit)
        detail = err or ("differs from a full build: " + ", ".join(diff[:4]) if diff else "")
        check(f"{code} {title}", ok and not err, detail)
        if sdiff:
            info.append(f"{code}: the --dirty search index differs from a full build's (reported, not gated)")
        if allowed is not None and not err:
            extra = sorted(rewritten - allowed)
            missing = sorted((must or set()) - rewritten)
            check(f"{code}n does not rebuild pages the edit cannot affect", not extra and not missing,
                  ("rebuilt: " + ", ".join(extra[:5]) if extra else "") + (" not rebuilt: " + ", ".join(missing) if missing else ""))

    # D1 — editing a default-language page updates it in the default language and wherever it is shown untranslated.
    #      en/guide is translated in fr, untranslated in he; the root holds the default language.
    d1_pages = {"en/guide/index.html", "guide/index.html", "he/guide/index.html"}
    run("D1", "editing a default-language page updates it and its untranslated copies",
        replace("docs/en/guide.md", "ENGUIDE body text.", "ENGUIDE edited text."), allowed=d1_pages, must=d1_pages)
    # D2 — editing a translation's body updates only that language's page.
    run("D2", "editing a translation updates that language's page",
        replace("docs/fr/guide.md", "FRGUIDE corps.", "FRGUIDE corps modifie."),
        allowed={"fr/guide/index.html"}, must={"fr/guide/index.html"})
    # D3 — adding a translation replaces the fallback: its page, its navigation title, the links from other languages.
    run("D3", "adding a translation replaces the fallback everywhere it shows",
        create("docs/fr/about.md", "# A Propos\n\nFRABOUT corps.\n"))
    # D4 — deleting a translation restores the fallback.
    run("D4", "deleting a translation restores the fallback", delete("docs/fr/guide.md"))
    # D5 — renaming a page's title updates every navigation and cross-language link showing it.
    run("D5", "renaming a title updates every navigation and link that shows it",
        replace("docs/en/about.md", "# About", "# About Us"))

    # D6 — `mkdocs serve --dirty` stays correct: add a translation, then the other French pages' navigation shows it.
    proj = work / "serve"; write(proj, ML_FILES)
    port = free_port()
    py = str(arm / ".venv/bin/python")
    proc = subprocess.Popen([py, "-m", "mkdocs", "serve", "--dirty", "-a", f"127.0.0.1:{port}"],
                            cwd=proj, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok6, detail6 = False, "server never answered"
    try:
        for _ in range(60):
            time.sleep(0.5)
            if fetch(port, "/fr/") is not None:
                break
        if fetch(port, "/fr/") is not None:
            time.sleep(TICK)
            write(proj, {"docs/fr/about.md": "# A Propos\n\nFRABOUT corps.\n"})
            detail6 = "after adding fr/about.md: /fr/about/ never showed the translation"
            for _ in range(60):
                time.sleep(0.5)
                page = fetch(port, "/fr/about/")
                if page and "FRABOUT" in page:
                    time.sleep(1.0)
                    idx = fetch(port, "/fr/") or ""
                    ok6 = "A Propos" in idx
                    detail6 = "" if ok6 else "/fr/about/ updated, but /fr/ navigation still lacks the new title"
                    break
    finally:
        proc.terminate()
        try: proc.wait(timeout=10)
        except Exception: proc.kill()
    check("D6 `mkdocs serve --dirty` stays correct after an edit", ok6, detail6)

    # D7 — a single-language site's --dirty build is unchanged: same pages rewritten, same output, as pristine.
    def plain_run(d):
        _, diff, rewritten, _, err = scenario(d, work / ("plain-" + d.name), "p", PLAIN_FILES,
                                              replace("docs/guide.md", "PLAINGUIDE body.", "PLAINGUIDE edited."))
        return rewritten, snap(work / ("plain-" + d.name) / "p" / "site"), err
    ra, sa, ea = plain_run(arm)
    rp, sp, ep = plain_run(pristine)
    same = not ea and ra == rp and sa.keys() == sp.keys() and all(sa[k] == sp[k] for k in sa)
    info.append("D7: a single-language --dirty build is " + ("unchanged from pristine" if same else
                "changed from pristine — " + (ea or (f"rewrote {sorted(ra)} vs pristine {sorted(rp)}" if ra != rp
                                                     else "output differs")) + " (reported, not gated)"))

    for code, rels in DATE_ONLY.items():
        info.append(f"{code}: rewritten only for the build date, not counted as rebuilt: {', '.join(rels[:5])}")
    shutil.rmtree(work, ignore_errors=True)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
    for line in info:
        print(f"INFO  {line}")
    passed = sum(ok for _, ok, _ in results)
    print(f"{passed}/{len(results)} probes pass — floor {'CLEAR' if passed == len(results) else 'BLOCKED'}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
