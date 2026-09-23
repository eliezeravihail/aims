## Ownership-disposition judge: `mkdocs export`, nine designs (N P Q R S T U V W)

T scores highest (9.46) and W is close behind (9.23). N, P and V are BLOCKED, each by one S4: the untranslated-page notice is written a second time in the export's own template instead of reusing the site's.

### Step 0: inventory from SPEC.md, held fixed for all nine
**Rules (R)**
- **R1** One file per language. A site without `languages` gets exactly one file.
- **R2** Every page of that language's site is in the file.
- **R3** The navigation becomes a table of contents (TOC) inside the file.
- **R4** Links between pages, including `page#frag`, become anchors inside the file. Ids from different pages must not collide.
- **R5** Images and stylesheets are embedded, and so is anything a stylesheet refers to. The file needs nothing beside it.
- **R6** An untranslated page appears **exactly as on the site**: default-language text plus the notice. This means one owner of the fallback and of the notice.
- **R7** `build` and `serve` are unchanged, including incremental rebuilds.
- **R8** (implied) Pages are read and rendered the way the build reads them: same plugins and pipeline.

**Change axes (X)**
- **X1** Another output format (EPUB/PDF/zip).
- **X2** A new kind of asset to embed (font, SVG, url() inside CSS).
- **X3** The language set or the default language changes.
- **X4** The notice's text or markup changes.
- **X5** New link forms (fragments, `use_directory_urls`, nav links).
- **X6** (unstated) `export --language fr`. Implied input: an arbitrary third-party theme.

**Acceptance cases (C)**
- **C1** A site with no languages gives 1 file.
- **C2** Languages en+fr give 2 files.
- **C3** All pages are present and the TOC nests.
- **C4** `guide.md#install` becomes an anchor that exists, with no duplicate ids.
- **C5** Images become `data:` URIs and `extra_css` is inlined, with its `url()` embedded.
- **C6** In the fr file, the untranslated page shows English text with a notice identical to the site's.
- **C7** The build still works.

### How I checked behaviour (it confirms the readings; it does not rank)
I ran the same probe against all nine: one site with no languages, one with en/fr, and one with a custom theme, `use_directory_urls: false` and a nav link. I also built each site and compared its notice with the export's. The files are in `/tmp/claude-0/-home-user-aims/e6c16176-2387-51c1-bd33-020a3b8815da/scratchpad/own-judge-7f3a/`.

- **All nine pass C1–C5 and C7.** Every internal link resolves, there are 0 duplicate ids, images are `data:` URIs, and the CSS marker is inlined.
- **C6, notice markup:**
  - Identical to the site in Q, R, S, T, U, W.
  - Different in N, P, V. The site renders `class="alert alert-info …"`; the export renders its own `<div class="untranslated-notice">` / `mkdocs-untranslated`.
- **Custom theme:** Q fails with "theme has no export.html" (exit code 1). The other eight succeed.
- **Theme CSS embedded:** only T, U and W embed the theme's CSS for a custom theme (Q and R only for the two built-in themes). N, P, S and V use their own document CSS plus `extra_css`.
- **The designs' own tests:** some failures in P, T and U all trace to a missing compiled `he` locale in this checkout. They are environmental and not scored.

### Applicable items (same set for every design)
- **§0:** encapsulation; published types; value objects.
- **§1:** correctness; edges; fail-fast; full input space.
- **§2:** one thing/SLAP; side effects.
- **§3:** names; failure messages.
- **§4:** value objects; concept fit.
- **§5:** one owner; information hiding; calibrate; Law of Demeter.
- **§6:** SRP; coupling/ISP; connascence.
- **§7:** OCP; DRY; localize change axes; YAGNI.
- **§8:** bloaters; couplers.
- **§9:** pattern chosen by force.
- **§10:** presentation separate from code; boundaries.
- **§11:** shared mutable state; functional core; idempotency.
- **§12:** tests.
- **N/A:** §13 (no performance requirement stated) and §14 (no trust boundary).

---

### N
**Chapter scores:** §0 5 · §1 10 · §2 5 · §3 10 · §4 5 · §5 2 · §6 10 · §7 5 · §8–§12 10

**Failed items**
- **§5 one owner — S4.** The notice is re-rendered in `offline/templates/document.html:70-74`, a 4th copy beside `themes/mkdocs/content.html:9`, `readthedocs/base.html:164` and `languages.render_fallback_ui` (`languages.py:404`). Violates R6/X4; the probe shows the markup differs.
- **§0 encapsulation — S3.** The export reaches into build's private members: `build._LanguagesLogFilter`, `_begin_build`, `_read_site`, `_validate_anchor_links` (`commands/export.py:77,148-152`).
- **§7 DRY — S2.** The strict-mode counter, log-filter wiring and Babel message are copied from `build._build_languages` (`export.py:74-89,113-115`).
- **§7 localize — S1.** The theme's favicon path `img/favicon.ico` is hard-coded (`offline/__init__.py:99-102`).
- **§2 SLAP — S1.** `export()` mixes naming, log wiring, strict mode and writing (`export.py:51-124`).
- **§4 value objects — S1.** TOC entries and sections are plain dicts (`offline/__init__.py:86-91,172-179`).

**Passes of note:** one `ReferenceRewriter` owns links, embedding and CSS; the reading pipeline is shared through `_read_site`.

**Grade 5.67 · worst chapter 2 (§5) · #S3 1 · #S4 1 · BLOCKED**

### P
**Chapter scores:** §5 2 · §6 7 · all others 10

**Failed items**
- **§5 one owner — S4.** The notice is re-rendered in `export/templates/document.html:33`, separate from `themes/mkdocs/content.html:10` and `readthedocs/base.html:163`. The probe shows the markup differs (R6/X4).
- **§6 coupling/ISP — S1.** The export must build an incremental `SiteScope()` and assert on an Optional (`commands/export.py:23,70-73`).

**Passes of note:**
- Build publishes `open_site`, `render_site`, `RenderedSite`, `strict_warnings` and `reporting_build_errors`, so there is one owner for pipeline, strict mode and errors.
- `Placement` owns anchors and uses a sum type (`PageLink`/`AssetLink`/`Unresolved`, `placement.py:403-420`).
- `Embedder` owns embedding.

**Grade 6.65 · worst chapter 2 · #S3 0 · #S4 1 · BLOCKED**

### Q
**Chapter scores:** §5 5 · §7 7 · §11 7 · all others 10

**Failed items**
- **§5 calibrate — S3.** The export requires every theme to provide `export.html` (`commands/export.py:89-92`). Every third-party theme fails; the probe exits with code 1.
- **§7 localize — S2.** The theme's stylesheet list is copied into `themes/mkdocs/export.html:29-34` from `base.html:20-25`; readthedocs does the same.
- **§11 mutable state — S1.** It temporarily swaps `config.site_dir` on the caller's config (`export.py:65-76`).

**Passes of note:**
- The `SitePublisher` strategy and `run_site` (build.py) give one pipeline owner; X1 would land as a new publisher.
- The notice comes from the theme's own `content.html` (`export.html:56`).
- `SingleFile` owns address mapping.

**Grade 8.29 · worst chapter 5 · #S3 1 · #S4 0 · CLEAR**

### R
**Chapter scores:** §6 7 · §7 5 · all others 10

**Failed items**
- **§7 DRY — S3.** `build.render_site` (`build.py:508-535`) re-runs the pipeline sequence of `_build_site` (`build.py:353`) in parallel. `commands/export.py:65-85` also copies strict mode and `on_build_error`. Build orchestration now has two owners.
- **§7 localize — S2.** The theme's CSS list is copied in `themes/mkdocs/export.html:3-5`.
- **§6 SRP — S1.** The export's page order lives in build (`build.py:534`).

**Passes of note:**
- The notice has one owner, the `LanguageSitePlugin.on_page_context` event, which the export reaches through that same event.
- A default `export-base.html` sits behind an optional per-theme override.
- `SiteAddresses` owns address mapping.

**Grade 8.56 · worst chapter 5 · #S3 1 · #S4 0 · CLEAR**

### S
**Chapter scores:** §0 5 · §2 5 · §5 8 · §7 7 · §8 5 · all others 10

**Failed items**
- **§0 encapsulation — S3.** It uses `build._reported_once`, `_read_site` and `_present_untranslated` (`commands/export/__init__.py:135,159,166`).
- **§7 DRY — S2.** The export re-implements strict mode, `on_build_error`, the Babel warning and the pre_build→post_build sequence (`__init__.py:73-117,156-201`).
- **§2 SLAP — S1.** `export()` at `__init__.py:67-117`.
- **§5 Law of Demeter — S1.** `self.config._language_site.tree.fallback_source` (`document.py:198-200`).
- **§8 couplers — S1.** It calls the private `Omissions._add` from outside that class (`document.py:249,261,265`).

**Passes of note:** the notice has one owner (`_present_untranslated`, shared with `build.py:298-299`); `OfflineDocument` owns rewriting.

**Grade 7.76 · worst chapter 5 · #S3 1 · #S4 0 · CLEAR**

### T
**Chapter scores:** §3 5 · §7 8 · all others 10

**Failed items**
- **§3 failure message — S1.** A blanket `except Exception` puts a raw `{e!r}` in the message (`commands/export/__init__.py:188-194`).
- **§7 DRY — S1.** The `on_config`/`on_pre_build` opening of `_build_site` is repeated (`__init__.py:92-93`).

**Passes of note:**
- Public `build.prepare_site`, `PreparedSite` and `reporting`.
- The notice has one owner, `LanguageSite.present(link_to=…)` (`languages.py:156`); the export only injects the link strategy.
- The theme's stylesheets come from the theme itself, so they work for any theme.
- `ExportAddresses` and `Embedder` each own one job, behind the `References` Protocol.

**Grade 9.46 · worst chapter 5 · #S3 0 · #S4 0 · CLEAR**

### U
**Chapter scores:** §0 5 · §6 7 · §10 5 · all others 10

**Failed items**
- **§0 encapsulation — S3.** `from mkdocs.commands.build import _build_site` (`commands/export.py:22`).
- **§6 connascence — S2.** The theme's page shell is recovered by finding `page.content` as a substring of the built HTML, with a fallback for when a plugin has rewritten it (`export.py:215-229`).
- **§10 presentation — S1.** The document is assembled by string concatenation in Python (`export.py:104-137,168-181`).

**Passes of note:** the full build is reused, so the notice, strict mode and errors each have one owner (`reporting_build_errors`); `References` owns the mapping, including cross-language links.

**Grade 8.18 · worst chapter 5 · #S3 1 · #S4 0 · CLEAR**

### V
**Chapter scores:** §0 5 · §2 5 · §5 2 · §6 7 · §7 5 · all others 10

**Failed items**
- **§5 one owner — S4.** The notice is re-rendered in `export/export.html:53-60`, and whether a page is translated is re-derived at `commands/export.py:307-310`. The probe shows the markup differs (R6/X4).
- **§0 encapsulation — S3.** It uses `build._LanguageSiteLogFilter` and `build._populate_page` (`export.py:84,157`).
- **§7 DRY — S3.** The page-reading loop of `_build_site` is re-implemented without `on_env` (`export.py:151-166`), and strict mode and `on_build_error` are copied (`export.py:67-117`).
- **§6 SRP — S2.** One 615-line module holds orchestration, ordering, TOC, links, embedding, CSS and the parser (`_Document`, `export.py:226-489`).
- **§2 SLAP — S1.** `export()` at `export.py:59-117`.

**Grade 5.74 · worst chapter 2 · #S3 2 · #S4 1 · BLOCKED**

### W
**Chapter scores:** §7 8 · §10 5 · §11 7 · all others 10

**Failed items**
- **§7 DRY — S1.** Strict-mode counting and its message are repeated next to `build_site`'s own (`commands/export.py:47-55`).
- **§10 presentation — S1.** The HTML is built with f-strings (`single_file.py:330-360`).
- **§11 mutable state — S1.** It mutates the caller's config: `config.site_dir` (`export.py:68`) and `config.plugins['mkdocs/export']` (`export.py:83-87`).

**Passes of note:**
- The whole public `build.build_site` pipeline is reused, observed through a collector plugin that hooks the published plugin events.
- The notice has one owner (`LanguageSitePlugin`).
- `SingleFileSite` owns the mapping and resolves against the built output.

**Grade 9.23 · worst chapter 5 · #S3 0 · #S4 0 · CLEAR**

---

### Ranking
| Rank | Design | Grade | Gate |
|---|---|---|---|
| 1 | T | 9.46 | CLEAR |
| 2 | W | 9.23 | CLEAR |
| 3 | R | 8.56 | CLEAR |
| 4 | Q | 8.29 | CLEAR |
| 5 | U | 8.18 | CLEAR |
| 6 | S | 7.76 | CLEAR |
| 7 | P | 6.65 | BLOCKED |
| 8 | V | 5.74 | BLOCKED |
| 9 | N | 5.67 | BLOCKED |

### Comparison: the structural choices that separate them
Two ownership questions decide most of the ranking.

**Who owns "what an untranslated page looks like"?**
- **Second owner (N, P, V).** Each re-renders the notice in its own export template. In each case the export already differs visibly from the site, and a change to the notice (X4) would have to be made in one more place. That is the only S4 in the set. It blocks P, whose structure is otherwise among the cleanest: a published `render_site`/`strict_warnings`/`reporting_build_errors`, and a sum-typed `Placement`.
- **Reuse (Q, R, S, T, U, W).** They reach the site's single owner in one of three ways:
  - the theme's `content.html` (Q);
  - the language plugin's `page_context` event (R, W);
  - a shared presenter function (S's `_present_untranslated`, T's `LanguageSite.present` with a link strategy);
  - or by taking the finished `page.content` from a real build (U).

**Who owns "read the site the way `build` does"?**
- **One published owner (P, Q, T, W).** P and T publish a read-without-writing function. Q is the strongest seam: a `SitePublisher` strategy, where X1 is just a new publisher. W runs the real public build and observes it through a plugin.
- **Private reuse (N, S, U, V).** They reuse build's private `_` functions, which is an S3 encapsulation breach.
- **Duplicated pipeline (R, V).** They re-implement the pipeline in parallel, an S3 DRY failure; V also drops `on_env`.

**Secondary separators**
- **Theme stylesheets.**
  - Derived from the theme itself (T, U, W), so they work for any theme. U's derivation, a substring search of the built HTML, is fragile.
  - Hard-coded per built-in theme (Q, R). Q has no fallback, so third-party themes cannot export at all (S3).
  - Replaced by the export's own CSS (N, P, S, V).
- **Module shape.** Every design has one owner for link and embed mapping. V alone folds that owner, orchestration and rendering into a single 615-line module.

T wins on ownership: every rule has one home, the seams are public, and the only defects are two S1s.
