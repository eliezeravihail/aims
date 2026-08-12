---
title: "The anchor must match the ontology of the claim — and be one cohesive target"
date: 2026-08-12
code: tools/aims_anchor.py
hash: "sha256:fd9bad9c0846166cc4bf66978337c3ded9349c9c41256ee59da07b6136fa808e"
---

Two lessons converged into the lean anchor. First: one staleness signal cannot serve every record —
forcing a content hash onto a structural claim fires on every unrelated edit; let the anchor follow
what the record claims about (content → hash, structure → shape). Second: the concerned code is named
once in `code:`; storing a path list inside the anchor duplicates it. And if a record cannot name its
code as ONE cohesive target, that is not a format gap to patch with a scattered list — it is a
cohesion smell in the code, to be fixed by a refactoring objective. The format's inability to express
scatter is the feature that surfaces it.
