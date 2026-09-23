# Six-design judgement: multi-language mkdocs (simplicity-first disposition)

**Bottom line:** only U clears the gate. P, Q, R, S and T each have one S4 in §1, and each S4 is a spec interaction the design did not trace. U scores 8.86. The rest range from 5.78 to 6.48. I read the code only and ran nothing: mkdocs' dependencies are not installed here, so none of the test suites were executed.

## Step 0 — fixed inventory, taken from SPEC.md alone

**Rules and invariants (R)**
- R1 `languages:{default, others}` is valid: codes are valid, none is duplicated, and there is exactly one default.
- R2 Pages live under `docs/<lang>/`. A page may exist in **any subset** of the languages.
- R3 Each language has a site at `/<lang>/`, and the default language is also at the root.
- R4 **Every page exists in every language.** A missing translation shows the default-language page in the target language's chrome, with a visible notice.
- R5 Each language has its own navigation, using **that language's page titles where a translation exists**.
- R6 Every page links to the same page in each other language.
- R7 Each language has its own search index, holding only what that reader sees.
- R8 With no `languages` key, the build is exactly as today.
- R9 No automatic language detection or redirect.
- R10 `mkdocs serve` works.

**Change axes (X)**
- X1 Add a language.
- X2 Theme or label variation, including third-party themes.
- X3 URL layout.
- X4 Fallback policy. The unstated variant I held fixed is a fallback chain such as `fr_CA → fr → en`.
- X5 An explicit `nav:` config interacting with R5.
- X6 Stateful plugins (search and others) interacting with per-language builds.

**Acceptance cases (C)**
- C1 Building a multi-language project gives `/`, `/en/`, `/fr/` and `/he/`.
- C2 A page missing in fr is shown in fr chrome with the notice.
- C3 Each language's nav uses its own titles.
- C4 Every page has the language switcher.
- C5 Each language's search index contains only that language's content.
- C6 A project with no `languages` builds unchanged.
- C7 `serve` works.
- C8 No redirect.

**Applicable items.** They are the same for all six designs:
- §0: 3 items
- §1: 6 items
- §2: 4 items
- §3: 3 items
- §4: 4 items
- §5: 4 items
- §6: 4 items
- §7: 4 items (schema-evolution is N/A)
- §8: 3 items
- §9: 2 items
- §10: 2 items
- §11: 2 items (concurrency is N/A)
- §12: 2 items
- §13 and §14 are N/A: no performance requirement is stated and there is no trust boundary.

**Two §1 interactions decide the gate.** They are X×R cases that no listed case exercises:
- **(a)** A page that exists only in a non-default language, which is allowed by "any subset". Under R4 it must still exist in every language.
- **(b)** An explicit `nav:` title (X5) applied to a translated page, which breaks R5.

All six designs build each language as an ordinary site, plus a root copy of the default language. They satisfy C1–C8, R9 and R8.

---

## P — grade **6.43** · worst chapter §1 = 2 · #S3 = 0, #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 · §2 7 · §3 10 · §4 10 · §5 5 · §6 10 · §7 10 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Passes worth noting**
- `build()` becomes a two-line dispatch (`commands/build.py:250-255`).
- Each site goes through `_build_site(..., get_files=site.get_files)` (`build.py:285`). The source is injected as a function, not switched by a flag.
- The fallback rule has one owner: `Languages.fallback_order` plus `LanguageTrees.resolve` (`structure/languages.py:105,176`). That same owner also absorbs X4.
- The nav, pages and search modules are untouched.
- Each site gets a fresh, re-validated config (`languages.py:228-239`), so no plugin state is shared.
- Collisions are rejected (`languages.py:161`).
- `Language` and `Languages` are frozen value objects (`languages.py:44,84`).

**Failed items**
- **§1 trace full input space — S4.** Explicit `nav:` titles are reused verbatim in every language: `configure` copies `nav` unchanged, and nothing adapts titles. A translated page listed as `- Guide: guide.md` keeps the default-language title in fr's nav. This violates R5 under X5.
- **§2 no surprising side effects — S2.** The base `Config.load_dict` now deep-copies and stores every patch of every `Config`, including plugin sub-configs, and silently disables itself when a copy fails (`config/base.py:259-270`). A foundational class gains a hidden mechanism that only `MkDocsConfig` needs.
- **§5 information hiding — S1.** `languages.py:21-26` imports the private `_default_exclude` and `_get_files_in`, and `languages.py:230` calls the private `config._derive()`.
- **§5 Law of Demeter — S1.** The templates reach through `config.language_site.language.direction` and `config.language_site.alternates(page)` (`themes/mkdocs/base.html:2,114-120`, `content.html:8-9`).

## Q — grade **5.91** · worst chapter §1 = 2 · #S3 = 0, #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 7 · §1 2 · §2 8 · §3 10 · §4 8 · §5 8 · §6 10 · §7 3 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Failed items**
- **§1 trace full input space — S4.** `_without_orphans` drops any page that has no default-language counterpart from every site (`structure/languages.py:267-282`). A page in the subset `{fr}` exists nowhere, which violates R2×R4.
- **§0 encapsulation — S2.** The language concern leaks out of `languages.py`:
  - `files.get_files` silently dispatches on the private `config._language_site` (`structure/files.py:569`).
  - `pages.py:455-456` adds a language-specific `../` link-resolution hook.
  - `build.py:51,81-84` branch in `get_context` and `_build_template`.
  - §6 low-coupling and §8 shotgun-surgery findings refer to this same defect.
- **§2 flag arguments — S1.** `_build_site(site=...)` switches site-dir preparation and nav localisation on whether `site` is set (`build.py:388-421`).
- **§4 immutability — S1.** `Language` and `LanguageLink` are mutable plain classes (`languages.py:38,73`).
- **§5 information hiding — S1.** `localize_nav` pops `page.__dict__['title']`, reaching into Page's cached-property storage (`languages.py:295`). `languages.py` also imports the private `_get_files`.
- **§7 Open/Closed — S2.** One plugin set is shared across all language builds (`configure` skips `plugins`, `languages.py:188-210`). That forced a `_lang_from_locale` special case into the search plugin (`contrib/search/__init__.py:65-81`), and any stateful plugin bleeds across languages (X6).
- **§7 localize change axes — S2.** The fallback policy is spread across three places: `get_files` hard-codes own→default (`languages.py:212-243`), `links()` recomputes whether a page is translated (`297-326`), and the templates re-derive "the content is in the default language" with `languages|selectattr('is_default')|first` (`themes/mkdocs/content.html:9`, `readthedocs/base.html:174`). X4 would have to reopen all three.
- **§7 YAGNI — S2.** `_LanguageSiteLogFilter` is about 50 lines that walk every `mkdocs.*` logger, compare thread IDs and rewrite `record.msg`, to de-duplicate warnings the spec never asked about (`build.py:337-385`). `get_shared_file` adds link aliasing nobody requested (`languages.py:245-258`).

## R — grade **5.84** · worst chapter §1 = 2 · #S3 = 1, #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 5 · §1 2 · §2 8 · §3 10 · §4 7 · §5 8 · §6 10 · §7 5 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Failed items**
- **§1 trace full input space — S4.** A page with no default-language counterpart exists only in its own language's site. The code warns about it (`structure/languages.py:309-321`), and `alternates()` omits the languages that lack it (`languages.py:457+`). This violates R4.
- **§0 encapsulation — S3, structural.** Language awareness is threaded through six existing modules:
  - `nav.py:135-140, 161, 217-235`
  - `pages.py:51-54, 119-146, 358-359, 459-553`
  - `files.py:553`
  - `build.py:50, 80, 193-260`
  - `contrib/search/__init__.py:95` reads `config._language_site`
  - `LanguageSite` exposes `nav_path`, `docs_prefix`, `uses_own_title`, `describe` and `is_fallback` purely for those consumers (`languages.py:425-455`).
- **§2 flag arguments — S1.** `_build_site(prepare_site_dir=False)` (`build.py:368`).
- **§4 concept fit — S2.** A fallback page is a synthetic `File`: its `src_uri` says `fr/guide.md`, but `abs_src_path` points at the English file (`languages.py:420`). That inert stand-in is what forces the prefix-stripping hacks in nav.py.
- **§5 information hiding — S1.** `languages.py:31` imports the private `_get_docs_files` and `_path_sort_key`.
- **§7 Open/Closed — S2.** Plugins are shared across builds, and the search plugin is reopened (`search/__init__.py:73-97`).
- **§7 YAGNI — S2.** `_reported_once` uses a hard-coded list of logger names (`build.py:373`), and suppression of fallback warnings is threaded into `pages.py:519-553` and `nav.py:161`. `Languages` is a hand-written `Sequence` with `__getitem__` overloads (`languages.py:98-140`) where a tuple would do.

## S — grade **5.78** · worst chapter §1 = 2 · #S3 = 0, #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 7 · §1 2 · §2 3 · §3 10 · §4 5 · §5 8 · §6 10 · §7 7 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Passes worth noting**
- Plugins are fresh per site (`_derive`), so the search plugin is not reopened.
- The `multilingual_ui` / `render_fallback_ui` fallback serves X2 (third-party themes), so it is earned, not speculative.

**Failed items**
- **§1 trace full input space — S4.** Pages with no default counterpart are removed with a warning (`structure/languages.py:217-228`). This violates R2×R4.
- **§0 encapsulation — S2.** The `Page` constructor calls `language_site.setup_page(self)` (`pages.py:56-57`). There are further branches in `build.py:51-57, 228-230` and `utils/yaml.py:106`.
- **§2 flag arguments — S2.** `_build(..., language_site=)` forks six behaviours of the main build function:
  - the strict-mode counter (`build.py:292`)
  - site-dir cleaning (`307`)
  - where files come from (`321`)
  - nav rewriting (`333`)
  - an early return that skips the strict-mode abort (`393`)
  - public `build()` dispatching on the private `config._language_site` (`268-271`)
- **§2 CQS — S2.** `get_files`, which reads as a query, populates `_fallback_src_uris` and `_src_aliases` (`languages.py:234, 237`), and `make_config` sets `root_site_url` (`182`). `is_translated`, `setup_page` and `localize_nav` return wrong answers if called before those two. This is temporal coupling.
- **§2 surprising side effects — S1.** `MkDocsConfig.load_dict` deep-copies every patch. When the copy fails, it keeps the original, which validation later mutates (`config/defaults.py:227-237`).
- **§4 tell-don't-ask — S1.** `setup_page` writes `Page` fields from outside, including overwriting `canonical_url` (`languages.py:327-335`).
- **§4 immutability — S1.** `Language` is a mutable class with hand-written `__eq__` and `__hash__` (`languages.py:50-92`).
- **§5 information hiding — S1.** Imports the private `_get_files_in`, and reads raw patches through `config._raw_value` (`languages.py:187`).
- **§7 YAGNI — S2.** `_LanguagesLogFilter` attaches to every handler, stamps attributes onto log records and rewrites `record.msg` (`build.py:469-512`).

## T — grade **6.48** · worst chapter §1 = 2 · #S3 = 0, #S4 = 1 · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 · §2 8 · §3 10 · §4 7 · §5 10 · §6 8 · §7 10 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Passes worth noting**
- This is the smallest footprint of the six. The whole feature enters through the **existing plugin seam**: `LanguageSitePlugin` (`structure/languages.py:180-249`) is added per site in `build.py:275`.
- The files, nav, pages and search modules are untouched, and there is no log machinery.
- The fallback rule has one owner: `fallback_chain` (`languages.py:66`). It already absorbs X4 and handles drafts.
- `derive` is public, and there are no private imports.

**Failed items**
- **§1 trace full input space — S4.** Explicit `nav:` titles stay verbatim in every language. `language_view` only selects files (`languages.py:104-157`), so a translated page keeps its default-language nav title. This violates R5 under X5.
- **§2 surprising side effects — S1.** `MkDocsConfig.load_dict` deep-copies every patch (`config/defaults.py:218-228`).
- **§4 value objects — S2.** A language is a bare `str` throughout (`languages.py:46, 58-59, 81, 90-95`). The BCP-47 conversion is re-done in two theme templates with `alternate.code|replace("_","-")` (`themes/mkdocs/base.html:121`, `readthedocs/versions.html:23`).
- **§6 connascence — S1.** Correctness depends on priority numbers: `@event_priority(100)` and `@event_priority(-100)` (`languages.py:194, 212`) decide that other plugins see only this language's files and that search does not index the notice.

## U — grade **8.86** · worst chapter §7 = 5 · #S3 = 0, #S4 = 0 · **CLEAR**

**Chapter scores:** §0 10 · §1 10 · §2 8 · §3 10 · §4 8 · §5 8 · §6 10 · §7 5 · §8 10 · §9 10 · §10 10 · §11 10 · §12 10

**Passes worth noting**
- U is the only design that traces both interactions:
  - The page set is the union over all languages, with one fallback order (`structure/languages.py:199-201, 270-277`).
  - Explicit nav titles give way to translated titles (`languages.py:205, 299-314`).
- There is one owner of the resolution rule.
- A page outside every language folder fails fast (`languages.py:220-246`), and collisions raise an error (`249-260`).
- The header and notice are theme-agnostic (`languages.py:146-160`), which covers X2.

**Failed items**
- **§2 flag arguments — S1.** An optional `language_site` is threaded through `_build_site` and `_build_page` (`commands/build.py:194, 300`).
- **§4 value objects — S1.** Languages are bare `str`, and the raw code is written straight into HTML `lang` attributes (`languages.py:160`), so `pt_BR` comes out instead of the BCP-47 `pt-BR`.
- **§5 information hiding — S1.** Imports the private `_AbsoluteLinksValidationValue` (`languages.py:26`).
- **§7 Open/Closed — S2.** Plugins are shared across builds, and the search plugin is reopened (`contrib/search/__init__.py:65-81`).
- **§7 DRY — S1.** `_walk_shared` re-implements the `get_files` walk (`languages.py:220-246`), and `_nav_lookup` copies nav.py's lookup rule (`263-267`).

---

## Comparison

All six share one frame: each language is an ordinary mkdocs site, plus a root copy of the default language. They separate on three structural choices.

1. **How a per-language site gets its config.**
   - **Shallow copy with shared plugins (Q, R, U).** Cheap, but each of these had to reopen the search plugin, and X6 bleeds into third-party plugins.
   - **Re-validate from snapshotted input (P, S, T).** Isolates plugins, but adds a deep-copy mechanism to config loading. P puts it on the base `Config`, which is the most invasive choice. S and T keep it on `MkDocsConfig`.
2. **Where language awareness lives.**
   - **T** injects it through the existing plugin seam and touches no pipeline module. This is the simplest shape that is fully earned.
   - **P** swaps the file source with a one-line injected function, which is nearly as clean.
   - **U** passes a `language_site` object through two build functions.
   - **Q, S and R** thread `getattr(config, '_language_site')` checks through files, pages, nav and search. R does it most, because its "fallback `File` carries the translated `src_uri`" trick forces nav.py and pages.py to strip language prefixes.
3. **What is built beyond the spec.** Q, R and S each carry a log de-duplication and prefix-rewriting filter, 30–50 lines that nobody asked for. P, T and U do without one.

On simplicity alone, T and P are the leanest, but both skipped the explicit-nav × R5 interaction. Q, R and S carry the most unearned structure and also narrowed "any subset" into "the default defines the page set". U is somewhat less minimal than T, but it is the only design that is complete. It therefore takes the highest grade and the only clear gate.
