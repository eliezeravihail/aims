# Incremental rebuilds for multi-language sites

`mkdocs serve` rebuilds after every edit, and `--dirty` skips pages whose file has not changed. On a
multi-language site both must stay **correct**: after any single edit, the site on disk must be exactly what a
full `mkdocs build` would produce.

In particular:

- Editing a default-language page updates that page in the default language **and** in every language that
  shows it untranslated.
- Editing a translation updates only that language's page.
- Adding a translation replaces the untranslated fallback in that language — its page, its navigation title,
  and the links to it from the other languages.
- Deleting a translation restores the fallback.
- Renaming a page's title updates every navigation and every cross-language link that shows it.

An edit must not rebuild pages it cannot affect.
