# The design record — how the method's outputs become capsa records

Everything the loop produces that is worth having *next year* — product intent, the substrate, the
architecture, the decisions and lessons behind them — is filed as a capsa record in the product's
`.capsa/` capsule. The complete format is `docs/format-profile.md` (short and self-contained); this
file is the Guide's working map from "what I just decided" to "which record, placed where, anchored".

## Why a capsule and not three flat files

Balash kept durable design in three flat files kept true by hand. They **bloat** (a later session reads
the whole thing to find the little that bears on the code in front of it) and **drift silently** ("keep
it true by hand" fails the moment code changes without the doc). A capsa capsule fixes both: **one
record per fact**, placed where **placement is scope** (a reader loads only what is in force where it
works), and **each record anchored** to the code it concerns so drift is *detected*, not trusted.

## The mapping — method output → record → placement

| The method produces… | capsa record | placed at | `code:` anchor |
|---|---|---|---|
| primary goal, non-goals, the product frame | `charter.md` | root | none (pure intent) |
| a use scenario / product rule as a checkable need | `requirements/NNNN-slug.md` | root, or the component it constrains | `code:` on the code that satisfies it, if any |
| the foundational substrate choice | a substrate `decisions/` ADR | root | none |
| the current structure of a part: boundaries, seams, what it must not know | `components/<slug>/component.md` | the component's node | `code: <its dir>` → **shape** anchor |
| a structural/boundary/ownership decision + rejected alternatives | `decisions/NNNN-slug.md` (append-only) | the component it governs, or root | `code:` on the file(s) it governs → content |
| a content invariant ("core stays pure") | a `decisions/` or `requirements/` record | the node it governs | `code: <that dir>/**` → content |
| an engineering lesson: what was tried, what failed, why | `insights/dev/*.md` | at/above the relevant node | `code:` if tied to specific code |
| a note anchored to specific code | `insights/code/*.md` | the relevant node | `code:` on those files |

Nothing declares its own scope — **the path is the scope.** File the record under the node it governs.

## The record is lean — write two fields + prose

Required frontmatter is `title` + `date`; the folder gives the kind; the body carries the rationale.
Add a `code:` line when the record concerns specific code, then anchor it. Everything else capsa offers
is optional — reach for it only when it earns its place. See `docs/format-profile.md` for the shape.

## `code:` is one cohesive target — and if it can't be, fix the architecture

A record names its code in a single `code:` field: one file, one directory, or one `dir/**` glob. This
is not just brevity — it is a **design check the method must act on.**

> **If you cannot name a record's code as one cohesive target — if the concern is scattered across an
> arbitrary subset of files in a directory (A, C, F but not B, D, E) — stop. Do not list the scattered
> paths. That inability is telling you the architecture is wrong:** the concern has no single home
> (shotgun surgery), or the directory is over-generic and mixes unrelated responsibilities.

When this happens, the right move is a **design objective on the code**, not a workaround in the record:
give the concern its own module/directory so it *can* be named as one unit (this is the
single-owner / cohesion / SRP work in `design-principles.md`). File the record only once the concern is
cohesive — then its `code:` is a single target and its anchor is one hash. The lean format is
deliberately unable to express a scattered anchor, so that poor cohesion surfaces as a task instead of
being quietly absorbed. Treat a record that *wants* to point at scattered files as a discovered
refactoring objective.

## Who files, and when

The Guide owns the capsule. You file the durable records — from your own decisions and from the design
reasoning the Worker returns. At planning time file the charter/requirements/substrate/decisions the
design commits to; at review time file the structural decisions and insights the round produced, and
append a *superseding* ADR when a decision changed. Don't batch it "for later" — an unfiled decision is
a lost one.

## Two rules that keep the capsule trustworthy

1. **`decisions/` are append-only.** To change one, write a new ADR naming the one it supersedes; never
   rewrite a decided record.
2. **Anchor on filing, never by hand.** Run `python3 tools/aims_anchor.py <record>` — it reads the
   record's `code:`, computes the right anchor (content, or shape for a `component.md`), and stamps the
   single `hash:`/`shape:` line. A read-time hook later re-hashes it and advises *"re-verify"* if the
   code drifted — it never blocks.

## Reading the capsule — the surfacing rule

Starting work at a node, read by placement: every normative record on the walk to the capsule root
(requirements, decisions, `component.md`) plus in-scope insights — not the whole capsule. This is the
whole point of the long-term layer: a continuation session does **not** start from scratch and
re-derive — it reads the records in force, builds on them, and files its own new conclusions the same
way. A stale-flagged record is *possibly* out of date; re-verify against the current code before
relying on it.

## Bootstrapping

If `.capsa/` does not exist, create `core/capsule.yaml` (the manifest — `capsa_version`, project
name/slug) on the first filing; add record directories as records appear. Templates for each record
type are in `../assets/capsa-record-templates.md`.
