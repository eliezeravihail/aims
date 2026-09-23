# An offline export per language

Add `mkdocs export`, which writes one self-contained HTML file per language — every page of that language's
site in a single file, for readers without network access.

- Navigation becomes a table of contents inside the file; links between pages become links to anchors inside
  the file.
- Images and stylesheets the pages use are embedded, so the file works with no other files beside it.
- Untranslated pages appear exactly as they do on the site: the default-language text, with the notice.
- A site with no `languages` exports a single file.

`mkdocs build` and `mkdocs serve` are unchanged.

*Scoring note.* Whether an exported file detects or chooses the reader's language is measured separately and is
**not** part of this scoring: neither its presence nor its absence counts for or against a design.
