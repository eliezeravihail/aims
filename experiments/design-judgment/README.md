# Open question — can a judgment of design quality pass through language, to or from a model?

**Status: open; designed, not yet run.** This chapter records a problem that the aims experiments ran into and
could not get around, and states it as a research question in its own right. It is kept for continuation.

## 1. The problem

aims rests on one hypothesis: a model optimizes the goal it is given, so design quality has to be part of the
goal ([paper](../../paper/aims_paper.pdf), Section 2). The hypothesis needs a **channel** in both directions:

- **To the model:** say what good design is, so that the model designs toward it. aims uses written principles
  and a scored form.
- **From the model:** find out whether a given design is good. aims uses a model reading the design and filling
  in the same form.

Both directions pass through **natural language**. No other channel to a model exists today. That includes the
assistant that ran and analysed these experiments, whose own readings of the judge reports went through the
same channel.

The experiments show that the **returning** direction does not work as a measurement. A model can state the
principles fluently and cite the design at length, and still not apply them in a way that repeats:

| observation | evidence |
|---|---|
| The same unchanged designs received grades from 5.7 to 9.8, depending on the judge. | [paper](../../paper/aims_paper.pdf), Table 4 |
| On design chapters alone (correctness removed), agreement on the grade is α 0.61 across all judges, below the 0.667 floor for even tentative conclusions. | [`judge-agreement`](../judge-agreement/README.md), `design_only` |
| At the level of the individual design chapter, agreement is α 0.36. | same |
| Two judges given the same protocol, differing only in their instructed disposition, flagged 56 design chapters as failed between them. They agreed on 21 of those. | same |
| When two judges gave similar grades (ICC 0.78), their named verdicts still matched only 5 of 9 times. | same |
| Every judge (9 of 9) recognized which method produced each design, at 97% confidence, from the surface of the text. | [`results-aims-real.md`](../principles-polish-vs-openspec/results-aims-real.md), [`results-openspec-real.md`](../principles-polish-vs-openspec/results-openspec-real.md) |
| Automatic metrics do not rescue this: they count size and branching, which good structure often increases. | [paper](../../paper/aims_paper.pdf), Section 7 |

The failure of the returning direction also leaves the outgoing direction untestable. If no reading of a design
repeats, there is no way to tell whether a model given design as its goal designed better.

## 2. What this chapter does not do

It does not replace the question with a **performance proxy**: build the code, run a sequence of changes, count
lines, files or broken tests. Such a proxy measures the cost of change, not design quality. It also escapes the
question instead of answering it. The question here is about the **judgment** itself: whether a
design-quality judgment can be communicated to a model and obtained from it in a form that holds.

## 3. The research question

> **Can a judgment of design quality be communicated to a language model, and obtained from it, in a way that
> is stable, responds to structure rather than surface, and agrees with established design knowledge?**

It splits into three sub-questions. Each can be tested on the judgment directly, with no execution and no
proxy.

**Q1 — Stability.** Does the *same* judge give the *same* judgment of the *same* design across repeated samples?
- *Why it comes first:* the current data mixes two things, a judge's own noise and real disagreement between
  judges. This separates them.
- *If the judgment is unstable within one judge:* no protocol built on top of it can repeat.

**Q2 — Surface invariance.** Does the judgment stay the same when only the surface changes?
- *The surface:* identifier names, the order of sections, the document format, the method's house style.
- *The structure:* who owns which rule, which types exist, where the seams are. This is held fixed.
- *If the judgment moves:* it is responding to the text, not the design. The 97% method recognition already
  points this way.

**Q3 — Minimal pairs.** Take two designs that differ in **exactly one** design decision, where the established
literature gives a clear verdict. Examples:
- a named type against a positional tuple;
- a rule with one owner against the same rule checked in two places;
- a concept modelled as itself against the same concept modelled as a degenerate instance of a neighbouring
  type.

Does the model reliably distinguish the two, and prefer the side the literature prefers?
- *Where the ground truth comes from:* the literature (the sources in the paper's Section 4). Not from a model,
  and not from tests.
- *Why this is the core test:* if a model cannot tell a minimal pair apart consistently, no rubric over whole
  designs can work.
- *If it can:* growing the difference, from one decision to several and then to whole designs, shows where the
  judgment breaks down.

Each sub-question is asked in **both directions**:
- *Obtaining a judgment:* the model evaluates a given design.
- *Communicating a goal:* the model is asked to produce the preferred side of a minimal pair from a
  description of the decision, and the result is checked against the pair.

## 4. What would count as an answer

- **A positive answer, at some scale:** the judgment is stable (Q1), invariant to surface (Q2), and correct on
  minimal pairs (Q3) at a stated agreement level. The scale at which this stops holding is then the finding.
- **A negative answer:** language, as the channel is used today, does not carry design judgment reliably, even
  on minimal pairs. The consequence goes beyond aims:
  - the claim that "a model can be made to design well" cannot currently be tested, by anyone;
  - "LLM-as-judge" results on code design should be read in that light.
- **Either answer is a result.** It is not a failure to show an effect.

## 5. What exists already, and what is missing

- **Exists:** the principles ([`design-principles.md`](../../skills/aims-guide/references/design-principles.md)),
  the form ([`assessment-form.md`](../judging-rubric/assessment-form.md)), 36 filled forms with measured
  agreement ([`judge-agreement`](../judge-agreement/README.md)), and one natural minimal pair: the ledger
  named-type vs tuple pair, the paper's Table 2.
- **Missing:**
  - a set of minimal pairs, each with its literature citation;
  - surface-rewrite rules that are shown to preserve structure;
  - repeated-sample runs;
  - a judge from a second model family, to tell a property of one model from a property of the channel.

## 6. Limits to keep in view

- Everything so far was run on one model family. The problem may belong to that family and not to language in
  general. Q1–Q3 on a second family is needed before generalizing.
- "Established design knowledge" is itself not unanimous. Minimal pairs should be restricted to decisions the
  literature does not dispute.
- The operator and the analyst of these experiments use the same channel as the judges. The protocol for Q1–Q3
  should keep every verdict mechanical where it can: which side of a pair was chosen, and whether a judgment
  changed.
