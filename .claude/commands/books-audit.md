---
description: "Knowledge hygiene: dedupe, ranking, decay, manifest consistency"
allowed-tools: Read, Write
---

## Checks
1. Duplicates — TOC overlap > 80% between two books
2. Missing fields — books without version or quality_score
3. Low quality — quality_score < 0.60
4. Stale + replacement available — stale=true but a better alternative exists
5. Broken refs — prompt_versions.yaml points to files that do not exist

## Output
Per issue: SEVERITY (high / medium / low) + DESCRIPTION + RECOMMENDED_ACTION
