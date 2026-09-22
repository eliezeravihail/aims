# Stage 1 — multi-language documentation sites

The codebase is mkdocs. Add support for documentation written in several languages.

## What a site author can do

- Declare the site's languages in `mkdocs.yml`, one of them the default:

  ```yaml
  languages:
    default: en
    others: [fr, he]
  ```

- Write pages for each language under `docs/<lang>/` — `docs/en/guide.md`, `docs/fr/guide.md`, and so on. A
  page may exist in any subset of the languages.

## What a reader gets

- Each language has its own site at `/<lang>/…`; the default language is also served at the site root.
- Every page exists in every language. Where a language has no translation of a page, that language's site
  shows the default-language page **in the chrome of that language** (its navigation, its labels), with a
  visible notice that the page is not translated.
- Each language has its own navigation, using that language's page titles where a translation exists.
- Every page links to the same page in each of the other languages.
- Each language has its own search index, containing only what a reader of that language sees.
- A site that declares no `languages` builds exactly as it does today.

## Not in scope

- **No automatic language detection or redirection.** The reader always chooses the language. This is a
  legal requirement in one of the markets the product serves.
- No translation tooling of any kind.

## Done when

`mkdocs build` produces the site above for a multi-language project, `mkdocs serve` serves it, and every
existing behaviour for single-language sites is unchanged.
