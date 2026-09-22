# Phase 1 — blind verification of S3/S4 findings

Done before the mapping was unsealed, by building small projects with each design's mkdocs (`run.sh`: the
design tree on `PYTHONPATH`, the pristine environment's interpreter). Labels only.

## `frpage` — a page that exists only in a non-default language

`languages: {default: en, others: [fr]}`; `docs/en/index.md`, `docs/fr/index.md`, `docs/fr/extra.md` (no English).
The card: "A page may exist in any subset of the languages." and "Every page exists in every language."

| design | `/en/extra/` | `/fr/extra/` | `/extra/` (root) | warning | finding |
|---|---|---|---|---|---|
| P | yes | yes | yes | — | — |
| Q | no | no | no | yes | S4 **reproduces** (dropped everywhere) |
| R | no | yes | no | yes | S4 **reproduces** (French only) |
| S | no | no | no | yes | S4 **reproduces** (dropped everywhere) |
| T | yes | yes | yes | — | — |
| U | yes | yes | yes | — | — |

## `navtitle` — an explicit `nav:` title over a translated page

`nav: [{Home: index.md}, {Guide: guide.md}]`; `docs/fr/guide.md` titled "Le Guide Traduit".
The card: "Each language has its own navigation, using that language's page titles where a translation exists."

| design | French nav shows the translated title | finding |
|---|---|---|
| P | no — keeps "Guide" | S4 **reproduces** |
| Q | yes | — |
| R | yes | — |
| S | yes | — |
| T | no — keeps "Guide" | S4 **reproduces** |
| U | yes | — |

All six builds exit 0 on both projects.

## R's S3 (§0 encapsulation — language logic threaded through existing modules)

Changed lines mentioning `lang` / `language_site` / `fallback`, per existing pipeline module (diff against pristine):

| design | nav.py | pages.py | files.py | build.py | search |
|---|---|---|---|---|---|
| P | 0 | 0 | 0 | 8 | 0 |
| Q | 0 | 1 | 8 | 28 | 7 |
| R | 12 | 27 | 4 | 30 | 11 |
| S | 0 | 14 | 0 | 41 | 0 |
| T | 0 | 0 | 0 | 12 | 0 |
| U | 0 | 0 | 0 | 12 | 7 |

R is the only design that reaches into all five. **Reproduces.**

## Disjoint judge — its further S3/S4 findings

**R §0 S4 — a contrib plugin reads a core private attribute.** `design-R/mkdocs/contrib/search/__init__.py:95`:
`getattr(config, '_language_site', None)`. Pristine `mkdocs/contrib/` reads no such attribute. **Reproduces.**

**R §1 S4 — a collision only warns.** Project `clash`: `docs/en/fr/stray.md` (the root copy would publish it at
`/fr/stray/`, inside the French site).

| design | exit | `/fr/stray/` left in the site | message |
|---|---|---|---|
| P | 1 | no | ERROR — "would be published where a language's site lives" |
| Q | 1 | no | ERROR — "cannot be published at the root… 'fr/' is where the…" |
| R | **0** | **yes** | WARNING — "…where that language's site is published instead" (it is not: the stray page remains) |
| S | 1 | no | error — "would be published at 'fr/stray/index.html' in the site root" |
| T | 1 | no | ERROR — "which is where the 'fr' language site is built. Rename it." |
| U | 1 | no | ERROR — "would be served under '/fr/'… Rename it." |

**Reproduces.**

**U §10 S3 — the switcher and notice markup live in the domain module.** `design-U/mkdocs/structure/languages.py:164-173`
(`_PAGE_HEADER`: a `<nav>` switcher and the notice `<div>`), rendered at `:150`, spliced into `page.content` at
`commands/build.py:225`; the build adds nothing to the template context. **Reproduces** as a structural fact.
