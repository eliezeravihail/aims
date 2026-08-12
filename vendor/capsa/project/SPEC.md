# Capsa Specification — the project format

**Version 0.8.0** · inherits [`core/PRINCIPLES.md`](../core/PRINCIPLES.md) v0.6.0

Capsa is a file format for a project's management capsule — the durable,
portable record of what a project needs, plans, decides, discusses, fixes,
ships, and learns. This document is normative: it defines what a conforming
capsule looks like. It defines **no behavior** — Capsa has no runtime.

The key words MUST, SHOULD, and MAY are used as in RFC 2119.

This is one format in the capsa family; the shared grammar it inherits —
addresses, `links`, tombstones, the verification block — is defined once in the
core and is not restated here.

---

## 1. Principles

1. **Passive.** A capsule is data, not a program. Nothing runs. There are no
   hooks, watchers, daemons, or services in the format. Validation is
   optional, read-only, and run on demand.
2. **Readable.** Every record is UTF-8 Markdown a human can read.
   Machine-readable fields live in a YAML frontmatter header; the prose body
   is for people. One file serves both — no duplicated representation.
3. **Portable & self-contained.** A capsule is a directory inside the
   project's repository. It depends on nothing outside itself. Copy the
   project, get the capsule; delete every tool, the capsule remains whole.
4. **Single home.** Each fact lives in exactly one record. Records
   *reference* one another by id; they MUST NOT duplicate one another's
   data. Anything derivable from records (metrics, roadmaps, dashboards) is
   computed by consumers, never stored.
5. **Truth, not run-state.** A capsule records durable project truth. Live
   operational state (who is working now, cost counters, telemetry) is the
   operating tool's concern and MUST NOT be written into a capsule.
6. **Versioned by a field, not a protocol.** A capsule declares
   `capsa_version`. A consumer checks that it supports that version. That is
   the entire coordination mechanism.
7. **Verifiable by construction.** Every claim that is subject to automated
   compliance checking — a license tier, a requirement's satisfaction, an
   issue's closure evidence, a release's contents — is a structured
   frontmatter field with an evidence reference, not prose. Code can check
   compliance; prose explains it.

## 2. Location & layout

A capsule is a single hidden directory named `.capsa/` at the root of a
project repository — the accepted dot-directory convention for project
tooling (like `.git/`, `.github/`). A project MUST have at most one capsule.

```
.capsa/
├── capsule.yaml          the manifest (§3)
├── charter.md            vision, constraints, ground rules (§4.8)
├── requirements/         (§4.1)
├── plans/                (§4.2)
├── decisions/            (§4.3)
├── discussions/          (§4.4)
├── issues/               (§4.5)
├── dependencies/         <ecosystem>-<name>.md (§4.6)
├── NOTICES               generated third-party attribution (§4.6)
├── releases/             (§4.7)
├── insights/             dev/ · design/ · code/ (§4.9)
├── components/           the component tree (§2.4, §4.10)
│   └── <slug>/
│       ├── component.md  the component record
│       ├── issues/       records owned by this component
│       └── components/   nested components
├── interfaces/           contracts others depend on (§4.11)
├── milestones/           dated points plans aim at (§4.12)
└── lines/                maintained release lines (§4.13)
```

This is the list of record **types**, not a checklist. Only `capsule.yaml` is
required to exist. Every other directory appears when the project has such a
record and is absent otherwise, and **an absent directory means "none of
these yet" — never an error, and never a judgment about importance.**

That distinction is worth stating flatly, because one word was doing two jobs
and they are not related:

| | question | answered by |
|---|---|---|
| **may be absent** | must a *writer* create this directory? | no — this section |
| **may be skipped** | should a *reader* open this record? | §2.4 placement, §2.7 normative/descriptive |

A reader never decides what to read from whether the format required a
directory. It decides from **where the record sits**: what is in force at a
node is everything normative on the walk from that node to the root (§2.7),
and that is not optional in any sense — a reader that skips it is reading
wrongly. Everything else is available and is read on demand.

The same rule answers "where does this belong": a record goes where it
applies, and the root means **cross-cutting**, not "miscellaneous" and not
"unfiled" (§2.4). There is no place in a capsule for a record whose scope is
unclear, because the place *is* the scope.

A consumer MUST tolerate files it does not recognize (forward compatibility)
and SHOULD leave them untouched. The capsule contains no product code; the
repository around it holds the product.

### 2.1 Record files

Every record (all files except `capsule.yaml` and `NOTICES`) is a Markdown
file of the form:

```markdown
---
<YAML frontmatter — the machine-readable fields for this record type>
---

<Markdown body — human-readable prose: context, detail, rationale>
```

- The frontmatter MUST be valid YAML between the first two `---` fences.
- Field names and types per record type are defined in §4, and checked by
  `tools/validator/`.
- Unknown frontmatter keys are permitted and MUST be preserved by writers.
- Dates are ISO-8601 (`YYYY-MM-DD`); timestamps are RFC-3339.
- A `*_ref` / `*_refs` field holds the `id` of another record, or a path
  relative to the capsule root. Any record MAY additionally carry `links`
  (core §Links) — the general typed edge, which is what makes a link
  expressible without a change to this spec.

### 2.2 Identity & names

**A record's identity is its path** relative to the capsule root with the
`.md` suffix removed — `requirements/0001-passive-format`,
`components/render/issues/tiling-seam`. Paths are what `links[].to` and
`*_ref` fields address (core §Addresses).

Names in `requirements/`, `plans/`, `decisions/`, `discussions/`,
`issues/`, and `releases/`:

- A filename MUST be kebab-case (`[a-z0-9]+(-[a-z0-9]+)*.md`), OPTIONALLY
  prefixed with `NNNN-` where `NNNN` is a zero-padded integer. Release
  slugs SHOULD be the version (`0007-v2.3.0.md`, or `v2.3.0.md`).
- The `NNNN-` prefix carries **ordering only**. It need not be
  monotonically increasing and MAY be omitted entirely.
- `id` is OPTIONAL. Where a filename carries `NNNN-` **and** `id` is
  present, they MUST agree.

*Why numbering is no longer required:* a monotonic counter in a flat
directory assumes a single writer. Several authors on separate branches
each claiming the next number collide by construction, and the collision is
in the one field that identifies the record. Path identity needs no
allocation, so two authors adding `components/render/issues/tiling-seam`
and `components/color/issues/gamut-clip` never contend. The sibling
organization format identifies by slug for the same reason, and two record
types here already identify without a number (below).

`dependencies/` records are named `<ecosystem>-<name>.md`
(e.g. `pypi-fastapi.md`); their identity is the `(ecosystem, name)` pair,
never the filename alone. Where `name` itself contains `/` — npm's scoped
packages, `@playwright/test`, `@babel/core` — the filename replaces every
`/` with `--` (`npm-@playwright--test.md`); the `name` field stays the
real, unescaped identifier. A filename cannot hold a path separator, and
an ecosystem is free to name things however it names them; escaping only
the filename is what keeps identity accurate without asking a filesystem
to do something it can't.

`insights/**` records MAY use any kebab-case filename; their identity is
the path relative to `insights/`.

### 2.3 The verification block

Any record whose truth is checkable carries a uniform `verification`
block, so one generic checker can read compliance off every type:

```yaml
verification:
  status: verified        # verified | unverified | failed
  method: test            # test | scan | ci | manual | none
  evidence_ref: "tests/test_auth.py::test_callback"   # or a path/commit/URL
  checked_at: 2026-07-29
```

- `status: verified` without an `evidence_ref` is non-conforming — a claim
  of verification MUST point at its evidence.
- The block is REQUIRED on requirements (§4.1) and OPTIONAL elsewhere.
- Consumers MUST treat a missing block as `status: unverified`. Absence of
  evidence is a visible fact, never an implied pass.

### 2.4 The component tree

A capsule MAY describe the structure of the system itself. A **component**
is a directory containing a `component.md` (§4.10); it MAY hold its own
record directories and its own nested components, without depth limit:

```
.capsa/
├── requirements/                       cross-cutting records stay at the root
├── decisions/
└── components/
    ├── render/
    │   ├── component.md
    │   ├── issues/tiling-seam.md
    │   ├── decisions/0003-tile-cache.md
    │   └── components/
    │       └── tiling/component.md
    └── color-engine/
        └── component.md
```

- Any record type valid at the capsule root is valid inside a component
  directory, with identical fields and rules.
- A record's **owning component** is the nearest ancestor directory
  containing a `component.md`. It is DERIVED from the path and MUST NOT be
  duplicated into a frontmatter field (§1.4 — nothing derivable is stored).
- A record at the root has no owning component. That means **cross-cutting**,
  never "unassigned".
- **Where a record sits is what it applies to** (core §Placement): a record
  under `components/render/` applies to `render` and everything nested inside
  it; a record at the root applies project-wide. §2.7 says which record types
  carry an obligation down that subtree and which do not.

This is the containment axis, and it is deliberately the same shape source
code already has: a module tree, plus a graph of links across it. Two things
follow. The component is the natural partition key for every other record
type — issues, requirements and decisions per subsystem rather than in one
undifferentiated directory. And filing a record correctly is what states its
scope, so scope needs no field, no glob, and no maintenance: it is asserted
once, at creation, by the directory chosen.

Where a component owns code, `code_globs` (§4.10) anchors it to the product
repository, so "which component owns this file" is answerable mechanically.

### 2.5 Facts that are not scalar

A project that maintains several versions at once holds facts a single field
cannot state. A requirement is met in the current line and unmet in a
maintained older one; a promise holds everywhere except in one subsystem.
Rounding that to one answer loses exactly the information a maintainer needs.

A record whose status differs somewhere carries `scoped_status`, and each
entry names **where** by addressing a record:

```yaml
status: met                                  # the project-wide answer
scoped_status:
  - {scope: lines/25-x,           status: unmet}
  - {scope: components/ios,       status: unmet}
  - {scope: requirements/0012-a11y, status: unmet}
```

- `scope` is an internal address (core §Addresses) and MUST resolve to an
  existing record. That is what makes "is this a real thing" a checkable
  question rather than a free string that silently means nothing.
- The address may name **any** record — a release line, a component, a
  requirement. The format does not enumerate which dimensions a project is
  allowed to vary along, because it cannot know them: a product varies by
  version, by subsystem, by regulation, by language, by accessibility target,
  by customer tier. Any dimension that matters is already something the
  capsule holds a record for; if it is not, the exception has no documented
  referent and naming it here would only look like documentation.
- `status` takes the same values as the record's own `status` field.
- `status` stays the project-wide answer, and is what a consumer reads when it
  does not care. `scoped_status` states **only the exceptions** — enumerating
  every value would duplicate the default (§1.4).

*Why there is no `platforms/` record type.* 0.4.0 had one, and 0.6.0 removed
it. "Runs on Windows" is a **requirement** of the code, and where Windows and
iPad are genuinely different code they are already **components** — so the
type was a third name for things the format could say twice already. Worse, it
privileged one dimension of variation with no principle behind the choice:
the same argument admits `languages/`, `accessibility/`, `regulations/`,
`tiers/`, without end. Constraints on the code are part of the code's own
record, and where they apply is said by placement (§2.4) or by an address
here.

### 2.6 Quantitative targets

"Opens a 100-megapixel file in under two seconds" is checkable only if the
number is a field rather than a sentence:

```yaml
targets:
  - {metric: open_time_ms,    op: "<=", value: 2000, unit: ms}
  - {metric: locale_coverage, op: ">=", value: 0.95}
```

- `metric` is a lowercase token naming what is measured; `op` is one of
  `<=`, `>=`, `<`, `>`, `==`; `value` is a number; `unit` is optional.
- `targets` states the bar. The verification block (§2.3) states the
  measurement and points at its evidence. Keeping them separate is what lets
  a target be raised without touching the record of what was last measured.

### 2.7 Normative and descriptive records

Core §Placement requires every format to say which of its record types bind
their subtree. The test is one question:

> **If this record were removed, would work anywhere beneath it become
> permissible that is not permissible now?**
> Yes → **normative**. No → **descriptive**.

A normative record states an obligation or a constraint. A descriptive record
states something that exists, happened, or was learned.

| Type | | Why |
|---|---|---|
| `requirements/` | **normative** | states what must hold |
| `decisions/` | **normative** | a choice made *and* the constraint it imposes from then on |
| `interfaces/` | **normative** | a published contract binds whoever implements or calls it |
| `charter.md` | **normative** | the capsule-wide frame; root-only by construction |
| `components/**/component.md` | **normative** | describes the node, and its `code_globs` bound what belongs to it |
| `issues/` | descriptive | a defect that exists; fixing it is a requirement's job, not the issue's |
| `plans/` | descriptive | intent, not obligation — a plan that constrains should say so as a requirement or a decision |
| `discussions/` | descriptive | the reasoning; the outcome is a decision |
| `releases/` | descriptive | what shipped |
| `insights/` | descriptive | what was learned; it informs, it does not bind |
| `dependencies/` | descriptive | what is used; a licence obligation it creates is a decision |
| `milestones/`, `lines/` | descriptive | a dated point aimed at, and a version stream |

Three rules complete the reading.

- **Status gates the obligation.** A normative record with `status:`
  `superseded`, `rejected`, `withdrawn`, `retired`, or `removed` no longer
  binds. It stays in place — the history of what once bound this subtree is
  worth as much as the current answer — but it is not collected as an
  obligation in force.
- **`scoped_status` narrows, it does not relocate.** A normative record with
  `scoped_status` (§2.5) still applies to the same subtree; the axis says
  where within it the answer differs.
- **A record binds where it sits, not where it was written.** A decision taken
  today that constrains a component authored a year ago is filed in that
  component's `decisions/`, and is thereby in force for it — the old records
  beneath it need no edit. This is why no `applies_to`-style scope field
  exists: the one operation it would enable is already available, as filing.

The classification is deliberately coarse. A reader that wants only what
binds a node has a rule it can apply without judgment; a reader that wants
the fuller picture reads the descriptive records too, and both are looking
at the same files.

## 3. The manifest — `capsule.yaml`

REQUIRED. Declares the capsule's version and the project's identity — the
only thing an operator's registry needs to know is that the project exists
and where it lives; everything else is inside.

```yaml
capsa_version: "0.6.0"        # REQUIRED — spec version this capsule conforms to
project:
  name: "Payments Gateway"    # REQUIRED — human name
  slug: payments-gateway      # REQUIRED — kebab-case identifier
  repo: "https://github.com/acme/payments"   # OPTIONAL — product repo URL
  created: 2026-07-29         # OPTIONAL
status: active                # REQUIRED — planning|active|maintained|paused|archived
```

`status` semantics:
- `planning` — a charter exists; no work has run yet.
- `active` — at least one initiative is in progress.
- `maintained` — no active initiative, but the project is alive and accepts
  work. This replaces a terminal "done": a project is never done; only its
  individual work-items complete.
- `paused` / `archived` — an explicit, deliberate management state.

## 4. Record types

### 4.1 Requirement (`requirements/NNNN-slug.md`)

A need the project must satisfy — the formal, checkable expression of "what
this project is for". Requirements are the anchor of automated compliance:
each carries the verification block (§2.3).

| field | req | type | notes |
|---|---|---|---|
| `id` | ✓ | integer | equals `NNNN` |
| `title` | ✓ | string | |
| `level` | ✓ | enum | `must` \| `should` \| `may` |
| `status` | ✓ | enum | `proposed` \| `accepted` \| `met` \| `unmet` \| `dropped` |
| `opened` | ✓ | date | |
| `verification` | ✓ | block | §2.3; `status: met` with `verification.status != verified` is non-conforming |
| `scoped_status` | | list | per-axis exceptions to `status` (§2.5) |
| `targets` | | list | quantitative bars this requirement sets (§2.6) |
| `plan_refs` | | integer[] | plans that implement it |
| `decision_refs` | | integer[] | decisions that shaped it |

Body: the need in prose — who needs it, why, acceptance nuance.

Checkable claims (examples a checker can compute): *every `must`
requirement is `met` with verified evidence before a release*; *no
requirement is `met` without `evidence_ref`*.

### 4.2 Plan (`plans/NNNN-slug.md`)

A unit of planned work. Serious planning decomposes: a project holds plans;
a plan's body holds its work-breakdown. Plans complete; the project doesn't.

| field | req | type | notes |
|---|---|---|---|
| `id` | ✓ | integer | |
| `title` | ✓ | string | |
| `kind` | ✓ | enum | `charter` \| `initiative` \| `maintenance` |
| `status` | ✓ | enum | `draft` \| `in_progress` \| `completed` \| `abandoned` |
| `opened` | ✓ | date | |
| `completed` | | date\|null | |
| `priority` | | enum\|null | `P1` \| `P2` \| `P3` |
| `target_date` | | date\|null | roadmap signal; the roadmap itself is derived |
| `milestone` | | string\|null | DEPRECATED — link to a milestone record instead (§4.12) |
| `requirement_refs` | | integer[] | requirements this plan serves |
| `decision_refs` | | integer[] | decisions this plan enacts |

Body: goal, approach, work-breakdown (sub-tasks), verification steps, open
questions.

### 4.3 Decision (`decisions/NNNN-slug.md`)

An architecture/product decision — an ADR. Append-only: to change a
decision, write a new one that supersedes it; never rewrite history.

| field | req | type | notes |
|---|---|---|---|
| `id` | ✓ | integer | |
| `title` | ✓ | string | |
| `status` | ✓ | enum | `proposed` \| `accepted` \| `superseded` \| `deprecated` |
| `date` | ✓ | date | |
| `supersedes` | | integer\|null | |
| `superseded_by` | | integer\|null | set on the old record when replaced |
| `discussion_ref` | | integer\|null | the discussion it grew from |
| `tags` | | string[] | |

Body: context → decision → consequences → alternatives considered (the
considerations belong here and in §4.4 — nowhere else).

### 4.4 Discussion (`discussions/NNNN-slug.md`)

A substantive discussion — a design debate, a trade-off exploration — worth
keeping even before (or without) a decision. A discussion that concludes
SHOULD graduate to a Decision, linked both ways.

| field | req | type | notes |
|---|---|---|---|
| `id` | ✓ | integer | |
| `title` | ✓ | string | |
| `status` | ✓ | enum | `open` \| `resolved` \| `archived` |
| `opened` | ✓ | date | |
| `decision_ref` | | integer\|null | the decision it produced, if any |

Body: the considerations themselves — positions, trade-offs, evidence.

### 4.5 Issue (`issues/NNNN-slug.md`)

A bug, risk, or standalone task — the canonical record of a problem and its
resolution. The record is the problem; the fix is a change referenced from
it.

| field | req | type | notes |
|---|---|---|---|
| `id` | ✓ | integer | |
| `title` | ✓ | string | |
| `kind` | ✓ | enum | `bug` \| `risk` \| `task` |
| `severity` | | enum\|null | `S1`..`S4`; null until triaged |
| `status` | ✓ | enum | `new` \| `triaged` \| `in_progress` \| `awaiting_verification` \| `closed` \| `rejected` |
| `source` | | string\|null | who reported it, and in what capacity — e.g. `"Lutz Roeder, maintainer"`, `"CI, flaky-test detector"` |
| `owner` | | string\|null | one owner from triage to close |
| `opened` | ✓ | date | |
| `triaged` | | date\|null | starts the SLA clock (targets are operator policy) |
| `closed` | | date\|null | |
| `fix_commit` | | string\|null | the fix on the default line |
| `fix_commits` | | list | per-line fixes: `{line, commit}` — a backport is not one commit (§4.13) |
| `fix_plan_ref` | | integer\|null | |
| `regression_ref` | | string\|null | the permanent regression test / evidence |
| `reopens` | | integer | default 0 |
| `verification` | | block | §2.3 — closure evidence in checkable form |

Checkable claims: *no `closed` bug without `fix_commit` and
`regression_ref`*; *no open `S1`* (a release gate an operator can enforce).
A `risk` uses the same lifecycle; `closed` means mitigated-with-evidence or
consciously retired (`rejected` with rationale).

*Why `source` is prose, not a fixed vocabulary:* an earlier version closed it
to `ceo`/`system`/`agent` — categories from one specific way of running a
project. No conformance rule has ever read `source` (unlike `severity` or
`status`, which gate real checks), so the closed set bought nothing but a
forced, sometimes false, choice: a solo maintainer who found and fixed their
own bug is neither a company's CEO nor an automated system. `source` is a
documentation field, not an authority or enforcement mechanism — it exists
so a reader knows who to ask, not so a machine can gate on it.

### 4.6 Dependency (`dependencies/<ecosystem>-<name>.md`) and `NOTICES`

One record per dependency the product uses or ships — its license and the
decision that admitted it. Product truth that outlives any initiative.

| field | req | type | notes |
|---|---|---|---|
| `name` | ✓ | string | |
| `version` | ✓ | string | pinned exact version |
| `ecosystem` | ✓ | enum | `pypi` \| `npm` \| `vendored-js` \| `other` |
| `license` | | string\|null | SPDX identifier; null = unresolved (a visible fact) |
| `tier` | ✓ | enum | `allow` \| `review` \| `deny` \| `unknown` |
| `direct` | ✓ | boolean | |
| `decision_ref` | | integer\|null | the ADR admitting a `review`/`deny`-tier item |
| `hash` | | string\|null | e.g. `sha256:…` of the installed artifact |
| `added` | | date | |

The license **policy** (which tiers a company allows) is NOT part of a
capsule — it is company-wide and lives with the operator. The capsule
carries the formal **facts** (`license`, `tier`, `decision_ref`) so any
tool can compute compliance in code: *no `deny`-tier dependency without an
admitting decision*; *no `unknown` license at release*.

`NOTICES` is a generated plain-text aggregation of third-party attributions
derived from `dependencies/`. It is a derived artifact: regenerating it
MUST be lossless.

### 4.7 Release (`releases/NNNN-vX.Y.Z.md`)

What shipped. The record that answers, years later, "what went out in 2.3
and why".

| field | req | type | notes |
|---|---|---|---|
| `id` | ✓ | integer | |
| `version` | ✓ | string | semver or the project's scheme |
| `date` | ✓ | date | |
| `commit` | ✓ | string | the released commit SHA |
| `line` | | string\|null | slug of the release line this belongs to (§4.13) |
| `plan_refs` | | integer[] | initiatives included |
| `issue_refs` | | integer[] | issues fixed in this release |
| `requirement_refs` | | integer[] | requirements newly met |
| `notices_hash` | | string\|null | hash of the `NOTICES` shipped with it |
| `sbom_ref` | | string\|null | path/URL of the SBOM for this release |

Checkable claims: *every `issue_refs` entry is `closed`*; *every `must`
requirement is `met`* — computable release gates.

Body: highlights, known gaps, upgrade notes.

### 4.8 Charter (`charter.md`)

The project's upfront, serious plan: vision, constraints, ground rules,
initial decisions of record. One Markdown file. Frontmatter OPTIONAL; if
present: `{updated: <date>}`. Detailed planning belongs in plans; lasting
choices graduate to decisions.

### 4.9 Insight (`insights/{dev,design,code}/*.md`)

Durable knowledge about this project that is not a decision, plan, or
issue. Three kinds — insights are not limited to code:

- `dev` — engineering lessons: what was tried, what failed, why.
- `design` — UX, product, visual-language reasoning.
- `code` — notes anchored to specific code; these carry `code_globs`.

| field | req | type | notes |
|---|---|---|---|
| `kind` | ✓ | enum | `dev` \| `design` \| `code`; MUST match the subdirectory |
| `title` | ✓ | string | |
| `created` | ✓ | date | |
| `updated` | | date\|null | |
| `code_globs` | | string[] | REQUIRED iff `kind: code` |
| `tags` | | string[] | |

Cross-project ("company-brain") insights do NOT belong in a capsule — a
capsule holds only what is true of this project. An insight that turns out
to be organisational MOVES to the organization capsule, leaving a tombstone
(core §Tombstones); it is never copied, because that would give one fact two
homes (§1.4).

### 4.10 Component (`components/**/component.md`)

One part of the system: a module, a subsystem, a service. The record that
answers "what is the architecture now" — decisions record *changes* to it,
and `charter.md` holds the vision, but neither states the current structure.

| field | req | type | notes |
|---|---|---|---|
| `title` | ✓ | string | |
| `status` | ✓ | enum | `planned` \| `active` \| `deprecated` \| `retired` |
| `created` | ✓ | date | |
| `code_globs` | | string[] | paths in the product repo this component owns |
| `links` | | link[] | core §Links; e.g. `depends_on` another component |
| `tags` | | string[] | |

Body: purpose, boundaries, the interfaces it exposes, what it must not know.

Checkable claims: *an `active` component SHOULD declare `code_globs`* — a
warning, not an error, since a component need not be code; *sibling
components SHOULD NOT declare overlapping `code_globs`*, because overlapping
ownership makes "who owns this file" unanswerable.

### 4.11 Interface (`interfaces/<slug>.md`, or under a component)

A contract the project exposes and other people depend on — a plugin API, a
file format, a wire protocol, a public library surface.

It is its own record because its lifecycle is not the project's: it appears in
one version, is deprecated in another, and is removed in a third, and every
consumer needs all three dates. Recording that in prose, or inferring it from
decisions, is how a removal surprises somebody.

| field | req | type | notes |
|---|---|---|---|
| `title` | ✓ | string | |
| `status` | ✓ | enum | `proposed` \| `stable` \| `deprecated` \| `removed` |
| `created` | ✓ | date | |
| `since` | | string\|null | version it first shipped in |
| `deprecated_in` | | string\|null | REQUIRED when `status` is `deprecated` or `removed` |
| `removed_in` | | string\|null | REQUIRED when `status` is `removed` |
| `code_globs` | | string[] | where the contract is implemented |
| `links` | | link[] | e.g. a component `exposes` it |

Body: the contract, its compatibility promise, and the migration path when it
is deprecated.

Checkable claims: *no `deprecated` interface without `deprecated_in`*; *no
`removed` interface without `removed_in`*; *no release removes an interface
whose `removed_in` is unset*.

### 4.12 Milestone (`milestones/<slug>.md`)

A dated point several plans aim at. Until now `milestone` was a free string on
a plan, so nothing could hang a date on it, two plans could spell it
differently, and no checker could tell.

| field | req | type | notes |
|---|---|---|---|
| `title` | ✓ | string | |
| `status` | ✓ | enum | `planned` \| `active` \| `reached` \| `missed` \| `cancelled` |
| `target_date` | ✓ | date | |
| `reached` | | date\|null | REQUIRED when `status: reached` |
| `links` | | link[] | |

A plan points at one with `{rel: aims_at, to: milestones/<slug>}`. The roadmap
stays derived (§1.4): it is computed from plans, milestones and their dates,
never stored.

### 4.13 Release line (`lines/<slug>.md`)

One maintained version stream — `26-x` shipping, `25-x` receiving fixes only.
A serious product maintains several at once, and a single monotonic list of
releases cannot express that.

| field | req | type | notes |
|---|---|---|---|
| `title` | ✓ | string | |
| `status` | ✓ | enum | `active` \| `maintained` \| `eol` |
| `created` | ✓ | date | |
| `eol_date` | | date\|null | REQUIRED when `status: eol` |
| `links` | | link[] | |

Releases name their line with `line` (§4.7); issues record a per-line fix with
`fix_commits` (§4.5), because a backport is a different commit on each line
and one `fix_commit` field can only ever describe one of them.

### 4.14 Platform — **removed in 0.6.0**

`platforms/<slug>.md` existed in 0.4.0 and 0.5.0. It is gone, and the number
is retired rather than reused so that a reference to §4.14 in an older
document still lands somewhere truthful. See §2.5 for why, and for what says
the same thing instead.

## 5. Conformance

A directory is a **conforming Capsa capsule** iff:

1. `capsule.yaml` exists and satisfies §3.
2. Every present record parses as frontmatter + body (§2.1) and satisfies
   its type's fields (§4).
3. Names follow §2.2.
4. Verification claims follow §2.3 (no `verified`/`met` without evidence).
5. Writers preserve unknown files and keys (§2, §2.1) and leave the capsule
   conforming.
6. Every `links` entry has a lowercase-token `rel` and a syntactically valid
   `to` address (core §Addresses, §Links).
7. Every **internal** `links[].to` resolves to an existing record. External
   (`@…`) addresses are exempt — a capsule stays valid alone (§1.3).
8. Under `components/`, every directory that holds records or nested
   components contains a `component.md` (§2.4).
9. Every `scoped_status[].scope` is a syntactically valid internal address
   and resolves to an existing record (§2.5).
10. Every `targets[]` entry has a lowercase `metric`, an `op` in
    `<=` `>=` `<` `>` `==`, and a numeric `value` (§2.6).
11. A record whose `status` demands a companion field carries it: an
    interface `deprecated`/`removed` names `deprecated_in`/`removed_in`, a
    milestone `reached` names `reached`, a line `eol` names `eol_date`
    (§4.11-4.13).
12. A release's `line`, when set, resolves to a record in `lines/` (§4.7).
13. No `links` entry restates the tree: `to` MUST NOT address a component
    that is an ancestor of — or is — the record's own owning component
    (core §Links, §2.4).
14. A relative address (`./…`, `../…`) resolves within the capsule; one that
    would escape the capsule root is non-conforming (core §Addresses).

The reference validator (`tools/validator/`) checks 1-4, 6-9, 13 and 14
mechanically. It is optional, read-only, and stdlib-only; the spec, not the
validator, is the source of truth.

Rule 7 is the one obligation a graph kept in files carries that a database
would carry for it: there are no foreign keys, so an edge can point at a
record that was deleted or renamed and nothing objects. Checking it is what
makes the links trustworthy enough to compute a neighbourhood from.

Rule 13 is rule 7's opposite number. Rule 7 catches an edge pointing at
nothing; rule 13 catches an edge pointing at something the path already
said. Both defend the same property — that a link is worth traversing —
from the two directions it can be lost.

## 6. Versioning of this spec

`capsa_version` is `MAJOR.MINOR.PATCH`:
- PATCH — clarification; no format change.
- MINOR — additive and backward-compatible (new optional field/type).
- MAJOR — breaking. Consumers MUST refuse a capsule whose MAJOR they do not
  support.

This document defines version **0.8.0**, and inherits core v0.6.0.

Changelog:
- **0.8.0** — inherits core v0.6.0 (§Addresses: a **Web** address form for
  citing a source outside any capsule). Own fix: a dependency whose `name`
  contains `/` (npm scoped packages — `@playwright/test`, `@babel/core`)
  now has a satisfiable filename — `/` escapes to `--` in the filename
  only, never in `name` (§2.2). Found live: a capsule documenting a real
  project (`examples/netron` in this repository) had exactly one such
  dependency, and the previous rule had no answer for it at all. Additive
  on both counts — no capsule that conformed before stops conforming.
- **0.7.0** — an issue's `source` (§4.5) is no longer a closed
  `ceo|system|agent` enum; it's an OPTIONAL `string|null` — a name and a
  capacity (`"Jane Doe, maintainer"`), not a forced category. No
  conformance rule ever read `source`, so the enum bought a false choice
  and nothing else — found while documenting a real solo-maintainer
  project the three values couldn't describe honestly. Additive: a
  capsule with `source: ceo` still conforms, since the old values remain
  valid strings; nothing is now required that wasn't before.
- **0.6.1** — inherits core v0.5.0 (§Checking: the validator checks
  conformance, not truth; `X-` reserved for operator-defined finding
  codes). No change to this document's own rules or fields — PATCH.
- **0.6.0** — the `platforms/` record type is **removed** (§2.5, §4.14), and
  `scoped_status[].scope` becomes an ordinary internal address that may name
  any record instead of `line:`/`platform:` (§2.5). Breaking for a capsule
  that used platforms; migration is mechanical — a platform that constrains
  shared code becomes a requirement, a platform with its own code becomes a
  component, and each `scope: "platform:x"` becomes the address of whichever
  it became. Release lines are unaffected (`scope: lines/25-x`).
- **0.5.0** — placement determines applicability (§2.4), and the
  normative/descriptive classification core v0.4.0 requires a format to make
  (§2.7); conformance rules 13 (a link may not restate the tree) and 14
  (relative addresses stay inside the capsule). §2.7 adds no field and no
  record type — it writes down what the existing types already meant, so a
  0.4.0 capsule's records are unchanged. Rule 13 is a restriction: a capsule
  carrying an ancestor link conforms again once that link is deleted, and
  deleting it loses nothing, since the path states the same fact.
- **0.4.0** — interfaces (§4.11), milestones (§4.12), release lines (§4.13)
  and platforms (§4.14) as records; `scoped_status` for facts that vary by
  line or platform (§2.5); quantitative `targets` (§2.6); `line` on a release
  and `fix_commits` on an issue. Additive; `milestone` as a free string on a
  plan is deprecated but still legal.
- **0.3.0** — identity is the path and `NNNN-` becomes optional ordering
  (§2.2); the component tree and the component record (§2.4, §4.10);
  referential-integrity conformance rules (§5.6-8). Additive: a 0.2.0
  capsule conforms unchanged, since numbered names and `id` stay legal and
  the component tree is optional. Inherits `links`, addresses and tombstones
  from core 0.2.0.
- **0.2.0** — the capsule directory is `.capsa/` (was `capsule/` in 0.1.0);
  a 0.1.0 capsule is migrated by renaming the directory.
