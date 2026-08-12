# capsa — now developed here

This directory contains **capsa**, the durable knowledge format aims writes against. Going
forward, **capsa is developed here**: this copy is its living home, edited and versioned in this
repository. The original standalone repository is retired; the link below is historical
attribution, not an upstream to sync from.

- **Origin (historical):** https://github.com/eliezeravihail/capsa — where capsa began; no longer
  the source of truth.
- **Current version:** `0.8.0` (project format) inheriting core `0.6.0`. Bump these here when the
  grammar changes.
- **License:** MIT (see `LICENSE` in this directory) — © 2026 eliezeravihail
- **Files:**
  - `core/PRINCIPLES.md` — the shared grammar (placement, addresses, links, tombstones,
    verification, manifest, versioning)
  - `project/SPEC.md` — the project format (record types: requirements, plans, decisions,
    discussions, issues, dependencies, releases, charter, insights, components, interfaces,
    milestones, lines)

capsa is a **passive file format** — data, not a program. Nothing in this directory runs. Editing
the grammar here is a deliberate, reviewable act (it changes what every aims capsule means), so
grammar changes go through the same review as any design decision and bump the version above.

## What aims uses, and what aims adds

aims does **not** use all of capsa, and it **relaxes** the spec's per-type required-field sets to a
lean minimal core: a record is `title` + `date` + a body, the kind comes from its folder, and every
other field is optional. A record concerning code declares it once in `code:` and carries a single
tool-stamped anchor (`hash:` or `shape:`). This lean profile — authoritative for aims records — is
defined in [`../../docs/format-profile.md`](../../docs/format-profile.md). The spec here is the
underlying grammar and lineage; where the profile is leaner, the profile wins for aims, and an aims
capsule stays a readable capsa capsule.

To change the grammar, edit these files here and bump the version above — this is where
capsa lives now. Keep the invariant that makes that safe: an aims capsule stays a
**conforming capsa capsule**, so the format remains readable by any capsa tool and the
`anchors:`/`shape:` fields stay ordinary unknown keys, never grammar the validator must know.
