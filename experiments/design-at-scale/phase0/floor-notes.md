# Phase 0 — floor results, with notes

The floor is `hidden/probes/stage1_probe.py`, frozen before any arm ran. A failure marks the arm-stage BLOCKED;
passing earns nothing. Verdicts below are the frozen probe's, unchanged. Where a failure's cause is narrow,
it is stated so the reader can weigh it — the probe is not edited after seeing a result.

| arm | probes | floor | note |
|---|---|---|---|
| 4 | 11/12 | BLOCKED (P10) | Every page of a no-languages site is byte-identical to pristine; the only difference is `messages.pot`, a translation template the mkdocs theme copies into every built site, which changed because the arm added two translatable labels. |
| 1 | 11/12 | BLOCKED (P10) | Same cause as arm 4: only `messages.pot` differs; the arm itself reported it ("already being copied into every site before this change, and it now contains the new strings"). |
| 2 | 11/12 | BLOCKED (P10) | Same cause: only `messages.pot` differs in the default-theme build. |
| 3 | 11/12 | BLOCKED (P10) | Differs in `messages.pot` and `css/base.css` — theme assets copied into every build; the arm reported adding CSS rules "which do nothing without `languages`". All HTML pages identical. |

**All four arms: 11/12, blocked only on P10, and only by theme asset files that mkdocs copies into every site.**
Every page each arm builds for a no-languages site is byte-identical to pristine. The floor does not enter
the gate decision (§2 decides on design only); it is reported as the frozen probe gave it.

## Isolation

Arm 3 reported that it once searched outside its working directory and once let `pip` download files into it
(removed). Its transcript was checked for every marker of the hidden material — `design-at-scale`, the stage-2
and stage-3 cards' distinctive phrases, `oracle.md`: **none occur.** The out-of-directory search was
`find / -name msgfmt.py` — a filename search for a gettext tool, which reads no file contents.

## Blinding

Labels K / L / M / N drawn with `random.SystemRandom`; the mapping, salted, is kept outside the repository and
outside anything the judge can read. Only its SHA-256 is committed (`MAPPING-SEAL.sha256`) before the judge
runs, so it can be checked when revealed. Each design had its prose `.md` changes outside `mkdocs/tests/`
reverted or removed (4 per arm) — authors described their own designs there. Patch sizes differ enough that
one could guess which arm is which; in Phase 0 that carries no information, because all four arms are the
same condition.
