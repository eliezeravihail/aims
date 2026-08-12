# aims format profile — the capsa subset aims uses, and the two fields it adds

aims stores durable design knowledge as a **capsa** capsule (`.capsa/` at the project root). The
grammar is defined by the vendored spec — [`../vendor/capsa/core/PRINCIPLES.md`](../vendor/capsa/core/PRINCIPLES.md)
and [`../vendor/capsa/project/SPEC.md`](../vendor/capsa/project/SPEC.md), pinned at project format
`0.8.0` / core `0.6.0`. This profile states only **which part of capsa aims uses** and **the two
consumer-side fields aims layers on top**. Where this profile and the spec ever disagree about the
grammar, the spec wins; this profile only narrows and extends within what the spec permits.

## 1. The subset aims uses

aims writes a small number of capsa record types — the ones that hold *design knowledge*:

| capsa type | aims uses it for | normative? (capsa §2.7) |
|---|---|---|
| `decisions/` (ADRs) | ownership/boundary decisions the design surfaces; append-only | normative |
| `requirements/` | what the product must hold, in checkable form | normative |
| `insights/dev/` | engineering lessons: what was tried, what failed, why | descriptive |
| `insights/design/` | product/UX/structure reasoning | descriptive |
| `insights/code/` | notes anchored to specific code (`code_globs` REQUIRED per capsa §4.9) | descriptive |
| `components/**/component.md` | the structural tree; a subtree = a component (carries scope) | normative |

The rest of capsa's types (`plans/`, `discussions/`, `issues/`, `dependencies/`, `releases/`,
`interfaces/`, `milestones/`, `lines/`, `charter.md`) are **valid but not written by the method** in
this skeleton. A project may use them; aims does not require them. An absent directory means "none of
these yet" (capsa §2), never an error.

**Placement carries scope.** A record under `components/render/` applies to `render` and everything
beneath; a record at the root is cross-cutting. Relevance is the walk from the working node to the
root (capsa §2.4, §2.7). No record declares its own scope. This is what replaces both a
central-folder store (bloats) and source-file-coupled notes (fragile).

## 2. The two fields aims adds

capsa permits unknown frontmatter keys and requires writers to preserve them (core §Grammar). aims
uses that to carry a **staleness anchor**. The anchor's *kind follows the ontology of the record's
claim* — this is the one rule that makes the whole thing honest.

### 2.1 `anchors:` — for a record that claims about **file content**

A list of the specific files the record is about, each with a whole-file content hash taken **at
write time**:

```yaml
anchors:
  - {path: src/tiling/cache.py, hash: "sha256:3af9c1…"}
  - {path: src/tiling/evict.py, hash: "sha256:91b0de…"}
```

- `path` is repo-relative (to the product root, not the capsule). `hash` is `sha256:` of the file's
  bytes at the moment the record was filed.
- The list is 0..n. Empty is legal — a pure-rationale ADR anchored to nothing concrete.
- Whole-file only. Line ranges are **not** used: line numbers drift as a file grows and would produce
  false staleness. If a file is too noisy to anchor whole, that is a signal to anchor a smaller,
  more specific file — not to track lines.
- For `insights/code/`, `anchors[].path` values SHOULD fall within the record's capsa `code_globs`.

### 2.2 `shape:` — for a record that claims about **arrangement / structure**

A structural claim ("we deliberately split `core/` and `api/`") has no file to hash. Its anchor is
its **placement** plus a fingerprint of the *shape* of its subtree — the set of child names, not
their contents:

```yaml
shape:
  root: src/            # the product-repo subtree this record describes
  children_hash: "sha256:be21…"   # hash of the sorted child-name set under root
```

- `children_hash` is over the **names** of the immediate children (and MAY, by a declared depth, the
  names beneath) — never file contents.
- This is deliberately **content-blind**. Editing a file's internals under a structural record does
  not make the structural claim false, so a content signal there would be a false-positive storm
  (exactly the whole-directory hash this design rejected). A structural claim is threatened only by a
  structural change — a move, rename, or merge — and `children_hash` catches precisely that.

### 2.3 Content invariants are not a third mechanism — they are `anchors:` on the files that embody them

A record may state a **content invariant** — "nothing under `core/` does I/O". This needs no new
mechanism. It is a record that **claims about file content**, so it takes a §2.1 `anchors:` list on
the specific files that carry the rule (e.g. `core/cache.py`, `core/model.py`). When one of them
changes, the read-time hook re-hashes it and advises *"this file changed since the record was
written — re-verify"*; a reader opens the "core stays pure" rule and checks the change against it.
Detection comes from the hash we already have.

The one thing `anchors:` does **not** do is decide *automatically* whether the change actually broke
the rule (still-pure vs. now-impure) — that verdict needs code re-analysis. Automatic **enforcement**
is therefore the only optional extra: a separate **opt-in** fitness-function that scans the code and
emits findings in capsa's shape with an `X-` operator code (core §Checking), composing with the
reference validator without polluting the format. aims does not build it; the passive layer gives
*detection*, and enforcement is a door left open, not a tier of its own.

**One caveat, stated honestly.** If an invariant spans a *whole* subtree and you anchor it to every
file, the record fires on every content change beneath it — which is the noisy whole-directory hash
this design rejected (§2.2). So anchor a broad invariant to the few files that genuinely embody it,
or accept it is detection-only, or wait until it earns the opt-in scanner. A narrow invariant (a
handful of files) is served cleanly by `anchors:` as-is.

## 3. What to read, and when — the surfacing rule

Relevance is **derived from placement**, not chosen by judgment. When work begins at a node (a file
or component in the product), the reader loads exactly:

1. **Every normative record in force on the walk** from that node to the capsule root — the
   `decisions/`, `requirements/`, and `component.md` records at each level whose `status` still binds
   (capsa §2.7). This is not optional; skipping it is reading wrongly.
2. **Insights on that same walk** — `insights/**` records placed at or above the node. Insights are
   descriptive (they inform, they do not bind), so they are read for context, not obligation, but the
   *walk* is still what selects them: an insight filed under `components/render/` surfaces for work in
   `render`, and stays invisible elsewhere. Placement does the filtering; there is no "read the whole
   insights folder" step, which is the bloat this design exists to avoid.
3. Anything else — records under sibling subtrees, deeper detail — **on demand only**.

**Surfacing runs the staleness check on what it loads.** Each record surfaced in steps 1–2 has its
anchor recomputed (§4); the session opens with, e.g., *"2 of 7 in-scope records are possibly stale —
re-verify before relying on them."* This is the same read-time check below, applied to the records
already being loaded — no scheduler, no background scan, no new mechanism.

## 4. Writing and checking

- **Writing** is done by the method (see the skill), and the anchor is stamped by
  [`../tools/aims-anchor`](../tools/aims-anchor.md) at file time — never by hand, never by a hook.
- **Reading** triggers the one active check: [`../hooks/staleness-read`](../hooks/staleness-read.md)
  recomputes the anchor for the record's kind (`anchors:` → re-hash each file; `shape:` → re-hash the
  child-name set) and, on mismatch, injects an advisory "re-verify" note. It never blocks.
- **Conformance** to the grammar itself is capsa's own concern; `anchors:`/`shape:` are unknown keys
  to the reference validator, which preserves and ignores them — so an aims capsule is a conforming
  capsa capsule, readable by any capsa tool.
