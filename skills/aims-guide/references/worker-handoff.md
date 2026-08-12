# Worker handoff

A handoff is a temporary objective function for the Worker. The single most important thing about
it: **an agent optimizes toward the goal you give it.** If you give the Worker a feature ticket,
it optimizes for the feature landing — and design quality is whatever survives that. If you want
good design, the design must *be* the goal.

## Frame the objective as a quality goal, not a feature ticket

The Worker is a senior engineer, as capable as you are — not a junior filling in a spec. Your
leverage is entirely in *what goal you point it at and how you frame it*, never in dictating the
solution. So:

- **State the design/quality outcome as the objective**, with the product behavior as the
  *constraint that outcome must satisfy* — not as the thing being optimized. "Design a domain that
  owns its own rules and a persistence boundary that doesn't leak, for the following behavior" —
  not "build feature X."
- **Do not pre-make the Worker's design decisions.** Do not tell it which classes, interfaces, or
  modules to create, or how to lay them out, or which specific abstraction to introduce. Naming the
  boundaries and the traps for it turns a peer architect into an operator, and then you are testing
  your own design, not getting theirs. Point at the quality; let the Worker design.
- **Point at `references/design-principles.md` as the target the design aims at**, not a checklist
  to tick. Ask the Worker to return its design reasoning so you can evaluate the design, not only
  whether it runs.
- Give it the behavior it must support and the real product constraints and non-goals you know —
  that much is context, not choreography.

The test for a good handoff: if you handed it to two strong engineers, would they be free to arrive
at genuinely different, equally good designs? If your handoff only permits the one design you
already had in mind, you over-specified — pull back to the quality goal.

Use this shape:

```text
ROLE
You are the implementation Worker — a senior engineer as capable as the Guide. The design is the
deliverable, not just working behavior. Do not redefine project priorities. If evidence invalidates
the objective, report it instead of expanding scope.

DESIGN GOAL (the objective — a quality outcome, not a feature)
<the design/quality outcome to reach: e.g. a domain that owns its rules; a real abstraction at this
boundary; one place that enforces this rule — expressed as an outcome, leaving the how to you>

BEHAVIOR IT MUST SATISFY (a constraint on the design, not the thing to optimize)
- <observable behavior the design has to support>

WHY NOW
<brief evidence/rationale>

WHAT "GOOD" AIMS AT
The standard is references/design-principles.md — the target the design should reach, not a
checklist. Where a principle doesn't apply at this scale, it's fine not to force it; be able to
say why.

TESTING
Work test-first: write the failing test for a decision before the code that satisfies it. Cover
every non-trivial decision, branch, and failure/retry/timeout path — including ones that already
look correct, since a test's job is catching a later regression, not only proving today's
behavior. Skip only what the language/type system already guarantees or pure wiring with no
decision in it — do not write a tautological test to pad a coverage number.

RELEVANT CONTEXT / PRESERVE / NON-GOALS
- <facts and prior durable decisions needed; boundaries to protect; tempting adjacent work excluded>
- The modules, classes, and interfaces are YOURS to choose. Design for what's here, not imagined futures.

RETURN TO GUIDE
- Working code + tests, and: a short account of the key design decisions and why (where behavior
  lives, what abstractions you introduced and what a second real implementation of each looks like,
  where each rule is enforced, any duplication you chose over a shared abstraction and why).
- Result: met | partially_met | invalidated | blocked, against the design goal.
- New facts or risks discovered.
```

## Implementation objectives: track fidelity to the design with a TODO list

When the objective is an *implementation* that must conform to a design already agreed and evaluated
(the design → implement rhythm), the handoff carries the binding design decisions and the required
evidence explicitly. Tell the Worker to turn those into a checklist and work against it: **maintain
a TODO list with one item per binding design decision and one per required test/evidence item, and
check each off before returning.** For a task whose whole point is fidelity to a prior design,
tracking each decision beats hoping none was dropped — a single quietly-skipped decision is exactly
how an implementation drifts from a sound design into something else. (A pure design objective does
not need this; a large or fidelity-bound implementation does.)

## Context discipline

Do not pass the entire project transcript. The Worker should get the objective and the evidence it needs. It can inspect repository files as needed.

## Worker autonomy

The Guide specifies outcomes and boundaries, not code choreography. The Worker is free to choose
implementation details — and, more than details, the *design*: which modules, classes, and
interfaces exist and how they relate — inside the handoff, unless a durable project decision
constrains them. Choreographing the design defeats the purpose; the Worker's design judgment is
exactly what the quality goal is meant to elicit.

Before returning, tell the Worker to run the **subtractive pass** on its own design (see
`references/review.md`): for every type, guard, wrapper, or abstraction it introduced, ask what
present product force requires it — and remove the ones whose deletion would not damage the ownership
of a current rule, invariant, or boundary. A design objective reliably over-produces machinery at the
seams; catching it before the handoff comes back is cheaper than catching it in review.

## Testing discipline

Tests do two independent jobs, and both belong in the handoff because they pull toward different
tests:

- **Prove the assumption right now** — the decision this objective embodies actually holds for the
  inputs, edge cases, and failure paths it claims to handle.
- **Protect it from breaking later** — a test is a tripwire for a change made somewhere else in the
  codebase next month, not a certificate for the code being written today. This is why "it obviously
  works" is not a reason to skip a test: obviousness describes the present; the test exists for the
  later change that silently breaks it, with nothing else positioned to notice. So coverage is not
  bounded by what this objective newly touches — a path already believed correct still needs its own
  test, precisely because nobody is currently watching it.

Have the Worker work **test-first**: write the failing test that states a decision, watch it fail for
the right reason, then write the minimum code that makes it pass, one decision at a time. Test-after
tends to describe whatever the implementation happens to do, mirrored back at it; test-first forces
the test to state the contract before there is an implementation to copy from. When the Worker is
characterizing existing untested behavior rather than adding new behavior (a refactor), write the
characterization test *before* touching the code, so the diff is provably behavior-preserving rather
than trusted by inspection.

**Scope, not volume.** Cover every non-trivial decision the code makes — every branch, computed
condition, validation rule, classification, and failure/retry/timeout path. Skip only what the
language or type system already guarantees (an assignment, a getter, a pure re-export, a call that
only forwards its arguments) — a test that restates one of those proves nothing a compiler didn't
already prove and exists only to inflate a number. That is the same metric-escape the project README
warns against ("test-coverage percentages... shallow performance metrics"): the instruction to the
Worker is *every decision has a test*, never *hit N% coverage* — a coverage number is a thing to
notice afterward, not a target that was ever requested.
