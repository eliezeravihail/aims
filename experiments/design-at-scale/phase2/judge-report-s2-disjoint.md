## Report: nine incremental-rebuild designs scored on §0–§14, from code properties only

### Step 0: the inventory, fixed from SPEC.md before opening any design

**R (rules and invariants)**
- R1: after any single edit, the site on disk is exactly what a full build produces. This holds for `serve` and for `--dirty`.
- R2: editing a default-language page updates it in the default site, in the root copy, and in every language that shows it untranslated.
- R3: editing a translation updates only that language's page.
- R4: adding a translation replaces the fallback in that language: the page, its nav title, and the cross-language links to it.
- R5: deleting a translation restores the fallback.
- R6: a title rename updates every nav and every cross-language link that shows the title.
- R7: an edit does not rebuild pages it cannot affect.

**X (change axes)**
- X1: a page's HTML comes to depend on a file other than its own source, for example a Markdown extension or plugin that includes a snippet.
- X2a: the cross-language link starts to show another language's title or translation state. The spec's own wording anticipates this ("every cross-language link that shows it").
- X2b: the templates show more of the neighbouring pages, for example front-matter fields in the nav.
- X3 (the unstated variant): a per-language fallback chain, for example fr→es→default.
- X4: languages are added or removed.

**C (acceptance cases)**
- C1: default-language edit with fr untranslated.
- C2: translation edit.
- C3: add a translation.
- C4: delete a translation.
- C5: title rename.
- C6: content-only edit has minimal effect.
- C7: `--dirty` result equals a full build.
- C8: the root alias stays in sync.

**How I calibrated severity** (applied the same way to all nine)
- A wrong output under a mainstream setting that exists today is §1, S4. The case that triggered this: a Markdown extension that reads other files, such as snippets, left unguarded.
- A dependency set that is restated by hand, which a foreseeable X would force open, is §7 quality (S1–S3). It is not treated as S4.
- The Page render-state snapshot being defined outside Page is scored once, under §7 "schema evolution one owner". It is not deducted again under §0.
- The `_src_uris` subclass hijack is scored once, under §9.
- R7 (minimality) is scored under §13, which applies here because the spec states the requirement.
- §3 and §14 are not applicable. §3 is excluded so that naming and comments earn no credit.
- Rounding is half-up. A chapter's score is min(computed score, ceiling of its worst failed item).

### Summary

Ranked by grade, highest first.

| Design | Grade | Worst chapter | #S3 | #S4 | Gate |
|---|---|---|---|---|---|
| E | 8.0 | 5 | 1 | 0 | CLEAR |
| H | 7.6 | 0 | 0 | 0 | CLEAR |
| K | 7.1 | 0 | 1 | 0 | CLEAR |
| J | 6.6 | 4 | 3 | 0 | CLEAR |
| G | 5.4 | 0 | 3 | 1 | BLOCKED |
| D | 5.0 | 0 | 4 | 0 | CLEAR |
| M | 4.2 | 0 | 3 | 1 | BLOCKED |
| L | 3.8 | 0 | 2 | 1 | BLOCKED |
| F | 3.6 | 0 | 2 | 1 | BLOCKED |

Items that pass in every design (cited in each design's own module):
- **§5 one owner.** No incremental module restates the language fallback rule.
- **§7 X3 localize.** The incremental code only observes the chosen source path or language. A change to the fallback chain never reopens it.
- **§10 boundary.** The incremental policy sits in its own module.
- **§12.** Incremental tests are present in every design.
- **§1 C1–C8.** Traced as passing for every design with the shipped themes.

All paths below are relative to `/tmp/claude-0/phase2/judge-s2/design-<L>/mkdocs/`.

---

### D — grade 4.95 · worst chapter 0 · (#S3 4, #S4 0) · CLEAR

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 (×4) | 10 | 8 | 10 | 10 | 10 | 4 (×4) | 0 (×2) | 10 | 10 | 10 | 10 | 0 (×2) |

**Failed items**
- **§0b, S3.** Trackability is keyed to a concrete plugin class: `isinstance(plugin, SearchPlugin)` at `commands/incremental.py:33,120`. The commands module depends on a contrib implementation, and a safe plugin cannot opt in. §6b refers to this item and is not deducted again.
- **§0a, S2.** Reads File's private `_content` at `incremental.py:301`.
- **§7a, S3 (X2a).** A whole site is skipped when its own sources are unchanged: `incremental.py:235-239` and `build.py:384-386`. If the cross-language link starts showing another language's state, this is silently stale, and the fix means reopening the skip rule.
- **§7b, S3 (X2b).** A page's output is assumed to be its own render plus a hand-picked "chrome" of titles and URLs: `incremental.py:271-272,325-336`.
- **§7c, S3.** Page render state is snapshotted and restored outside Page, including writes to `page._title_from_render`: `incremental.py:150-197`.
- **§8a, S2.** `rebuild is None` branches are threaded through `_build_site`: `build.py:356,384,402,421,430,432,442,448`.
- **§8b, S2.** `_show_unchanged_page` is a parallel copy of `_build_page`'s context path and has already diverged: it never sets `page.active`. See `build.py:251-265` against `:207`.
- **§2c, S1.** `has_changes` and `chrome_changed` both store state and return a value: `incremental.py:235-239,261-264`.
- **§13, S2 (R7).** A multi-language `mkdocs build --dirty` is always a full build: `build.py:286-290`.

---

### E — grade 8.0 · worst chapter 5 · (#S3 1, #S4 0) · CLEAR

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 7 (×2) | 10 | 10 | 7 | 5 (×4) | 5 | 10 | 10 | 10 | 10 | 10 |

**Failed items**
- **§7c, S3.** The page conversion state is re-declared outside Page and written back, including `page._title_from_render`: `commands/outputs.py:114-128,286-317`.
- **§2b, S2.** The record file `.<site>.mkdocs-build.json` is written beside site_dir on every multi-language build, including a plain `mkdocs build`: `build.py:333,346` and `outputs.py:137-145`.
- **§7b, S1.** Other pages are digested only by url, title, meta, canonical URL and update date (`outputs.py:536-537`), so a theme that shows a neighbour's toc would be missed. The page's own context is digested in full: `outputs.py:510-533`.
- **§6c, S1.** serve.py's temporary-directory layout is coupled to where `record_path` puts the record: `serve.py:37-43` and `outputs.py:137-145`.
- **§8a, S1.** `(outputs or AllOutputs())` appears four times (`build.py:126,192,223,294`), plus the `owns_site_dir` inference at `:379`.

**Passes worth noting**
- An `Outputs` strategy with two implementations (`outputs.py:59-99,260`).
- `produce` is tell-don't-ask.
- Conversions are not reused under non-builtin extensions (`outputs.py:438-444`).
- The record persists across processes, so R7 holds for `build --dirty` (`build.py:331`).

**Residual, not scored.** A third-party plugin whose `on_post_page` output depends on state outside its arguments is not guarded against.

---

### F — grade 3.55 · worst chapter 0 · (#S3 2, #S4 1) · BLOCKED

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 (×2) | 2 (×8) | 5 (×2) | 5 | 10 | 10 | 3 (×4) | 5 (×2) | 0 (×2) | 10 | 0 (×2) | 10 | 0 (×2) |

**Failed items**
- **§1b, S4 (X1×R1).** There is no guard for Markdown extensions. The render key covers only the page file and its lookups (`commands/incremental.py:302-309`). The build key covers only excluded files (`:516-522`). Editing a snippet under `docs/` leaves stale HTML in `--dirty` mode.
- **§7b, S3.** `page_key` hand-lists 14 page attributes and the alternates' fields: `incremental.py:327-359`. §7a (X2a) refers to this item and is not deducted again.
- **§7c, S3.** Render state is snapshotted outside Page: `incremental.py:99-179`.
- **§0a, S2.** Reads `plugins._event_origins`: `incremental.py:492`.
- **§2a, S2.** Flag arguments `unchanged: bool` and `prepare_site_dir: bool`, and `dirty=dirty and inc is None`: `build.py:263,477,568`.
- **§8a, S2.** `inc is not None` branches: `build.py:487,520,538,544,548,571`.
- **§9a, S2.** `_RecordingFiles(Files)` skips `Files.__init__` and aliases the private `files._src_uris`: `incremental.py:435-449`.
- **§11a, S2.** Module-global `_records`: `incremental.py:90`.
- **§13, S2 (R7).** `build --dirty` in a new process has no record and rebuilds every page: `incremental.py:220,226-231`.
- **§4b, S1.** Two-phase `_Rendering`: `digest=''` is set, then reassigned (`incremental.py:133,147`).
- **§2c, S1.** `is_unchanged` records and returns: `:361-373`.
- **§7d, S1.** The `_MAX_RECORDS` LRU is speculative: `:87-91,266-268`.

---

### G — grade 5.42 · worst chapter 0 · (#S3 3, #S4 1) · BLOCKED

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 2 (×8) | 8 | 10 | 10 | 10 | 4 (×4) | 10 | 10 | 10 | 10 | 10 | 0 (×2) |

**Failed items**
- **§1b, S4 (X1×R1).** There is no Markdown-extension guard. `_fingerprint` checks only plugins (`commands/incremental.py:358-382`), and a snapshot is keyed on the page's own stamp and the file set (`:198-213`). Because this is the default `mkdocs serve` path, a snippet edit now goes stale where pristine serve rebuilt everything.
- **§7a, S3 (X2a).** A site is skipped when its own sources and date are unchanged: `incremental.py:184-190` and `build.py:345-346`.
- **§7b, S3.** `_page_inputs` is hand-listed and the structure is limited to titles and URLs: `incremental.py:230-235,317-330`.
- **§7c, S3.** Render state is snapshotted outside Page: `incremental.py:135-146,205-228`.
- **§2c, S1.** `_needs` records and answers: `:276-290`.
- **§13, S2 (R7).** `build --dirty` does a full build into a staging directory, then syncs: `build.py:314,357-368`.

**Passes worth noting.** The `SitePlan` base class with `FULL_BUILD` as a null object means the pipeline has no branches (`incremental.py:44-94`).

---

### H — grade 7.59 · worst chapter 0 · (#S3 0, #S4 0) · CLEAR

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 (×2) | 10 | 10 | 5 | 10 | 10 | 7 (×2) | 5 (×2) | 10 | 10 | 10 | 10 | 0 (×2) |

**Failed items**
- **§0a, S2.** Reads File's private `_content`: `commands/incremental.py:249`.
- **§7b, S2.** The whole template context is digested, but neighbours are projected to kind, title and URL only: `incremental.py:211-215,238-241`. X2b needs a reopen here. X2a is absorbed.
- **§8a, S2.** `memo is None` branches: `build.py:232,357,385,402,420,449`.
- **§4a, S1.** The rendered state travels as `dict[str, Any]` or tuples: `incremental.py:89` and `structure/pages.py:294-316`.
- **§13, S2 (R7).** `build --dirty` is always a full build: `build.py:295-299`.

**Passes worth noting**
- §7c passes. Page owns its render-state snapshot through `_rendered_state` and `_restore_rendered_state` (`pages.py:294-329`); H is the only design that does this.
- Commands are tell-don't-ask: `populate`, `build_page`, `copy_static`.
- Extensions and plugins are guarded: `incremental.py:286-309`.

---

### J — grade 6.55 · worst chapter 4 · (#S3 3, #S4 0) · CLEAR

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 (×2) | 10 | 5 (×2) | 5 | 10 | 10 | 4 (×4) | 5 (×2) | 5 (×2) | 10 | 10 | 10 | 10 |

**Failed items**
- **§7a, S3 (X2a).** A site is skipped via `scope.unchanged`, which looks only at the site's own files and sources: `commands/incremental.py:327-335` and `build.py:379-382`.
- **§7b, S3.** The output key is hand-composed from chrome, rendered content, source and the excluded flag: `incremental.py:367-391`.
- **§7c, S3.** Render state is snapshotted outside Page: `incremental.py:144-203`.
- **§0a, S2.** Imports the private `_DirPlaceholder` from utils.yaml: `incremental.py:52,650`.
- **§2b, S2.** A pickle is written to `.cache/mkdocs/` beside mkdocs.yml on every multi-language build: `incremental.py:558-579` and `build.py:281-298`.
- **§8b, S2.** `_include_unchanged_page` duplicates the `_build_page` prologue: `build.py:462-478`.
- **§9a, S2.** `_LookupRecorder(Files)` bypasses `__init__` and assigns `_src_uris`: `incremental.py:126-137`.
- **§2c, S1.** `templates_changed` and `output_changed` mutate the record and return: `:374-391`.
- **§4b, S1.** `_PageRecord.output` stays None until it is known and is mutated in steps: `:207-211,383,397`.

**Passes worth noting.** The `SiteScope` null object (`:242-296`) and the extension whitelist (`:595-605`).

---

### K — grade 7.06 · worst chapter 0 · (#S3 1, #S4 0) · CLEAR

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 8 | 10 | 10 | 7 | 5 (×4) | 5 | 10 | 10 | 0 (×2) | 10 | 10 |

**Failed items**
- **§7c, S3.** `_Converted` re-declares and writes Page render state: `commands/incremental.py:115-160`.
- **§11a, S2.** A process-wide, irremovable `sys.addaudithook`, with global and thread-local flags: `commands/_reads.py:34-36,120-126`.
- **§7b, S2.** Other pages are digested only by title, URL and source: `incremental.py:525-538`.
- **§6c, S1.** The serve temp layout is coupled to `memory_path`: `serve.py:37-40` and `incremental.py:591-595`.
- **§8a, S1.** `is_recording` flag checks inside `BuildMemory`, `Output` and `Conversion` in place of a distinct type: `:95,106,175,193,210,342`.
- **§2c, S1.** `Output.is_current` both remembers and answers: `:89-104`.

**Passes worth noting**
- X1 is covered by tracing what the conversion reads (`_reads.py`), and extension objects are never reused (`incremental.py:463-465`).
- Page contexts are digested in full.
- One mechanism serves single-language and multi-language `--dirty` alike (`build.py:318-324`).
- The record is persisted, so R7 holds for `build --dirty`.

**Residual, not scored.** Same as E: plugin `on_post_page` output that depends on outside state.

---

### L — grade 3.81 · worst chapter 0 · (#S3 2, #S4 1) · BLOCKED

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 (×2) | 2 (×8) | 5 | 10 | 10 | 10 | 3 (×4) | 0 (×2) | 10 | 10 | 0 (×2) | 10 | 0 (×2) |

**Failed items**
- **§1b, S4 (X1×R1).** There is no guard for Markdown extensions or third-party plugins. Render reuse is keyed on the page's own bytes (`commands/incremental.py:165-187`), so in `--dirty` mode a snippet edit, or a plugin reading an outside file, leaves stale output.
- **§7b, S3.** Every input of the output fingerprint is hand-listed, including the language links' fields: `incremental.py:189-229`. §7a refers to this item and is not deducted again.
- **§7c, S3.** Render state is snapshotted outside Page: `incremental.py:76-105`.
- **§0a, S2.** Reads `file._content` and `config._language_site`: `incremental.py:289,223`.
- **§8a, S2.** Eight `if tracker` branches: `build.py:489-566`.
- **§8b, S2.** `_visit_page` duplicates the `_build_page` prologue: `build.py:204-218`.
- **§11a, S2.** Module-global `_records`: `incremental.py:307`.
- **§13, S2 (R7).** `build --dirty` in a new process is a full build: `build.py:354-366`.
- **§2a, S1.** Flag argument `tracked: bool`: `build.py:325`.
- **§2c, S1.** `_is_current` updates the record: `:256-270`.
- **§7d, S1.** The `_MAX_RECORDS` LRU: `:307-322`.

---

### M — grade 4.23 · worst chapter 0 · (#S3 3, #S4 1) · BLOCKED

**Chapter scores**

| §0 | §1 | §2 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | §12 | §13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 (×4) | 2 (×8) | 3 (×2) | 5 | 10 | 7 (×2) | 5 (×4) | 5 (×2) | 0 (×2) | 10 | 0 (×2) | 10 | 10 |

**Failed items**
- **§1b, S4 (X1×R1).** There is no Markdown-extension guard, and the grep count of `markdown_extensions` in the incremental module is 0. `reuse_markdown` checks only the page's own source and its lookups (`commands/incremental.py:934-975`). Because this is default `serve`, a snippet edit goes stale.
- **§0a, S3.** It monkeypatches the Jinja Environment's `getattr` and `getitem` and its `context_class`, and attaches `env._mkdocs_reads`: `incremental.py:460-496`.
- **§7a, S3 (X2a).** A site is skipped on its own inventory: `incremental.py:854-869` and `build.py:599`.
- **§7c, S3.** Render state is snapshotted outside Page: `incremental.py:557-573,955-1006`.
- **§2d, S2.** `_build_languages` does logging filters, state load and discard, planning, cleaning, the per-site skip and replay, reporting and strict mode, all in one function: `build.py:533-640`.
- **§6a, S2.** A 1140-line module, and `SiteTracker` combines Markdown reuse, read-tracking, static copying, log capture and replay, and reporting.
- **§8a, S2.** `tracker is not None` branches across six functions: `build.py:109,174,204,224,286,315,337,423,464,471,509`.
- **§9a, S2.** `_RecordingFiles` overrides Files' private `_src_uris` property: `incremental.py:515-541`.
- **§11a, S2.** A global `setLogRecordFactory` swap and the module counter `_opaque_counter`: `:288,795-814`.
- **§2a, S1.** A mutable default `output_paths: set[str] = set()`, and a coupled `env`/`tracker` pair: `build.py:82-84,109`.
- **§2c, S1.** `reuse_output` and `reuse_markdown` record state as they answer.
- **§4b, S1.** Previous records are mutated in place: `:875,953,1121`.
- **§7d, S1.** The racy-timestamp re-hash and refresh, `SiteReport`, and the content pool are optimizations with no stated force behind them: `:85-181,610-618,768-774`.

**Passes worth noting.** §7b passes: dependencies are derived from what templates actually read. M is the only design that does this.

---

### Comparison

The nine split on three structural choices.

1. **Where a page's dependencies come from.** E, H and K digest the actual template context each page is rendered with. They also run every site's pipeline on every rebuild. Both the cross-language variant (X2a) and plugin-added context variables are therefore absorbed with no reopen. D, G, J and M add a site-level skip keyed only on the site's own sources. That is correct today, because every design's language links are URL-only, but it is the first thing the spec-anticipated "link shows the title" change would silently break. F and L hand-list every input of a page's output, and F, G, J and L all restate dependencies inside the incremental owner.
2. **How full versus incremental is modelled.** E (an `Outputs` strategy), G (the `SitePlan`/`FULL_BUILD` null object), J (`SiteScope`) and K (the `NO_MEMORY` instance) keep the build pipeline free of branches. D, F, H, L and M thread an optional collaborator through the pipeline with `None`-checks, and D, J and L also add a parallel "unchanged page" path beside `_build_page`.
3. **What the design refuses to trust.** D, E, H, J and K guard or trace the inputs they cannot see, such as non-builtin Markdown extensions. F, G, L and M do not. That is the only precondition failure found, and it is what BLOCKs them. Every other correctness trace (C1–C8) passes for all nine.

Two further differences:
- H alone leaves the render-state snapshot on Page. All eight others re-declare Page's private rendered fields in the incremental module (§7c, S3).
- E, J, K and M persist the record, so a cold `build --dirty` stays minimal. D, F, G, H and L rebuild everything there.

**Net ranking.** E has the fewest and mildest defects. H is the leanest and the only one where Page owns its snapshot, but it pays for None-threading and for its R7 gap on `build --dirty`. K is sound but installs a global audit hook. M is the most precise at dependency tracking, yet it is blocked and sprawling.

No files were modified.