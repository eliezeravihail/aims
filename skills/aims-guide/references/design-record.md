# The design record — how the method's outputs become capsa records

This is the one reference that turns the design method into durable, long-lived knowledge. Everything
the loop produces that is worth having *next year* — product intent, the substrate, the architecture,
the decisions and the lessons behind them — is filed as a **capsa** record in the product's `.capsa/`
capsule. The grammar is `docs/format-profile.md` (and the vendored spec under `vendor/capsa/`); this
file is the Guide's working map from "what I just decided" to "which record, placed where, anchored how".

## Why a capsule and not three flat files

The method's durable output used to be three flat files at the repo root (`GOALS.md`,
`ARCHITECTURE.md`, `BASE-DEPENDENCIES.md`), kept true by hand. Two problems that cost you over a
project's life:

- **They bloat.** One growing file per concern means a later session reads the whole thing to find the
  little that bears on the code in front of it.
- **They drift silently.** "Keep it true by hand" fails the moment code changes without the doc
  changing, and a formal doc that lies with authority is worse than none.

A capsa capsule fixes both: **one record per fact**, placed in a tree where **placement is scope**
(a record under `components/api/` governs `api` and everything beneath it), so a reader loads only
what is in force where it is working; and **each record is anchored** to the code it describes, so
drift is *detected* mechanically instead of trusted to discipline.

## The mapping — method output → record type → placement

| The method produces… | capsa record | placed at | anchor |
|---|---|---|---|
| primary goal, non-goals, the product frame | `charter.md` | capsule root | usually none (pure intent) |
| a use scenario / product rule as a checkable need | `requirements/NNNN-slug.md` | root, or the component it constrains | `anchors:` on the code that satisfies it, if any |
| the foundational substrate choice (language, core framework, foundational deps) | a substrate `decisions/` ADR | capsule root | none |
| a concrete foundational package | `dependencies/<eco>-<name>.md` | root | none |
| the current structure of a part: boundaries, seams, what it must not know, change axes, confined deps | `components/<slug>/component.md` | the component's own node | `--shape` on the component's source subtree |
| a structural/boundary/ownership decision + rejected alternatives | `decisions/NNNN-slug.md` (append-only) | the component it governs, or root if cross-cutting | `anchors:` on the files that carry the decision |
| a content invariant ("core stays pure") | a `decisions/` ADR **or** a `requirements/` record | the node it governs | `anchors:` on the files that embody it |
| an engineering lesson: what was tried, what failed, why | `insights/dev/*.md` | at or above the relevant node | `anchors:` if tied to specific code |
| a note anchored to specific code | `insights/code/*.md` (carries `code_globs`) | the relevant node | `anchors:` on those files |

Nothing here declares its own scope — **the path is the scope.** Do not add an `applies_to` field; file
the record under the node it governs and the walk finds it.

## Who files, and when

- **The Guide owns the capsule.** You file the durable records — from your own decisions and from the
  design reasoning the Worker returns (the handoff asks for that reasoning precisely so it can be
  filed, not lost in chat). An `insights/dev` lesson that surfaced during the Worker's build is filed
  by you from the Worker's return.
- **When:** at planning time, file the `charter`/`requirements`/substrate/`decisions` the design
  commits to. At review time, file the structural `decisions` and `insights` the round produced, and
  append a *superseding* ADR when a decision changed. Do not batch it "for later" — an unfiled decision
  is a lost one.

## Two rules that keep the capsule trustworthy

1. **`decisions/` are append-only.** To change a decision, write a new ADR whose `supersedes:` names
   the old one, and set the old one's `superseded_by:` / `status: superseded`. Never rewrite a decided
   record — the history of what once bound this code is worth as much as the current answer.
2. **Anchor on filing — never by hand.** The moment you file a record, stamp its anchor with the
   explicit command (below). You never compute a hash yourself.

## Anchoring — the command, and which kind

The anchor kind **follows what the record claims about** (`docs/format-profile.md` §2):

```
tools/aims_anchor.py <record> <path>...        # anchors: — one content hash per file
tools/aims_anchor.py --shape <record> <root>   # shape: — child-name fingerprint of a subtree
```

- A record about **file content** (a decision carried by specific files, a code insight, a requirement
  a module satisfies) → `anchors:` on those files.
- A record about **structure/arrangement** (a `component.md`: "these are the parts, this is the
  boundary") → `--shape` on the component's source subtree. Content-blind by design: a reorg trips it,
  an ordinary edit inside does not.
- A pure-intent record (`charter`, a substrate ADR) → no anchor.

A read-time hook later re-hashes each anchor and, if the code drifted, injects an advisory *"re-verify"*
when a later session reads the record. It never blocks and never edits. That advisory — surfaced
exactly when someone is about to rely on the record — is what replaces "keep it true by hand".

## Reading the capsule — the surfacing rule

When you (or a later, fresh session) start work at a node in the product, read, by placement:

1. **every normative record in force on the walk to the capsule root** — the `requirements/`,
   `decisions/`, and `component.md` records at each level whose `status` still binds — this is
   mandatory, it is what tells you the rules you must not break;
2. **the insights on that same walk** — for context, not obligation;
3. everything else on demand.

This is the whole point of the long-term layer: a continuation session does **not** start from scratch
and re-derive the design — it reads the records already in force, builds on them, and files its own new
conclusions the same way. If a record is flagged stale by the read hook, re-verify it against the
current code before relying on it (a flag is *possible* staleness, not proof it is wrong).

## Bootstrapping a capsule

If `.capsa/` does not exist yet, create it on the first filing: `core/capsule.yaml` (the manifest —
`capsa_version`, project name/slug), then the record directories as records appear. An absent directory
means "none of these yet", never an error. Templates for each record type are in `../assets/`.
