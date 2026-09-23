## Step 0 inventory (taken from SPEC.md before opening any design, and used unchanged for all nine)

**Rules and invariants (R)**
- R1: `mkdocs export` writes one file per language. The root copy of the default language does not get a second file.
- R2: Each file holds every page of its language's site, each page once.
- R3: The navigation becomes a table of contents inside the file.
- R4: Links between pages become in-file anchors, including links with a `#fragment`. Ids from different pages must not collide.
- R5: The images and stylesheets the pages use are embedded, so the file needs nothing beside it.
- R6: An untranslated page appears exactly as it does on the site: the default-language text with the notice. The notice therefore has one owner, shared with the site.
- R7: A site with no `languages` exports a single file.
- R8: `build` and `serve`, including incremental rebuilds, are unchanged.

**Change axes (X)**
- X1: The output format, for example a second single-file format such as EPUB.
- X2: The set of languages.
- X3: The kinds of resource that get embedded.
- X4: The theme. A different theme changes the stylesheets the pages use and the look of the export.
- Unstated variant: embedding a new resource kind, such as scripts.

**Acceptance cases (C)**
- C1: One file per language.
- C2: A page link, with and without a fragment, becomes an anchor.
- C3: The same heading on two pages gets two distinct ids.
- C4: An image and `extra_css` are embedded, including their `url()` references.
- C5: An untranslated page shows the default text plus the site's notice.
- C6: No `languages` gives one file.
- C7: Nav sections become a nested TOC, and drafts are excluded.
- C8: Build and serve output is unchanged.

**How I applied the form**
- The same items apply to every design:
  - §0 has two items.
  - §1 has five.
  - §2 has four.
  - §3 has one.
  - §4 has four.
  - §5 has four; one-owner is the precondition.
  - §6 has three.
  - §7 has four: OCP for X1 and the unstated variant, localizing X4, DRY, and YAGNI.
  - §8 has three.
  - §9 has two.
  - §10 has two.
  - §11 has two.
  - §12 has two.
- §13 and §14 are N/A: there is no performance requirement and no trust boundary.
- A chapter's score is the smaller of round-half-up(10 × passed / applicable) and the ceiling set by its worst failure.
- **Scope decision:** I did not score exotic raw-HTML edges, such as `<link>` in the body, `aria-*` or `url(#id)` inside page content, because designs vary on these arbitrarily. §1 edge coverage was judged on the spec-central edges: fragments, `use_directory_urls` off, pages outside the nav, drafts and id collisions. All nine pass these.
- **Private access across modules:** I scored reaching into `build`'s private internals under §0.
  - Referencing a private *class* of another module breaks the literal seam rule, so I rated it S4.
  - Driving private *functions* I rated S3.
- **Theme stylesheets:** I scored a design that drops the theme's stylesheets for its own fixed core template as an X4 under-provision. That is §7 at S3, per the tie-break rule, not a §1 failure.

---

## N
**Chapter scores:** §0 2 · §1 10 · §2 5 · §3 10 · §4 8 · §5 2 · §6 10 · §7 5 · §8 7 · §9–§12 10

**Failed items**
- **§0 seam, S4.** export.py:77 builds `build._LanguagesLogFilter()`, a private class inside `build`. export.py:148-152 drives `build._begin_build`, `_read_site` and `_validate_anchor_links`. offline/__init__.py:147 reads `config._language_site`.
- **§5 one owner, S4.** offline/templates/document.html:70-74 writes its own untranslated notice, alongside the site's owners at themes/mkdocs/content.html:9, readthedocs/base.html:164 and structure/languages.py:391. This breaks R6 and C5.
- **§7 localize X4, S3.** The export template is fixed in core (offline/templates/document.html). offline/__init__.py:94-97 embeds only its own `document.css` plus `extra_css`, so the theme's stylesheets are dropped and a theme cannot shape the export.
- **§7 DRY, S2.** export.py:74-115 copies the strict-mode counter, log filter and babel scaffolding from `_build_languages` (build.py:585-594, 623-627, 671-679).
- **§2 one job / SLAP, S1.** `export()` at export.py:51-124 does several jobs at different levels.
- **§2 flag argument, S1.** references.py:274 takes `resource(..., embed=True)`.
- **§4 value objects, S1.** Sections and TOC entries are dicts, and the stylesheet kind is a `'style'`/`'link'` string (offline/__init__.py:85-97, 172-179).
- **§8 couplers, S1.** `_Context` calls the rewriter's private `_locate`, `_stylesheet_text` and `_fallback` (references.py:418-434).

**Grade 4.73** · worst 2 · (#S3 1, #S4 2) · **BLOCKED**

## P
**Chapter scores:** §0 10 · §1 10 · §2 10 · §3 10 · §4 8 · §5 2 · §6 10 · §7 5 · §8–§12 10

**Failed items**
- **§5 one owner, S4.** export/templates/document.html:32-36 writes the notice again, alongside themes/mkdocs/content.html:8-10 and readthedocs/base.html:161-163. This breaks R6.
- **§7 localize X4, S3.** document.py:193-204 uses its own `document.css` plus `extra_css`. The template is fixed in `export/templates`.
- **§4 illegal states, S1.** `render_site` returns `RenderedSite | None`, and the export has to `assert` the `None` away (export.py:70-73).

**Passes worth noting.** Uses build's public API (export.py:16-22: `open_site`, `render_site`, `strict_warnings`, `reporting_build_errors`). The `Target` sum type is well modelled (placement.py:228-245). Unit tests cover placement, embed and html.

**Grade 6.26** · worst 2 · (#S3 1, #S4 1) · **BLOCKED**

## Q
**Chapter scores:** §0–§1 10 · §2 8 · §3–§6 10 · §7 8 · §8–§10 10 · §11 5 · §12 10

**Failed items**
- **§2 side effects, S1.** `_SingleFilePublisher.publish` overwrites `page.content` in place (export.py:95-96).
- **§7 DRY, S1.** themes/mkdocs/export.html:29-34 repeats the theme's stylesheet list from base.html:20-25.
- **§11 shared state, S1.** export.py:65-76 temporarily reassigns `config.site_dir` on the shared config.

**Passes worth noting.** The `SitePublisher` protocol (build.py:381) and `run_site` (build.py:391) serve both build and export. The export template is owned by the theme. The notice has one owner: `content.html`, reused by export.html:56, and the readthedocs theme was refactored to include it. `SingleFile` lives in `structure/`.

**Grade 9.31** · worst 5 · (0, 0) · **CLEAR**

## R
**Chapter scores:** §0–§1 10 · §2 8 · §3–§6 10 · §7 7 · §8–§12 10

**Failed items**
- **§7 DRY, S2.**
  - export.py:65-85 copies build's strict-mode and `on_build_error` scaffolding.
  - `render_site` (build.py:517-536) re-sequences on_config, pre_build, the read loop and on_env in parallel to `_build_site`.
  - themes/mkdocs/export.html:3-4 repeats theme CSS paths (S1).
- **§2 parameters, S1.** `_attribute` in addresses.py:166-175 takes 7 parameters.

**Passes worth noting.** The notice is injected once by `LanguageSitePlugin.on_page_context` (languages.py:229-246), and the export reaches it through `_show_page_to_plugins` (build.py:252-266). A theme can supply `export.html` extending `export-base.html`, loaded via a ChoiceLoader (export/__init__.py:66-71). `SiteAddresses` owns the addressing rule.

**Grade 9.43** · worst 7 · (0, 0) · **CLEAR**

## S
**Chapter scores:** §0 5 · §1 10 · §2 8 · §3 10 · §4 8 · §5 8 · §6 10 · §7 5 · §8–§10 10 · §11 5 · §12 5

**Failed items**
- **§0 reaching into build internals, S3.** export/__init__.py:135 calls `build._reported_once()`, :159 `build._read_site` and :166 `build._present_untranslated`.
- **§7 localize X4, S3.** export/export.html is fixed in core, and document.py:306-319 embeds only `extra_css`.
- **§7 DRY, S2.** export/__init__.py:73-117 copies build's strict and build-error scaffolding. export/__init__.py:164-166 repeats build's `is_fallback` guard from build.py:298-299.
- **§2 SLAP, S1.** `export()` at :67-117 and `_export_site` at :149-202 mix levels.
- **§4 illegal states, S1.** `Stylesheet(css=None, href=None)` allows neither or both (document.py:322-327). `Article.content` is filled after construction.
- **§5 Demeter, S1.** document.py:198-200 goes through `getattr(config, '_language_site').tree.fallback_source(...)`.
- **§11 shared state, S1.** export/__init__.py:166 overwrites `page.content`.
- **§12 pyramid, S1.** 16 tests, 14 of them end-to-end. The rewrite decisions have no unit tests.

**Grade 7.05** · worst 5 · (#S3 2, #S4 0) · **CLEAR**

## T
**Chapter scores:** §0–§1 10 · §2 8 · §3–§4 10 · §5 8 · §6 10 · §7 8 · §8–§10 10 · §11 5 · §12 10

**Failed items**
- **§2 one job, S1.** `_head` at export/__init__.py:172-216 renders a theme page, parses it, falls back, classifies links and embeds, all in one function.
- **§5 errors, S1.** export/__init__.py:188-194 catches every `Exception` from theme rendering and downgrades it to "extra_css only" with a warning.
- **§7 DRY, S1.** export/__init__.py:92-93 repeats build's on_config and pre_build opening (build.py:361-364).
- **§11 shared state, S1.** export/__init__.py:104-106 overwrites `page.content` in place.

**Passes worth noting.** Uses build's public API: `build.reporting`, `prepare_site`, `PreparedSite`. The notice has one owner, `LanguageSite.present` (languages.py:156), with an injected `link_to` strategy. The theme's own stylesheets are carried. Value objects: `TocEntry`, `PageSection`, `Head`.

**Grade 9.15** · worst 5 · (0, 0) · **CLEAR**

## U
**Chapter scores:** §0 5 · §1 10 · §2 5 · §3 10 · §4 7 · §5 10 · §6 7 · §7 8 · §8 7 · §9 10 · §10 5 · §11–§12 10

**Failed items**
- **§0 reaching into build internals, S3.** export.py:22 imports `_build_site` from build.
- **§4 concept fit, S2.** export.py:214-229 treats the theme's layout as whatever surrounds `page.content` in a built file, found with `built.find(content)`, and falls back when a plugin changed the content.
- **§2 SLAP, S1.** `_document` at export.py:104-137 assembles the HTML by string concatenation.
- **§2 parameters, S1.** `_attribute` at export_references.py:146 takes 7 parameters.
- **§6 cohesion, S1.** export.py mixes orchestration, document assembly and parsing of the theme's shell.
- **§7 YAGNI, S1.** `_woff2_only` (export_references.py:219, 267) prunes fonts with no stated need.
- **§8 data clump, S1.** `_Outside.result` returns a 5-tuple unpacked by position (export.py:278-284).
- **§10 I/O at the edge, S1.** `References` opens staging files itself (export_references.py:198-200, 255-258).

**Passes worth noting.** The notice comes from the language owner inside `page.content`, so there is one owner. Links from the language switcher across languages resolve into the sibling file.

**Grade 7.41** · worst 5 · (#S3 1, #S4 0) · **CLEAR**

## V
**Chapter scores:** §0 2 · §1 10 · §2 8 · §3 10 · §4 8 · §5 2 · §6 7 · §7 3 · §8–§11 10 · §12 5

**Failed items**
- **§0 seam, S4.** export.py:84 uses `build._LanguageSiteLogFilter()`, a private class of build. export.py:157 re-drives build's per-page step `build._populate_page`.
- **§5 one owner, S4.** export/export.html:53-60 writes the notice again, alongside themes/mkdocs/content.html:8-10 and readthedocs/base.html:173-176. This breaks R6.
- **§7 localize X4, S3.** The export's html and css are fixed in core, and `_extra_css` (export.py:415) embeds only `extra_css`.
- **§7 DRY, S2.** export.py:67-117 copies the strict and build-error scaffolding. export.py:140-166 re-sequences on_config, pre_build, the page loop and anchor validation in parallel to build.py:506-521.
- **§7 OCP X1, S2.** Collecting the site and rendering the document are fused inside the command module (private `_Document` at export.py:226). A second format would reopen it or copy the pipeline again.
- **§6 SRP, S2.** One 615-line module holds orchestration, the document, an HTML parser (:563), the CSS rewriter and the embedder. §0a and §8a point to this defect and are not scored again.
- **§2 SLAP, S1.** `export()` at :59-117.
- **§4 tell-don't-ask, S1.** `_is_translated` at :307-310 derives translation status from the language links.
- **§12 pyramid, S1.** 14 tests, mostly end-to-end.

**Grade 4.48** · worst 2 · (#S3 1, #S4 2) · **BLOCKED**

## W
**Chapter scores:** §0–§1 10 · §2 8 · §3 10 · §4 8 · §5–§6 10 · §7 7 · §8–§10 10 · §11 5 · §12 10

**Failed items**
- **§7 DRY, S2.** export.py:46-56 re-implements the strict-mode `CountHandler`/`Abort` logic.
- **§11 shared state, S2.** export.py:64-76 reassigns `config.site_dir` on the caller's config. export.py:80-84 inserts and deletes `mkdocs/export` in the shared `config.plugins` around each build.
- **§2 SLAP, S1.** single_file.py:330-363 builds the whole document with f-strings.
- **§4 primitives, S1.** Positional 5-tuples in single_file.py:88, and `site_path` returns a bare tuple (:166).

**Passes worth noting.** Uses build's public `build_site` and `language_site_config`. The notice has a single plugin owner (languages.py:246), and the export collects it at `on_post_page`. A collector plugin, used as an observer, carries the theme's real stylesheets.

**Grade 9.33** · worst 5 · (0, 0) · **CLEAR**

---

**Ranking:** R 9.43 · W 9.33 · Q 9.31 · T 9.15 · U 7.41 · S 7.05 · P 6.26 (blocked) · N 4.73 (blocked) · V 4.48 (blocked).

## How the nine compare

Three structural choices separate the designs.

**1. Who owns the untranslated notice.** This is the precondition that decides the gate. N, P and V copy the notice into their own export template beside the site's owners, and are BLOCKED. The other six reuse one owner:
- Q uses the theme's `content.html` partial.
- R and W use the language plugin's `page_context` injection.
- S uses `build._present_untranslated`.
- T uses `LanguageSite.present`.
- U uses the language header already inside `page.content`.

**2. How the export uses the build pipeline.** From strongest to weakest:
- Q injects a `SitePublisher` strategy into one shared `run_site`.
- P, R and T use a published "rendered or prepared site" value. R still copies the pipeline sequence and the strict scaffolding.
- U and W run the full build and harvest its output: U by an inferred substring "shell" through a private `_build_site`, W through an observer plugin that mutates the shared config.
- N and S call build's private read phase.
- V re-drives build's per-page internals and log-filter class, and keeps the pipeline, document, parser and embedder in one 615-line module.

**3. Whether the theme can reach the export (X4).** Q and R let the theme own an `export.html`. T, U and W carry the theme's actual stylesheets. N, P, S and V fix a core template and embed only `extra_css`.

**The top four are near a tie.** Following the rubric's tie-break, I tried an unstated second single-file format (X1) as corroboration only; it is not scored. Q absorbs it by adding one publisher. R, T and W would each reopen their export command's `_export_site`/`_document`. So Q holds the most change-ready seam, even though its minor config and `page.content` mutations put its grade a hair below R and W.