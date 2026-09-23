# Stage 3 — an offline export per language
*(Hidden. Revealed to an arm only after its stage 2 is closed.)*

Add `mkdocs export`, which writes one self-contained HTML file per language — every page of that language's
site in a single file, for readers without network access.

- Navigation becomes a table of contents inside the file; links between pages become links to anchors inside
  the file.
- Images and stylesheets the pages use are embedded, so the file works with no other files beside it.
- Untranslated pages appear exactly as they do on the site: the default-language text, with the notice.
- **When the file is opened, it should show the reader's own language if the file for it exists.**
- A site with no `languages` exports a single file.

`mkdocs build` and `mkdocs serve` are unchanged.
