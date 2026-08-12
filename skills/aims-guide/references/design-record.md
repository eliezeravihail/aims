# The design record — how the method's outputs become co-located records

Everything the loop produces that is worth having *next year* — product intent, the substrate, the
architecture, the decisions and lessons behind them — is filed as a record **in the code tree, next to
the code it describes.** The complete format is `../../../knowledge/format.md` (short, self-contained);
this file is the Guide's working map from "what I just decided" to "which record, placed where".

## The idea — the structure carries both the code and the knowledge

Design knowledge does not live in a separate folder or a `.capsa/` tree that mirrors the code. It lives
**in** the code tree: a component's record is a `component.md` inside that component's directory, its
`decisions/` and `insights/` beside it; cross-cutting records live at the repo root. The one directory
structure is *both* the code graph and the knowledge tree — understanding and navigation come from the
structure itself, and moving a directory moves its knowledge with it. There is no parallel tree to sync.

## The mapping — method output → where it is filed

| The method produces… | record | placed |
|---|---|---|
| primary goal, non-goals, the product frame | `charter.md` | repo root |
| a use scenario / product rule as a checkable need | a `decisions/` or a `requirements/` record | root if cross-cutting, else in the component it constrains |
| the foundational substrate choice | a substrate `decisions/` record | repo root |
| the current structure of a part: boundaries, seams, what it must not know | `component.md` | **inside that part's directory** |
| a structural/boundary/ownership decision + rejected alternatives | `decisions/NNNN-slug.md` (append-only) | the component's directory, or root if cross-cutting |
| a project-wide norm ("all types are PascalCase") | a `decisions/` record | repo root (no anchor) |
| an engineering lesson: what was tried, what failed, why | `insights/{dev,design,code}/*.md` | in the relevant component's directory (or root) |

**Location is scope.** File a record where the code it governs lives; a reader walks from where it works
up to the root, reading the records at each level.

## The record is lean — two fields + prose, no `code:`

`title` + `date` + a body carrying the rationale. The **kind comes from the location**; there is **no
`code:` field** — the record's own directory is its subject. See `../../../knowledge/format.md`.

## A component is a directory — and if a concern can't get one, fix the architecture

Because a record lives *in* a directory, a design component **is** a directory of code.

> **If a concern cannot be given its own directory — if it is scattered across an arbitrary subset of
> files — do not scatter records to chase it.** That inability is an architecture smell: the concern
> lacks a single home (shotgun surgery), or a directory is over-generic. The fix is a **design
> objective on the code** — give the concern its own directory (single-owner / cohesion / SRP,
> `design-principles.md`) — after which it has a natural home for its record. Treat a concern that wants
> to scatter as a discovered refactoring objective.

**The exception — a genuine project-wide norm.** A convention that applies to *all* code uniformly
("PascalCase types", a house style) is not the smell: it is a root record (no anchor), like the charter.
Distinguish by one question — one responsibility that leaked across files (→ refactor), or a uniform
norm that by nature applies everywhere (→ root). Enforcing a norm is an opt-in linter, never a record.

## Anchor on filing — the target is the record's location, never by hand

The moment you file a record, stamp its anchor: `python3 knowledge/anchor.py <record>`. The tool derives
the target from where the record sits — a `component.md` gets a `shape:` of its directory; a
decision/insight gets a `hash:` of its component's code; a cross-cutting root record gets none — and
writes the single `hash:`/`shape:` line (design records are excluded, so editing knowledge never trips
its own anchor). A read-time hook later re-derives and, on drift, advises *"re-verify"* — never blocks.

## `decisions/` are append-only

To change a decision, add a new one that supersedes it (name the superseded one in the body, mark the
old one superseded); never rewrite a decided record.

## Who files, and when

The Guide owns the records — from its own decisions and the design reasoning the Worker returns. At
planning time file the charter/substrate/decisions the design commits to; at review time file the
structural decisions and insights the round produced, and add a *superseding* decision when one changed.
An unfiled decision is a lost one.

## Reading — walk from where you work

Starting work in a directory, read the record in force there (its `component.md` and local
`decisions/`/`insights/`) and walk up to the root (`charter.md`, root `decisions/`) — not the whole
tree. This is the point of the long-term layer: a continuation session reads the records in force and
builds on them instead of re-deriving, and files its own new conclusions the same way. A stale-flagged
record is *possibly* out of date; re-verify against the current code before relying on it.
