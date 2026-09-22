## Scoring six multi-language mkdocs designs (P–U) with the §0–§14 form

**Result:** U is the only design that isn't blocked, with a grade of 7.82. The other five each fail one precondition (S4), so their gate is BLOCKED. Their grades are close together: T 6.14, P 6.00, S 5.78, R 5.34, Q 5.31. No files were modified.

**How the checks were made.** I read each design's code changes. I then built three small test projects with every design, using scratch copies of the dependencies, and checked the output myself:
- a project whose English, French and Hebrew pages cover different subsets, including a page that exists only in French;
- the same project with an explicit `nav:` that gives titles;
- a project with a bare custom theme.

I also compared a single-language build against the unmodified codebase in both built-in themes, and ran `mkdocs serve` for every design. All six pass the listed acceptance cases C1–C8 (C8, invalid config, checked in code only). In all six the root page is real content (HTTP 200, no redirect or language detection), and the single-language HTML output is byte-identical to today's. The S4 failures below come from inputs the spec allows but does not list as cases.

### Step 0 inventory (held fixed for all six)

**Rules (R)**
- R1: `languages` has one default and some others; codes are valid and not repeated.
- R2: pages live under `docs/<lang>/`; a page may exist in any subset of languages.
- R3: each language is served at `/<lang>/`, and the default is also served at the root.
- R4: every page exists in every language. A missing translation shows the default page in that language's chrome, with a visible notice.
- R5: each language has its own navigation, using that language's page titles where a translation exists.
- R6: every page links to the same page in each other language.
- R7: each language has its own search index, holding only what its reader sees.
- R8: a site with no `languages` builds exactly as today.
- R9: no automatic language detection or redirect.
- R10: `mkdocs serve` works.

**Change axes (X)**
- X1: adding a language.
- X2: new labels in the chrome.
- X3: themes, including third-party ones.
- X4: fallback policy.
- X5: URL layout.
- X6: search language.
- Unstated variant I chose: a regional fallback chain (pt_BR, then pt, then the default).

**Acceptance cases (C)**
- C1: the site layout.
- C2: a fallback page in the other language's chrome, with the notice.
- C3: per-language navigation and titles.
- C4: links to the same page in other languages.
- C5: per-language search.
- C6: no redirect.
- C7: single-language output unchanged.
- C8: invalid config is rejected.

**Applicable chapters.** §0–§12 apply to all six, 53 items in total. §13 and §14 do not apply: the spec states no performance need and there is no trust boundary. §11 concurrency does not apply either.

### Grades

Each chapter cell reads score (weight). §13 and §14 are left out because they do not apply.

| | §0 | §1 | §2 | §3 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | Grade | Worst chapter | #S3 / #S4 | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **U** | 7(1) | 10(1) | 6(1) | 10(1) | 7(2) | 8(1) | 10(1) | 7(2) | 10(1) | 10(1) | 7(2) | 5(2) | 10(1) | **7.82** | §11 = 5 | 0 / 0 | CLEAR |
| **T** | 10(1) | 2(8) | 8(1) | 8(1) | 7(2) | 10(1) | 10(1) | 6(2) | 10(1) | 10(1) | 7(1) | 10(1) | 10(1) | **6.14** | §1 = 2 | 0 / 1 | BLOCKED |
| **P** | 10(1) | 2(8) | 8(1) | 10(1) | 10(1) | 6(1) | 8(1) | 5(4) | 10(1) | 10(1) | 10(1) | 10(1) | 10(1) | **6.00** | §1 = 2 | 1 / 1 | BLOCKED |
| **S** | 7(2) | 2(8) | 4(2) | 10(1) | 8(1) | 8(1) | 10(1) | 6(2) | 10(1) | 10(1) | 7(1) | 10(1) | 10(1) | **5.78** | §1 = 2 | 0 / 1 | BLOCKED |
| **R** | 5(4) | 2(8) | 8(1) | 10(1) | 7(2) | 7(2) | 7(2) | 4(2) | 7(2) | 10(1) | 7(1) | 5(2) | 10(1) | **5.34** | §1 = 2 | 1 / 1 | BLOCKED |
| **Q** | 5(4) | 2(8) | 6(1) | 10(1) | 8(1) | 7(2) | 7(2) | 4(4) | 10(1) | 10(1) | 10(1) | 5(2) | 10(1) | **5.31** | §1 = 2 | 2 / 1 | BLOCKED |

### The design-by-design form

In every citation, "languages" means that design's `mkdocs/structure/languages.py`. Other paths are relative to that design's `mkdocs/` folder.

**P — each language built as a whole site from a fresh copy of the config; the file set is passed in as a function**

*Passes worth noting:*
- `build.py:253,281` passes `get_files` into the site build as a parameter, so navigation, pages and search never need to know about languages.
- Fallback lives in one place: `Languages.fallback_order` and `LanguageTrees.resolve` (languages 105-107, 176-187). The unstated fallback-chain variant therefore lands at that one method.
- A page that exists only in French appears in every language (verified).
- `Language` and `Languages` are frozen value objects, and repeated codes are rejected when `Languages` is constructed (languages 43-107).

*Failures:*
- §1 Trace the full input space — **S4**. Crossing R5 with an explicit titled `nav:`, the French navigation shows "Guide" even though `fr/guide.md` exists. The per-site config reuses the same nav and nothing replaces its titles (languages 228-239; verified). The test `test_explicit_nav_is_shared_with_fixed_texts_verbatim` shows this was a deliberate reading of the spec. It still breaks R5.
- §7 Open/Closed — **S3**. Along X3 (themes), both the notice and the language links exist only inside the two built-in themes (`themes/mkdocs/content.html:8-16`, `themes/mkdocs/base.html:113-126`, `themes/readthedocs/base.html:161-169`, `themes/readthedocs/versions.html:26-32`). With a custom theme there is no notice and no links (verified). Each new theme has to repeat the rule.
- §7 DRY — S1. The strict-mode warning counter block is duplicated (`build.py:258-272`, repeated inside `_build_site`).
- §2 No surprising side effects — S1. `Config._derive` rebuilds from the original input, so values assigned after loading are silently lost unless they are carried over by hand (`config/base.py:272-293`).
- §5 Information hiding — S1. Imports the private `_get_files_in` and `_default_exclude` from the files module (languages 21-27).
- §5 Law of Demeter — S1. Templates chain `config.language_site.alternates(page)` and `...language.direction` (`themes/mkdocs/base.html:117-120`).
- §6 Single responsibility — S1. The base `Config` class, which every sub-config uses, now snapshots its input on every load (`config/base.py:160-270`).

**Q — a site per language from a deep-copied config; one plugin set shared by all language builds**

*Failures:*
- §1 Edge and boundary coverage — **S4**. A page that exists only in French is dropped from every site with a warning (`_without_orphans`, languages 267-282; verified). This contradicts both "a page may exist in any subset" and "every page exists in every language".
- §0 Encapsulation — **S3**. Existing pipeline modules now branch on a hidden, private `config._language_site`: `files.py:569`, `pages.py:455-456`, and `build.py:51,81-84,400,421`.
- §7 Open/Closed — **S3**. The notice and the links exist only in the themes (`themes/mkdocs/content.html:8-17`, `themes/readthedocs/base.html:173-181`, and a `languages` block in each base template). A custom theme gets neither (verified).
- §7 Localize change axes — S2. "Fall back to the default" is hard-coded in `get_files` (219-229), `_without_orphans` (267-282) and `links` (309-312). The fallback-chain variant reopens all three.
- §7 DRY — S2. "Is this page translated" is worked out twice: `file.lang` in `localize_nav` (294) and `pages_by_language` in `links` (312). Each language folder is also walked twice (261 and 341).
- §5 Information hiding — S2. `page.__dict__.pop('title')` reaches into how Page caches its title (languages 295).
- §6 Acyclic dependencies — S2. A hidden cycle: the files module calls `LanguageSite.get_files`, which calls the files module's private `_get_files` (`files.py:569`, languages 26).
- §11 Minimize shared mutable state — S2. One plugin set serves every language build (languages 197-203). The search plugin needed a `_lang_from_locale` state patch as a result (`contrib/search/__init__.py:65-81`).
- §2 Flag arguments — S1. `_build_site(site=None)` switches between two modes (`build.py:388-421`).
- §2 No surprising side effects — S1. The log filter attaches itself to every mkdocs logger and rewrites `record.msg` (`build.py:337-386`).
- §4 Immutability — S1. A mutable `File.lang` field is added and set after construction (languages 262-264).

**R — a site per language, with each fallback file presented as if it were the translation**

*Failures:*
- §1 Edge and boundary coverage — **S4**. A page that exists only in French is published only on the French site. `check` itself warns that it "exist[s] only in the 'fr' site" (languages 308-322; verified).
- §0 Encapsulation — **S3**. This design bends the most existing modules, all through `getattr(config, '_language_site')`:
  - `files.py:553`
  - `nav.py:135-141,161,217-235`
  - `pages.py:51-54,119-146,358-359,459,519,552`
  - `build.py:50,80`
  - `contrib/search/__init__.py:95`
  - `theme.py:125`
- §4 Concept fit — S2. A fallback is modelled as a made-up French file: `src_uri` is `fr/guide.md` but `abs_src_path` points at the English source (languages 411-421). The tell is the code that exists only to undo that disguise: `describe()` (435-440) and the fallback warning suppression in `nav.py` and `pages.py`.
- §5 Information hiding — S2. `nav.py:220` glues `docs_prefix` onto paths itself, so knowledge of how source paths are laid out leaks into navigation.
- §6 Acyclic dependencies — S2. Hidden cycles run from the files, nav and pages modules into the languages module and back.
- §7 Open/Closed — S2. The language switcher exists only in the themes (`themes/mkdocs/base.html:174`, `themes/readthedocs/base.html:111`). The notice, by contrast, has one core owner with a theme override (`build.py:201-219`).
- §7 Localize change axes — S2. The default-only fallback is hard-coded in `LanguageTree.__init__` (246-257), `content_language` (442-443) and `check` (303-322).
- §7 DRY — S2. `_path_sort_key` re-implements `file_sort_key` with a different README rule (`files.py:615-619`). The notice markup exists in three copies (`build.py:193-198` and both `untranslated.html` templates).
- §8 Change-preventers — S2. The "report each problem once" rule is scattered across four places: `build.py:373-399`, `nav.py:161`, `pages.py:519` and `pages.py:552`.
- §11 Minimize shared mutable state — S2. Plugin instances are shared across language builds, and the search plugin reads `_language_site` (`search/__init__.py:95`).
- §2 Flag arguments — S1. `_build_site(prepare_site_dir: bool)` (`build.py:423,431`).
- §10 UI/domain separation — S1. Default notice HTML sits in `commands/build.py:193-198`.

**S — a site per language from a fresh copy of the config with `docs_dir` pointed at the language folder; a theme can declare that it draws the language UI itself**

*Passes worth noting:*
- For themes that don't declare `multilingual_ui`, core adds the notice and links itself (`build.py:228-230`). A custom theme gets both (verified).
- Plugins are fresh for each language build.

*Failures:*
- §1 Edge and boundary coverage — **S4**. A page that exists only in French is dropped (languages 215-229; verified).
- §0 Encapsulation — S2. The private config attribute is read by `Page.__init__` (`pages.py:56-57`), by `yaml.py:106`, and by build (`build.py:51,268-271`).
- §2 Do one thing — S2. `_build` covers both the whole-site and single-language modes, with six branches on `language_site` (`build.py:292,302,307,321,333,393`). It also relies on a recursion guard held in config state.
- §2 Command–query separation — S2. `get_files` quietly fills `_fallback_src_uris` and `_src_aliases`, which `setup_page` and `localize_nav` later depend on (languages 230-237). `make_config` likewise sets `root_site_url` (182). The result is an order dependency between calls.
- §7 Localize change axes — S2. The default-only fallback is hard-coded in `get_files` (212-237) and `setup_page` (329-331).
- §7 DRY — S2. `localize_nav` re-implements the nav-config grammar and file lookup (288-319). The notice condition and markup exist three times (languages 382-394, `themes/mkdocs/content.html:9`, `themes/readthedocs/base.html:164`).
- §2 No surprising side effects — S1. Values set after loading are lost when the config is copied, and the log filter rewrites messages.
- §4 Rich domain model — S1. `setup_page` pushes fields into Page from outside and overwrites its `canonical_url` (327-335).
- §5 Information hiding — S1. Imports the private `_get_files_in` and re-reads raw config input through `_raw_value` (187).
- §10 UI/domain separation — S1. `_UI_TEMPLATE` HTML lives in the structure module (382-394).

**T — a site per language from a fresh copy of the config; the language behaviour is applied by an internal plugin on the existing plugin events**

*Passes worth noting:*
- `LanguageSitePlugin` hooks `on_files`, `on_template_context` and `on_page_context` (languages 180-249). No existing pipeline module reads any language state.
- `fallback_chain` is one method (66-68), so the unstated fallback-chain variant lands in one place.
- A page that exists only in French appears in every language (verified).
- The notice has one core owner with a theme-template override, and a custom theme gets it (verified).

*Failures:*
- §1 Trace the full input space — **S4**. The explicit-`nav:` titles problem is the same as P's, and deliberate here too (`test_explicit_nav_is_shared_and_resolved_per_language`). There is no language-aware navigation step (verified).
- §4 Value objects over primitives — S2. Languages are bare `str` codes throughout (languages 46, 59-60, 90-95). Turning `pt_BR` into `pt-BR` is redone inside templates (`themes/mkdocs/base.html:121`, `themes/readthedocs/versions.html:23`).
- §7 Open/Closed — S2. The switcher exists only in the built-in themes (`themes/mkdocs/base.html:113-126`, `themes/readthedocs/versions.html:20-26`).
- §3 One word per concept — S1. `LanguageLink.url` is relative to the current page and must not go through the `url` filter (languages 83). Everywhere else in mkdocs, `url` is relative to the site root.
- §2 No surprising side effects — S1. The same loss of after-loading values on copy (`config/defaults.py:230-254`).
- §7 DRY — S1. The notice text exists three times (languages 172-177 and both `untranslated-notice.html` templates).
- §10 UI/domain separation — S1. Default notice HTML sits in the structure module (languages 172-177).

**U — a site per language from a shallow config copy; core adds the language header to each page's content, with no theme changes**

*Passes worth noting:*
- One resolution owner: `Languages.fallback_order` plus the precedence list passed to `_resolve` (languages 59-63, 199-201, 270-277).
- A page that exists only in French appears in every language, and explicit nav titles give way to translations (both verified).
- The notice and links reach any theme (custom theme verified).
- `build.py` receives the language site as an explicit parameter; there is no hidden channel.

*Failures:*
- §4 Value objects over primitives — S2. Languages are bare `str` (languages 40-57, 82-85). `lang="{source_language}"` emits `pt_BR`, which is not a valid HTML language tag (160, 167-168).
- §7 DRY — S2. `_nav_lookup` copies how `nav.py` resolves targets (263-267). `_nav_for` re-parses the nav grammar (299-314). `_walk_shared` re-implements the docs walk without README/index conflict handling (220-246). "Translated" is computed twice (202 and 130-131).
- §10 UI/domain separation — S2. The domain module renders the language menu and notice HTML, and themes have no hook to move the switcher into the chrome (languages 146-175).
- §11 Minimize shared mutable state — S2. Plugins are shared across language builds (languages 284-287), with the same search-plugin `_lang_from_locale` patch as Q (`search/__init__.py:65-81`).
- §0 Encapsulation — S1. `_build_page` gained a language parameter and injects the header inline (`build.py:194,224-227`).
- §2 Do one thing — S1. `get_language_sites` walks, validates, resolves, rewrites the nav and builds configs all in one function (183-208).
- §2 Flag arguments — S1. An optional `language_site` mode parameter on `_build_site` and `_build_page` (`build.py:194,300`).
- §5 Information hiding — S1. Imports the private `_AbsoluteLinksValidationValue` (languages 26).

**Seen but not scored**
- Missing theme message catalogs (a data gap, not a design choice).
- No right-to-left `dir` attribute in T and U.
- The French 404 page's base URL when `site_url` is unset: Q, R and T handle it; P, S and U do not. The pre-existing mkdocs limitation carries over.
- Drafts: R and T fall back to a published version of a draft translation. The others are unaffected in practice, because draft patterns apply to the same path in every language.

### How the six compare

All six build each language as a complete ordinary site. What separates them is where the language logic sits and whether the rest of the pipeline can reach it.
- **T** has the cleanest ownership. Everything language-related is one module applied through the existing plugin event seam. Fallback is a single chain, and no core module reads language state.
- **P** is nearly as clean, keeping the pipeline unaware of languages by passing it the file set.
- Both P and T chose to show explicit nav titles verbatim, which breaks R5. P also left the notice and switcher inside each built-in theme, which is S3 on the theme axis.
- **Q and R** reach the language state through a private attribute on the config, which the files, pages and nav modules check, and R also threads it into search. That spreads one concept over many owners (S3). R adds a disguised fallback file whose effects then have to be undone in several places. Both share plugin instances across language builds.
- **S** sits between those two groups. Core owns a fallback UI that any theme can take over by declaration, but its build function runs two modes on one flag, and its file gathering mutates state.
- **Q, R and S** all treat the default language as the definition of the page set. That breaks the rule that a page may exist in any subset of languages, which is their S4.
- **U** is the only design without an S4. It resolves pages over the union of all languages with one precedence owner, and puts the notice and links in core, so any theme gets them. Its costs are local: plain string language codes, copied nav-parsing logic, HTML in the domain module and shared plugin instances. None of them spread across owners.
- On the unstated fallback-chain variant, P, T and U change in one method. Q, R and S each reopen two or three methods inside their language module.