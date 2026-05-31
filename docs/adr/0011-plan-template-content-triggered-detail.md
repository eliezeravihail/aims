# ADR-0011: Plan template — content-triggered detail, configurable summary language, structured documentation actions
Status: proposed
Date: 2026-05-31
Supersedes: parts of ADR-0010 (plan template length cap, section list, and the "ADRs to record after implementation" format)
Superseded by: —

## תקציר מנהלים

- **בעיה:** התבנית הנוכחית (ADR-0010) קובעת יעד אורך אחיד "≤80 שורות" לכל פלאן. כשפלאן מערב גם שינוי מכני (config flip, rename) וגם רכיב אלגוריתמי חדש, לחץ האורך דוחס את הרכיב האלגוריתמי — בדיוק היכן ש-edge cases חיים. נצפה ראיה: פלאן OBB עם file:line refs ספציפיים אך בלי pseudo-code לאלגוריתם החדש; edge cases (קבוצת offsets ריקה, downscale-floor, מתחרים מרכזיים) נעלמו לפרוזה.
- **גישה:** להחליף את יעד האורך הכמותי בכלל צורה תלוי-תוכן — שינוי מכני נשאר one-liner, אלגוריתם חדש מקבל קוד ברמת copy-paste; להוסיף סעיף Open design questions שמכריח זיהוי מפורש של edge cases לא פתורים (מובחן מ-Risks); להחליף את checklist ה-ADRs ב-Documentation actions מובנה ל-machine consumption.
- **שפה:** התקציר נשמר בשפה שהוגדרה ב-`/install-on` ונכתבה אל `.claude/aims-summary-lang` (ברירת מחדל: `en`). `/plan` קורא אותה ומחליף את הכותרת.
- **סיכון:** הסרת cap-אורך מאפשרת פלאנים שתופחים. הכלל הצורתי מונע זאת רק אם מודלים יישמו אותו נכון. lint עתידי יוכל לאכוף.
- **תוצאה צפויה:** פלאנים יחזיקו את הצורה המינימלית הנדרשת לכל סוג צעד; edge cases לא יישארו מוסתרים בפרוזה; auto-close-out יוכל לפעול על checklist מובנה.

## Context

ADR-0010 set the plan template at: TL;DR first, "Options considered"
conditional, target ≤ 80 lines.

The uniform-length target has a documented failure mode. When a plan
mixes mechanical changes (config flips, renames) with algorithmic
changes (new computations, geometric routines, state machines), the
80-line cap forces compression onto whichever step type is largest —
almost always the algorithm. Mechanical steps compress to one line
without information loss; algorithmic steps compress only by dropping
edge-case enumeration.

Concrete evidence inspected this session: a plan titled "Tame OBB
augmentations" had file:line refs for every existing-code reference but
described its new algorithm (random mosaic crop with object-centered
guarantee + downscale-to-fit) in prose only. Critical branches — empty
valid-offset set, competing centered objects, downscale-floor below
minimum, two objects on the same seam — were either invisible or
mentioned in passing. The plan read as specific but was unimplementable
without re-deriving the geometry.

The cap also amplifies a user-level preference misinterpretation. The
"no speculation" directive (about runtime fallbacks) can be over-
generalized by the model to mean "no speculative artifacts in plans",
which discourages pseudo-code precisely where it's most needed.

The fix is to remove the length target entirely and replace it with
content-level rules: a step's shape is determined by what it does, not
by a global cap; algorithmic steps must surface their unresolved
branches in a dedicated section; test descriptions specify the
assertion shape, not the test code. The executive-summary language
becomes a project config so non-English users get summaries in their
language without per-plan asking.

## Decision

We will replace the plan template's section list and length cap with
the following six-section structure. Order is fixed; length is not.

```
## תקציר מנהלים                ← problem + approach, in the configured language
## Technical design             ← content-triggered detail
## Open design questions        ← unresolved edge cases from Technical design
## Tests to add                 ← assertion shape, no code
## Risks                        ← what could go wrong even if design holds
## Documentation actions        ← structured checklist
```

### Per-section rules

**1. Executive summary** (heading per configured language)
One short block — 3–5 bullets or one paragraph. States the problem
and the chosen approach. Heading and body in the language stored at
`.claude/aims-summary-lang` (default `en`). Built-in heading
translations: `en` → "Executive summary", `he` → "תקציר מנהלים".
Unknown codes fall back to `en`.

**2. Technical design** — content-triggered shape:

- *Mechanical change* (config flip, rename, file move, dependency
  bump): one bullet, `before → after`, with `file:line`.
- *Refactor without new logic:* before/after signatures or diff
  sketch.
- *New algorithm, new data structure, new geometric computation, new
  state machine:* pseudo-code or actual code, with arg/return types
  and a concrete worked example. Edge-case enumeration goes either
  inline or under "Open design questions".

No global line cap. If in doubt about a step's category, expand.

**3. Open design questions**
Every algorithmic step in section 2 either resolves its edge cases
inline or lists them here. Distinct from Risks: "Risks" is "what
could go wrong even if our design holds"; "Open design questions"
is "what we didn't fully specify yet". Closing a plan with open
questions is acceptable; closing one without realizing it has any
is the failure mode this section prevents.

**4. Tests to add**
Each entry specifies the assertion shape, not the test function:

```
- Given <input>: assert <expected output / invariant>.
```

Test code is written at implementation time.

**5. Risks**
What could go wrong even if every specified behavior is correct
(env assumptions, perf regressions, integration surprises).

**6. Documentation actions** — structured checklist:

```
- ADRs to draft (proposed status):
  - [ ] ADR-NNNN — <title>
- Plan status: completed | superseded | aborted; append ## Outcome.
- Memory nodes to flag dirty: <list of docs/memory/ paths>
- CLAUDE.md sections to update: <list, or "none">
- External (optional): changelog, release notes, Slack, etc.
```

Preserved as a parseable block so the auto-close-out flow can act on
it without re-deciding.

### Configurable summary language

`.claude/aims-summary-lang` is a single-line plain text file containing
an ISO 639-1 code (`en`, `he`, `es`, `fr`, …) or a language name.
`/install-on` interview asks once; default `en`. `/plan` reads it
when drafting and substitutes the first heading. Adding a language
heading is a one-line patch to the heading map.

## Consequences

- ✅ Algorithmic steps can no longer hide edge cases in prose. Length
  pressure no longer makes "complete the plan" mean "compress the
  algorithm."
- ✅ Mechanical plans stay short. The content trigger means a config
  flip remains one bullet, not six.
- ✅ Documentation actions become machine-readable, enabling the
  auto-close-out flow (ADR-0010 Phase 4) to execute the list instead
  of re-deciding per item.
- ✅ Non-English users get summaries in their language without per-
  plan asking.
- ⚠️ Removing the line cap allows over-long plans. Mitigation is
  social for now (reviewers reject sprawl); a future lint pass can
  enforce per-step content rules.
- ⚠️ The model must judge "is this step algorithmic?" — borderline
  cases exist. Bias is to expand: if in doubt, treat as algorithmic.
- 🔒 Closes the door on uniform length targets for plans. Templates
  proposing fixed caps must justify why the content rule isn't
  enough.

## Alternatives considered

- **Keep the 80-line cap, add a per-step shape rule on top.**
  Rejected. The cap and the shape rule are in tension: if the cap
  binds, the shape rule loses. Removing the cap is cleaner.
- **Use Markdown front-matter to tag each step (`type: mechanical |
  algorithmic`).** Rejected as over-engineered. Conventional bullet
  structure suffices; revisit if lint enforcement is added.
- **Hard-code English for the executive summary.** Rejected. The
  project owner is a Hebrew speaker; a one-line config gives the
  same outcome without forking the template.
- **Mandate test code in plans.** Rejected per design discussion —
  separates plan-time intent from implementation-time code. Plans
  describe what to assert; implementers write the test.
- **Keep the "ADRs to record after implementation" single checklist
  from ADR-0010.** Rejected. The structured Documentation actions
  block subsumes it and also captures memory nodes, CLAUDE.md
  sections, and external comms — fields the close-out flow needs.

## Verification

- `templates/commands/plan.md` Phase 1 step 4 lists exactly the six
  required sections in the order above, with no `target ≤N lines`
  clause.
- `templates/commands/plan.md` Phase 2 step 4 produces a file with the
  six headings in order.
- `templates/commands/install-on.md` Phase 2 includes a question for
  the summary language; Phase 4 writes the chosen value to
  `TARGET/.claude/aims-summary-lang`.
- `templates/commands/plan.md` reads `.claude/aims-summary-lang` (or
  defaults to `en`) and substitutes the first heading accordingly.
- A plan for a mechanical-only change remains short (a natural ≤30
  lines); a plan for a new algorithm contains pseudo-code or actual
  code with edge-case enumeration (either inline or in Open design
  questions).
