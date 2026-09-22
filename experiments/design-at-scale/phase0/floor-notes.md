# Phase 0 — floor results, with notes

The floor is `hidden/probes/stage1_probe.py`, frozen before any arm ran. A failure marks the arm-stage BLOCKED;
passing earns nothing. Verdicts below are the frozen probe's, unchanged. Where a failure's cause is narrow,
it is stated so the reader can weigh it — the probe is not edited after seeing a result.

| arm | probes | floor | note |
|---|---|---|---|
| 4 | 11/12 | BLOCKED (P10) | Every page of a no-languages site is byte-identical to pristine; the only difference is `messages.pot`, a translation template the mkdocs theme copies into every built site, which changed because the arm added two translatable labels. |
