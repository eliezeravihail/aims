---
description: Record an Architecture Decision (one decision, append-only log)
argument-hint: "<decision title>"
model: opus
---

# /adr

You are recording an Architecture Decision Record (ADR) for: **$ARGUMENTS**

ADRs are append-only. Past records are never edited; if a decision changes,
write a new ADR that supersedes the old one.

## Steps

1. **Locate the ADR directory.** Default `docs/adr/`. If it doesn't exist,
   create it with a fresh `README.md` and `_template.md` from the plugin's
   `templates/` dir. (User probably should have run `/init-workflow` first —
   warn them but proceed.)

2. **Compute the next number.** Scan `docs/adr/NNNN-*.md`, take max+1, pad to 4
   digits. Skip `_template.md` and `README.md`.

3. **Compute slug.** Lowercase, hyphenated, ≤6 words from $ARGUMENTS.

4. **Read context.** Before drafting, read:
   - The most recent 3 ADRs (so terminology and tone match).
   - Any active plan in `docs/plans/` with `status: in-progress` (the ADR may
     be referenced there).
   - The relevant code paths (cited via `file:line`).

5. **Draft the ADR** using `docs/adr/_template.md`. Required sections:

   ```markdown
   # ADR-NNNN: <title>
   Status: proposed
   Date: YYYY-MM-DD
   Supersedes: —
   Superseded by: —

   ## Context
   What forces are at play (technical, organizational, constraints)?
   Cite code with file:line. Be factual, not aspirational.

   ## Decision
   In active voice: "We will use X". One paragraph.

   ## Consequences
   What gets better, what gets worse, what becomes possible/impossible.
   Include trade-offs you accept.

   ## Alternatives considered
   - **A**: <one line> — rejected because …
   - **B**: <one line> — rejected because …

   ## Verification
   How a future maintainer can confirm this decision is still in force.
   A command, a test, a metric, or a code anchor (file:line) is best.
   ```

6. **Inverted-pyramid style**: most important content (decision + consequences)
   high in the document. Background and alternatives lower.

7. **Pithy.** One to two pages max. Link out to longer design docs rather than
   inlining them.

8. **Show the draft to the user before writing**, then ask:
   `Save as docs/adr/NNNN-<slug>.md with status=proposed? [yes / edit / abort]`

9. **Write the file** to `docs/adr/NNNN-<slug>.md`.

10. **Update the index** `docs/adr/README.md`: append a row to the table:
    ```
    | NNNN | <title>                  | proposed | YYYY-MM-DD |
    ```
    If `README.md` doesn't have an index table, create one.

11. Print: `ADR-NNNN drafted as proposed. Promote to accepted via PR review.`

## Superseding an existing ADR

If $ARGUMENTS implies replacing a previous decision:

1. Ask which ADR is being superseded; write `Supersedes: ADR-MMMM` in the new ADR.
2. Edit the **old** ADR's status to `superseded by ADR-NNNN` (this is the only
   permitted edit to a past ADR — a status pointer).
3. Update the index for both rows.

## Hard rules

- Never edit a past ADR's body. Status pointer only.
- Status starts at `proposed`. Promotion to `accepted` happens externally
  (via PR review, team meeting, etc.). Do not auto-accept.
- Do not write an ADR for a decision that hasn't been made. If the user is
  still deciding, suggest `/plan` instead.
- If `$ARGUMENTS` is empty, ask for the title before doing anything else.
