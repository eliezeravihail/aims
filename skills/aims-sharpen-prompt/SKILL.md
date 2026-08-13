---
name: aims-sharpen-prompt
description: Sharpen a vague or open-ended task into a real brief BEFORE executing it. Use whenever handed a substantial task — "plan a pension", "review this", "find the bugs", "build X", "write the report" — whose framing decides whether the result actually helps: it surfaces the real outcome, the hard judgment the ask hides, what only the person can decide (ask, don't guess), what "done" checkably means, what to protect, and what evidence must back the claims. The general-purpose companion to aims-guide, which does this for software design.
user-invocable: true
---

# aims — sharpen the prompt

You have been handed a task. Before you do it, **frame it** — because you optimize whatever you were
told, so the framing, not just the effort, decides whether the result helps. This is **not a form to
fill in**. The six ideas below are a way of thinking, and the test is not that six fields got filled —
it is that you refused to start until you actually understood what would make the result help. A frame
you can tick without thinking is not a frame; it is the failure this skill exists to prevent.

## Why framing is the work

You will produce *something* for any task. The danger is never that you do nothing — it is that you
optimize the literal ask and quietly settle everything it left open by whatever default is easiest.
"Plan a pension" collapses into "list some funds"; "find the bugs" into "skim for the obvious ones". The
output looks like an answer and misses the thing that mattered. Framing is the short, deliberate act of
surfacing — *before* you execute — the few things that decide whether the result is genuinely useful.
Reason through the six ideas below **in the task's own terms**, not by restating these headings.

## 1. Optimize the real outcome, not a proxy for it

You hit exactly the target you were given, so name the outcome that would truly help the person, in
their terms — not the nearest easy-to-produce substitute. A pension plan's real outcome is "the money
lasts through a bad market to the end of life", not "a portfolio exists". A bug hunt's real outcome is
"the failures that would actually hurt a real user are found", not "a list of warnings was produced". If
you cannot yet state the real outcome plainly, you are not ready to start — closing that gap is the
first move.

## 2. Find the hard judgment the task hides — and face it, don't route around it

Every task worth doing turns on one or two genuinely hard calls, and the lazy framing lets exactly those
evaporate. The value of the work lives there. For a pension: *how much loss can this person actually
endure without bailing out at the bottom* — the number that silently governs everything downstream. For
bugs: *which failure is catastrophic versus cosmetic* — because a hunt with no sense of severity buries
the one that matters under noise. Say the hard call out loud and make confronting it part of the task,
instead of slipping past it to the easy parts.

## 3. Separate what you know, what only the person can decide, and what you may choose freely

Three kinds of open point, and the discipline is not to confuse them. Facts you already have. Decisions
that change the result and belong to the person alone — **ask these, never guess**, because a plausible
guess here is still a guess, and it quietly decides someone's life or system for them. And free choices
with no real consequence — pick something sensible and move on, without turning them into a
questionnaire. Pension: retirement age, dependents, real appetite for risk — ask. Bugs: what "correct"
even means here, what is in and out of scope — ask. The cardinal error is disguising a decision that is
the person's as a technical assumption of your own.

## 4. Say, checkably, what a good result looks like

A target you cannot test against is one you will meet on paper and miss in fact. Replace "a good plan"
or "be thorough" with a few conditions that could actually be checked. Pension: "it survives a
2008-scale drop without the money running out before age 90." Bugs: "every failure reported comes with
an input that reproduces it, or a precise pointer to the line." This is what stops you from declaring a
success you did not earn — and from leaving the exact hard cases unhandled because nobody named them as
part of "done".

## 5. Say what not to optimize, and what must not break

An unbounded "make it good" quietly trades away things that mattered. Name the constraints and the
things to preserve, so they are not sacrificed to the headline goal. Pension: don't chase the maximum
return; keep enough liquid for an emergency. Bugs: don't refactor while hunting; preserve the current
behavior. Naming what to hold fixed is as much of the frame as naming what to pursue — often more,
because it is what your own drive to optimize will otherwise erode.

## 6. Trust evidence, not your own say-so

You — like anyone — will be tempted to report confidence you have not earned: "the plan is safe", "I
checked every path". A self-report cannot be verified, whether it is mistaken or glib; asking yourself
"am I sure?" only invites the same answer again. So make the *evidence* present in the result, or mark
the claim unverified. Pension: "this survives a bad decade" means nothing without the actual drawdown it
was tested against. Bugs: "I checked all the inputs" means nothing without the list of what was checked.
Show the basis; don't offer reassurance — the presence or absence of the basis is something that can be
observed, and a promise is not.

## Using it

Reason through the six in the task's own terms, write the short framed brief they produce — the real
outcome, the hard call, what to ask, what "done" checkably means, what to protect, and what evidence
will back the claims — then ask the person the few things only they can answer, and only then do the
work. For a software product that will evolve, hand off to **aims-guide**, which applies this same
discipline with design as the goal.

---

*Credit: the discipline of sharpening a vague ask into a small, well-defined brief before handing it to
an agent was learned from **Kritt-ai**'s [open·kritt](https://github.com/Kritt-ai/open-kritt) — whose
approach is to break work into focused, precisely-framed tasks rather than point a model at a broad
goal. aims adapts that idea to framing a single task before you execute it.*
