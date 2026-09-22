# The design record — how the method's outputs become co-located records

Everything the loop produces worth having *next year* — **that the code itself cannot hold** — is filed as
a record **in the code tree**. This file owns the filing decision: whether a thing belongs in a record at
all, which of the two homes it goes in, and who files it when. The *shape* of a record — frontmatter, the
three sections, how the anchor is derived — is `../../../knowledge/format.md`; fill-in skeletons are in
`assets/record-templates.md`.

## The rule — one rule, and everything below is it applied

**Knowledge goes to the narrowest thing it is true of.** That is the whole method. A reader looks where
they already are, so knowledge waits there; a filer's only question is *what is this true of?* — and the
answer is the address.

| true of… | goes… | anchored? |
|---|---|---|
| one line | a **comment** right there | — |
| one function | its **name**, **signature**, **docstring**, or a **test** | — |
| one file | its **companion**, `<file>.md` beside it | yes, to that file |
| one directory / package | a record **beside the directory**, `<dir>.md` | no — a directory has no single content |
| one dependency | `dependencies.md` — it is true of the library, not of whoever calls it | no |
| the whole project | the **root record it concerns** — `goals.md`, `architecture.md`, `dependencies.md`, an ADR | no |

**The ladder ranges only over what the code cannot carry.** Run the *first gate* below before reading the
table at all: it decides whether this is knowledge for a record or for the code, and the ladder then places
what survives. An external reason — a library's defect, a contract, an incident — does not exempt a fact
from the gate; if a comment at the line can state it, that is where it goes, and only what the comment
cannot say (an alternative weighed, a fix attempted and failed) reaches a record.

Two consequences do all the work, and they are the two halves of the same rule:

- **Narrower wins.** If a docstring is the narrowest true home, a companion is the wrong one — that is the
  *first gate* below, and it is the case that disposes of most candidates.
- **Wider is wrong too.** A fact true of six parsers and nothing else is not an `architecture.md` invariant;
  filing it there claims the whole system obeys it. It goes beside `src/parsers/`, as `src/parsers.md`.

**A thing that no longer exists is not an address.** Knowledge about something deleted goes to the narrowest
thing that now holds its responsibility — the file or directory that took it over — and to the project only
if nothing did. Never file a companion for a removed file: with no sibling to anchor to it is an orphan, which
the hook reports as a fault, not a home.

**Scope is continuous, not two-valued.** There is no rule that knowledge must be about exactly one file or
about everything; "count the files it binds" below is a way of *finding* the narrowest true scope, not a
choice between two homes.

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

**"The code carries it" means a reader would meet it** — in a name, a signature, a guard, a test, or a
convention every instance already follows. It does not require the code to *enforce* it. A convention the
code exhibits everywhere is carried; what is not carried is *why* it is that way and what it rules out, and
only that reaches a record.

**When the product *is* prose** (a method, a spec, guidance — this repo included), "the code" is the shipped
text, and the gate reads: *could the file itself simply say it?* Usually yes, and then it belongs in the file.
What survives is what a text cannot assert about itself — how it was misread, what it deliberately leaves out,
an alternative wording weighed and dropped.

**Why this is a rule and not a preference.** A record that restates the design is **duplicate state**, and
it is the only part of a record that can *go wrong on its own*: the code changes, the restatement is now
false, and the anchor merely **flags** the drift — nothing repairs it. Knowledge the code cannot hold has
no such failure mode, because nothing else asserts it. Every restated line you file buys drift and pays
nothing. A short companion of things the code cannot say is worth more than a long one that narrates it.

The homes below are that ladder, written out.

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

## Directory-level → a record beside the directory

A fact true of every file in `src/parsers/` and of nothing else goes in `src/parsers.md`, beside the
directory it describes — same three sections. It takes **no anchor**: a directory has no single content to
hash, so the tool files it as a system record, which is correct. Reach for this exactly when the narrowest
true scope is a package: not a fact about one file that several happen to share, and not a fact the rest of
the system obeys too.

Copying the same note into six companions, or promoting it to `architecture.md`, are the two ways of getting
this wrong — one understates the scope, the other overstates it.

## Project-level → a record at the repo root

Knowledge that is **cross-cutting** (not about one file) goes to the matching root record:

| The method produces… | root record |
|---|---|
| primary goal, use scenarios, non-goals | `goals.md` |
| boundaries, seams, invariants, change axes — the shape of the system | `architecture.md` |
| the foundational substrate (language, framework, pervasive base) | `base-dependencies.md` |
| a dependency — what it is for, and what is known about it (a defect to guard against, a constraint it imposes) | `dependencies.md` |
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
- Is it true of a **dependency** rather than of your code? → `dependencies.md`. A file that merely guards
  against a library's defect is not what the defect is true of; counting callers would misaddress it.
- Otherwise, unclear? **Count the files it binds** — this finds the narrowest true scope. One file → its companion,
  *even if the reason is system-wide* (an external consumer, a contract, an incident) — an external
  justification does not widen what the knowledge is true of. One directory → beside that directory. The
  whole system → the root record it concerns.

**Cross-cutting learning goes in the root record it concerns** — an insight about what the project is for
or what the evidence supports belongs in `goals.md`; one about the system's shape belongs in
`architecture.md`. There is no separate root "Insights" record and none is needed: the three headings of a
companion describe *a companion*, not a shape the root level has to repeat.

Do not put a file-level insight at the root, and do not scatter a system-wide decision across file
companions. A would-be file-level insight that concerns *several* files at once belongs at their narrowest common
scope — their directory if that is what it is true of, a root record if the whole system obeys it — and it
may also be a signal that those files share a responsibility wanting its own home (an add-feature
objective). What it is never is a note copied into many companions.

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
