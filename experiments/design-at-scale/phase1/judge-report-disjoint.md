## Step 0: fixed inventory (from SPEC.md only, applied to all six)

**R (rules):** R1 `languages:{default, others}` validated (default required, codes valid, no duplicates, clear error) · R2 a page is its path inside `docs/<lang>/` and may exist in *any subset* of languages · R3 `/<lang>/` per language, default also at root · R4 every page exists in every language · R5 missing translation shows the default-language content in the target language's chrome, with a notice · R6 per-language nav using that language's titles where a translation exists · R7 every page links to the same page in each other language · R8 per-language search index holding only that site's content · R9 no `languages` means an unchanged build · R10 no detection or redirect · R11 `serve` works.
**X (change axes):** X1 add a language · X2 a new per-language artifact or plugin behaviour (sitemap, hreflang, 404, a plugin reading locale) · X3 a change to the fallback policy (e.g. a chain fr-CA→fr→default) · X4 theme variation (a third-party theme renders the switcher/notice) · X5 (unstated) per-language overrides of site settings (site_name, nav).
**C (acceptance cases):** C1 the build produces `/en/ /fr/ /he/` plus root · C2 an en-only page appears at `/fr/…` in fr chrome with a notice · C3 the fr nav uses fr titles, for auto nav **and for an explicit `nav:` in mkdocs.yml** · C4 switcher links are correct, including on fallback pages · C5 per-language search · C6 a single-language site is unchanged · C7 serve works · C8 **a page that exists only in a non-default language** (allowed by R2) still exists in every language · C9 invalid config is rejected clearly.

Scoring conventions: the applicable set is the same for all six (§0,1,2,3,4,5,6,7,8,9,10,11,12). §13 and §14 are N/A (no stated performance need, no trust boundary). Chapter score = min(round-half-up(10·pass/applicable), ceiling). When a defect is scored in one item and another item references it, the second item is not re-deducted.

---

## P
Chapters: §0 10 · **§1 2** · §2 10 · §3 10 · §4 10 · §5 5 · §6 7 · §7 8 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10
Failed items:
- §1 trace the full input space, **S4**. An explicit `nav:` keeps its default-language titles in every language. Nothing in `LanguageSite.configure` (design-P/mkdocs/structure/languages.py:228) or in the build localizes nav titles. Violates R6/C3.
- §5 program to an interface / calibrate it, S2. Themes are bound to the concrete `LanguageSite` (build methods `configure`/`get_files` included) through `config.language_site` (config/defaults.py:209; themes/mkdocs/base.html:2,117,120 `config.language_site.alternates(page)`, `.language.direction`). This is the theme seam (X4). The Demeter chain references this defect.
- §5 information hiding, S1. Imports the private `_default_exclude` and `_get_files_in` from files (languages.py:24-25).
- §6 SRP, S2. Snapshot/`_derive` added to the generic base `Config` (config/base.py:165,259,262-293), so every Config subclass load now deep-copies its input.
- §7 DRY, S1. The strict-mode counter is duplicated (commands/build.py:260 vs :296).
Passes worth noting: the fallback rule has one owner (`fallback_order`/`resolve`, languages.py:105,176); the build pipeline stays closed behind a `get_files` strategy (build.py:281,285); C8 passes through the fallback chain; search and plugins are fresh per site; the notice lives in the themes (content.html).
**Grade 6.73** · worst §1 = 2 · (#S3, #S4) = (0, 1) · **BLOCKED**

## Q
Chapters: §0 10 · **§1 2** · §2 7 · §3 10 · §4 10 · §5 7 · §6 7 · §7 5 · §8 8 · §9 10 · §10 10 · §11 5 · §12 10
Failed items:
- §1 edge & boundary coverage, **S4**. `_without_orphans` (design-Q/mkdocs/structure/languages.py:267) drops a page that exists only in fr from every site. Violates R2/R4/C8.
- §2 flag argument, S1. `_build_site(site=None)` branches on it (commands/build.py:393,400,405,420).
- §5 information hiding, S2. `page.__dict__.pop('title', None)` reaches into Page's weak_property storage (languages.py:295).
- §6 acyclic dependencies, S2. `files.get_files` calls back into `LanguageSite.get_files` through `config._language_site` (structure/files.py:569), while languages imports files' private `_get_files` (languages.py:26).
- §7 open/closed, S2. Plugin instances are shared across sites (`configure` keeps plugins, languages.py:199), which forced the search plugin to be reopened (`_lang_from_locale`, contrib/search/__init__.py:65,76-81). X2.
- §7 localize change axes, S2. Language branches threaded into build `get_context` (build.py:51), `_build_template` (:81-84), `get_files` (files.py:569) and link resolution (structure/pages.py:455).
- §8 couplers (middle man), S1. `LanguageLink` has five pass-through properties (languages.py:116-132).
- §11 global mutable state, S1. The log filter is installed on every `mkdocs*` logger and rewrites `record.msg` (build.py:337,360,383).
**Grade 5.83** · worst §7 = 5 · (0, 1) · **BLOCKED**

## R
Chapters: **§0 2** · **§1 2** · §2 7 · §3 10 · §4 5 · §5 7 · §6 7 · §7 3 · §8 10 · §9 10 · §10 10 · §11 5 · §12 10
Failed items:
- §0 speak only published types across a seam, **S4**. The contrib search plugin reads core's private `config._language_site` (design-R/mkdocs/contrib/search/__init__.py:95). No plugin does this in the pristine code.
- §1 edge coverage, **S4**. A fr-only page exists only in the fr site ("exist only in the '{code}' site", structure/languages.py:318-320; entries come from own + default only, :250). Violates R4/C8.
- §1 fail fast, **S4**. A root-site file whose destination collides with a language site only triggers a warning (languages.py:325-331). The build continues, and because language sites are built after the root without cleaning (commands/build.py:351,368), the stray file is left inside `/<lang>/`.
- §2 boolean flag argument, S1. `prepare_site_dir=False` (build.py:368,423,431).
- §4 illegal states, S1. The `Languages` constructor accepts duplicates (only `from_config` checks).
- §4 concept fit, S2. The notice (chrome) is spliced into `page.content` (build.py:193,260).
- §5 information hiding, S2. `file.abs_src_path` is overwritten to point at another language's file (languages.py:420), plus private imports `_get_docs_files` and `_path_sort_key` (languages.py:31; structure/nav.py:9).
- §6 acyclic dependencies, S2. files→languages via config (files.py:553); nav→languages; pages↔languages.
- §7 open/closed, S2. Shared plugins forced a search reopen (search/__init__.py:76-97).
- §7 localize change axes, **S3**. Fallbacks keep `fr/`-prefixed `src_uri`s, which forces the language concept into `get_files`, nav (structure/nav.py:135,161-162,217-220), Page (structure/pages.py:51-54,130,144), link validation (pages.py:358,459,519,552), the build (build.py:50,80,260) and search.
- §7 DRY, S1. `_path_sort_key` re-encodes `file_sort_key` (files.py:603 vs :615).
- §11 global state, S1. `_reported_once` puts filters on global loggers (build.py:373-393).
**Grade 4.36** · worst = 2 · (1, 3) · **BLOCKED**

## S
Chapters: §0 10 · **§1 2** · §2 7 · §3 10 · §4 8 · §5 8 · §6 7 · §7 5 · §8 5 · §9 10 · §10 10 · §11 0 · §12 10
Failed items:
- §1 edge coverage, **S4**. A page lacking a default counterpart is removed ("so it is not part of the site", design-S/mkdocs/structure/languages.py:222-228). Violates R2/R4/C8.
- §2 do one thing, S2. The single-site `_build` doubles as the per-language builder, branching on `language_site` five times (commands/build.py:292,307,321,333,393), and `build()` dispatches on `config._language_site` (:268).
- §4 illegal states, S1. `Languages.__init__` accepts duplicates (languages.py:120); the check exists only in the config option (config/config_options.py:840-843).
- §5 information hiding, S1. `_raw_value('theme')` rebuilds the theme from pre-validation input (languages.py:187; config/defaults.py:239), plus the private `_get_files_in` (languages.py:29).
- §6 SRP, S1. MkDocsConfig snapshots and deep-copies every loaded patch (defaults.py:224-257).
- §7 localize change axes, S2. The language concept is threaded through `_build`, `get_context` (build.py:51-69), the Page constructor (structure/pages.py:56-57) and yaml (utils/yaml.py:106).
- §7 DRY, S2. `localize_nav` re-implements the nav-config grammar owned by `nav._data_to_navigation` (languages.py:288).
- §8 couplers, S2. `LanguageSite.setup_page` writes `language`, `content_language`, `language_links` and `canonical_url` into Page from inside `Page.__init__` (pages.py:57; languages.py:327).
- §8 duplicated code, S1. Clean-site and strict logic is copied (build.py:290/309 vs :422/432).
- §11 mutable state, S2. `LanguageSite` fills `_fallback_src_uris` and `_src_aliases` during `get_files` and `root_site_url` during `make_config` (languages.py:165,182,234,237), so `is_translated`, `localize_nav` and `setup_page` are order-dependent.
- §11 global state, S1. A log filter is attached to handlers (build.py:428,469).
**Grade 5.13** · worst §11 = 0 · (0, 1) · **BLOCKED**

## T
Chapters: §0 10 · **§1 2** · §2 10 · §3 10 · §4 3 · §5 10 · §6 7 · §7 8 · §8 8 · §9 10 · §10 10 · §11 5 · §12 10
Failed items:
- §1 trace the full input space, **S4**. Explicit `nav:` titles are never localized: every site derives the same nav (design-T/mkdocs/commands/build.py:264-276) and languages.py has no nav handling. Violates R6/C3.
- §4 value objects, S2. A language is a bare `str` throughout (structure/languages.py:46,59-60,80,90). The code→BCP-47 rule is re-derived in templates (`alternate.code|replace("_","-")`, themes/mkdocs/base.html:121, themes/readthedocs/versions.html:23), and display names are recomputed per page (:229,237,239).
- §4 illegal states, S1. `SiteLanguages` does not reject duplicates (only config_options.py:826-833 does).
- §4 concept fit, S2. The notice (chrome) is prepended to `page.content`, relying on `event_priority(-100)` to run after search indexing (languages.py:212,219).
- §6 SRP, S1. MkDocsConfig snapshots every patch for `derive` (config/defaults.py:215-247).
- §7 DRY, S1. The notice text lives in three places (languages.py:172 plus two theme templates).
- §8 bloaters, S1. `language_view(files, config, languages, site)` returns a `(Files, dict)` tuple (languages.py:104-105).
- §11 mutable state, S1. The plugin holds `_source_languages` and `_env` as temporary fields (languages.py:191-192).
Passes worth noting: build.py is untouched apart from the per-site loop. All language behaviour attaches at the existing plugin-event seam (build.py:275), so X2 needs no reopen. `fallback_chain` is the single owner of fallback (X3; C8 passes, drafts are handled at :138). `derive(overrides)` is the X5 seam. Only public imports are used (languages.py:26-29).
**Grade 5.71** · worst §1 = 2 · (0, 1) · **BLOCKED**

## U
Chapters: §0 10 · §1 10 · §2 7 · §3 10 · §4 5 · §5 10 · §6 10 · §7 5 · §8 10 · §9 10 · **§10 5** · §11 10 · §12 10
Failed items:
- §10 UI/domain separation, **S3** (§0 "add an interface" references it). The switcher and notice markup lives in the domain module (`_PAGE_HEADER`, design-U/mkdocs/structure/languages.py:164; `page_header`/`wrap_content` :146,155) and is injected into content by the build (commands/build.py:224-226). Nothing is exposed to TemplateContext, so a theme (X4) cannot place or restyle either without reopening core.
- §2 flag-like parameter, S1. `language_site` is threaded through `_build_site` and `_build_page` (build.py:194,224,300,333,391).
- §4 value objects, S2. A language is a bare `str` (languages.py:49,75,82,105), and the `lang` attribute gets the raw code (:160).
- §4 concept fit, S2. Chrome is placed in `page.content` (build.py:225).
- §7 open/closed, S2. Shared plugin instances (languages.py:286) forced a search reopen (contrib/search/__init__.py:65,76-81).
- §7 DRY, S2. `_nav_lookup` "mirrors mkdocs.structure.nav" (languages.py:263-264), `_nav_for` re-parses the nav grammar (:299), and `_walk_shared` re-implements the docs walk (:220-223).
Passes worth noting: the page set is the union of all languages and resolution has one owner (`_resolve` + `fallback_order`, :59,200,270), so C8 passes. C3 passes, including explicit nav (`_nav_for`). Fail-fast `BuildError`s at :241,257. The `Languages` constructor rejects duplicates (:46). Language folders are walked with the public `get_files` (:217).
**Grade 8.17** · worst §10 = 5 · (1, 0) · **CLEAR**

---

## Summary
| design | grade | worst chapter | #S3 | #S4 | gate |
|---|---|---|---|---|---|
| U | 8.17 | 5 | 1 | 0 | CLEAR |
| P | 6.73 | 2 | 0 | 1 | BLOCKED |
| Q | 5.83 | 5 | 0 | 1 | BLOCKED |
| T | 5.71 | 2 | 0 | 1 | BLOCKED |
| S | 5.13 | 0 | 0 | 1 | BLOCKED |
| R | 4.36 | 2 | 1 | 3 | BLOCKED |

**How much the ranking depends on two S4 calls.** Every single-S4 design is blocked by one of two interaction cases:
- C3 with an explicit `nav:` (blocks P and T).
- C8, a non-default-only page, which R2 explicitly allows (blocks Q and S).

Without those S4s, the §1 row becomes 10 at ×1 weight: P would be 9.47, T 8.14, Q 8.00 and S 6.88, all CLEAR. R stays blocked by its §0 seam leak and its fail-fast gap.

## Comparison
All six build each language as an ordinary site plus a root copy. They differ in five structural choices:

1. **Where language resolution enters the pipeline.**
   - Keep it closed: P injects a `get_files` strategy into an unchanged builder; T attaches an internal plugin at the existing event seam, leaving `_build_site` untouched.
   - Reopen owners, lightest to heaviest: U (a parameter through `_build_site`/`_build_page`), S (five branches in `_build` plus a Page-constructor hook), Q (`get_files`, link resolution, build context), R (the language concept spread through files, nav, Page, link validation, build and search, because fallbacks keep `fr/`-prefixed source paths).
2. **How each site's config is made.** Fresh derived configs (P, S, T) give fresh plugins and leave search alone, at the cost of snapshotting config input. Shallow copies with shared plugins (Q, R, U) forced the search plugin to be reopened, and R reads a core private attribute from inside it.
3. **The theme seam.** Q, R, S and T publish language data to templates (a value object in the context, or fields/properties on Page), so themes own the chrome. P exposes the concrete build-time site object through config. U exposes nothing and renders HTML in the domain module.
4. **The page-set policy.** Union with a fallback chain (P, T, U) satisfies "any subset" together with "every page in every language". A default-defined page set drops (Q, S) or confines (R) non-default-only pages.
5. **Explicit-nav titles.** Q, R, S and U localize them; P and T do not.

U alone avoids every correctness failure. P and T have the cleanest seams, and each would lead once its single nav-title gap was fixed. R has the heaviest spread and the most precondition failures.

No files were modified.