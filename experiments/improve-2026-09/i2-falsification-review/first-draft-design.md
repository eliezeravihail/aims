# First-draft design (given IDENTICALLY to both review arms) — request rate limiter

This is a returned first-pass design to be reviewed. Do not rewrite it from scratch; **review it** per the
method and return findings.

## Requirement (the design was built to this)
- **R1** A client may make at most **N requests per 60-second window**. Beyond that, requests are rejected.
- **R2** Each client is limited independently.
- **R3** `allow(client, now) -> bool` is the only operation; `now` is a Unix timestamp in seconds (float).
- **R4** The limit N and the window length may later be re-tabled (config).
- **X1** Later, limits may be **per-endpoint** as well as per-client.
- **X2** Later, a **burst allowance** (a short grace above N) may be added.

## The design (as returned)

Types:
```
class Counter:
    window_start: int     # the integer minute index this counter is for: floor(now / 60)
    count: int            # requests seen so far in this minute

class RateLimiter:
    limit: int                       # N
    counters: dict[ClientId, Counter]
```

Operation:
```
allow(client, now):
    minute = int(now // 60)
    c = counters.get(client)
    if c is None or c.window_start != minute:
        c = Counter(window_start=minute, count=0)   # new minute → fresh counter
        counters[client] = c
    if c.count < limit:
        c.count += 1
        return True
    return False
```

Contracts claimed by the design:
- "Each client gets a fresh count every minute, so no client exceeds N per minute." (R1, R2)
- "limit is a field, so re-tabling N is a config change." (R4)
- "per-endpoint (X1) is a wider key: `dict[(ClientId, Endpoint), Counter]`."
- "burst (X2) is `limit + burst` in the comparison."

## Acceptance the design passes
- C1 N=3: three `allow` in the same minute → True, True, True; the fourth → False. ✓
- C2 two different clients each get their own N. ✓

Review this design and return your findings.
