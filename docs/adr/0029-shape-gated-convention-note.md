# ADR-0029: The convention note is gated by prompt shape, not intent classes
Status: proposed
Date: 2026-07-15
Supersedes: — (supersedes the intent-classification mechanism of ADR-0015; its draft-on-disk behavior stands)
Superseded by: —

## Context

`prompt-submit.sh` carried a ~200-line regex intent classifier (bug /
feature / refactor / decision / mechanical / question / ambiguous),
including a Hebrew-interrogatives list and a multilingual length
fallback. Every actionable class resolved to the **same constant
outcome**: inject one factual planning-convention paragraph. Questions
and short prompts resolved to nothing. The classifier therefore bought
per-language keyword fragility (it needed a dedicated Hebrew patch and
a char-vs-byte locale fix just to avoid misfiring) with no behavioral
payoff — a binary gate was doing a seven-way classification's job.

## Decision

We will gate the convention note on **prompt shape**: length ≥ 30
characters ∧ ≤ 4096 ∧ no ``` fence ∧ not ending in `?`. Any prompt
passing the gate gets the (unchanged, self-conditional) factual note;
anything else gets nothing. No intent classes exist anywhere in the
hook. The gate is language-neutral by construction; the UTF-8
char-counting locale block remains load-bearing. Under-firing (e.g. a
short "fix the crash") is backstopped by `pre-write.sh`'s state-aware
first-edit note (ADR-0023); over-firing (a long statement that wasn't a
task) is cheap because the note is conditional on "a non-trivial
change" by its own wording.

## Consequences

- ✅ ~150 lines and all language special-casing removed; Hebrew and any
  other language get identical treatment.
- ✅ One less thing to rot: no keyword lists to keep in sync with how
  users phrase tasks.
- ⚠️ Tasks phrased as trailing-`?` questions ("can you refactor X?")
  get no note — accepted; ADR-0023's first-edit note covers the miss.
- 🔒 Rules out re-introducing intent-conditional routing in this hook;
  if differentiated behavior is ever needed, it must justify a new ADR.

## Alternatives considered

- **Keep classifier, add languages as needed**: rejected — unbounded
  keyword maintenance for zero behavioral difference.
- **Always inject (no gate)**: rejected — pollutes question/paste turns
  and duplicates the session-start conventions block on every prompt.

## Verification

- `templates/hooks/prompt-submit.sh` — the single `router_text` gate
  (no `intent` variable exists in the file).
- `bash tests/router-auto-plan.sh` — 8 cases, incl. language-neutral
  positive (Hebrew task) and negative (short Hebrew, char-counted).
