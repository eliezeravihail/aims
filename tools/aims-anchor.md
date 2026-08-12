# `aims anchor` — the write-time anchor stamper

A small, explicit, idempotent command the **method** calls at the moment it files a record. It is
**not** a hook — nothing runs it automatically. Its whole job is to compute a hash reliably (which a
model cannot do by hand) and write it into the record's frontmatter, as an `anchors:` list
(file-content claim) or a `shape:` block (structural claim). See
[`../docs/format-profile.md`](../docs/format-profile.md) §2.

## Usage

```
aims anchor <record> <path>...            # stamp anchors: — one content hash per file
aims anchor --shape <record> <root>       # stamp shape: — child-name fingerprint of a subtree
aims anchor --shape --depth N <record> <root>
```

- `<record>` — a capsa record identity (path under `.capsa/`, `.md` optional), e.g.
  `components/render/decisions/0003-tile-cache`.
- `<path>` — repo-relative product-source paths the record is about (for `anchors:`).
- `<root>` — the repo-relative subtree a structural record describes (for `shape:`).
- `--depth N` — how many directory levels of child **names** feed the shape fingerprint (default 1).

## Contract

- **Idempotent.** Re-running with the same inputs and unchanged sources rewrites identical frontmatter
  (stable key order, sorted lists) — no spurious diffs.
- **Preserves everything else.** Unknown keys, body, and formatting outside the touched block are left
  intact (capsa: writers preserve unknown keys).
- **Content hash** is `sha256:` over file bytes. **Shape hash** is `sha256:` over the sorted set of
  child *names* under `<root>` to `--depth`, never file contents.
- **Fails loudly** if a `<path>`/`<root>` does not exist, if `<record>` is not a readable capsa
  record, or if the record already carries the *other* anchor kind (a record is content-anchored or
  structure-anchored, not both — the kind follows the single claim it makes).
- **Never blocks anything else** and has no side effects beyond the one record file.

Stdlib-only, read-only except for the single record file — mirroring capsa's own tooling posture.
Reference stub: [`aims_anchor.py`](aims_anchor.py).
