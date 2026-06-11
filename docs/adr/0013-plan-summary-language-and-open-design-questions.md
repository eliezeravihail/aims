# ADR-0013: Plan template — configurable summary language and explicit Open design questions
Status: accepted
Date: 2026-05-31
Supersedes: —
Superseded by: —

## תקציר מנהלים

- **בעיה 1:** ה-TL;DR של כל פלאן באנגלית בלבד; משתמשים שאינם דוברי אנגלית חוזרים על אותה פעולה ידנית פלאן אחר פלאן.
- **בעיה 2:** התבנית הנוכחית (ADR-0010 + #25/#26) מטפלת היטב ב-post-implementation accounting (`## Close-out checklist`) אבל אין סעיף חובה ל-pre-implementation unresolved branches. דוגמה אמיתית: פלאן OBB אוגמנטציה שראינו השאיר edge cases אלגוריתמיים בפרוזה ("pick a random object that fully fits") בלי לזהות שקבוצת המועמדים יכולה להיות ריקה.
- **גישה:** (1) קובץ `.claude/aims-summary-lang` בן שורה אחת, נשאל ב-`/install-on`, ברירת מחדל `en`. `/plan` קורא אותו ומחליף את הכותרת ושפת הגוף של ה-TL;DR. מפת תרגום מובנית: `en` → `## TL;DR`, `he` → `## תקציר מנהלים`. (2) סעיף חובה חדש `## Open design questions` בין `## Changes` ל-`## Verification`, שנבדל מ-Risks (env/ops) ומ-Close-out (post-impl accounting).
- **סיכון:** סעיף "Open design questions" עלול להיהפך ל-dumping ground אם משתמשים לא ימחקו אותו כשהוא ריק. Mitigation: ההוראה היא "Omit only if you actually verified there are none — not 'I didn't think of any'", ובפאזת close-out כל שאלה פתוחה נסגרת או מועברת ל-TODO.
- **תוצאה צפויה:** משתמשים לא-אנגלים מקבלים TL;DR בשפתם בלי לבקש בכל פעם; edge cases אלגוריתמיים מקבלים מקום מפורש בתבנית, לא נשארים חבויים בפרוזה.

## Context

After PRs #25 ("plan: reframe template to signal-only") and #26 ("plan:
mandatory always-present close-out checklist"), the plan template already
covers the main failure modes of ADR-0010 — uniform length cap dropped,
content-trigger applied via `## Changes` (snippet IS the spec),
post-implementation accounting enforced via `## Close-out checklist`.

Two gaps remain.

**1. Summary language is hard-coded English.** The project owner reads
Hebrew preferentially; some collaborators read other languages. Asking
"what language" per plan is friction; configuring it once at install is
the matching shape for project-level preference.

**2. No pre-implementation unresolved-branches section.** A plan
inspected this session ("Tame OBB augmentations") described a new
algorithm in prose with `file:line` cites for *existing* code references,
but the algorithm's edge cases — empty valid-offset set, competing
centered objects, downscale-floor below minimum — were either invisible
or mentioned in passing. The plan looked specific but was unimplementable
without re-deriving the geometry. `## Changes` (which carries code) and
`## Risks` (env/ops surprises) don't catch this; `## Close-out checklist`
records what was done, not what was left ambiguous. A distinct section
forces the writer to state "did I actually pin down all the branches?"
before approval.

## Decision

Two additive changes to `/plan` and `/install-on`. Both layered on top
of the current master template — no supersession of #25/#26's structure.

### Change 1 — `.claude/aims-summary-lang` (one-line config)

- `/install-on` Phase 2 asks question 6: "Plan executive-summary
  language (default `en`)." Re-install keeps the existing value.
- Phase 4 writes the chosen value to `TARGET/.claude/aims-summary-lang`
  (single-line plain text).
- `/plan` Phase 1 step 4: when writing the TL;DR section, read the file
  (default `en` if missing). Substitute the heading via:
  - `en` → `## TL;DR`
  - `he` → `## תקציר מנהלים`
  - any other code → fall back to `en` heading; body still goes in the
    requested language. Adding a new heading translation is a one-line
    patch to the map.
- The TL;DR body is in the configured language. The rest of the plan
  stays in English: identifiers, paths, code, ADR titles, verification
  commands — language-neutral content.

### Change 2 — `## Open design questions` section

- Inserted in the required-sections list between `## Changes` and
  `## Verification`.
- Captures pre-implementation branches that `## Changes` does NOT pin
  down: empty/edge inputs, racing concurrent cases, undefined behavior
  on the boundary of a new algorithm.
- Omitted only when the writer actually verified there are none — not
  by default and not "because I didn't think of any."
- Distinct from `## Risks` (which is env/ops surprises that survive a
  correct spec) and from `## Close-out checklist` (which is post-
  implementation accounting).
- Phase 4 close-out resolves each question: either **answered inline**
  (rewrite the bullet with the answer) or **carried forward** as a
  `TODO:` line in the Close-out checklist. A closed plan may not
  leave an open question unaddressed.

## Consequences

- ✅ Non-English users get TL;DR in their language without per-plan
  asking. Project-level config matches the granularity of the
  preference.
- ✅ Algorithmic edge cases get a dedicated home. They no longer have
  to be smuggled into `## Risks` (wrong place) or skipped because the
  writer didn't realize they were open.
- ✅ Close-out forces resolution — open questions either become
  answers or become explicit TODOs. They cannot survive a closed plan
  silently.
- ⚠️ `## Open design questions` is the section most likely to be left
  empty by reflex ("none" without checking). The instruction text
  explicitly distinguishes "verified none" from "didn't look" but this
  is enforceable only by reviewer judgment until a future lint pass.
- ⚠️ The TL;DR-only language scoping (rest stays English) is a
  deliberate choice; users who want full-Hebrew plans will find the
  English `## Changes` jarring. Re-evaluate if this complaint surfaces.
- 🔒 Closes the gap that ADR-0011 (the proposed full-template ADR I
  drafted earlier this session) was trying to fill — but does so by
  layering two additions on top of master rather than by replacing the
  whole template. PRs #25 and #26 already did the heavy lifting.

## Alternatives considered

- **Localize the whole plan (including `## Changes`).** Rejected. Code,
  paths, and identifiers are language-neutral; localizing prose around
  English code looks worse than English-with-localized-summary.
- **Hard-code English; let users translate per-plan in their head.**
  Rejected. The project owner is a Hebrew speaker working with the tool
  daily; one-line config has equal cost to a hard-code and no friction.
- **Fold "Open design questions" into the existing
  `## Risks / unknowns` section** by widening its definition. Rejected.
  Risks and unresolved-branches answer different questions ("what
  could break even if our spec holds" vs "is our spec actually
  complete"). Conflating them was the OBB plan's failure mode.
- **Require `## Open design questions` always present, even when
  empty (NONE — verified)**. Rejected for now in favor of "omit only
  if verified" — keeps the per-plan visual cleaner when the section
  is genuinely not needed. Revisit if writers start skipping by
  reflex.

## Verification

- `templates/commands/plan.md` Phase 1 step 4 lists `## Open design
  questions` between `## Changes` and `## Verification`.
- `templates/commands/plan.md` Phase 2 step 4 file template shows the
  TL;DR heading comment referencing the language map and includes the
  `## Open design questions` block.
- `templates/commands/plan.md` Phase 4 close-out step 4 includes the
  "resolve every open question" sub-step.
- `templates/commands/install-on.md` Phase 2 includes question 6;
  Phase 4 table writes `.claude/aims-summary-lang`; the variable
  `{{SUMMARY_LANG}}` is listed; doctor report includes the line.
- A plan written under the new template by a Hebrew-configured project
  has `## תקציר מנהלים` as the first heading.
- A plan for a new algorithm has `## Open design questions` with real
  unresolved branches listed; a plan for a config flip can omit the
  section.
