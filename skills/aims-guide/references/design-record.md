# The design record — how the method's outputs become co-located records

Everything the loop produces worth having *next year* — **that the code itself cannot hold** — is filed as
a record **in the code tree**. This file owns the filing decision: whether a thing belongs in a record at
all, where it goes, and who files it when. The *shape* of a record — frontmatter, the
three sections, how the anchor is derived — is `../../../knowledge/format.md`; fill-in skeletons are in
`assets/record-templates.md`.

## Where knowledge goes

**Write it next to what it is about.** That is the whole idea; everything else here is it applied.

Someone will need this knowledge while they are looking at something — a line, a file, a folder, the
project as a whole. Put it there and they meet it without going to look for it. Put it anywhere else and
they don't, and it might as well not exist.

Two things follow.

**Say it in the code whenever the code can say it.** A name, a signature, a comment at the line, a guard, a
test — these sit closer to the thing than any record can, and they are read by people who never open a
record. So a record is not the default home for what you learned; it is what you write when the code has no
way to say it.

**Otherwise write it beside the thing it is about.** About one file → a companion next to that file. About a
folder → a record next to that folder. About the project → the root record that concerns it. About a
library → with the library, however many files call it. About something you deleted → wherever its job went.

Nothing here needs classifying or counting. Ask what the knowledge is about, and go there.

## What only a record can hold

The code can describe what is, and nothing else. A record is for what is **not** there, which is why nothing
in the code asserts it:

- why an alternative was **rejected** — the road not taken leaves no trace;
- a **non-goal**, or a boundary you declared deliberately — an absence leaves nothing to read (this is the
  one category measured to be unrecoverable from code alone:
  `../../../experiments/improve-2026-09/bp19-aims-filed-records/`);
- what you **tried and it failed**, and the symptom that killed it;
- an **assumption the work rests on that was never proved** — said as unproved;
- the **reason behind a decision once that reason is gone** — an incident, a consumer, a constraint that expired;
- the **history** — what a superseded decision was, and why it no longer holds.

**The test, in one line: if you could delete the entry, write it in the code, and lose nothing, then it
belonged in the code.** That disposes of most candidates. It applies to a fact with an external cause too —
a library's defect, a contract, an incident: if a comment at the line states it, that is where it goes, and
only what the comment cannot say reaches a record. And "the code says it" means a reader would meet it — in
a name, a guard, a test, or a convention every instance already follows — not that something enforces it.

**When the product is prose** (a method, a spec, guidance — this repo included), "the code" is the shipped
text, and the question reads: *could the file simply say it?* Usually yes. What survives is what a text
cannot assert about itself — how it was misread, what it deliberately leaves out.

**Why this is a rule and not a preference.** A record that restates the code is **duplicate state**, and the
only part of a record that can go wrong on its own: the code changes, the restatement is now false, and the
anchor merely **flags** the drift — nothing repairs it. What the code cannot hold has no such failure mode,
because nothing else asserts it. A short record of things the code cannot say is worth more than a long one
that narrates it.


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
hash, so the tool files it as a system record, which is correct.

This is for a fact that is genuinely about the folder — not one about a single file that the others happen
to share, and not one the rest of the system obeys too. Copying the same note into six companions says too
little; putting it in `architecture.md` says too much.

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

## In short

Ask what the knowledge is about, and go there.

- Can the code say it? Then it goes in the code, and you file nothing. Most candidates end here, and most
  files never earn a companion.
- About one file → that file's companion. An external reason for it — a consumer, a contract, an incident —
  does not change what it is about.
- About a folder → a record beside the folder. Not copied into each file's companion, which understates it,
  and not raised to `architecture.md`, which claims the whole system obeys it.
- About a library → `dependencies.md`. A file that merely guards against a library's defect is not what the
  defect is about.
- About the project → the root record that concerns it: what it is for and what its evidence supports →
  `goals.md`; its shape → `architecture.md`; a decision, correction or finding → an ADR. There is no
  separate root "Insights" file and none is needed — a companion has three headings because it holds
  everything about one file; a root record is already about its subject.
- About something you deleted → wherever its job went. Never a companion for a removed file: with nothing
  to sit beside, it is an orphan the hook reports as a fault.

Several files sharing one insight can also be a signal that they share a responsibility wanting its own
home — an add-feature objective, not a record.

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
