# The design record — where design knowledge goes

**The rule.** Discussions and decisions that are **not evident from the code itself** go in a `.md` file
next to what they are about: beside the relevant file, in the relevant module's folder, or at the project
root if they concern the whole project.

**Everything else belongs in the code's own documentation** — a name, a signature, a docstring, a comment
at the line, a guard, a test. If the code can say it, that is where it goes, and no record is written.

That is the whole idea. The rest of this file is detail.

*(Shape of a record — frontmatter, sections, the anchor: `../../../knowledge/format.md`. Skeletons:
`assets/record-templates.md`.)*

## What is not evident from the code

The code describes what *is*. A record is for what is **not** there — which is why nothing in the code
asserts it:

- why an alternative was **rejected**;
- a **non-goal**, or a boundary declared deliberately (the one category measured unrecoverable from code
  alone — `../../../experiments/improve-2026-09/bp19-aims-filed-records/`);
- what was **tried and failed**, and the symptom;
- an **assumption never proved** — said as unproved;
- the **reason behind a decision once that reason is gone**;
- the **history** — what a superseded decision was, and why it no longer holds.

**The test: if you could delete the entry, write it in the code, and lose nothing, it belonged in the
code.** This disposes of most candidates, including facts with an external cause — a library's defect, a
contract, an incident. An external reason does not make something record material; only what a comment
cannot say does. And "the code says it" means a reader would meet it, not that something enforces it.

A record that restates the code is **duplicate state** — the one part of a record that can go wrong by
itself. The code changes, the restatement is now false, and the anchor only *flags* the drift; nothing
repairs it. What the code cannot hold has no such failure mode, because nothing else asserts it.

*(When the product is prose — a method, a spec, this repo — "the code" is the shipped text: could the file
simply say it? What survives is what a text cannot assert about itself, such as how it was misread.)*

## Where

| about… | goes in… |
|---|---|
| one file | `<file>.md` beside it — `src/render.py` → `src/render.py.md` |
| a folder | `<dir>.md` beside it — `src/parsers/` → `src/parsers.md` |
| a library | `dependencies.md` — a file that merely guards against a defect is not what the defect is about |
| the project | the root record it concerns (below) |
| something deleted | wherever its job went — never a companion for a removed file, which would sit beside nothing |

**Most files never get a companion.** One appears the first time there is something durable to record about
that file, never mechanically.

Each of these holds the same three sections:

- **Insights** — what was learned: tried, failed, why. Not what the code shows.
- **Decisions** — the choice and the rule it imposes, **with what it rules out**. Append-only: supersede in
  place, never rewrite. A rule the code already enforces is a docstring, not a Decision.
- **Discussions** — trade-offs weighed, options considered, the road not taken.

## Root records

| about… | record |
|---|---|
| what the project is for — goal, use scenarios, non-goals | `goals.md` |
| its shape — boundaries, seams, invariants, change axes | `architecture.md` |
| the foundational substrate (language, framework, pervasive base) | `base-dependencies.md` |
| a dependency: what it is for, and what a caller must respect about it | `dependencies.md` |
| a system-wide decision, correction, or finding of record | `decisions/NNNN-slug.md` |

An ADR is **not only a decision**. It is also where a correction or a finding goes — that an earlier ADR's
evidence no longer holds, that a result was withdrawn, that an alternative is *considered-but-untested*
rather than rejected. Such an entry may leave the ADR it concerns unsuperseded; it corrects the record
beside it rather than replacing it. ADRs are append-only.

There is no root "Insights" file and none is needed: a companion has three sections because it holds
everything about one file, while a root record is already about its subject.

## Anchoring

A companion is anchored on filing: `python3 .aims/anchor.py <companion>` — it hashes the same-named source
file. *(That is where `/install-on` puts the tool; this repo runs it from `knowledge/anchor.py`. This line
owns the invocation; everywhere else refers to it.)* Folder and root records take no anchor — there is no
single file to hash.

A source file is any file the project ships, **including a Markdown one**: a companion for `guide.md` is
`guide.md.md`. The double extension looks like a slip; it is the derivation working as specified.

## Who files, and when

The Guide owns the records — from its own decisions and the design reasoning the Worker returns. At planning
time: `goals.md`, `base-dependencies.md`, the substrate and architecture decisions. At build and review
time: Insights/Decisions/Discussions on the files touched, and a superseding ADR when a system decision
changed. An unfiled decision is a lost one.

## Reading

To understand a file, open its companion — all of it. For system context, read the root records. Navigate to
what bears on the work; never read the whole project. A companion flagged stale is *possibly* out of date —
re-verify against the current code first.
