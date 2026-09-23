---
title: "design-at-scale Phase 0 — the difficulty gate PASSES"
date: 2026-09-22
---

# Result

**The gate passes.** Four capable agents, working without any method, implemented the same stage-1 change on
mkdocs. One produced a design with no structural (S3/S4) finding; at least two produced a precondition (S4)
failure, each verified against the code. Unaided agents therefore sometimes get this design wrong and sometimes
right — the condition, fixed in advance (`../DESIGN.md` §2), under which a method can show whether it helps.

| blind | arm | grade | worst | (#S3, #S4) | gate | the precondition failure | verified |
|---|---|---|---|---|---|---|---|
| **K** | 4 | **8.56** | 7 | (0, 0) | CLEAR | — | the one plausible hidden risk checked (below) |
| **L** | 1 | 6.00 | 2 | (0, 1) | BLOCKED | §1 — a page written only in a non-default language exists in **no** language | **reproduced** |
| **M** | 2 | 6.04 | 2 | (0, 1) | BLOCKED | §0 — reads `Page`'s private `_title_from_render` and probes `vars(page)` from outside the structure package, re-deriving Page's own title rule | **verified as cited** |
| **N** | 3 | 5.91 | 2 | (0, 1) | BLOCKED | §1 fail-fast — on a path collision the root copy omits a page instead of refusing to build | **contested** (below) |

Scored blind by the disjoint-vocabulary judge (`judge-prompt.md`, frozen), from code with every author note
stripped. Mapping drawn with `SystemRandom`, salted, kept out of reach; its SHA-256 committed before the judge
ran (`MAPPING-SEAL.sha256`, commit `590c253`) and **verified on unsealing**.

**The decision does not rest on a judgement call.** It holds on L's reproduced defect alone: discount both M's
and N's findings and at least one design is still flawed and one clean.

# Verification — every load-bearing finding re-checked, still blind

- **L — reproduced.** A project with `docs/fr/only-fr.md` and no English counterpart: K, M and N serve the page
  at `/fr/only-fr/`, `/en/only-fr/` and the root; **L serves it nowhere.** The cause is structural — L builds
  every site's page set from the default language's pages (`structure/languages.py:235-240`) and drops a
  translation without a default counterpart with a warning (`:263-268`). The card says a page "may exist in any
  subset of the languages" and "every page exists in every language"; L breaks both.
- **M — verified as cited.** `mkdocs/languages.py:342-348` reads `page._title_from_render` — in pristine mkdocs
  private to `structure/pages.py` and read nowhere else — and tests `'title' in vars(page)` to learn how Page
  stored its title. The instrument classes reaching into another module's internals as a §0 precondition.
- **N — contested.** The behaviour is real: with a default-language file at `docs/en/fr/clash.md`, K, L and M
  refuse to build; N builds, serves the page at `/en/fr/clash/`, and omits it from the root copy. But the judge's
  "silently" is **wrong** — N warns, and `--strict` aborts. Warn-and-continue is mkdocs' own convention. The
  judge itself called this its most judgement-dependent score (N ≈ 8.1 CLEAR if scored a pass). It does not
  affect the decision.
- **K — the risk that would have flipped the gate, checked.** K points the shared config at each language site
  in place — a design cost the judge scored S2. Had it not restored the config when a build fails,
  `mkdocs serve` would rebuild on a corrupted config: a correctness failure the judge would have missed. It does
  restore — `configure()` is a context manager whose `finally` restores every key it touched, `nav` included
  (`structure/languages.py:214-235`).

# What the gate did not show — a correction to my own design

`../DESIGN.md` §0 named "run the whole build once per language" as **the tempting shortcut** for stage 1, and
predicted the good design would make language a first-class dimension of one build. **All four arms built one
ordinary mkdocs build per language** — and the judge did not score that as a defect; it credited it as what
"gets per-language search, chrome and serve for free". The variation the gate found is not on the axis I
predicted: it is in how each arm handled the cases around that shared skeleton — where a page's fallback comes
from, whether a new module reaches into another's internals, whether a collision refuses or degrades.

What this means for later phases: stages 2 and 3 were written to make a per-language loop "pay for it twice
more". With every unaided arm on that skeleton, Phase 2 will test whether it does — the frozen design stands,
but my stated expectation of *where* the arms would differ was wrong and is recorded as such.

# The floor

All four: **11 of 12 probes, BLOCKED on P10 only** — a no-languages site differs from pristine solely in theme
asset files mkdocs copies into every build (`messages.pot`; for arm 3 also `css/base.css`), because each arm
added translatable labels. Every page is byte-identical. The frozen verdict stands as given; see
`floor-notes.md`. The floor does not enter the gate.

# Other observations

- **No arm asked the product owner anything.** Each made its own calls on the cases the card leaves open and
  listed them at hand-back (`oracle-log.md`). Three of four independently chose to fall back to another
  language for a page the default lacks; one dropped it — the S4 above.
- **Isolation.** Arm 3 self-reported a filename-only `find /` for a gettext tool; its transcript contains no
  marker of the hidden stage cards (`floor-notes.md`).

# Cost

| | tokens | tool calls | wall-clock |
|---|---|---|---|
| arm 1 | 296 k | 89 | 24.6 min |
| arm 2 | 333 k | 96 | 24.5 min |
| arm 3 | 332 k | 114 | 26.5 min |
| arm 4 | 267 k | 89 | 20.1 min |
| judge | 233 k | 55 | 13.1 min |
| **total** | **≈ 1.46 M** | | |

About 1.5× the ~1 M the design estimated: each unaided stage-1 build cost ~300 k, not the ~120 k assumed from
the campaign's small tasks. Phase 1 and 2 estimates scale accordingly — Phase 1 is nearer **4–5 M** than 3 M.

# Next

Phase 1: three aims stage-1 runs and three **fresh** unaided runs (the four above selected the task and are not
reused), judged by the full panel — two opposite-disposition judges and the disjoint-vocabulary judge. Its
prompts are not yet written (`../DESIGN.md` §10).
