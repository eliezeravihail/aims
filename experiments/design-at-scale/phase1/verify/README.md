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
