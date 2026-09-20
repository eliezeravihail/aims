---
hash: "sha256:b0724e7f34a0df9c3975ea78a23c1e51fc0f5ab6bf2bafa6e305989f397f6ada"
---

# inventory.py — Design Insights & Decisions

**Date:** 2026-09-20

## Insights

### The availability invariant has one owner: Inventory

The core rule "available never goes negative and never exceeds added minus reserved" is enforced at construction by the Inventory class. No external code can compute or manage availability; it is always derived from the two canonical sources:

1. `_stock_added[sku]`: cumulative total added for a SKU
2. `_reservations`: the active reservation ledger

Available is computed on-demand: `total_added(sku) - sum(reserved qty for sku)`. Since it is never stored, it always reflects current state.

### Atomicity of reserve: precondition check before mutation

The `reserve()` method checks `qty <= available(sku)` **before** creating the reservation entry. If the check fails, `InsufficientStock` is raised and state is unchanged. This ensures R4 is satisfied: "raise InsufficientStock if qty > available; change nothing."

### Idempotency of release

The `release()` method uses `dict.pop(..., None)` to remove a reservation. If the ID is unknown or already released, the operation is a silent no-op, which is idempotent behavior per spec.

### Opaque, unique reservation IDs

Reservation IDs are generated as UUID strings. They are:
- **Opaque:** Not reconstructible from external data (SKU, qty, time, etc.)
- **Unique:** Each call to `reserve()` generates a fresh UUID
- **Contextless:** The ID carries no information; it is pure identity

### Edge cases covered by design

1. **Unknown SKU in available():** Returns 0 (no stock added, so none available)
2. **Unknown SKU in reserve():** If qty > 0, available(sku) = 0, so `InsufficientStock` is raised
3. **Negative or zero quantity in add_stock() or reserve():** `ValueError` is raised (precondition guard)
4. **Releasing unknown ID:** Silent no-op (idempotent)
5. **Multiple reservations of same SKU:** Each holds its own qty; available = total_added - sum(all)

## Decisions

### Single class, no abstractions

The design introduces no separate classes for Reservation, ReservationStore, or StockLedger. The Inventory class is sufficient: it owns the invariant and exposes exactly the four operations the spec requires. Adding abstractions would introduce indirection without a corresponding product force (no plan to vary reservation storage, no need to swap ledger implementations).

### In-memory only (stage 1)

The design assumes single-threaded, in-memory use. No persistence or concurrency safety is implemented. This aligns with stage 1 scope ("no persistence required").

### ValueError for non-positive quantities

Both `add_stock()` and `reserve()` raise `ValueError` if qty ≤ 0. This is a precondition guard at the boundary. The spec itself does not explicitly forbid these calls, but a quantity must be positive to have semantic meaning.

## Discussions

### Why not store available directly?

Storing available as a separate field would require keeping it in sync with `_stock_added` and `_reservations` on every mutation. The rule would be split across three operations (add_stock, reserve, release), creating a second owner. Computing available on-demand is cheaper in code complexity and eliminates drift.

### Why UUID instead of sequential IDs?

Sequential IDs could be reconstructed or guessed. UUID is opaque: callers cannot construct a valid ID from external data. This satisfies R3 ("ids unique/opaque").
