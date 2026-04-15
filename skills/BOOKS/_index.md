# BOOKS — Loading Guide

## Loading protocol
1. Receive required category and topic
2. Read `skills/BOOKS/<category>/_meta.md`
3. Select the book with the highest quality_score that is not stale
4. Load only the exact topic file needed
5. Cite in your answer: which book was used + its quality_score

## Book selection rules
| Condition | Action |
|-----------|--------|
| quality_score >= 0.80, stale=false | Use |
| quality_score 0.60–0.79 | Use with caveat |
| quality_score < 0.60 | Do not use — report |
| stale = true | Do not use — suggest books-update |
| duplicate_of != null | Use the original book instead |
