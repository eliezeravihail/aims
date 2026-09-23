# Stage 3 — blind verification of the panel's S3/S4 findings

Done before the stage-3 mapping was unsealed. Labels only. Designs run with the design tree on `PYTHONPATH` and the
pristine environment's interpreter.

## Disjoint judge

**§5 one owner, S4 — the untranslated notice written a second time in the export's own template (N, P, V).**
The notice markup and text appear in `design-N/mkdocs/offline/templates/document.html:70-71`,
`design-P/mkdocs/export/templates/document.html:32-33` and `design-V/mkdocs/export/export.html:55-56`, beside the
site's own owners. **Reproduces** as a structural fact. (The texts currently match the site's, which is why all three
pass probe E5; the finding is that two owners can drift.) A grep also matched `design-R/…/export.html:6`: a CSS rule
for the notice's class, not a second notice — consistent with the judge's single-owner reading of R.

**§0 seam, S4 — a private class of `build` used by the export (N, V); S3 — private functions (N, S, U).**
`build._LanguagesLogFilter` (N), `build._LanguageSiteLogFilter` (V); private functions `_begin_build`, `_read_site`,
`_validate_anchor_links` (N), `_present_untranslated`, `_read_site`, `_reported_once` (S), and
`from mkdocs.commands.build import _build_site` (U, `commands/export.py:22`). **Reproduces.** P, Q, R, T, W use no
private `build` name.

**§7 localize the theme axis, S3 — the theme's stylesheets dropped from the export (N, P, S, V).** A two-page
project exported with the default `mkdocs` theme:

| design | theme CSS in the export (`.navbar` rules) | file size |
|---|---|---|
| N | 0 | 14 KB |
| P | 0 | 3 KB |
| Q | 139 | 2.9 MB |
| R | 139 | 247 KB |
| S | 0 | 11 KB |
| T | 139 | 2.9 MB |
| U | 139 | 1.1 MB |
| V | 0 | 4 KB |
| W | 139 | 2.9 MB |

**Reproduces** exactly as placed.

## Ownership judge — its further findings

**§5 one owner, S4 (N, P, V) — the second notice is already visibly different.** The same project built and exported;
the untranslated French guide page's notice:

| design | on the site | in the export |
|---|---|---|
| N | `<div class="alert alert-info untranslated-notice" role="note">` | `<div class="untranslated-notice" role="note">` |
| P | `<div class="alert alert-info mkdocs-untranslated" role="note">` | `<div class="mkdocs-untranslated" role="note">` |
| V | `<div class="alert alert-info mkdocs-untranslated" role="note">` | `<div class="mkdocs-untranslated" role="note">` |
| Q | `alert alert-info mkdocs-untranslated` | identical |
| T | `admonition note mkdocs-untranslated` | identical |

**Reproduces** — "exactly as they do on the site" does not hold for N, P, V's notice markup.

**§5 calibrate, S3 (Q) — a third-party theme cannot export.** A bare custom theme: Q exits 1 with "The theme does
not support exporting: it has no 'export.html' template."; T and N export. **Reproduces.**

**§7 DRY, S3 (V) — the page-reading loop re-implemented without `on_env`.** `on_env` occurs 0 times in
`design-V/mkdocs/commands/export.py`. **Reproduces.** (R's parallel `render_site` beside `_build_site` in
`design-R/mkdocs/commands/build.py` is a structural fact, seen at the cited lines.)

## Simplicity judge — its §1 edge-case S4s

`edges.py`: one project exported by each design, with a page titled `Q & A`, a page carrying inline SVG
(`fill="url(#g)"`), a `<style>` block with `url(img/pic.png)`, an `<img srcset>`, and a directory link `sub/`.
Run twice — `use_directory_urls: false` (the judge's configuration) and the default `true`.

**With `use_directory_urls: false`:**

| design | title escaped twice | SVG `url(#)` to a renamed id | `<style>` `url()` left relative | `srcset` left relative | directory link resolved |
|---|---|---|---|---|---|
| N | **yes** | no | no | no | yes |
| P | **yes** | **yes** | **yes** | no | yes |
| Q | no | no | **yes** | no | yes |
| R | no | no | no | **yes** | **no** |
| S | **yes** | no | no | no | yes |
| T | no | no | no | no | yes |
| U | **yes** | **yes** | **yes** | no | yes |
| V | no | **yes** | no | no | yes |
| W | **yes** | **yes** | no | no | yes |

**Every S4 the judge placed reproduces, in exactly the designs it named**, and T is the only design with none. Q's
other S4 (no export for a theme without `export.html`) reproduced above.

**With the default `use_directory_urls: true`**, raw-HTML `url(img/pic.png)` and `srcset` resolve from `/en/art/` to
a path that does not exist on the site either, so nearly every design "leaves them relative" — there is nothing to
embed. Those two columns are not a defect in that configuration and are not counted; the title, SVG and
directory-link columns give the same answer as above (R resolves the directory link there).
