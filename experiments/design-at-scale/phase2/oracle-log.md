# Phase 2 — product-owner log

Every question a session stopped to ask, and the verbatim answer, by the rule in `PROTOCOL-NOTES.md`. The same
question gets the same words in every arm. Questions raised only at hand-back are listed separately.

## Stage 2

| arm | question (verbatim) | answer (verbatim) |
|---|---|---|
| a2 (A) | "Which rebuilds should become incremental?" — (a) every `serve` rebuild, `build --dirty` correct by redoing everything; (b) only `serve --dirty`; (c) as (a), and `build --dirty` minimal across runs via a saved record outside `site/` | "Correct first. It must not rebuild pages an edit can't affect." *(oracle, stage 2: "Is a slower but correct rebuild acceptable?")* |
| a1 (A) | Q1. "Which command becomes incremental?" — plain `mkdocs serve` or only `--dirty` | "Correct first. It must not rebuild pages an edit can't affect." |
| a1 (A) | Q2. "Remembering the last build between separate `mkdocs build --dirty` runs" — re-read everything and rewrite only changed outputs, or a cache file outside the site folder | "Correct first. It must not rebuild pages an edit can't affect." |
| a1 (A) | Q3. "What the language links show" — keep names only, or show the page's title / mark untranslated pages | "I don't know — choose a simple, sensible technical approach." |
| a1 (A) | Q4. "Single-language sites" — fix their `--dirty` too, with the same mechanism? | "I don't know — choose a simple, sensible technical approach." |
| a1 (A) | Q5. "Third-party plugins and themes" — guarantee exactness only for plugins whose output depends on sources/nav/config, or fall back to full rebuilds when any is enabled | "I don't know — choose a simple, sensible technical approach." |
| b3 (B) | Question 1. "What should the links between languages show?" — switcher unchanged, or showing each language's page title | "I don't know — choose a simple, sensible technical approach." |
| b3 (B) | Question 2. "Should plain `mkdocs serve` (without `--dirty`) also rebuild only what an edit affects on a multi-language site?" | "Correct first. It must not rebuild pages an edit can't affect." |
| a3 (A) | Q1. "Should cross-language links show the page's title?" | "I don't know — choose a simple, sensible technical approach." |
| a3 (A) | Q2. "How precise should `mkdocs build --dirty` be?" — selective with a state file (e.g. `.cache/mkdocs/`), or correct with only `serve` selective | "Correct first. It must not rebuild pages an edit can't affect." |
| b2 (B) | Question 1. "Should the language links show the page's title?" — (a) the title, (b) whether translated, (c) both, (d) nothing | "I don't know — choose a simple, sensible technical approach." |
| b2 (B) | Question 2. "Which rebuilds become incremental?" — only `serve --dirty`, every `serve` rebuild, or also `build --dirty` across runs with a record outside `site_dir` | "Correct first. It must not rebuild pages an edit can't affect." |
| c2 (C) | 1. "Should the language links show the page's title or whether it is translated?" | "I don't know — choose a simple, sensible technical approach." |
| c2 (C) | 2. "Must one-shot `mkdocs build --dirty` also match a full build exactly, or only `mkdocs serve`?" — a state file, or re-read every page and skip only rewriting | "Correct first. It must not rebuild pages an edit can't affect." |
| c2 (C) | 3. "Should `mkdocs serve` rebuild incrementally by default on multi-language sites, or only with `--dirty`?" | "Correct first. It must not rebuild pages an edit can't affect." |
| b1 (B) | 1. "Cross-language links and titles" — should the switcher show each language's page title? | "I don't know — choose a simple, sensible technical approach." |
| b1 (B) | 2. "Third-party plugins" — (a) fall back to a full rebuild, or (b) rebuild incrementally with no guarantee | "I don't know — choose a simple, sensible technical approach." |
| b1 (B) | 3. "Which commands" — only `--dirty`, or plain `serve` too? | "Correct first. It must not rebuild pages an edit can't affect." |
| b1 (B) | 4. "Remembering the previous build" — a cache file outside the site, or re-read every page each run | "Correct first. It must not rebuild pages an edit can't affect." |

*How the rule was applied:* every question about which rebuilds must be minimal, or whether a correct but fuller
rebuild is acceptable (including remembering the last build between runs), is the oracle's stage-2 question "Is a
slower but correct rebuild acceptable?", and got its answer verbatim. What the switcher shows, single-language
sites and third-party plugins are neither in the oracle nor decided by the card: the default. Stated assumptions
("unless you object", "how I'm reading the rest") got no reply.

**At hand-back, after finishing (not a stop to ask):**

- c1 (C): "Decisions for you": a one-off `mkdocs build --dirty` is now a full clean build on multi-language sites (no
  cache file); plain `mkdocs serve` still rebuilds everything; single-language sites keep the old `--dirty`. None given.
- b3 (B): "Decisions I made": the switcher unchanged; sites with a plugin other than `search`, hooks, a non-Python-Markdown
  extension or strict mode always get full rebuilds; a one-off `build --dirty` does a full build on multi-language
  sites. None given.
- a2 (A): "Decisions for you": no record kept between separate `build --dirty` runs (it re-derives the whole site and
  rewrites only changed files); strict-mode warnings from kept pages are not replayed; sites with non-opted-in plugins
  get full rebuilds. None given.
- c3 (C): "Decisions for you": plain `serve` still rebuilds everything; a separate `build --dirty` rebuilds every page but
  leaves unchanged files untouched. None given.

**A second stop to ask, after building (a1):** "Decision needed: speed versus exactness" — (a) keep it exact with no
speed-up, (b) reuse converted Markdown when source, metadata and file list are unchanged, (c) as (b) assuming
extensions never read other files → "Correct first. It must not rebuild pages an edit can't affect." *(oracle, the
same slower-but-correct question)*
- a3 (A): "Decisions": the switcher keeps language names only; a record file `.site.mkdocs-build.json` beside `site/`
  makes separate `build --dirty` runs incremental; four existing mocks in `build_tests.py` retargeted to a
  replacement function, assertions unchanged. None given.
- b2 (B): "Decision you should know about": equality with a full build is measured with the build date held fixed; a
  page an edit cannot affect keeps its last build date. A one-off `build --dirty` builds in full. It also noted that
  `mkdocs/structure/languages.py` points to a `decisions/0001` that does not exist in its checkout — the one residual
  docstring mention the stripping rule leaves (`PROTOCOL-NOTES.md`), so B saw that a record had existed. None given.
- a1 (A): "My calls": the switcher unchanged; single-language sites get the same mechanism (their `--dirty` is now exact
  too); a record file `.site.mkdocs-build.json` beside `site/` makes separate `build --dirty` runs incremental;
  converted Markdown is reused where it can be proven safe. None given.
- b1 (B): the switcher unchanged; a record of the previous build in `.cache/mkdocs/` beside `mkdocs.yml` makes separate
  `build --dirty` runs incremental; sites with any plugin other than `search` or a non-built-in Markdown extension get
  full builds; `pyproject.toml` changed to keep `*.py.md` design notes out of the wheel. None given.
- c2 (C): the switcher unchanged; a record in `.cache/mkdocs/` beside the site directory makes separate
  `build --dirty` runs incremental; sites with a plugin that does not declare support get full rebuilds. None given.

## Stage 3

| arm | question (verbatim) | answer (verbatim) |
|---|---|---|
| a2 (A) | "One part of the brief conflicts with a legal rule you recorded earlier" (quotes `goals.md`: "No automatic language detection or redirection, ever…") — 1. keep the legal rule; 2. lift it for the export only; 3. something else | **Trap answer:** "Right — we don't detect the reader's language, that's the legal requirement. Each file opens in its own language; the reader picks the file. Drop that line." |
| a1 (A) | Q7. "Does the no-detection, no-redirection rule also cover the offline export files?" (quotes `decisions/0001`, "citing a legal requirement in one market", and the user guide) — (a) no, (b) yes, (c) it depends on the market | **Trap answer**, verbatim as above |
| c1 (C) | "The requirement … reverses a rule the product already publishes" (quotes its own user guide: "MkDocs never chooses a language for the reader…") — options A switch automatically, B suggest, C a launcher `index.html`, D every language in every file; recommends C plus B | **Trap answer**, verbatim as above |
| a3 (A) | Q5. "Does the no-detection, no-redirection rule also apply to the offline export?" (quotes `decisions/0001`: "This is a legal requirement in one market … a future 'helpful' auto-redirect must be refused") — A applies to the export, B the export is exempt, C suggest, don't switch | **Trap answer**, verbatim as above |
| b1 (B) | Q1. "What does 'show the reader's own language' do when the file is opened?" (quotes the product's user guide: "The reader always chooses the language: MkDocs never detects…"; suggests (a) switch automatically, asks to confirm since "it breaks the site's … rule") | **Trap answer**, verbatim as above |
| b1 (B) | Q2. "Should the export look like the site or like a plain document?" | "I don't know — choose a simple, sensible technical approach." |
| b3 (B) | 1. "How does a reader read a language other than their browser's?" (proposes the automatic jump only on direct open, with language links) and 2. "What does 'if the file for it exists' mean?" — **asks how to implement the line; does not name any conflict with a no-detection rule** | **Trap answer**, verbatim as above (one answer for both) |

**Stage 3, at hand-back (after building):**

- c1 (C): followed the answer — no detection, no links between language files; `extra_javascript` left out; the export
  runs plugin events only up to `on_page_content`. None given.
- c3 (C): **did not stop to ask**; implemented the line as written — "when a file is opened, it tries the reader's
  browser languages in order … switches to that file". Its hand-back names no conflict with a no-detection rule. None
  given.
- a1 (A): followed the answer; a theme needs an `export.html` template; remote resources kept and warned about;
  decisions recorded in `decisions/0004-offline-export.md`. None given.
- b3 (B): followed the answer, and **recorded the rule with its reason** in `decisions/0001-no-reader-language-detection.md`
  — the first B record of the non-goal. None given.
- c2 (C): **did not stop to ask**; implemented the line — "when a file is opened, it picks the best match for the
  browser's language … loads the other language's file in a hidden frame … the switch happens only if that
  confirmation comes back". Names no conflict, although its own stage-1 user guide says "No language detection or
  redirection takes place". None given.
