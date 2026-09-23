## Judge report (simplicity disposition): nine `mkdocs export` designs

**Summary.** Only one design is shippable. T scores 8.64 with no S4 and gate CLEAR. The other eight are BLOCKED. Each fails at least one edge case of §1, the correctness chapter, and I reproduced every one of those failures by running the design. Ranking by grade: **T 8.64** > R 6.48 > W 6.33 > P 6.26 > Q 6.14 > V 5.30 > N 5.12 > U 4.73 > S 4.69.

### Step 0 inventory (fixed from SPEC.md, used for all nine)

**Rules (R)**
- **R1** `mkdocs export` writes one self-contained HTML file per language.
- **R2** Each file holds every page of that language's site.
- **R3** The navigation becomes a table of contents inside the file.
- **R4** Links between pages become anchors inside the file, and ids from different pages must not collide.
- **R5** The images and stylesheets the pages use are embedded, with nothing needed beside the file.
- **R6** Untranslated pages appear exactly as on the site: the default-language text plus the notice.
- **R7** A site without `languages` exports a single file.
- **R8** `build` and `serve` are unchanged.

**Change axes (X)**
- **X1** New output format.
- **X2** New asset kinds, such as fonts inside CSS, SVG or srcset.
- **X3** A change to the fallback or notice rule.
- **X4** New link forms (fragments, directory URLs, nav links).
- **X5** Theme change or a third-party theme, which changes "the stylesheets the pages use".
- **Unstated variant:** page titles or inline SVG containing characters or references that must survive id-scoping and escaping.

**Acceptance cases (C)**
- **C1** A single-language site gives one file with every page and a TOC.
- **C2** With `en` and `fr`, there are two files, and the `fr` file shows untranslated pages in `en` with the notice.
- **C3** A link `page.md#frag` resolves inside the file.
- **C4** Page images and `extra_css` are embedded.
- **C5** Duplicate headings across pages produce distinct anchors.
- **C6** `site_dir` is untouched.
- **C7** Nested, relative and navigation links work.
- **C8** No relative `src`/`href` escapes the file.

**How §1 was checked.** I ran each design's own `mkdocs export` on probe projects in my scratchpad:
- single-language, multi-language, a custom theme, and an explicit nav;
- `use_directory_urls: false` with a `<style>` block and `srcset`;
- a page titled `Q & A`;
- inline SVG using `url(#g)`.

All nine pass C1–C8 on the basic projects. The edge probes are what separated them:
- **TOC shows `Q &amp; A` (title escaped twice):** N, P, S, U, W.
- **Inline SVG `fill="url(#g)"` left pointing at an id that was renamed:** P, U, V, W.
- **Page `<style>` block's `url()` left unembedded:** P, Q, U.
- **`srcset` left unembedded:** R.
- **Refuses any theme without `export.html`:** Q.

T passed every probe.

**Applicable items (the same set for every design).** 40 items in total, by chapter:
- §0: 3
- §1: 4 (1a correctness, 1b edges, 1c fail fast, 1d full input space)
- §2: 4
- §3: 2
- §4: 5 (4a value objects, 4b rich model, 4c concept fit, 4d illegal states, 4e immutability)
- §5: 5 (5a calibrate, 5b hiding, 5c Demeter, 5d one owner, 5e errors)
- §6: 3
- §7: 4 (7a OCP, 7b DRY, 7c YAGNI, 7d change axes)
- §8: 2
- §9: 2
- §10: 2
- §11: 2
- §12: 2
- §13 and §14 are N/A: no performance requirement and no trust boundary.

Passing items not listed below hold at the files cited in each design's summary.

---

### N — grade 5.12 · worst chapter 2 · #S3 = 2 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 5 · §1 2 · §2 5 · §3 10 · §4 10 · §5 8 · §6 7 · §7 3 · §8 10 · §9 10 · §10 10 · §11 5 · §12 10

**Failed items**
- **0b, S3.** The export reaches into private build internals: `commands/export.py:77` (`build._LanguagesLogFilter`) and `:148-152` (`_begin_build`, `_read_site`, `_validate_anchor_links`). `offline/__init__.py:147` reads `config._language_site`. This breaks the seam with `commands.build`.
- **1b, S4.** `offline/__init__.py:155-156` builds an autoescaping environment and `:172` passes the raw HTML title, so `document.html:60` escapes it again. The TOC shows `Q &amp; A` (R3).
- **2b, S1.** `offline/__init__.py:58-137`: `render_document` mixes the favicon lookup (99-105), copyright rewriting, language and assembly.
- **2c, S1.** `references.py:274` takes a flag argument `embed: bool`.
- **5b, S1.** `references.py:146-150` exposes mutable `published`/`remote` sets, which `export.py:172-187` reads.
- **6a, S1.** `references.py` is 541 lines and handles resolution, CSS `@import` inlining, data URIs, fallback reporting and scanning.
- **7a, S3.** `document.html:18-29` embeds only its own CSS plus `extra_css`. The theme's stylesheets are never carried (X5).
- **7b, S2.** `export.py:74-115` copies build's strict-mode and log-filter block (build.py:474-560). `document.html:70-74` re-renders the untranslated notice that the themes and `languages.py:391-395` already own.
- **7c, S1.** `references.py:333-345`: fallback links to the published site via `site_url`. `offline/__init__.py:99-111`: favicon and copyright. Neither was asked for.
- **11a, S1.** `offline/__init__.py:80-84` mutates `config._current_page`.

**Passing items hold at:** `render_document` as the interface; the `Alternate` value object (37); `page_anchor`/`element_anchor` as the single anchor owner (references.py:39-46); `page.untranslated` as the single owner of which pages are untranslated; `_check_export_dir` (export.py:127) for fail-fast; `BuildError`→`Abort` (163-169).

---

### P — grade 6.26 · worst chapter 2 · #S3 = 1 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 · §2 10 · §3 10 · §4 10 · §5 8 · §6 10 · §7 5 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Failed items**
- **1b, S4.** Three reproduced edge failures:
  - `templates/document.html:20` applies `{{ entry.title|e }}` to an HTML title, escaping it twice.
  - `export/html.py:155-167` rewrites only start tags, so a page `<style>` block's `url(../img)` stays relative (R5).
  - `document.py:153-154` scopes ids but leaves `fill="url(#g)"`, breaking the SVG reference (R4).
- **5a, S1.** `commands/export.py:23,70-73` must construct incremental's `SiteScope()` and assert the result is non-None. `render_site`'s contract (build.py:455-470) leaks the incremental concept into the export.
- **7a, S3.** `document.py:193-204` uses only its own `document.css` plus `extra_css`, with no theme stylesheets (X5).
- **7b, S2.** `templates/document.html:31-37` duplicates the notice in `themes/mkdocs/content.html:10` and `readthedocs/base.html:163`.

**Passing items:** a clean public seam into build (`open_site`, `render_site`, `strict_warnings`, `reporting_build_errors`; export.py:16-22). The `Target` union (`PageLink | AssetLink | Unresolved`, placement.py:228-245) is a real sum type. `Placement.anchor`/`scoped` is the single id owner (257-263). The parts are small (html, embed, placement, document). It has true unit tests per module, 47 in total.

---

### Q — grade 6.14 · worst chapter 2 · #S3 = 0 · #S4 = 2 · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 · §2 10 · §3 10 · §4 10 · §5 10 · §6 10 · §7 8 · §8 5 · §9 10 · §10 10 · §11 5 · §12 10

**Failed items**
- **1d, S4.** `commands/export.py:89-92` raises `BuildError` whenever the theme lacks `export.html`, and only the two built-in themes have one. Any other theme cannot export at all (R1/R7 crossed with X5). A custom-theme probe exits with rc=1.
- **1b, S4.** `utils/html_tags.py:291-301` handles start tags only, so a page `<style>` block's `url()` is not embedded (R5).
- **7b, S1.** The scoped-id formula `f'{anchor}{_ID_SEPARATOR}…'` is written inline four times (`single_file.py:116,158,168,254`).
- **8b, S2.** `themes/mkdocs/export.html` and `themes/readthedocs/export.html` each carry the TOC macro and page loop (lines 9-21 and 53-58). A layout change is shotgun surgery across themes.
- **11a, S1.** `export.py:65-76` swaps the caller's `config.site_dir`, and `:95-96` overwrites `page.content`.

**Passing items:** the `SitePublisher` Protocol in `run_site` (build.py:381-450) has two real implementations (`_SiteDirectory` and `_SingleFilePublisher`), so the Strategy is justified by an actual need. The notice has a single owner because the export includes the theme's `content.html`. `SingleFile` is the single resolution owner. It has 28 unit tests.

---

### R — grade 6.48 · worst chapter 2 · #S3 = 0 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 · §2 8 · §3 10 · §4 8 · §5 10 · §6 10 · §7 7 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Failed items**
- **1b, S4.** Two edge failures:
  - `export/addresses.py:41` has no `srcset` in `_EMBEDDED`, so `srcset` candidates stay relative and the image breaks offline (R5).
  - `addresses.py:282-291` does not resolve a directory link `sub/`, and `:202-211` then drops the attribute (R4).
- **2c, S1.** `addresses.py:166-175`: `_attribute` takes seven parameters.
- **4d, S1.** `addresses.py:99-105`: `_Target(page, file, fragment)` has both fields optional, so "unresolved" is modelled as both being absent.
- **7b, S2.** `commands/export.py:65-85` copies build's strict-mode and `on_build_error` block (build.py:367-490).

**Passing items:** a public `render_site` → `RenderedSite` seam (build.py:497-536). The notice has a single owner in `LanguageSitePlugin.on_page_context` (languages.py:212-220), which the export reaches through `page_context`. `_allocate_anchors` is the single anchor owner (300-314). `document_html` post-processes the whole template output (`export/__init__.py:125`). A theme can override the export through `export-base.html` blocks and falls back to a plain default, which is earned by X5.

---

### S — grade 4.69 · worst chapter 2 · #S3 = 2 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 5 · §1 2 · §2 5 · §3 10 · §4 6 · §5 6 · §6 7 · §7 3 · §8 5 · §9 10 · §10 10 · §11 5 · §12 10

**Failed items**
- **0b, S3.** `commands/export/__init__.py:135,159,166` call `build._reported_once`, `_read_site` and `_present_untranslated`. `document.py:198` uses `getattr(config,'_language_site')`.
- **1b, S4.** `export.html:10-16` applies `|e` to HTML titles, escaping them twice.
- **2a, S1.** `document.py:156-194`: the constructor performs all the rewriting.
- **2b, S1.** `__init__.py:149-202` mixes plugin events, notice presentation, validation and template context.
- **4d, S1.** `document.py:322-327`: `Stylesheet(css=None, href=None)` has both fields optional.
- **4e, S1.** `document.py:96-102,193`: `Article.content` is a temporary mutable field filled in later.
- **5b, S1.** `document.py:249,261,265` call the private `Omissions._add` from another class.
- **5c, S1.** `document.py:198-200`: a Demeter chain through `config._language_site.tree.fallback_source`.
- **6a, S1.** `document.py` is 479 lines and mixes resolution, CSS, reporting and parsing.
- **7a, S3.** `__init__.py:187` and `document.py:306-319`: own CSS plus `extra_css` only (X5).
- **7b, S2.** `__init__.py:73-117` duplicates build's strict-mode block (build.py:339-365).
- **7c, S1.** `document.py:105-147,250-251`: the three-category `Omissions` report and the `site_url` fallback were not asked for.
- **8b, S1.** `__init__.py:164-166` repeats build's `is_fallback` guard (build.py:298).
- **11a, S1.** `__init__.py:88-89,166` mutate a config copy and `page.content`.

**Passing items:** the notice has a single owner in `_present_untranslated` (build.py:226-251). Unique anchors are allocated at `document.py:181-191`.

---

### T — grade 8.64 · worst chapter 5 · #S3 = 0 · #S4 = 0 · **CLEAR**

**Chapter scores:** §0 10 · §1 10 · §2 5 · §3 10 · §4 10 · §5 7 · §6 7 · §7 10 · §8 10 · §9 10 · §10 10 · §11 5 · §12 10

**Failed items**
- **2b, S1.** `commands/export/__init__.py:172-216`: `_head` mixes theme rendering, link classification, remote reporting and embedding.
- **2d, S1.** `__init__.py:60` empties `export_dir` first. This is documented but destructive.
- **5e, S2.** `__init__.py:188-194` uses `except Exception` and turns any theme-render failure into a warning.
- **6b, S1.** `__init__.py:219-223` renders `main.html` for the homepage only to scrape its `<link>` tags, which couples the export to theme template naming.
- **11a, S1.** `__init__.py:104-106` overwrites `page.content` twice.

**Passing items:** a public seam (`build.prepare_site`, `PreparedSite`, `reporting`). `LanguageSite.present` (languages.py:156-162) is the single notice owner, shared by build (build.py:229) and export. `page_anchor` and `local_id` are the single id owner (addresses.py:15-26). The rewriter handles ids, `<style>` blocks, `srcset`, SVG `url(#)` and `usemap` (html.py:104-139). Theme stylesheets come from the theme's own head (X5). The `References` Protocol is small, has one implementation and serves as the test seam: small and load-bearing, not ceremony. It has 48 tests.

---

### U — grade 4.73 · worst chapter 2 · #S3 = 0 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 7 · §1 2 · §2 5 · §3 5 · §4 8 · §5 10 · §6 3 · §7 5 · §8 10 · §9 10 · §10 5 · §11 5 · §12 5

**Failed items**
- **0b, S2.** `commands/export.py:22` imports the private `_build_site`.
- **1b, S4.** Three edge failures:
  - `export.py:173` applies `{{ item.title|e }}`, escaping titles twice.
  - `export_references.py:333-367` rewrites start tags only, so `<style>` `url()` is not embedded.
  - `:146-164` scopes ids (147) but not `url(#g)`.
- **2b, S1.** `export.py:104-137`: HTML is assembled by string concatenation.
- **2c, S1.** `export_references.py:146`: `_attribute` takes eight parameters.
- **3a, S1.** `_Outside` and `_Shell` (`export.py:202,254`) are opaque names.
- **4a, S1.** `export.py:223,228,284`: a 5-tuple is spread positionally into `_Shell`.
- **6a, S1.** `export_references.py` mixes resolution, disk reads, CSS, font pruning and HTML scanning.
- **6b, S2.** `export.py:215-229` finds the theme's wrapper by searching for `page.content` inside the built HTML, which couples the export to the built text.
- **7b, S1.** `export_references.py:148,150,181` repeat the `f'{anchor}:…'` formula.
- **7c, S1.** `:267-284` `_woff2_only` prunes fonts, a size optimization nobody asked for.
- **10a, S1.** `export.py:109-137,168-188`: presentation lives in Python strings next to the scraping.
- **11b, S1.** `export_references.py:199-201,257-260`: the rewriting core opens files on disk itself.
- **12a, S1.** `:96-100,250-255`: `References` needs a staging directory holding a built site, so it cannot be tested in isolation.

**Passing items:** the notice arrives inside `page.content` from build (build.py:249-258). The theme's look carries over (X5).

---

### V — grade 5.30 · worst chapter 2 · #S3 = 3 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 5 · §1 2 · §2 8 · §3 10 · §4 10 · §5 6 · §6 7 · §7 5 · §8 5 · §9 10 · §10 10 · §11 5 · §12 10

**Failed items**
- **0b, S3.** `commands/export.py:84,157` call `build._LanguageSiteLogFilter` and `build._populate_page`. `:144,162,270` touch `config._language_site` and `config._current_page`.
- **1b, S4.** `export.py:343-360` scopes ids but not `fill="url(#g)"`, and `_embed` passes `#` URLs through unchanged (396).
- **2b, S1.** `export.py:267-305`: `render()` does file I/O, rewriting and templating.
- **5b, S1.** `:595` reads the stdlib parser's internal `cdata_elem`.
- **5c, S1.** `:307-310` scans `site.links(page)` to find whether the current page is translated.
- **6a, S2.** One 615-line module. `_Document` (226-489) owns ids, links, embedding, CSS, TOC and rendering.
- **7a, S3.** Own `export.html` and `export.css` plus `extra_css` only (415-429) (X5).
- **7b, S2.** `:67-117` duplicates the strict-mode block (build.py:290-314). `export/export.html:53-60` duplicates the notice.
- **8b, S3.** `:151-166` re-implements build's page-reading loop (build.py:515-521: `Page(None, …)` then `_populate_page`) and anchor validation, without `on_env`. This is a second pipeline that must track build.
- **11a, S1.** Config mutation at `:144,162,270`.

**Passing items:** unique anchors are allocated at `export.py:253-262`.

---

### W — grade 6.33 · worst chapter 2 · #S3 = 0 · #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 · §2 10 · §3 10 · §4 8 · §5 10 · §6 10 · §7 7 · §8 10 · §9 10 · §10 10 · §11 5 · §12 10

**Failed items**
- **1b, S4.** `commands/single_file.py:370` applies `escape(item.title)`, escaping titles twice. `:217-228` scopes ids while `rewrite_css` skips `#` URLs (135), which breaks SVG references.
- **4a, S1.** `:88` stores tags as 5-tuples, and `site_path` returns a `(path, fragment)` tuple (166-176).
- **7b, S2.** `commands/export.py:47-57` keeps its own strict-mode counter, duplicating build's policy (build.py:383-490).
- **11a, S1.** `export.py:67-78` swaps the caller's `config.site_dir`, and `:83-87` inserts and deletes a plugin in `config.plugins`.

**Passing items:** only public seams (`build.build_site`, `language_site_config`). A collector plugin hooks the existing event system, which is the pattern justified by an actual need. The notice has a single owner in `LanguageSitePlugin` (languages.py:213-219) and is captured in `page.content`. `SingleFileSite` is the single anchor owner. Theme stylesheets are collected from pages as they are written (X5). The export code is about 540 lines.

---

### Comparison: the structural choices that separate the nine

Three choices separate them.

**1. How the export reuses site reading.** P, R, T, W and Q use a public build seam:
- P: `render_site`, though it leaks `SiteScope`.
- R: `render_site` → `RenderedSite`.
- T: `prepare_site`.
- W: `build_site` plus a collector plugin.
- Q: `run_site` with a publisher Strategy.

N, S, U and V reach into private build internals. V goes further and re-implements build's page-reading loop.

**2. Who owns the untranslated notice.** Q, R, S, T, U and W reuse the site's single owner. N, P and V re-render the notice in their own templates.

**3. Whether the theme's stylesheets are carried (X5).**
- T, U and W derive them from the theme's own output.
- R offers a theme override seam with a plain fallback.
- Q makes an `export.html` mandatory, so any other theme cannot export at all. That is its S4.
- N, P, S and V ignore the theme's look.

On simplicity, P is the leanest well-factored design and W the leanest overall: a plugin plus one 380-line module. In N's and S's added machinery (the `site_url` fallback, the Omissions report, favicon and copyright) I found none that the specification pays for. V is the one real God module. U's approach of building the site to disk and finding the theme's shell by string search is the most fragile. What decided the ranking, though, is the chapter these approaches never touched: rewriting HTML consistently.
- Scoping ids forces every reference to follow them. Four designs miss SVG `url(#id)`.
- Titles are already HTML. Five designs escape them a second time.
- `<style>` blocks and `srcset` also load images. Four designs leave one or the other unembedded.

T alone gets all of these right, with small parts and one owner for each rule. That puts it first by a wide margin even though it has a few S1 impurities and one S2 blanket `except`.

Side effect to note: my probe runs (`python -m mkdocs export` with `PYTHONPATH` pointing at each design, plus one test-suite run on P) wrote `.pyc` caches into `__pycache__` directories under the design trees. Some `__pycache__` directories were already there from earlier runs. No source file was changed. Probe projects and outputs are in `/tmp/claude-0/-home-user-aims/e6c16176-2387-51c1-bd33-020a3b8815da/scratchpad/judge-simp/`.