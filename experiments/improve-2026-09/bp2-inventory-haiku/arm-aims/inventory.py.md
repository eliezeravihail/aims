---
hash: "sha256:3c3f7ae342e8b564d3e31d3932af08ded49522a5825146e7c98776bfdf51484e"
---

# inventory.py — Design Insights & Decisions

**Date:** 2026-09-20 (updated 2026-09-20)

## Insights

### The availability invariant has one owner: Inventory (extended for TTL)

The core rule "available never goes negative and never exceeds added minus reserved (non-expired)" is enforced at construction by the Inventory class. No external code can compute or manage availability; it is always derived from the three canonical sources:

1. `_stock_added[sku]`: cumulative total added for a SKU
2. `_reservations`: the active reservation ledger with expiry times
3. `now`: the current time parameter (injected, not read from system clock)

Available is computed on-demand: `total_added(sku) - sum(reserved qty for sku where expiry is None or expiry > now)`. Since it is never stored, it always reflects current state. Time is injected; the module reads no real clock.

### Atomicity of reserve: precondition check before mutation

The `reserve()` method checks `qty <= available(sku, now=now)` **before** creating the reservation entry. If the check fails, `InsufficientStock` is raised and state is unchanged. This ensures R4 is satisfied: "raise InsufficientStock if qty > available; change nothing." The check respects the current `now` parameter, so expired reservations are not counted as obstacles to a new reservation.

### TTL: Reservations stored with expiry, no cleanup daemon

Reservations store three values: `(sku, qty, expiry)` where `expiry` is `None` (never expires) or a float timestamp. At availability computation time, only non-expired reservations count. An expired reservation with `expiry <= now` holds zero units. No garbage collection daemon runs; expired entries remain in the store until explicitly released. This eliminates the need for background maintenance and keeps the design simple (all state changes are synchronous and explicit).

### Idempotency of release (including expired reservations)

The `release()` method uses `dict.pop(..., None)` to remove a reservation. If the ID is unknown, already released, or expired, the operation is a silent no-op, which is idempotent behavior per spec. This prevents double-counting of units when releasing an expired reservation: since expired reservations don't count in `available()`, removing them from the store changes nothing (R7).

### Opaque, unique reservation IDs

Reservation IDs are generated as UUID strings. They are:
- **Opaque:** Not reconstructible from external data (SKU, qty, time, etc.)
- **Unique:** Each call to `reserve()` generates a fresh UUID
- **Contextless:** The ID carries no information; it is pure identity

### Edge cases covered by design

1. **Unknown SKU in available():** Returns 0 (no stock added, so none available)
2. **Unknown SKU in reserve():** If qty > 0, available(sku, now=now) = 0, so `InsufficientStock` is raised
3. **Negative or zero quantity in add_stock() or reserve():** `ValueError` is raised (precondition guard)
4. **Releasing unknown ID:** Silent no-op (idempotent)
5. **Releasing expired ID:** Silent no-op; units were already returned when expiry <= now
6. **Multiple reservations of same SKU:** Each holds its own qty and expiry; available = total_added - sum(non-expired)
7. **Expiry boundary (expiry <= now):** At exact expiry time, the reservation is considered expired and does not count
8. **ttl_seconds with now parameter:** expiry = now + ttl_seconds; both injected, never read from system clock

## Decisions

### TTL is injected time, not system clock

Reservations accept optional `ttl_seconds` (time-to-live in seconds) and expire at `now + ttl_seconds`. Both `reserve()` and `available()` accept an injected `now` parameter (default 0.0). The module reads no system clock. This allows:
- Deterministic testing (no flaky time-dependent tests)
- Backwards compatibility (existing calls with no `now`/`ttl_seconds` work as before)
- Simulation and replay (callers control time progression)

The expiry condition is `expiry <= now` (not `<`), so at the exact expiry instant the reservation is expired.

### Single class, no abstractions

The design introduces no separate classes for Reservation, ReservationStore, or StockLedger. The Inventory class is sufficient: it owns the invariant and exposes exactly the four operations the spec requires. Adding abstractions would introduce indirection without a corresponding product force (no plan to vary reservation storage, no need to swap ledger implementations).

### In-memory only (stage 1)

The design assumes single-threaded, in-memory use. No persistence or concurrency safety is implemented. This aligns with stage 1 scope ("no persistence required").

### ValueError for non-positive quantities

Both `add_stock()` and `reserve()` raise `ValueError` if qty ≤ 0. This is a precondition guard at the boundary. The spec itself does not explicitly forbid these calls, but a quantity must be positive to have semantic meaning.

## Discussions

### Why not store available directly?

Storing available as a separate field would require keeping it in sync with `_stock_added` and `_reservations` on every mutation. The rule would be split across three operations (add_stock, reserve, release), creating a second owner. Computing available on-demand is cheaper in code complexity and eliminates drift. With TTL, the time-dependent nature of availability makes cached values even less viable.

### Why UUID instead of sequential IDs?

Sequential IDs could be reconstructed or guessed. UUID is opaque: callers cannot construct a valid ID from external data. This satisfies R3 ("ids unique/opaque").

### Why store expired reservations instead of deleting them?

Deleting expired reservations would require either a garbage-collection background task or a cleanup call in `available()`. Keeping them in the store:
- Eliminates the need for background machinery (no daemon, no maintenance loop)
- Keeps all state changes synchronous and explicit
- Preserves idempotency of `release()` on expired reservations (releasing an expired entry is a silent no-op)
- Simplifies the design: `available()` is a pure function of current state and injected time

The storage cost is negligible for a single-module in-memory service.
