# Phase 1 — protocol notes, frozen before any arm runs

Operational detail `../DESIGN.md` leaves open, fixed here before any result exists.

## Arms

| dir | condition | method |
|---|---|---|
| `w1`, `w2`, `w3` | aims | the aims method pinned at commit `6108677b7ec9b778383b645771869adca73bec0d`, copied to `/tmp/claude-0/phase1/aims/`; its anchor tool installed at `.aims/anchor.py` as `/install-on` does. The two hooks are not installed — hooks do not run inside a subagent, and neither bears on a first build with no prior records. |
| `w4`, `w5`, `w6` | unaided | none — **fresh** runs; the four Phase 0 arms selected the task and are not reused |

Every arm: the pinned mkdocs checkout, its own `.venv`, the identical stage-1 card, the same model, and
no access to this repository.

**The aims arm's request** is the unaided request plus one line: *follow the `aims-guide` skill*, with its location
(`PROTOCOL.md` §2). Nothing else — the method decides everything, including which flow to use for existing code,
whether to convene the panel-plan, and whether to delegate to a Worker.

**Correction, before any aims result existed.** The first frozen version of this prompt also said *"this is a change
to existing code: plan it as `aims-add-feature` describes, and drive the full loop as `aims-plan-and-build`
describes"* and named the anchor tool's location. That chose the flow for the method, which is steering, and it
went beyond the one line the protocol allows. The owner flagged it. The three aims arms were stopped while still
reading the method — none had written a file (each directory was checked: zero changes) — their directories
were reset to fresh copies, and they were relaunched with this prompt. The unaided arms were unaffected and ran
on. The pinned method copy was also checked for anything about this experiment (mkdocs, languages, detection,
later stages): nothing.

## The product owner

Every arm may stop and return questions. Each question is answered from `../hidden/oracle.md`, verbatim, and the
arm is continued with its context intact. The same question gets the same words in every arm. Anything the
oracle does not cover gets its default: *"I don't know — choose a simple, sensible technical approach."* Every
exchange is logged in `oracle-log.md`.

## Anonymization — applied identically to all six

For each judge copy:
1. every `.md` file the arm added or changed outside `mkdocs/tests/` is reverted to pristine or removed — this
   removes aims' records (goals, architecture, decisions, companions) and any author's prose about its design;
2. `.aims/` is removed;
3. in code files, a **comment line** (`#` after whitespace) naming an aims artifact — `goals.md`,
   `architecture.md`, `base-dependencies.md`, `dependencies.md`, `decisions/NNNN`, `.aims/`, `aims` — is removed.
   The count per design is reported. A mention inside a docstring or string is left, and counted as residual.

Labels `P`–`U`, drawn with `SystemRandom`, salted; only the SHA-256 is committed before any judge runs.

## The panel, and how three judges make one verdict

Three judges score all six designs on the §0–§14 form from the code, blind, each with the same Step 0 instruction:

- **ownership** — weights whether every rule and concept has one owner that cannot be bypassed;
- **simplicity** — weights whether every abstraction pays for itself now; "small is not unearned";
- **disjoint-vocabulary** — scores from code properties and may not credit a design's self-description (the
  Phase 0 judge, adapted to six designs).

**Per judge**, with F = the lowest grade of an arm's three designs and M = their mean:

- **aims** if F(aims) > F(unaided) **and** M(aims) > M(unaided);
- **unaided** if both are lower;
- otherwise **no clear advantage**.

**The verdict:** if the ownership and simplicity judges agree, that is it. If they differ, the disjoint-
vocabulary judge decides — but only by agreeing with one of them; otherwise **no clear advantage**
(`PROTOCOL.md` §6, §7).

**The pre-registered prediction is `../DESIGN.md` §6's, unchanged:** at stage 1, aims' floor is above the unaided
floor; falsified if it is not. No prediction is added here.

Every S3 and S4 finding a verdict rests on is re-checked against the code, blind, before unsealing. A finding
that does not reproduce is reported as such, and the verdict is recomputed without it.
