# The design record — how the method's outputs become co-located records

Everything the loop produces worth having *next year* is filed as a record **in the code tree**. The
complete format is `../../../knowledge/format.md` (short, self-contained); this file maps "what I just
decided" to "which record". There are two homes, and the split is by *what the knowledge is about*.

## File-level → a companion beside the source file

Knowledge **about one source file** goes in that file's companion — the same name plus `.md`, right
next to it (`src/render.py` → `src/render.py.md`) — under three sections:

- **Insights** — what was learned about this file (tried, failed, why).
- **Decisions** — file-level choices and the rule they impose (append-only within the section).
- **Discussions** — trade-offs weighed, options considered, the road not taken.

You read the whole companion when you touch the file, because it is all about that file. Anchor it on
filing (`python3 knowledge/anchor.py <companion>`) — it hashes the same-named source file.

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

## The split, sharply

- Is the knowledge **about one file**? → its companion, in the right section.
- Is it **cross-cutting**? → the matching root record.

Do not put a file-level insight at the root, and do not scatter a system-wide decision across file
companions. If a would-be file-level insight actually concerns *several* files at once, that is usually a
system-level fact (→ `architecture.md` or an ADR) or a signal the files share a responsibility that
wants its own home (a refactoring objective) — not a note copied into many companions.

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
