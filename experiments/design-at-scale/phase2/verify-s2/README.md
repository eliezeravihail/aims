# Stage 2 — blind verification of the judge's S3/S4 findings

Done before the stage-2 mapping was unsealed. Labels only.

## The S4 — "no guard for Markdown extensions that read other files" (F, G, L, M)

`snip.py`: a project with a local Markdown extension (`incl`) that includes `docs/en/snip.txt` into the English home
page. `mkdocs serve` runs with the design on `PYTHONPATH`; the included file is edited; the page is fetched for 30 s.

**A correction to the check itself, before any result was used.** The first run passed `--no-livereload`, which in
this mkdocs also stops file watching: every design, and both controls, stayed "stale" because nothing rebuilt. The
flag was removed and everything re-run; only the second run is reported.

| design | `serve --dirty` | plain `serve` |
|---|---|---|
| D | updated | — |
| E | updated | — |
| F | **stale** | updated |
| G | **stale** | **stale** |
| H | updated | — |
| J | updated | — |
| K | updated | — |
| L | **stale** | updated |
| M | **stale** | **stale** |

Control: the stage-1 design (no incremental engine) under `serve --dirty` is stale too — pristine's own `--dirty`
rebuilds only pages whose own file changed. The stage-2 card requires the dirty output to equal a full build, so the
finding stands for all four; and for G and M it also breaks plain `serve`, which pristine always rebuilt in full.
**All four S4s reproduce, exactly as the judge placed them.**

## A spot-check of the most common S3 — §7c, Page's render state re-declared outside Page

`_title_from_render` written or read in `mkdocs/commands/`: 3 occurrences in D, E, F, G, J, K, L, M; 0 in H, whose
`structure/pages.py` carries the snapshot methods (`_rendered_state`, `_restore_rendered_state`). **Reproduces.**
