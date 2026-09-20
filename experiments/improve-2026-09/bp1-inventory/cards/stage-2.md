# Stage 2 — reservation expiry (TTL)

Extend `inventory.py`. Some reservations should **expire** and return their units automatically.

## API changes (backward compatible — existing calls must keep working)
```python
    def reserve(self, sku: str, qty: int, ttl_seconds: float | None = None, *, now: float = 0.0) -> str:
        """As before. If ttl_seconds is given, the reservation EXPIRES at now + ttl_seconds:
        from that instant its units are available again automatically. ttl_seconds=None never expires."""
    def available(self, sku: str, *, now: float = 0.0) -> int:
        """Units available for sku AT TIME `now`: outstanding non-expired reservations hold their units;
        a reservation whose expiry <= now no longer holds any (its units are available)."""
```
- `release` unchanged. `now` is a float clock passed in by the caller (no wall-clock inside).
- A reservation with no ttl behaves exactly as in stage 1.

## Rules (added)
- **R5** At time `now`, a reservation with `expiry <= now` holds zero units; its units are available.
- **R6** Expiry is by the injected `now`, deterministic; the module reads no real clock.
- **R7** Releasing an already-expired reservation is still a no-op; its units are not double-counted.

Existing stage-1 behavior and tests must still pass. Build it well.
