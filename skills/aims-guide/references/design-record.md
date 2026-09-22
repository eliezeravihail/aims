# The design record — how the method's outputs become co-located records

Everything the loop produces worth having *next year* — **that the code itself cannot hold** — is filed as
a record **in the code tree**. This file owns the filing decision: whether a thing belongs in a record at
all, which of the two homes it goes in, and who files it when. The *shape* of a record — frontmatter, the
three sections, how the anchor is derived — is `../../../knowledge/format.md`; fill-in skeletons are in
`assets/record-templates.md`.

## First gate — does it belong in the **code** instead?

**A record is for knowledge the code cannot carry.** Most of what a design session produces *can* be
carried by the code, and is worth more there — beside the thing it describes, where a reader already is.
So before filing anything, ask where it is most useful to someone who has the file open:

| if it is… | it belongs in… |
|---|---|
| what the code does now | the **docstring** |
| why *this particular line* is surprising | a **comment right there** |
| an invariant you can make unbreakable | the **signature, the type, a private field, a guard** |
| a behaviour worth guaranteeing | a **test** |
| a concept | a **name** |

Only what survives that gate is a record — and all of it shares one property: **nothing in the code
asserts it.**

- **Why a considered alternative was rejected** — the road not taken leaves no trace in the code.
- **A non-goal, or a boundary declared deliberately** — an absence leaves nothing to read. (This is the
  one category measured to be unrecoverable from code alone:
  `../../../experiments/improve-2026-09/bp19-aims-filed-records/`.)
- **What was tried and failed**, and the symptom that made it fail.
- **An assumption the file rests on that was never proven** — stated *as* unproven.
- **The context a decision was taken in, when that context has since gone** — an incident, an external
  consumer, a contract, a constraint that expired.
- **The history** — what a superseded decision was, and why it no longer holds.

**The test, in one line: if you could delete the entry, write it as a docstring, and lose nothing, then it
was a docstring.**

**When the product *is* prose** (a method, a spec, guidance — this repo included), "the code" is the shipped
text, and the gate reads: *could the file itself simply say it?* Usually yes, and then it belongs in the file.
What survives is what a text cannot assert about itself — how it was misread, what it deliberately leaves out,
an alternative wording weighed and dropped.

**Why this is a rule and not a preference.** A record that restates the design is **duplicate state**, and
it is the only part of a record that can *go wrong on its own*: the code changes, the restatement is now
false, and the anchor merely **flags** the drift — nothing repairs it. Knowledge the code cannot hold has
no such failure mode, because nothing else asserts it. Every restated line you file buys drift and pays
nothing. A short companion of things the code cannot say is worth more than a long one that narrates it.

There are two homes, and the split is by *what the knowledge is about*.

## File-level → a companion beside a source file that has earned one

**Most files never get a companion** — one is created the first time there is something durable to record
about that file, never mechanically for every file. Knowledge **about one source file** goes in that file's companion — the same name plus `.md`, right
next to it (`src/render.py` → `src/render.py.md`) — under three sections:

- **Insights** — what was *learned* about this file: what was tried, what failed, why. Not what the code
  shows — a reader can see that.
- **Decisions** — a file-level choice and the rule it imposes, **with what it rules out** (append-only
  within the section). A decision whose rule the code already enforces is a docstring, not a Decision.
- **Discussions** — trade-offs weighed, options considered, the road not taken.

"Source file" means any file the project ships, **including a Markdown one** — in a documentation product
that is most of them. A companion for `guide.md` is therefore `guide.md.md`; the double extension looks like
a slip but is the anchor derivation working exactly as specified (strip `.md`, the sibling exists, hash it).

You read the whole companion when you touch the file, because it is all about that file. Anchor it on
filing (`python3 .aims/anchor.py <companion>`) — it hashes the same-named source file. That path is
where `/install-on` puts the tool in every project; the aims repo itself runs it from its source
location, `knowledge/anchor.py`. This line owns the invocation — everywhere else refers to it.

## System-level → a record at the repo root

Knowledge that is **cross-cutting** (not about one file) goes to the matching root record:

| The method produces… | root record |
|---|---|
| primary goal, use scenarios, non-goals | `goals.md` |
| boundaries, seams, invariants, change axes — the shape of the system | `architecture.md` |
| the foundational substrate (language, framework, pervasive base) | `base-dependencies.md` |
| a confined, replaceable dependency and what it is for | `dependencies.md` |
| a system-wide architecture decision + rejected alternatives | `decisions/NNNN-slug.md` (an ADR) |

System records take **no anchor** (they are intent/architecture, not tied to one file). `decisions/`
ADRs are append-only — to change one, add a new ADR that supersedes it, naming it.

**An ADR is not only a decision.** It is also where a **correction** or a **finding of record** goes: that an
earlier ADR's evidence no longer holds, that a result was withdrawn, that an alternative is
*considered-but-untested* rather than rejected. Such an entry may leave the ADR it concerns **unsuperseded** —
it corrects the record beside it rather than replacing it. Read literally as "a decision + rejected
alternatives", the table above would leave these unfilable; in practice they are the reason several of this
repo's own ADRs exist.

## The split, sharply

- **Could the code carry it?** → put it there (see *First gate* above) and file nothing. This question
  comes first and disposes of most candidates; most files never earn a companion at all.
- Is the knowledge **about one file**? → its companion, in the right section.
- Is it **cross-cutting**? → the matching root record.
- Unclear? **Count the files it binds.** One file → its companion, *even if the reason is system-wide*
  (an external consumer, a contract, an incident) — an external justification does not make it an ADR.
  Several files → system-level.

**Cross-cutting learning goes in the root record it concerns** — an insight about what the project is for
or what the evidence supports belongs in `goals.md`; one about the system's shape belongs in
`architecture.md`. There is no separate root "Insights" record and none is needed: the three headings of a
companion describe *a companion*, not a shape the root level has to repeat.

Do not put a file-level insight at the root, and do not scatter a system-wide decision across file
companions. If a would-be file-level insight actually concerns *several* files at once, that is usually a
system-level fact (→ `architecture.md` or an ADR) or a signal the files share a responsibility that
wants its own home (an add-feature objective) — not a note copied into many companions.

## Who files, and when

The Guide owns the records — from its own decisions and the design reasoning the Worker returns. At
planning time file `goals.md`, `base-dependencies.md`, the substrate/architecture decisions; at build
and review time, add file-level Insights/Decisions/Discussions to the companions of the files touched,
and a superseding ADR when a system decision changed. An unfiled decision is a lost one.

## Reading — navigate, don't read everything

To understand a file, open its companion (all of it). For system context, read the root records
(`goals.md`, `architecture.md`, the relevant ADR). Relevant knowledge is reached by *navigating* to the
file or the root record — never by reading the whole project. A stale-flagged companion is *possibly*
out of date; re-verify against the current code first.

## Bootstrapping

Create root records as they earn their place (`goals.md` first, usually). A source file gets a companion
the first time there is something durable to record about it — not mechanically for every file.
