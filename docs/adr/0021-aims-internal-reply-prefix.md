# ADR-0021: Demarcate aims-internal narration in user-facing replies
Status: accepted
Date: 2026-06-02
Supersedes: —
Superseded by: —

## Context

aims hooks inject factual context into the model (ADR-0020). The model is
free to act on that context — update a memory node, run consolidation,
flag a dirty leaf — and to mention what it did in its reply to the user.

Observed failure mode: in a session focused on an unrelated task (e.g.
training-run status reports about `net_0`/`net_1`), a `Stop` consolidation
turn caused the reply to begin with "0 dirty nodes. ה-inbox מכיל רק קובץ
plan — dropped" with no demarcation. From the user's point of view this
is noise from an unrelated subsystem, mixed inline with substantive work.
The injected text already carries `[aims]` / `[aims-memory]` prefixes,
but those are context labels for the model — they do not propagate into
the user-facing reply.

The hook injections are the only durable surface aims controls in every
project where it is installed; CLAUDE.md is editable per-project.

## Decision

We will adopt a project-wide convention: **only the Stop /
consolidation-update hook's result report is prefixed with
`==== AIMS (internal) ====`** — one line or a short phrase
("nodes updated", "queue drained", "4 dirty"). The prefix is NOT
applied to regular conversational mentions of aims topics (questions,
plans, status, dirty-node notes that arise mid-conversation); those
flow naturally as part of the reply. The prefix exists to demarcate
the one place where the hook actively reports back to the user — the
end-of-turn consolidation pass — from the substantive work.

No per-node prose under the prefix unless the user asks for it.

The convention is propagated into every aims-injected context blob:
- `session-start.sh` adds it as a fourth standing-conventions bullet.
- `prompt-submit.sh` appends it to the router note for actionable prompts.
- `post-edit-marker.sh` appends it to the per-edit node-naming note.
- `stop-consolidate.sh` appends it to the consolidation-queue prompt.

Phrasing is factual ("is prefixed with …"), not imperative, per ADR-0020:
imperative injections trip Claude's prompt-injection defense and surface
to the user as quoted text instead of being absorbed as context.

Boundary: the prefix demarcates a *section of the reply*, not whole
replies. A reply that is entirely substantive needs no prefix. A reply
that is entirely aims-internal carries the prefix once at the top.

## Consequences

- ✅ Users in non-aims-focused sessions can scan past plugin plumbing at
  a glance; the noise the user reported on 2026-06-02 stops mattering.
- ✅ Convention rides on the hook injections, so it applies automatically
  in every project where aims is installed — no per-project CLAUDE.md
  edit required.
- ⚠️ Slight verbosity in injected text. Acceptable: one sentence each.
- ⚠️ The model must remember the convention across turns. Mitigated by
  every aims-relevant hook re-injecting it.
- 🔒 Rules out an alternative where aims-internal work is invisible
  (silent edits to nodes). The user explicitly wants to see what aims
  is doing — they want it labeled, not hidden.

## Alternatives considered

- **A**: Suppress aims-internal narration entirely in user-facing replies
  — rejected: the user wants visibility, just clearly demarcated.
- **B**: Encode the prefix in CLAUDE.md instead of in hook injections —
  rejected: CLAUDE.md is per-project and aims has no write access to it
  post-install. Hook injections are the durable surface aims controls.
- **C**: Use an HTML-comment marker (`<!-- aims -->`) — rejected: not
  visible to the user, defeats the purpose.

## Verification

Grep for the convention across all hook injection points:

    grep -l '===\[aims:' templates/hooks/

Should list at least `session-start.sh` and `stop-consolidate.sh`
(the only two surfaces that still carry the convention text after
the 2026-06-02 narrowing). The same files in `.claude/hooks/`
(dogfooded copies) must match.

## Amendment 2026-06-02: marker form shortened

The original marker was a two-line wrapper
(`==== AIMS (internal) ====` / `==== /AIMS ====`). User feedback:
too prominent for what is meant to be a terse plumbing report.
Adopted form is now a single line
`===[aims: <message>]===` (examples: `===[aims: nodes updated]===`,
`===[aims: queue drained]===`, `===[aims: 4 dirty]===`). Convention
scope and Decision above are unchanged — only the literal marker
form changed.
