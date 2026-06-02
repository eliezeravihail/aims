# Plan: Anchor "first action = write draft" to prevent planning skips
Status: completed
Started: 2026-06-02
Completed: 2026-06-02

## TL;DR

Two mitigations for the conversational-drift failure mode that let the
assistant skip the plan-first convention on the ADR-0022 work:

1. **PreToolUse hook becomes state-aware** — instead of a generic
   planning-convention reminder, it injects: "About to edit `<file>`;
   no draft/in-progress plan in `docs/plans/` covers this work.
   Convention: Write the draft first." Fires at the moment of the
   first source edit, not at session-start or prompt-submit, so it
   anchors the trigger to the concrete moment of decision.
2. **Self-discipline addendum in CLAUDE.md** — codify that user
   approval of a proposal (`כן`/`yes`/`do it`) on an actionable
   prompt triggers Phase 2 (write draft), NOT Phase 4 (implement).
   The plan flow is non-skippable even when approval is brief.

Both stay factual / non-blocking per ADR-0020. (3) is documentation;
(1) is a hook behavior refinement.

## Changes

### templates/hooks/pre-write.sh — state-aware planning note

Current behavior: on first source edit of a session with no
in-progress plan, inject a generic planning-convention note once.

New behavior: still no block. The note becomes anchored to the
concrete moment:

```sh
# Replace the current static NOTE with one that names the file and
# the missing plan state. Still factual; still per-session once.

NOTE="About to edit '$target_rel'. No \`Status: draft\` or
\`Status: in-progress\` plan in \`$PLAN_DIR\` covers this prompt.
Project convention: a non-trivial change is materialized as a draft
plan in \`$PLAN_DIR/<YYYY-MM-DD>-<slug>.md\` BEFORE the first source
edit. The plan file is the contract; the edit comes after it lands
on disk and the user confirms. (Informational only; nothing is
blocked. This note fires once per session — subsequent edits are
silent.)"
```

The existing per-session inject-once marker
(`.claude/.aims-plan-note-${sid}`) stays — keeps the hot path silent.

### CLAUDE.md — self-discipline addendum under "Workflow"

Add a short paragraph after the existing planning-as-behavior text:

```md
**Approval is for Phase 2, not Phase 4.** When the user says
"כן"/"yes"/"do it" to a *proposal* (a sketch the assistant offered
in conversation), that approves moving to Phase 2 — writing the
`Status: draft` plan to `docs/plans/` — NOT Phase 4 (implementing).
The plan-on-disk + a re-confirm gate stays in force even when the
conversational reply is brief. This closes the conversational-drift
gap that the PreToolUse note exists to anchor.
```

### .claude/hooks/pre-write.sh — mirror refresh

Standard dogfood: `cp templates/hooks/pre-write.sh .claude/hooks/`.

### docs/adr/0023-anchor-first-action-to-prevent-skips.md — new ADR

Records the diagnosis (conversational drift on "do it" approvals)
and the two mitigations. Cites the ADR-0022 implementation incident
as the motivating case. Status: proposed.

### docs/adr/README.md — index row

Append ADR-0023 row.

## Open design questions

- Should the per-session inject-once still be once-per-session, or
  once-per-prompt? Once-per-session keeps signal-to-noise high but
  means a second non-trivial prompt in the same session may not get
  the anchor. **Tentative: keep once-per-session**; the
  `prompt-submit` router still nudges on each actionable prompt.
- Should the note also surface when a draft EXISTS but its
  `## Changes` clearly doesn't cover the file being edited? Out of
  scope for this plan — would require parsing draft bodies. File as
  TODO if it bites.

## Verification

- `bash -n templates/hooks/pre-write.sh && bash -n .claude/hooks/pre-write.sh`
  → OK.
- `bash tests/inform-never-block.sh` → still passes (the hook still
  exits 0 with `permissionDecision: allow`).
- `bash tests/router-auto-plan.sh` → still passes (no behavior
  change to the router-side trigger).
- Manual: in a fresh session, ask for a non-trivial code change
  without `/plan`. After the first Edit attempt, the PreToolUse note
  names the file and the missing plan. (Cannot be automated end-to-
  end; the anchor is the model's reading of the injection.)
- `bash .claude/memory/lint.sh` → clean.

## Close-out checklist

- ADR: WRITE — 0023-anchor-first-action-to-prevent-skips
- Nodes: UPDATE — hooks/pre-write (note string changed)
- CLAUDE.md: UPDATE — Workflow (new "Approval is for Phase 2" paragraph)
- Tests: EXISTING — inform-never-block + router-auto-plan cover the
  invariant; the textual note change has no test surface.
- TODO: per-prompt vs per-session retrigger (see Open questions);
  draft-coverage detection (out of scope).

## Risks / unknowns

- The state-aware note is longer than the current one. Larger
  injections risk being skimmed; mitigated by being concrete (file
  name + missing-plan fact) rather than abstract.

## Outcome

Two mitigations landed:

1. `templates/hooks/pre-write.sh:84` (+ `.claude/hooks/` mirror): NOTE
   rewritten to name (a) the file about to be edited, (b) the missing
   `Status: draft`/`Status: in-progress` plan in `docs/plans/`, and
   (c) the approval-semantics rule ("yes"/"do it" → Phase 2, not 4).
   Hook still never blocks; per-session inject-once preserved.
2. `CLAUDE.md` "Workflow" section: new paragraph **"Approval is for
   Phase 2, not Phase 4."** codifying the same rule in durable session
   context.

ADR-0023 records the diagnosis (conversational drift on brief
approvals) and the decision. `docs/memory/hooks/pre-write.md` carries
a stale-warning note + Pointers updated to ADR-0020/0023; full body
rewrite carried as a follow-up (out of scope for this plan).

## Closing checks

- Plan: docs/plans/2026-06-02-anchor-first-action.md → completed
- Verification:
  - `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → OK.
  - `bash tests/router-auto-plan.sh` → all PASS.
  - `bash tests/inform-never-block.sh` → 26 passed, 1 failed
    (English-bug planning-note test). Pre-existing failure — the
    test sends a raw string but the hook expects JSON via jq.
    Reproduced on the parent commit (1bdc1f3) before any change
    here. Carried as TODO; not a regression.
  - `grep -F "About to edit" templates/hooks/pre-write.sh
    .claude/hooks/pre-write.sh` → both hits present.
  - `grep -F "Approval is for Phase 2" CLAUDE.md` → present.
  - `bash .claude/memory/lint.sh` → clean (15 nodes).
  - `bash .claude/memory/find-dirty.sh` → empty.
- ADR:      WROTE — docs/adr/0023-anchor-first-action-to-prevent-skips.md
- Nodes:    UPDATE — hooks/pre-write (Pointers + stale-warning;
            full body rewrite deferred).
- CLAUDE.md: UPDATE — Workflow ("Approval is for Phase 2" paragraph)
- Tests:    EXISTING — inform-never-block + router-auto-plan cover
            the never-block + once-per-session invariants. The
            English-bug test failure is pre-existing.
- TODO:
  - Fix `tests/inform-never-block.sh` line 53 to pass a JSON
    payload (`{"prompt":"…","session_id":"…"}`) — the hook switched
    to JSON-only parsing some commits ago.
  - Full body rewrite of `docs/memory/hooks/pre-write.md` (currently
    annotated stale; describes pre-ADR-0020 blocking behavior).
  - Per-prompt vs per-session retrigger of the pre-write note (see
    Open design questions).
  - Draft-coverage detection (file mentioned in `## Changes`) — out
    of scope; revisit if the anchor proves insufficient.
