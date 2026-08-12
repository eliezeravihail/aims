# `aims_anchor.py` — the write-time anchor stamper

A small, explicit, idempotent command the **method** calls when it files a record. **Not a hook** —
nothing runs it automatically. It reads the record's `code:` field (a single cohesive target) and
stamps one anchor line — `hash:` (content) or `shape:` (structure) — so a model never computes a hash
by hand. Format details are in [`../docs/format-profile.md`](../docs/format-profile.md).

```
python3 tools/aims_anchor.py <record>            # content hash (or shape for a component.md)
python3 tools/aims_anchor.py <record> --shape    # force a structure anchor
python3 tools/aims_anchor.py <record> --content  # force a content anchor
```

- Reads `code:` from the record; a record with no `code:` (pure intent) is a no-op.
- `code:` names ONE cohesive target (a file, a dir, or a `dir/**` glob). It deliberately cannot express
  a scattered subset of files — that inability is an architecture signal (see
  [`../skills/aims-guide/references/design-record.md`](../skills/aims-guide/references/design-record.md)).
- Idempotent; preserves every other frontmatter key and the body; writes only the single
  `hash:`/`shape:` line. Stdlib only.
