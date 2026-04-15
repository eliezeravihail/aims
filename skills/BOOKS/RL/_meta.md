# BOOKS / RL

## Encoded books

| slug | title | version | quality_score | last_used | stale | duplicate_of |
|------|-------|---------|--------------|-----------|-------|-------------|
| —    | —     | —       | —            | —         | false | —           |

## Ranking policy
1. Prefer tier_1a > tier_1b > tier_2
2. Break ties by higher quality_score
3. Do not load a book with duplicate_of set — use the original
4. Do not load quality_score < 0.60
