---
id: 4
title: "Two staleness anchors — content hash and shape fingerprint; the anchor follows the claim"
status: accepted
date: 2026-08-12
tags: [staleness, anchors]
anchors:
- {path: "docs/format-profile.md", hash: "sha256:3eb92d47d4ded4c8ee66660032c647db9c50183e98aaacad30151bf89cf9c150"}
- {path: "tools/aims_anchor.py", hash: "sha256:d93324b3d2f9b9a150582f1855cb92361b8288c6277948fe9054238cd85939b5"}
---

## Context
A record can claim about file content, about arrangement, or state a content invariant. One anchor kind
cannot serve all three honestly.

## Decision
The anchor kind follows the claim: a record about file content → `anchors:` (per-file content hash); a
record about structure → `shape:` (child-name fingerprint, content-blind). A content invariant is not a
third mechanism — it is `anchors:` on the files that embody it. Automatic enforcement (a code scanner)
is an opt-in fitness-function emitting capsa `X-` findings, never in the passive layer.

## Consequences
Shape anchors do not false-fire on ordinary edits under a component; content anchors pinpoint the file.
Detection reuses one mechanism; only enforcement is extra and optional.

## Alternatives considered
A whole-directory content hash — rejected: a false-positive storm, since most edits under a structural
boundary do not falsify the structural claim.
