---
kind: dev
title: "The anchor must match the ontology of the claim"
created: 2026-08-12
tags: [staleness, design]
anchors:
- {path: "tools/aims_anchor.py", hash: "sha256:d93324b3d2f9b9a150582f1855cb92361b8288c6277948fe9054238cd85939b5"}
---

The dead-end was trying to make one staleness signal serve every record. Forcing a content hash onto a
structural claim ("we split core and api") fires on every unrelated edit beneath it — the noisy
whole-directory hash. The fix that unlocked the whole design: **let the anchor follow what the record
actually claims about.** Content claim → content hash; structural claim → shape fingerprint
(content-blind); a content invariant is just content anchors on the few files that carry it. Once the
anchor tracks the ontology, false positives disappear and "tier 3" collapses into "content anchors +
an optional linter for enforcement".
