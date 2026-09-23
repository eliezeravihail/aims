# Phase 0 — the judge's report, verbatim

Scored blind, labels K/L/M/N; mapping in `MAPPING-REVEALED.txt`. Extracted from the judge's transcript, unedited.

---

## Step 0: the inventory, taken from SPEC.md alone and applied to all four designs

**R (rules and invariants)**
- R1: `languages: {default, others}` is validated. Exactly one default, no duplicates, codes usable as a directory and a URL segment.
- R2: pages live under `docs/<lang>/`, and a page may exist in any subset of the languages, including a subset without the default.
- R3: each language has a site at `/<lang>/`, and the default language is also served at the root.
- R4: every page exists in every language. A missing translation shows the default-language page in the target language's chrome, with a visible "not translated" notice.
- R5: each language has its own navigation, using translated titles where a translation exists.
- R6: every page links to the same page in every other language.
- R7: each language has its own search index containing only what that language's reader sees.
- R8: a site with no `languages` builds exactly as today.
- R9: no language detection or redirect.
- R10: no translation tooling.
- R11: `serve` serves the site.

**X (change axes)**
- X1: add a language.
- X2: per-language chrome and labels.
- X3: per-language artifacts (search, sitemap, 404).
- X4: plugins whose behaviour depends on the language.
- X5 (unstated variant): a fallback chain, for example pt_BR → pt → en.

**C (acceptance cases)**
- C1: the /en, /fr, /he and root layout.
- C2: an untranslated page in fr shows en content with fr chrome and a notice.
- C3: fr nav titles.
- C4: the language switcher on every page.
- C5: per-language search index contents.
- C6: single-language output is byte-identical.
- C7: serve.
- C8: no redirect.
- C9: invalid config is rejected clearly.

**Applicable items (the same set for all four).** 57 items:
- §0: 4
- §1: 6
- §2: 6
- §3: 3 (one word per concept, no dead or commented-out code, failure speaks the consumer's concept)
- §4: 6
- §5: 6
- §6: 7
- §7: 6
- §8: 5
- §9: 3
- §10: 4
- §11: 4 (no real concurrency, so §11.5 is N/A)
- §12: 4
- §13 is N/A (no performance requirement). §14 is N/A (the site author is trusted; all four still validate codes against path injection).

**Behaviour probes.** I built and served a scratch project with each tree, using a scratchpad virtualenv; no files were modified. All four meet C1–C8 on the common path:
- The single-language HTML is identical to pristine; the only differences are theme asset and catalog files.
- `serve` returns 200 for `/`, `/fr/guide/`, `/he/` and `/fr/search/search_index.json` on all four.
- There are no redirects.
- Each fr index holds fr pages plus the en fallback content.
- fr navigation shows "Accueil".

**The one behavioural divergence:** L drops a page that exists only in `fr/`. There is no `/fr/only-fr/` or `/en/only-fr/`, only a warning. K, M and N serve it everywhere.

---

## K — grade **8.56** · worst chapter 7 · (#S3 0, #S4 0) · **CLEAR**

**Chapter scores:** §0 10 · §1 10 · §2 8 · §3 7 · §4 10 · §5 10 · §6 10 · §7 7 (×2) · §8 7 (×2) · §9 10 · §10 10 · §11 7 (×2) · §12 10

**Failed items**
- **§7 Open/Closed — S2.** The search plugin had to be reopened to re-derive its language for each site, because `on_config` runs only once, with the user's locale (`contrib/search/__init__.py:76-98`). Any third-party plugin that reads `theme.locale` in `on_config` gets the wrong language on the fr and he sites (X4).
- **§7 DRY — S2.** `LanguageSite.localize_nav` reproduces nav.py's nav-config grammar and its absolute-link rule. It imports `_AbsoluteLinksValidationValue` to do so (`structure/languages.py:318-340`, duplicating pristine `nav.py:205-209`).
- **§8 OO-abusers — S2.** The single-language vs multi-language choice is a switch on `site is None` spread through build.py (`commands/build.py:50,98,424,429,438,456`), plus `site=` threaded through four builder signatures (39, 85, 123, 161).
- **§11 Minimize shared mutable state — S2.** `LanguageSite.configure` mutates the shared config in place (`docs_dir`, `site_dir`, `site_url`, `nav`, theme locale) and restores it afterwards (`structure/languages.py:214-234`). `build.py:440` also sets `config.nav` in place. Plugins see a config that is re-pointed for each site.
- **§2 CQS — S1.** `collect_files` returns the files and also sets `_translated` and `_content_languages` (`structure/languages.py:236-289`).
- **§3 Failure speaks the consumer's concept — S1.** `src_uri` is now relative to the language directory, but the messages were not updated, so warnings say "Doc file 'guide.md'…" without naming the language.

**Passes worth citing**
- Frozen value objects `Language` and `Alternate` (`structure/languages.py:63-119`).
- The fallback order has a single owner, the `chain` in `collect_files` (`structure/languages.py:263`), so X5 is a one-line change.
- Root collisions fail fast (`structure/languages.py:291-302`).
- `get_files` gains `docs_dir` and `path_prefix` additively (`structure/files.py:527,554`).
- The `!relative` YAML tag is fixed through the public `file.src_dir` (`utils/yaml.py:108`).
- The dependency graph is acyclic.

---

## L — grade **6.00** · worst chapter 2 · (#S3 0, #S4 1) · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 (×8) · §2 7 · §3 10 · §4 7 · §5 10 · §6 7 (×2) · §7 7 (×2) · §8 6 (×2) · §9 10 · §10 10 · §11 7 (×2) · §12 10

**Failed items**
- **§1 Functional correctness — S4 (R2, R4, C1).** The page set of every site is fixed to the default language's pages (`structure/languages.py:236-240`). A translation with no default counterpart is warned about and dropped (`structure/languages.py:263-268`). A page that exists in a subset of languages without the default therefore exists in no language. The probe confirmed that `/fr/only-fr/` is missing. The same root decision hard-wires the default as the only fallback source, which blocks X5; that is referenced here, not deducted again.
- **§6 Low coupling — S2.** The generic nav module now depends on the languages feature: `_is_translation` reads `config.languages` and `File.language` inside `_data_to_navigation` (`structure/nav.py:223-232`).
- **§7 Open/Closed — S2.** The search plugin was reopened (`contrib/search/__init__.py:65-92`).
- **§8 OO-abusers — S2.** A switch on `site` / `_language_site` (`commands/build.py:49,79,345,363,371,385,389`).
- **§8 Bloaters — S1.** `LanguageSite.get_files` is about 75 lines, with three nested helpers and interleaved policy (`structure/languages.py:198-272`).
- **§11 Minimize shared mutable state — S2.** `activated()` mutates and restores the shared config (`structure/languages.py:182-196`).
- **§2 CQS — S1.** `get_files` also sets `_written_in` (`structure/languages.py:241`).
- **§2 No surprising side effects — S1.** Validating `languages` overwrites the user's `theme.locale` (`config/config_options.py:1299`).
- **§4 Value objects over primitives — S1.** `File.language` is a bare `str` code even though a `Language` type exists (`structure/files.py:238`).
- **§4 Immutability — S1.** `Language` and `PageAlternate` are mutable classes, and `Language` has a hand-written `__eq__`/`__hash__` over mutable fields (`structure/languages.py:49-88, 106-122`).

**Passes worth citing**
- `docs_uri` gives one owner for how files are named in messages (`structure/files.py:264`), which is why L passes §3.
- The notice is rendered in one place (`commands/build.py:222-284`).

---

## M — grade **6.04** · worst chapter 2 · (#S3 0, #S4 1) · **BLOCKED**

**Chapter scores:** §0 2 (×8) · §1 10 · §2 8 · §3 7 · §4 7 (×2) · §5 10 · §6 7 (×2) · §7 8 · §8 6 (×2) · §9 10 · §10 10 · §11 10 · §12 10

**Failed items**
- **§0 Across a seam, published types only; no reaching into internals — S4.** `localize_nav_titles` in `mkdocs/languages.py`, which sits outside `structure/`, reads `vars(page)` and `page._title_from_render` (`languages.py:342-348`). This means it depends on Page's private representation and re-derives Page's own title rule outside Page. §5 information hiding references this defect rather than deducting again.
- **§4 Rich model / Tell-Don't-Ask — S2.** `LanguageSite` is mostly data. The free function `get_site_files` fills `site.untranslated` from outside (`languages.py:273, 310`). Config derivation, nav localisation and context building are also free functions around it.
- **§6 Acyclic dependencies — S2.** The generic `structure.files.get_files` dispatches into `mkdocs.languages` (`structure/files.py:557-561`), and `languages.get_site_files` imports `structure.files` back (`languages.py:270`). The cycle is hidden by deferred imports. `config_options` also imports `languages` at module load (`config/config_options.py:36`).
- **§8 OO-abusers — S2.** A switch on `get_language_site(config)` (`commands/build.py:59,78,220,369`, `structure/files.py:559`).
- **§8 Couplers (middle man) — S1.** `LanguageContext` and `AlternateLink` are made of delegating properties (`languages.py:362-372, 432-462`).
- **§7 Open/Closed — S1.** The search plugin had to be made re-entrant, because the shared plugin instance's `on_config` now runs for every site (`contrib/search/__init__.py:65-81`).
- **§2 CQS — S1.** `get_site_files` returns the files and mutates the site (`languages.py:257-315`).
- **§3 Failure speaks the consumer's concept — S1.** Messages show the language-relative path without the language ("Doc file 'about.md'…").

**Passes worth citing**
- Each site gets a derived config copy instead of a mutated shared one (`languages.py:233-254`, `theme.py:125`), so M passes §11.
- `Language` rejects invalid codes in its constructor, and `LanguageSite` rejects a non-default root (`languages.py:85-88, 181-182`).
- The fallback order has one owner (`languages.py:290-310`).
- Root collisions fail fast (`languages.py:318-326`).

---

## N — grade **5.91** · worst chapter 2 · (#S3 0, #S4 1) · **BLOCKED**

**Chapter scores:** §0 10 · §1 2 (×8) · §2 5 · §3 7 · §4 7 (×2) · §5 8 · §6 10 · §7 7 (×2) · §8 6 (×2) · §9 10 · §10 10 · §11 10 · §12 10

**Failed items**
- **§1 Fail fast — S4 (R3, C9).** The root copy silently drops default-language files whose paths collide with a language site, and only the primary site warns (`structure/languages.py:351-361`). The build ships a root site that is missing pages, where K, L and M raise a `BuildError`. A missing default-language directory is likewise only a warning (`config/config_options.py:989`). **This is the most judgment-dependent call in the whole form:** warn-and-continue is mkdocs' usual convention, and `--strict` would abort. Scored as a pass, N would be CLEAR at about 8.1.
- **§4 Concept fit — S2.** A fallback page is a synthetic `File` that claims `fr/<path>` but has its `abs_src_path` swapped to the en file (`structure/languages.py:319-330`). It needs compensating code elsewhere: `real_src_uri` (369-372), overriding `edit_uri`, and a patch in yaml.py.
- **§7 DRY — S2.** `localize_nav` re-implements the default-nav construction with `nest_paths` (`structure/languages.py:391-398`, duplicating pristine `nav.py:136`) and re-walks the nav grammar. This follows from keeping the language prefix in `src_uri`.
- **§7 Localize change axes — S2.** The log-deduplication policy is scattered: `is_primary` (`structure/languages.py:252-255`), the `quiet()` sites (`commands/build.py:307,325,353,407-415,431`) and `structure/languages.py:300,356`.
- **§8 OO-abusers — S2.** This is the widest `_language_site` switch of the four (`commands/build.py:50,59,81,223,263,268,288,296,307,412`, `utils/yaml.py:107`).
- **§8 Bloaters — S1.** `localize_files` is about 90 lines with six concerns (`structure/languages.py:274-362`).
- **§5 Law of Demeter — S1.** yaml.py reaches through the config to the site: `self.config._language_site.real_src_uri(...)` (`utils/yaml.py:107`).
- **§2 Do one thing — S1.** The public `build()` is dual-mode, switching on a hidden config attribute and recursing into itself (`commands/build.py:261-266, 418-432`).
- **§2 CQS — S1.** `localize_files` also sets `_sources` and `_translated` (`structure/languages.py:307-330`).
- **§2 No surprising side effects — S1.** Every `load_dict` now deep-copies and records its patch, and swallows any exception to `None`, including in single-language builds (`config/defaults.py:227-233`).
- **§3 One word per concept — S1.** `Translation.is_translated == False` means "a translation that is not translated" (`structure/languages.py:187-205`).

**Passes worth citing**
- Each language gets a freshly validated config with its own plugin instances (`config/defaults.py:235-256`, `structure/languages.py:257-267`). As a result the search plugin is untouched and passes X4; N is the only design that passes §7 Open/Closed outright.
- There is no shared mutation (§11 passes).
- The fallback order is modelled once, in `_order` (`structure/languages.py:269-272`).
- `LanguageCode` catches the YAML-boolean `no` (`config/config_options.py:926`).

---

## Comparison

All four share the same skeleton:
- A `LanguageSite` for each language plus a default-language copy at the root.
- A full ordinary build for each site, which is what gets per-language search, chrome and serve for free.
- The notice injected into `page.content` in `_build_page`.
- A branch on "is there a language site" spread through `build.py`. None of the four models that dimension as a strategy or null object, which is why every one takes the §8 S2.

**What separates them is how each site gets its configuration and how each learns about the page it shows.**
- **K** mutates the shared config in place and restores it. It keeps every language concern inside `LanguageSite`, owns the fallback order in one place, fails fast on collisions, and leaves nav.py and pages.py untouched. The cost is duplicating the nav-config grammar and reopening the search plugin. It is the only design with no precondition failure.
- **L** also mutates in place. It hard-wires the default as the only source of pages, so a translation-only page is lost (the S4). It also reopens nav.py with language knowledge.
- **M** derives a config copy for each site, which is a structural improvement over K and L. But its nav-title localisation reads Page's private state from outside the structure package (the S4), and it introduces a files↔languages cycle and an anemic `LanguageSite`.
- **N** has the strongest isolation: a freshly validated config and fresh plugins for each language, and the search plugin is untouched. But keeping the language prefix in `src_uri` leads to a synthetic fallback `File`, a re-implemented default nav, patches reaching through into yaml.py, and scattered log-quieting. It also warns and continues on root collisions instead of rejecting them (the S4, and the most debatable call).

On the §0–§14 reading, **K ranks clearly first**. M, L and N are clustered near 6 and all BLOCKED:
- L's S4 is a spec behaviour the probe confirmed.
- M's is a seam leak.
- N's is a fail-fast policy choice; scored as a pass, N would be CLEAR at about 8.1.

Two things I noted but did not score, because they are message-catalog content rather than structure: only N ships a French translation of the notice as a compiled `.mo`, and L adds no fr catalog entry for its notice.